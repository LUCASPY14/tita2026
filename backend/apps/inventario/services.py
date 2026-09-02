"""
Servicios de dominio para inventario
Lógica de negocio centralizada y reutilizable
"""

from decimal import Decimal
from typing import Dict, List

from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.productos.models import Producto

from .models import MovimientoStock, Stock


class TipoAlertaStock(models.TextChoices):
    STOCK_MINIMO = "STOCK_MINIMO", "Stock bajo el mínimo"
    STOCK_CERO = "STOCK_CERO", "Stock agotado"
    STOCK_CRITICO = "STOCK_CRITICO", "Stock crítico (50% del mínimo)"


class StockService:
    """
    Servicio centralizado para operaciones de stock.

    Ventajas:
    - Lógica reutilizable desde cualquier punto (API, admin, scripts)
    - Validaciones consistentes
    - Manejo de concurrencia con select_for_update()
    - Transacciones ACID garantizadas
    """

    @staticmethod
    def validar_disponibilidad(producto_id: int, cantidad_solicitada: Decimal) -> Dict:
        """
        Valida si hay stock disponible para una operación.

        Returns:
            dict con: disponible, stock_actual, faltante, mensaje, permite_negativo
        Raises:
            ValidationError: Si el producto no existe
        """
        try:
            producto = Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist:
            raise ValidationError(f"Producto ID {producto_id} no existe")

        try:
            stock = Stock.objects.get(producto=producto)
            stock_actual = stock.cantidad
        except Stock.DoesNotExist:
            stock_actual = Decimal("0.000")

        if producto.permite_stock_negativo:
            return {
                "disponible": True,
                "stock_actual": stock_actual,
                "faltante": Decimal("0.000"),
                "mensaje": "Stock disponible (permite negativo)",
                "permite_negativo": True,
            }

        disponible = stock_actual >= cantidad_solicitada
        faltante = max(cantidad_solicitada - stock_actual, Decimal("0.000"))

        return {
            "disponible": disponible,
            "stock_actual": stock_actual,
            "faltante": faltante,
            "mensaje": (
                "Stock disponible"
                if disponible
                else f"Stock insuficiente. Faltan {faltante} unidades"
            ),
            "permite_negativo": False,
        }

    @staticmethod
    def validar_disponibilidad_multiple(items: List[Dict]) -> Dict:
        """
        Valida disponibilidad para múltiples productos.

        Args:
            items: Lista de dict con {'producto_id': int, 'cantidad': Decimal}
        """
        # Pre-fetch todos los productos para evitar N+1
        ids = [item["producto_id"] for item in items]
        productos_map = {p.pk: p for p in Producto.objects.filter(pk__in=ids)}

        resultados = []
        productos_faltantes = []

        for item in items:
            resultado = StockService.validar_disponibilidad(item["producto_id"], item["cantidad"])
            producto = productos_map.get(item["producto_id"])
            if producto:
                resultado["producto"] = {
                    "id": producto.pk,
                    "descripcion": producto.descripcion,
                    "codigo_barra": producto.codigo_barra,
                }
            resultados.append(resultado)
            if not resultado["disponible"]:
                productos_faltantes.append(resultado)

        return {
            "todo_disponible": len(productos_faltantes) == 0,
            "items": resultados,
            "productos_faltantes": productos_faltantes,
        }

    @staticmethod
    @transaction.atomic
    def reservar_stock(
        producto_id: int,
        cantidad: Decimal,
        autorizado_por,
        motivo: str = MovimientoStock.Motivo.VENTA,
    ) -> Stock:
        """
        Descuenta stock con bloqueo pesimista (select_for_update).

        Raises:
            ValidationError: Si no hay stock o cantidad inválida
        """
        if cantidad <= 0:
            raise ValidationError({
                "error": "La cantidad debe ser mayor a 0",
                "cantidad": str(cantidad),
            })

        # Validación sin lock (respuesta temprana antes de adquirir el lock)
        validacion = StockService.validar_disponibilidad(producto_id, cantidad)
        if not validacion["disponible"]:
            raise ValidationError({
                "error": "Stock insuficiente",
                "producto_id": producto_id,
                "stock_actual": str(validacion["stock_actual"]),
                "cantidad_solicitada": str(cantidad),
                "faltante": str(validacion["faltante"]),
            })

        producto = Producto.objects.get(pk=producto_id)

        stock, _ = Stock.objects.get_or_create(
            producto=producto,
            defaults={"cantidad": Decimal("0.000")},
        )
        # Re-fetch con lock dentro de la transacción activa
        stock = Stock.objects.select_for_update().get(pk=stock.pk)

        # Segunda validación con datos bloqueados (estado puede haber cambiado)
        if not producto.permite_stock_negativo and stock.cantidad < cantidad:
            raise ValidationError({
                "error": "Stock insuficiente (verificación con lock)",
                "stock_actual": str(stock.cantidad),
                "cantidad_solicitada": str(cantidad),
            })

        stock.cantidad -= cantidad
        stock.save()

        MovimientoStock.objects.create(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=motivo,
            cantidad=cantidad,
            stock_resultante=stock.cantidad,
            autorizado_por=autorizado_por,
        )

        return stock

    @staticmethod
    def obtener_productos_bajo_stock() -> List[Dict]:
        """Retorna productos con stock por debajo del mínimo."""
        from django.db.models import F

        productos = (
            Producto.objects
            .filter(stock__cantidad__lte=F("stock_minimo"), activo=True)
            .select_related("stock")
            .order_by("stock__cantidad")
        )

        resultado = []
        for producto in productos:
            try:
                stock_actual = producto.stock.cantidad
            except Stock.DoesNotExist:
                stock_actual = Decimal("0.000")

            resultado.append({
                "producto_id": producto.pk,
                "descripcion": producto.descripcion,
                "codigo_barra": producto.codigo_barra,
                "stock_actual": stock_actual,
                "stock_minimo": producto.stock_minimo,
                "faltante": producto.stock_minimo - stock_actual,
                "critico": stock_actual == 0,
            })

        return resultado

    @staticmethod
    def calcular_valor_inventario() -> Dict:
        """Calcula el valor total del inventario (costo promedio × cantidad)."""
        stocks = Stock.objects.select_related("producto").all()

        valor_total = Decimal("0")
        productos_detalle = []

        for stock in stocks:
            valor_producto = stock.valor_inventario
            valor_total += valor_producto
            productos_detalle.append({
                "producto": stock.producto.descripcion,
                "cantidad": stock.cantidad,
                "costo_promedio": stock.costo_promedio,
                "valor_total": valor_producto,
            })

        return {
            "valor_total": valor_total,
            "cantidad_productos": len(productos_detalle),
            "productos": sorted(
                productos_detalle, key=lambda x: x["valor_total"], reverse=True
            ),
        }

    @staticmethod
    def obtener_rotacion_inventario(dias: int = 30) -> List[Dict]:
        """Calcula rotación de inventario de los últimos N días."""
        from datetime import timedelta

        from django.db.models import Avg, Sum
        from django.utils import timezone

        fecha_desde = timezone.now() - timedelta(days=dias)

        movimientos_venta = (
            MovimientoStock.objects
            .filter(
                tipo=MovimientoStock.Tipo.EGRESO,
                motivo=MovimientoStock.Motivo.VENTA,
                fecha__gte=fecha_desde,
            )
            .values("producto")
            .annotate(
                total_vendido=Sum("cantidad"),
                stock_promedio=Avg("stock_resultante"),
            )
        )

        resultado = []
        for mov in movimientos_venta:
            try:
                producto = Producto.objects.get(pk=mov["producto"])
            except Producto.DoesNotExist:
                continue

            stock_promedio = mov["stock_promedio"] or Decimal("1.000")
            rotacion = (
                mov["total_vendido"] / stock_promedio
                if stock_promedio > 0
                else Decimal("0.00")
            )

            resultado.append({
                "producto": producto.descripcion,
                "total_vendido": mov["total_vendido"],
                "stock_promedio": stock_promedio,
                "rotacion": rotacion,
                "dias_stock": (
                    int(stock_promedio / (mov["total_vendido"] / dias))
                    if mov["total_vendido"] > 0
                    else 999
                ),
            })

        return sorted(resultado, key=lambda x: x["rotacion"], reverse=True)

    @staticmethod
    def ajustar_stock(
        producto: Producto,
        cantidad: Decimal,
        tipo: str,
        motivo: str,
        autorizado_por,
        ajuste=None,
        observaciones: str = "",
    ) -> MovimientoStock:
        """
        Aplica un ingreso o egreso de stock con bloqueo pesimista y registra
        el MovimientoStock correspondiente. Debe llamarse dentro de una
        transacción atómica del caller (ej. el flujo de aprobación de un
        AjusteInventario).

        Raises:
            ValidationError: Si es egreso, el producto no permite stock
                negativo y no hay suficiente cantidad disponible.
        """
        stock, _ = Stock.objects.get_or_create(
            producto=producto,
            defaults={"cantidad": Decimal("0.000")},
        )
        stock = Stock.objects.select_for_update().get(pk=stock.pk)

        es_ingreso = tipo == MovimientoStock.Tipo.INGRESO
        if not es_ingreso and not producto.permite_stock_negativo and stock.cantidad < cantidad:
            raise ValidationError({
                "error": f"Stock insuficiente para {producto.descripcion}.",
                "disponible": str(stock.cantidad),
                "requerido": str(cantidad),
            })

        stock.cantidad += cantidad if es_ingreso else -cantidad
        stock.save()

        return MovimientoStock.objects.create(
            producto=producto,
            tipo=tipo,
            motivo=motivo,
            cantidad=cantidad,
            stock_resultante=stock.cantidad,
            ajuste=ajuste,
            autorizado_por=autorizado_por,
            observaciones=observaciones,
        )

    @staticmethod
    def calcular_alertas_stock(search: str = None) -> List[Dict]:
        """
        Única fuente de verdad para "qué productos están bajo el stock
        mínimo ahora mismo", calculada en vivo contra Stock. La usan la
        pantalla de Inventario, el Dashboard, el WebSocket de KPIs y la
        notificación diaria a ADMIN — evita que cada consumidor tenga su
        propio criterio y terminen mostrando números distintos entre sí.
        """
        stocks = (
            Stock.objects
            .select_related("producto")
            .filter(
                producto__stock_minimo__gt=0,
                producto__requiere_stock=True,
                cantidad__lte=models.F("producto__stock_minimo"),
            )
        )
        if search:
            stocks = stocks.filter(producto__descripcion__icontains=search)

        alertas = []
        for i, s in enumerate(stocks):
            minimo = s.producto.stock_minimo
            if s.cantidad <= 0:
                tipo = TipoAlertaStock.STOCK_CERO
            elif minimo and s.cantidad <= minimo * Decimal("0.5"):
                tipo = TipoAlertaStock.STOCK_CRITICO
            else:
                tipo = TipoAlertaStock.STOCK_MINIMO

            alertas.append({
                "id": i + 1,
                "producto": s.producto_id,
                "producto_nombre": s.producto.descripcion,
                "tipo": tipo,
                "stock_actual": s.cantidad,
                "stock_minimo": minimo,
            })
        return alertas
