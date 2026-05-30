"""
Servicios de negocio para compras
"""

from decimal import Decimal

from django.db import models, transaction

from rest_framework.exceptions import ValidationError

from apps.inventario.models import Stock, MovimientoStock, CostoHistorico
from .models import (
    Proveedor,
    CuentaCorrienteProveedor,
    Compra,
    DetalleCompra,
)


class CompraService:
    """Servicio para registrar y confirmar compras."""

    @staticmethod
    def validar_items(items: list) -> list:
        """Valida los items antes de registrar la compra."""
        errores = []
        productos_vistos = set()

        if not items:
            return [{"error": "La compra debe tener al menos un producto."}]

        for idx, item in enumerate(items):
            producto = item.get("producto")
            cantidad = item.get("cantidad", 0)
            costo = item.get("costo_unitario", 0)

            if not producto:
                errores.append({"linea": idx + 1, "error": "Producto no especificado."})
                continue

            if not producto.activo:
                errores.append({
                    "linea": idx + 1,
                    "producto": producto.descripcion,
                    "error": "El producto esta inactivo.",
                })

            if cantidad <= 0:
                errores.append({
                    "linea": idx + 1,
                    "producto": producto.descripcion,
                    "error": "La cantidad debe ser mayor a 0.",
                })

            if costo <= 0:
                errores.append({
                    "linea": idx + 1,
                    "producto": producto.descripcion,
                    "error": "El costo unitario debe ser mayor a 0.",
                })

            if producto.pk in productos_vistos:
                errores.append({
                    "linea": idx + 1,
                    "producto": producto.descripcion,
                    "error": "Producto duplicado en la compra.",
                })

            productos_vistos.add(producto.pk)

        return errores

    @staticmethod
    def _actualizar_stock_y_costos(compra, autorizado_por):
        """Actualiza stock, movimientos y costos para una compra (uso interno)."""
        detalles = compra.detalles.select_related("producto").all()
        if not detalles.exists():
            raise ValidationError({"error": "La compra no tiene productos."})

        for detalle in detalles:
            producto = detalle.producto
            cantidad = detalle.cantidad
            costo = detalle.costo_unitario

            stock, _ = Stock.objects.select_for_update().get_or_create(
                producto=producto,
                defaults={"cantidad": Decimal("0")},
            )
            stock.cantidad = models.F("cantidad") + cantidad
            stock.save()
            stock.refresh_from_db()

            MovimientoStock.objects.create(
                producto=producto,
                tipo=MovimientoStock.Tipo.INGRESO,
                motivo=MovimientoStock.Motivo.COMPRA,
                cantidad=cantidad,
                stock_resultante=stock.cantidad,
                compra=compra,
                autorizado_por=autorizado_por,
            )

            CostoHistorico.objects.create(
                producto=producto,
                compra=compra,
                costo_unitario=costo,
                cantidad_comprada=cantidad,
                fecha_compra=compra.fecha,
            )

    @staticmethod
    def registrar_compra(
        *,
        proveedor,
        creado_por,
        tipo_pago: str = "CONTADO",
        medio_pago=None,
        items: list = None,
        nro_factura_proveedor: str = "",
        observaciones: str = "",
    ) -> Compra:
        """
        Registra una compra con sus detalles.
        Para compras CONTADO: actualiza stock inmediatamente.
        Para compras CREDITO: queda pendiente de confirmacion de entrega.
        """
        errores = CompraService.validar_items(items or [])
        if errores:
            raise ValidationError({"errores": errores})

        with transaction.atomic():
            monto_total = Decimal("0")
            detalles_data = []

            for item in items:
                producto = item["producto"]
                cantidad = item["cantidad"]
                costo = item["costo_unitario"]
                subtotal = cantidad * costo
                monto_total += subtotal

                detalles_data.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "costo_unitario": costo,
                    "subtotal": subtotal,
                })

            compra = Compra.objects.create(
                proveedor=proveedor,
                creado_por=creado_por,
                tipo_pago=tipo_pago,
                medio_pago=medio_pago,
                monto_total=monto_total,
                nro_factura_proveedor=nro_factura_proveedor,
                observaciones=observaciones,
                estado_pago="PAGADO" if tipo_pago == "CONTADO" else "PENDIENTE",
                estado_entrega=(
                    Compra.EstadoEntrega.RECIBIDA if tipo_pago == "CONTADO"
                    else Compra.EstadoEntrega.PENDIENTE
                ),
            )

            for det in detalles_data:
                DetalleCompra.objects.create(compra=compra, **det)

            # Compras CONTADO: actualizar stock inmediatamente
            if tipo_pago == "CONTADO":
                CompraService._actualizar_stock_y_costos(compra, creado_por)

            # Compras CREDITO: registrar en cuenta corriente
            if tipo_pago == "CREDITO":
                # Bloquear fila del proveedor para serializar el acceso a su CC,
                # incluso cuando no existen movimientos previos (ultimo_cc sería None).
                Proveedor.objects.select_for_update().get(pk=proveedor.pk)
                ultimo_cc = (
                    CuentaCorrienteProveedor.objects
                    .filter(proveedor=proveedor)
                    .select_for_update()
                    .order_by("-id")
                    .first()
                )
                saldo_anterior = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")
                CuentaCorrienteProveedor.objects.create(
                    proveedor=proveedor,
                    tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
                    monto=monto_total,
                    saldo_anterior=saldo_anterior,
                    saldo_resultante=saldo_anterior + monto_total,
                    compra=compra,
                    descripcion=f"Compra #{compra.pk}",
                    creado_por=creado_por,
                )

            return compra

    @staticmethod
    def confirmar_compra(compra, autorizado_por) -> Compra:
        """
        Confirma la recepcion de mercaderia de una compra a credito.
        Actualiza stock, movimientos y costos.
        NO cambia estado_pago (sigue PENDIENTE hasta que se pague).
        """
        with transaction.atomic():
            compra = Compra.objects.select_for_update().get(pk=compra.pk)

            if compra.estado_entrega != Compra.EstadoEntrega.PENDIENTE:
                raise ValidationError({
                    "error": "La mercaderia de esta compra ya fue recibida.",
                    "estado_entrega": compra.estado_entrega,
                })

            CompraService._actualizar_stock_y_costos(compra, autorizado_por)
            compra.estado_entrega = Compra.EstadoEntrega.RECIBIDA
            compra.save()

            return compra