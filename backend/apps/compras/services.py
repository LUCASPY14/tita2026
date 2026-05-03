"""
Servicios de dominio para compras
Lógica de negocio centralizada y reutilizable
"""

from decimal import Decimal
from typing import Dict, List

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.inventario.models import CostosHistoricos, MovimientosStock, StockUnico
from apps.productos.models import Productos
from apps.usuarios.models import Empleados

from .models import Compras, DetallesCompra, Proveedores


class CompraService:
    """
    Servicio centralizado para operaciones de compras.

    Ventajas:
    - Lógica reutilizable desde cualquier punto (API, admin, scripts)
    - Validaciones consistentes antes de confirmar compras
    - Manejo transaccional garantizado
    - Auditoría completa
    """

    @staticmethod
    def validar_compra(detalles_compra: List[Dict]) -> Dict:
        """
        Valida coherencia de una compra antes de confirmarla.

        Validaciones:
        1. Cantidad > 0 para todos los productos
        2. Precio > 0 para todos los productos
        3. Productos existen y están activos
        4. No hay duplicados en la misma compra

        Args:
            detalles_compra: Lista de dict con:
                - id_producto: int
                - cantidad: Decimal
                - precio_unitario: Decimal

        Returns:
            dict con:
                - valido: bool
                - errores: lista de errores encontrados
                - warnings: lista de advertencias

        Ejemplo:
            >>> detalles = [
            ...     {'id_producto': 1, 'cantidad': 10, 'precio_unitario': 5000},
            ...     {'id_producto': 2, 'cantidad': 0, 'precio_unitario': 3000}  # ERROR
            ... ]
            >>> resultado = CompraService.validar_compra(detalles)
            >>> resultado['valido']
            False
        """
        errores = []
        warnings = []
        productos_vistos = set()

        if not detalles_compra or len(detalles_compra) == 0:
            errores.append({"campo": "detalles", "mensaje": "La compra debe tener al menos un producto"})
            return {"valido": False, "errores": errores, "warnings": warnings}

        for idx, detalle in enumerate(detalles_compra):
            producto_id = detalle.get("id_producto")
            cantidad = detalle.get("cantidad")
            precio_unitario = detalle.get("costo_unitario") or detalle.get("precio_unitario")

            # Convertir a Decimal si vienen como strings
            if isinstance(cantidad, str):
                try:
                    cantidad = Decimal(cantidad)
                except (ValueError, TypeError):
                    cantidad = None

            if isinstance(precio_unitario, str):
                try:
                    precio_unitario = Decimal(precio_unitario)
                except (ValueError, TypeError):
                    precio_unitario = None

            # Validar producto existe
            try:
                producto = Productos.objects.get(id_producto=producto_id)

                # Advertencia si producto inactivo
                if not producto.estado:
                    warnings.append(
                        {
                            "producto_id": producto_id,
                            "producto": producto.descripcion,
                            "mensaje": "El producto está marcado como inactivo",
                        }
                    )

            except Productos.DoesNotExist:
                errores.append(
                    {
                        "linea": idx + 1,
                        "producto_id": producto_id,
                        "mensaje": f"El producto ID {producto_id} no existe",
                    }
                )
                continue

            # Validar cantidad > 0
            if not cantidad or cantidad <= 0:
                errores.append(
                    {
                        "linea": idx + 1,
                        "producto": producto.descripcion,
                        "campo": "cantidad",
                        "mensaje": "La cantidad debe ser mayor a 0",
                    }
                )

            # Validar precio > 0
            if not precio_unitario or precio_unitario <= 0:
                errores.append(
                    {
                        "linea": idx + 1,
                        "producto": producto.descripcion,
                        "campo": "costo_unitario",
                        "mensaje": "El costo unitario debe ser mayor a 0",
                    }
                )

            # Validar no hay duplicados
            if producto_id in productos_vistos:
                errores.append(
                    {
                        "linea": idx + 1,
                        "producto": producto.descripcion,
                        "mensaje": f"El producto aparece duplicado en la compra (línea {idx + 1})",
                    }
                )

            productos_vistos.add(producto_id)

        return {"valido": len(errores) == 0, "errores": errores, "warnings": warnings}

    @staticmethod
    @transaction.atomic
    def confirmar_compra(id_compra: int, empleado) -> Compras:
        """
        Confirma una compra de manera transaccional.

        Flujo:
        1. Valida estado (solo 'Pendiente' → 'Confirmado')
        2. Actualiza inventario (trigger signal actualizar_stock_compra)
        3. Registra en cuenta corriente proveedor
        4. Cambia estado a 'Confirmado'

        Args:
            id_compra: ID de la compra a confirmar
            empleado: Empleado que autoriza la confirmación

        Returns:
            Compras: Instancia de la compra confirmada

        Raises:
            ValidationError: Si la compra no existe o no está en estado Pendiente
        """
        try:
            compra = Compras.objects.select_for_update().get(id_compra=id_compra)
        except Compras.DoesNotExist:
            raise ValidationError({"error": "Compra no encontrada", "id_compra": id_compra})

        # Validar estado
        if compra.estado_pago != "Pendiente":
            return {
                "exito": False,
                "error": "Solo se pueden confirmar compras en estado Pendiente",
                "estado_actual": compra.estado_pago,
                "id_compra": id_compra,
            }

        # Validar detalles
        detalles = DetallesCompra.objects.filter(id_compra=compra)
        if not detalles.exists():
            return {
                "exito": False,
                "error": "La compra no tiene productos asociados",
                "id_compra": id_compra,
            }

        # Obtener empleado autorizador: el que se pasa, o el primero activo del sistema
        empleado_autoriza = empleado
        if empleado_autoriza is None:
            empleado_autoriza = Empleados.objects.filter(estado=True).first()
        if empleado_autoriza is None:
            return {
                "exito": False,
                "error": "No hay empleados registrados en el sistema para autorizar el movimiento",
                "id_compra": id_compra,
            }

        # Actualizar inventario por cada detalle
        for detalle in detalles:
            producto = detalle.id_producto
            cantidad = detalle.cantidad
            costo = detalle.costo_unitario

            # Obtener o crear registro de stock
            stock, _ = StockUnico.objects.select_for_update().get_or_create(
                id_producto=producto,
                defaults={"cantidad": Decimal("0.000")},
            )

            nuevo_stock = stock.cantidad + cantidad
            stock.cantidad = nuevo_stock
            stock.save()

            # Registrar movimiento de stock
            MovimientosStock.objects.create(
                tipo_movimiento="Ingreso",
                motivo="compra",
                cantidad=cantidad,
                stock_resultante=nuevo_stock,
                observaciones=f"Compra #{compra.id_compra} - Factura {compra.nro_factura or 'S/N'}",
                id_compra=compra,
                id_producto=producto,
                id_empleado_autoriza=empleado_autoriza,
            )

            # Registrar costo histórico para costo promedio ponderado
            CostosHistoricos.objects.create(
                costo_unitario=costo,
                cantidad_comprada=cantidad,
                fecha_compra=compra.fecha,
                id_compra=compra,
                id_producto=producto,
            )

        # Confirmar compra
        compra.estado_pago = "Confirmado"
        compra.save()

        return {"exito": True, "compra": compra, "id_compra": id_compra}

    @staticmethod
    def calcular_totales_compra(detalles_compra: List[Dict]) -> Dict:
        """
        Calcula los totales de una compra.

        Args:
            detalles_compra: Lista de dict con cantidad y precio_unitario

        Returns:
            dict con:
                - subtotal: Decimal (antes de IVA)
                - iva_5: Decimal
                - iva_10: Decimal
                - total: Decimal
        """
        subtotal = Decimal("0.00")
        iva_5 = Decimal("0.00")
        iva_10 = Decimal("0.00")

        for detalle in detalles_compra:
            cantidad = Decimal(str(detalle.get("cantidad", 0)))
            precio = Decimal(str(detalle.get("costo_unitario") or detalle.get("precio_unitario", 0)))
            subtotal_linea = cantidad * precio

            # Obtener tipo de IVA del producto
            try:
                producto = Productos.objects.select_related("id_impuesto").get(id_producto=detalle["id_producto"])
                porcentaje_iva = producto.id_impuesto.porcentaje

                if porcentaje_iva == Decimal("5.00"):
                    iva_5 += subtotal_linea * Decimal("0.05")
                elif porcentaje_iva == Decimal("10.00"):
                    iva_10 += subtotal_linea * Decimal("0.10")
                # Exento (0.00) no suma IVA

            except Productos.DoesNotExist:
                pass

            subtotal += subtotal_linea

        total = subtotal + iva_5 + iva_10

        return {
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "iva_5": iva_5.quantize(Decimal("0.01")),
            "iva_10": iva_10.quantize(Decimal("0.01")),
            "total": total.quantize(Decimal("0.01")),
        }

    @staticmethod
    def obtener_compras_pendientes_confirmacion() -> List[Compras]:
        """
        Retorna lista de compras pendientes de confirmación.

        Returns:
            QuerySet de Compras con estado_pago='Pendiente'
        """
        return Compras.objects.filter(estado_pago="Pendiente").select_related("id_proveedor").order_by("fecha")

    @staticmethod
    def obtener_cuenta_corriente_proveedor(id_proveedor: int) -> Dict:
        """
        Obtiene el estado de cuenta corriente con un proveedor.

        Args:
            id_proveedor: ID del proveedor

        Returns:
            dict con:
                - total_compras: Monto total de compras
                - total_pagado: Monto total pagado
                - saldo_pendiente: Saldo por pagar
                - compras_pendientes: Lista de compras con saldo
        """
        from django.db.models import Sum

        from .models import AplicacionPagosCompras

        # Total de compras (todas las compras del proveedor)
        compras = Compras.objects.filter(id_proveedor=id_proveedor)

        total_compras = compras.aggregate(total=Sum("monto_total"))["total"] or Decimal("0.00")

        # Total pagado
        total_pagado = compras.aggregate(pagado=Sum("monto_total") - Sum("saldo_pendiente"))["pagado"] or Decimal(
            "0.00"
        )

        # Saldo pendiente total
        saldo_pendiente = compras.aggregate(saldo=Sum("saldo_pendiente"))["saldo"] or Decimal("0.00")

        # Compras con saldo pendiente
        compras_pendientes = []
        for compra in compras.filter(saldo_pendiente__gt=0):
            compras_pendientes.append(
                {
                    "id_compra": compra.id_compra,
                    "fecha": compra.fecha,
                    "nro_factura": compra.nro_factura,
                    "monto_total": str(compra.monto_total),
                    "saldo_pendiente": str(compra.saldo_pendiente),
                    "dias_vencimiento": ((timezone.now().date() - compra.fecha.date()).days if compra.fecha else None),
                }
            )

        return {
            "total_compras": total_compras,
            "total_pagado": total_pagado,
            "saldo_pendiente": saldo_pendiente,
            "cantidad_compras": compras.count(),
            "cantidad_pendientes": len(compras_pendientes),
            "compras_pendientes": compras_pendientes,
        }
