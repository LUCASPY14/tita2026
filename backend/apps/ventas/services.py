"""
Servicios de dominio para el módulo de ventas.
Contiene la lógica de negocio para promociones y devoluciones.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError as DRFValidationError


class PromocionService:
    """
    Servicio centralizado para aplicar promociones y descuentos.

    Responsabilidades:
    - Validar vigencia de promociones (fecha, hora, día de semana)
    - Calcular descuentos según tipo de promoción
    - Aplicar promociones a ventas
    - Registrar historial de promociones aplicadas
    """

    @staticmethod
    def obtener_promociones_aplicables(
        items: List[Dict],
        monto_total: Decimal,
        cliente_id: Optional[int] = None,
        codigo_promocion: Optional[str] = None,
        fecha_hora: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Obtiene promociones aplicables según contexto de venta.

        Args:
            items: Lista de {'id_producto': int, 'cantidad': Decimal, 'precio': Decimal}
            monto_total: Monto total antes de descuentos
            cliente_id: ID del cliente (para verificar límite de usos)
            codigo_promocion: Código ingresado por el usuario
            fecha_hora: Momento de la venta (default: now)

        Returns:
            Lista de promociones aplicables ordenadas por prioridad
        """
        from apps.ventas.models import Promociones, PromocionesAplicadas

        if fecha_hora is None:
            fecha_hora = timezone.now()

        # 1. Filtrar promociones activas y vigentes
        promociones_query = Promociones.objects.filter(estado=True, fecha_inicio__lte=fecha_hora.date()).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=fecha_hora.date())
        )

        # 2. Si hay código, filtrar por código
        if codigo_promocion:
            promociones_query = promociones_query.filter(codigo_promocion__iexact=codigo_promocion)
        else:
            # Solo promociones sin código requerido
            promociones_query = promociones_query.filter(requiere_codigo=False)

        promociones_aplicables = []

        for promo in promociones_query:
            # 3. Validar vigencia horaria
            if not PromocionService._validar_horario(promo, fecha_hora):
                continue

            # 4. Validar días de semana
            if not PromocionService._validar_dia_semana(promo, fecha_hora):
                continue

            # 5. Validar monto mínimo
            if monto_total < promo.monto_minimo:
                continue

            # 6. Validar límite de usos totales
            if promo.max_usos_total and promo.usos_actuales >= promo.max_usos_total:
                continue

            # 7. Validar usos por cliente
            if cliente_id and promo.max_usos_cliente:
                usos_cliente = PromocionesAplicadas.objects.filter(
                    id_promocion=promo, id_venta__id_cliente_id=cliente_id
                ).count()

                if usos_cliente >= promo.max_usos_cliente:
                    continue

            # 8. Validar alcance (producto/categoría)
            if not PromocionService._validar_alcance(promo, items):
                continue

            promociones_aplicables.append({"promocion": promo, "prioridad": promo.prioridad})

        # 9. Ordenar por prioridad (menor número = mayor prioridad)
        return sorted(promociones_aplicables, key=lambda x: x["prioridad"])

    @staticmethod
    def calcular_descuento(promocion, items: List[Dict], monto_total: Decimal) -> Dict:
        """
        Calcula el descuento de una promoción específica.

        Args:
            promocion: Instancia de Promociones
            items: Lista de productos en la venta
            monto_total: Monto total antes de descuentos

        Returns:
            {
                'monto_descuento': Decimal,
                'tipo_descuento': str,
                'productos_afectados': List[int],
                'descripcion': str
            }
        """
        if promocion.tipo_promocion == "porcentaje":
            # Descuento porcentual
            descuento = monto_total * (promocion.valor_descuento / 100)
            return {
                "monto_descuento": descuento.quantize(Decimal("0.01")),
                "tipo_descuento": "porcentaje",
                "productos_afectados": PromocionService._obtener_productos_afectados(promocion, items),
                "descripcion": f"{promocion.valor_descuento}% de descuento",
            }

        elif promocion.tipo_promocion == "monto_fijo":
            # Descuento de monto fijo
            return {
                "monto_descuento": promocion.valor_descuento,
                "tipo_descuento": "monto_fijo",
                "productos_afectados": [],
                "descripcion": f"Gs. {promocion.valor_descuento:,.0f} de descuento",
            }

        elif promocion.tipo_promocion == "2x1":
            # 2x1 (paga 1, lleva 2)
            descuento_2x1 = PromocionService._calcular_2x1(promocion, items)
            return {
                "monto_descuento": descuento_2x1,
                "tipo_descuento": "2x1",
                "productos_afectados": PromocionService._obtener_productos_afectados(promocion, items),
                "descripcion": "2x1 aplicado",
            }

        elif promocion.tipo_promocion == "combo":
            # Precio especial por combo
            descuento_combo = PromocionService._calcular_combo(promocion, items)
            return {
                "monto_descuento": descuento_combo,
                "tipo_descuento": "combo",
                "productos_afectados": PromocionService._obtener_productos_afectados(promocion, items),
                "descripcion": "Combo especial",
            }

        return {
            "monto_descuento": Decimal("0.00"),
            "tipo_descuento": "ninguno",
            "productos_afectados": [],
            "descripcion": "Tipo de promoción no implementado",
        }

    @staticmethod
    @transaction.atomic
    def aplicar_promociones_a_venta(venta, promociones_seleccionadas: List, empleado) -> Dict:
        """
        Aplica las promociones a una venta y registra en historial.

        Args:
            venta: Instancia de Ventas
            promociones_seleccionadas: Lista de tuplas (promocion, descuento_calculado)
            empleado: Empleado que procesa

        Returns:
            {
                'monto_total_descuentos': Decimal,
                'promociones_aplicadas': List[PromocionesAplicadas],
                'detalle': str
            }
        """
        from apps.ventas.models import PromocionesAplicadas

        total_descuentos = Decimal("0.00")
        aplicaciones = []

        for promocion, descuento_info in promociones_seleccionadas:
            # Registrar aplicación
            aplicacion = PromocionesAplicadas.objects.create(
                monto_descontado=descuento_info["monto_descuento"],
                fecha_aplicacion=timezone.now(),
                id_promocion=promocion,
                id_venta=venta,
            )

            # Incrementar contador de usos
            promocion.usos_actuales += 1
            promocion.save()

            total_descuentos += descuento_info["monto_descuento"]
            aplicaciones.append(aplicacion)

        return {
            "monto_total_descuentos": total_descuentos,
            "promociones_aplicadas": aplicaciones,
            "detalle": f"{len(aplicaciones)} promoción(es) aplicada(s)",
        }

    # Métodos privados auxiliares

    @staticmethod
    def _validar_horario(promocion, fecha_hora: datetime) -> bool:
        """Valida si la promoción está vigente en el horario actual"""
        if promocion.hora_inicio is None and promocion.hora_fin is None:
            return True  # Sin restricción horaria

        hora_actual = fecha_hora.time()

        if promocion.hora_inicio and hora_actual < promocion.hora_inicio:
            return False

        if promocion.hora_fin and hora_actual > promocion.hora_fin:
            return False

        return True

    @staticmethod
    def _validar_dia_semana(promocion, fecha_hora: datetime) -> bool:
        """Valida si la promoción aplica el día de hoy"""
        if not promocion.dias_semana:
            return True  # Sin restricción de días

        dia_actual = fecha_hora.isoweekday()  # 1=lunes, 7=domingo
        return dia_actual in promocion.dias_semana

    @staticmethod
    def _validar_alcance(promocion, items: List[Dict]) -> bool:
        """Valida si los productos cumplen el alcance de la promoción"""
        from apps.productos.models import Productos
        from apps.ventas.models import CategoriasPromocion, ProductosPromocion

        if promocion.aplica_a == "total":
            return True  # Aplica a cualquier compra

        if promocion.aplica_a == "producto":
            # Verificar si algún producto está en la promoción
            productos_promo = set(
                ProductosPromocion.objects.filter(id_promocion=promocion).values_list("id_producto", flat=True)
            )

            productos_venta = set(item["id_producto"] for item in items)
            return bool(productos_promo & productos_venta)  # Intersección

        if promocion.aplica_a == "categoria":
            # Verificar si alguna categoría está en la promoción
            categorias_promo = set(
                CategoriasPromocion.objects.filter(id_promocion=promocion).values_list("id_categoria", flat=True)
            )

            for item in items:
                producto = Productos.objects.get(id_producto=item["id_producto"])
                if producto.id_categoria_id in categorias_promo:
                    return True

            return False

        return False

    @staticmethod
    def _obtener_productos_afectados(promocion, items: List[Dict]) -> List[int]:
        """Retorna IDs de productos afectados por la promoción"""
        from apps.productos.models import Productos
        from apps.ventas.models import CategoriasPromocion, ProductosPromocion

        if promocion.aplica_a == "total":
            return [item["id_producto"] for item in items]

        if promocion.aplica_a == "producto":
            productos_promo = set(
                ProductosPromocion.objects.filter(id_promocion=promocion).values_list("id_producto", flat=True)
            )
            return [item["id_producto"] for item in items if item["id_producto"] in productos_promo]

        if promocion.aplica_a == "categoria":
            categorias_promo = set(
                CategoriasPromocion.objects.filter(id_promocion=promocion).values_list("id_categoria", flat=True)
            )

            afectados = []
            for item in items:
                producto = Productos.objects.get(id_producto=item["id_producto"])
                if producto.id_categoria_id in categorias_promo:
                    afectados.append(item["id_producto"])

            return afectados

        return []

    @staticmethod
    def _calcular_2x1(promocion, items: List[Dict]) -> Decimal:
        """Calcula descuento para promoción 2x1"""
        productos_aplicables = PromocionService._obtener_productos_afectados(promocion, items)
        descuento_total = Decimal("0.00")

        # Por cada 2 unidades, regala 1 (descuenta el más barato)
        for id_producto in productos_aplicables:
            items_producto = [i for i in items if i["id_producto"] == id_producto]

            for item in items_producto:
                cantidad = int(item["cantidad"])
                precio_unitario = item["precio"]

                # Cada 2 unidades, descuenta 1
                unidades_gratis = cantidad // 2
                descuento_total += unidades_gratis * precio_unitario

        return descuento_total

    @staticmethod
    def _calcular_combo(promocion, items: List[Dict]) -> Decimal:
        """Calcula descuento para combo: todos los productos del combo deben estar en el carrito."""
        from apps.ventas.models import ProductosPromocion

        # Obtener los productos requeridos en el combo
        productos_combo = set(
            ProductosPromocion.objects.filter(id_promocion=promocion).values_list("id_producto", flat=True)
        )

        if not productos_combo:
            # Sin productos definidos: aplicar descuento fijo directo
            return promocion.valor_descuento

        # Verificar que TODOS los productos del combo estén presentes en el carrito
        ids_en_carrito = {item["id_producto"] for item in items}
        if not productos_combo.issubset(ids_en_carrito):
            return Decimal("0.00")

        # Calcular cuántos combos completos se pueden armar
        min_repeticiones = min(int(item["cantidad"]) for item in items if item["id_producto"] in productos_combo)

        return promocion.valor_descuento * min_repeticiones


class DevolucionService:
    """
    Servicio para gestionar devoluciones de clientes.

    Responsabilidades:
    - Validar que la venta puede devolverse
    - Crear notas de crédito
    - Reintegrar stock de productos devueltos
    - Actualizar saldo del cliente
    """

    # Constantes de configuración
    DIAS_LIMITE_DEVOLUCION = 7  # Días máximos para devolver

    @staticmethod
    @transaction.atomic
    def crear_nota_credito(
        id_venta: int,
        productos_devolucion: List[Dict],
        motivo: str,
        empleado_autoriza,
        tipo_devolucion: str = "parcial",
    ) -> Dict:
        """
        Crea nota de crédito por devolución de productos.

        Args:
            id_venta: ID de la venta original
            productos_devolucion: Lista de {'id_producto': int, 'cantidad': Decimal, 'motivo_item': str}
            motivo: Motivo general de la devolución
            empleado_autoriza: Empleado que autoriza
            tipo_devolucion: 'total' o 'parcial'

        Returns:
            {
                'exito': bool,
                'nota_credito': NotasCreditoCliente,
                'monto_devuelto': Decimal,
                'stock_actualizado': bool,
                'mensaje': str
            }

        Raises:
            ValidationError: Si la venta no existe o productos inválidos
        """
        from apps.inventario.models import MovimientosStock, StockUnico
        from apps.productos.models import Productos
        from apps.ventas.models import (
            DetallesNotaCredito,
            DetallesVenta,
            NotasCreditoCliente,
            Ventas,
        )

        # 1. Validar venta existe
        try:
            venta = Ventas.objects.select_for_update().get(id_venta=id_venta)
        except Ventas.DoesNotExist:
            raise DRFValidationError({"error": "Venta no encontrada", "id_venta": id_venta})

        # 2. Validar que no hayan pasado más de X días (política de devolución)
        dias_transcurridos = (timezone.now().date() - venta.fecha.date()).days

        if dias_transcurridos > DevolucionService.DIAS_LIMITE_DEVOLUCION:
            raise DRFValidationError(
                {
                    "error": f"Devolución fuera de plazo (máximo {DevolucionService.DIAS_LIMITE_DEVOLUCION} días)",
                    "dias_transcurridos": dias_transcurridos,
                    "fecha_venta": venta.fecha.date().isoformat(),
                }
            )

        # 3. Validar estado de venta (debe estar confirmada)
        if venta.estado not in ["Activa"]:
            raise DRFValidationError({"error": "Solo se pueden devolver ventas activas", "estado_venta": venta.estado})

        # 4. Validar productos en la venta original
        detalles_venta = DetallesVenta.objects.filter(id_venta=venta)
        productos_venta = {d.id_producto_id: d for d in detalles_venta}

        monto_total_devolucion = Decimal("0.00")
        detalles_nota = []

        for item_dev in productos_devolucion:
            id_producto = item_dev["id_producto"]
            cantidad_dev = Decimal(str(item_dev["cantidad"]))

            # Validar que el producto esté en la venta
            if id_producto not in productos_venta:
                raise DRFValidationError(
                    {
                        "error": f"Producto {id_producto} no está en la venta original",
                        "id_producto": id_producto,
                    }
                )

            # Validar cantidad (no puede devolver más de lo comprado)
            if cantidad_dev > productos_venta[id_producto].cantidad:
                raise DRFValidationError(
                    {
                        "error": f"Cantidad a devolver excede lo comprado",
                        "id_producto": id_producto,
                        "cantidad_comprada": float(productos_venta[id_producto].cantidad),
                        "cantidad_devolucion": float(cantidad_dev),
                    }
                )

            # Obtener precio del detalle original
            detalle_original = productos_venta[id_producto]
            precio_unitario = detalle_original.precio_unitario
            subtotal = cantidad_dev * precio_unitario

            monto_total_devolucion += subtotal

            detalles_nota.append(
                {
                    "id_producto": id_producto,
                    "cantidad": cantidad_dev,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal,
                    "motivo": item_dev.get("motivo_item", ""),
                }
            )

        # 5. Generar número de nota de crédito
        ultimo_nro = NotasCreditoCliente.objects.aggregate(max_nro=models.Max("nro_nota_credito"))["max_nro"] or 0

        nuevo_nro = ultimo_nro + 1

        # 6. Crear nota de crédito
        nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=nuevo_nro,
            fecha_emision=timezone.now(),
            motivo=motivo,
            monto_total=monto_total_devolucion,
            estado="Emitida",
            id_cliente=venta.id_cliente,
            id_empleado_autoriza=empleado_autoriza,
            id_venta_origen=venta,
        )

        # 7. Crear detalles de nota
        for detalle_dict in detalles_nota:
            DetallesNotaCredito.objects.create(
                cantidad=detalle_dict["cantidad"],
                precio_unitario=detalle_dict["precio_unitario"],
                subtotal=detalle_dict["subtotal"],
                id_nota=nota,
                id_producto_id=detalle_dict["id_producto"],
            )

        # 8. Reintegrar stock (si es devolución física)
        for detalle_dict in detalles_nota:
            producto = Productos.objects.get(id_producto=detalle_dict["id_producto"])
            cantidad = detalle_dict["cantidad"]

            # Bloqueo pesimista para evitar condiciones de carrera
            stock, created = StockUnico.objects.select_for_update().get_or_create(
                id_producto=producto, defaults={"cantidad": Decimal("0.000")}
            )

            stock_anterior = stock.cantidad
            stock.cantidad += cantidad  # REINGRESO
            stock.save()

            # Registrar movimiento
            MovimientosStock.objects.create(
                tipo_movimiento="Ingreso",
                motivo="devolucion_cliente",
                cantidad=cantidad,
                stock_resultante=stock.cantidad,
                observaciones=f"Devolución NC #{nuevo_nro} - Venta #{id_venta}",
                id_venta=venta,
                id_empleado_autoriza=empleado_autoriza,
                id_producto=producto,
            )

        # 9. Actualizar saldo de la venta (si venta a crédito)
        if venta.tipo_venta == "Crédito":
            venta.saldo_pendiente = (venta.saldo_pendiente or Decimal("0.00")) - monto_total_devolucion

            if venta.saldo_pendiente <= 0:
                venta.estado_pago = "Pagada"

            venta.save()

        return {
            "exito": True,
            "nota_credito": nota,
            "monto_devuelto": monto_total_devolucion,
            "stock_actualizado": True,
            "mensaje": f"Nota de crédito #{nuevo_nro} creada exitosamente",
        }

    @staticmethod
    @transaction.atomic
    def anular_nota_credito(id_nota: int, empleado_autoriza, motivo_anulacion: str) -> Dict:
        """
        Anula una nota de crédito y revierte el stock.

        Args:
            id_nota: ID de la nota de crédito
            empleado_autoriza: Gerente que autoriza anulación
            motivo_anulacion: Razón de la anulación

        Returns:
            {'exito': bool, 'mensaje': str}
        """
        from apps.inventario.models import MovimientosStock, StockUnico
        from apps.ventas.models import DetallesNotaCredito, NotasCreditoCliente

        try:
            nota = NotasCreditoCliente.objects.select_for_update().get(id_nota=id_nota)
        except NotasCreditoCliente.DoesNotExist:
            raise DRFValidationError({"error": "Nota de crédito no encontrada"})

        if nota.estado == "Anulada":
            raise DRFValidationError({"error": "Nota de crédito ya anulada"})

        # Revertir stock (descontar lo que se reintegró)
        detalles = DetallesNotaCredito.objects.filter(id_nota=nota)

        for detalle in detalles:
            stock = StockUnico.objects.select_for_update().get(id_producto=detalle.id_producto)

            stock.cantidad -= detalle.cantidad  # DESCONTAR
            stock.save()

            # Registrar movimiento de anulación
            MovimientosStock.objects.create(
                tipo_movimiento="Egreso",
                motivo="correccion_manual",
                cantidad=detalle.cantidad,
                stock_resultante=stock.cantidad,
                observaciones=f"Anulación NC #{nota.nro_nota_credito} - {motivo_anulacion}",
                id_empleado_autoriza=empleado_autoriza,
                id_producto=detalle.id_producto,
            )

        # Marcar como anulada
        nota.estado = "Anulada"
        nota.save()

        return {"exito": True, "mensaje": f"Nota de crédito #{nota.nro_nota_credito} anulada"}

    @staticmethod
    def validar_productos_devolucion(id_venta: int, productos: List[Dict]) -> Dict:
        """
        Valida si los productos pueden devolverse.

        Args:
            id_venta: ID de la venta
            productos: Lista de {'id_producto': int, 'cantidad': Decimal}

        Returns:
            {
                'valido': bool,
                'errores': List[str],
                'warnings': List[str]
            }
        """
        from apps.ventas.models import DetallesVenta, Ventas

        errores = []
        warnings = []

        try:
            venta = Ventas.objects.get(id_venta=id_venta)
        except Ventas.DoesNotExist:
            return {"valido": False, "errores": [f"Venta {id_venta} no existe"], "warnings": []}

        detalles_venta = DetallesVenta.objects.filter(id_venta=venta)
        productos_venta = {d.id_producto_id: d for d in detalles_venta}

        for item in productos:
            id_producto = item["id_producto"]
            cantidad = Decimal(str(item["cantidad"]))

            if id_producto not in productos_venta:
                errores.append(f"Producto {id_producto} no está en venta #{id_venta}")
                continue

            if cantidad > productos_venta[id_producto].cantidad:
                errores.append(
                    f"Producto {id_producto}: Cantidad {cantidad} excede lo comprado "
                    f"({productos_venta[id_producto].cantidad})"
                )

        # Validar plazo
        dias = (timezone.now().date() - venta.fecha.date()).days
        if dias > DevolucionService.DIAS_LIMITE_DEVOLUCION:
            warnings.append(f"Venta tiene {dias} días (límite: {DevolucionService.DIAS_LIMITE_DEVOLUCION} días)")

        return {"valido": len(errores) == 0, "errores": errores, "warnings": warnings}
