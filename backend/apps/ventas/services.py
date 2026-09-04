"""
Servicios de negocio para ventas
"""

import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

logger = logging.getLogger(__name__)

from rest_framework.exceptions import ValidationError

from apps.clientes.models import CuentaCorrienteCliente
from apps.inventario.models import Stock, MovimientoStock
from apps.core.models import Tarjeta, MovimientoTarjeta
from .models import Venta, DetalleVenta, PagoVenta, AplicacionPago, NotaCredito, DetalleNotaCredito


def _calcular_iva_producto(producto, subtotal: Decimal) -> dict:
    """
    IVA incluido en el precio, según el impuesto asignado al producto
    (apps.productos.models.ProductoImpuesto) — nunca se confía en un IVA
    que mande el cliente del POS, porque no hay forma de validarlo ahí.
    Sin impuesto asignado (o porcentaje 0) se trata como exenta.
    """
    from apps.productos.models import ProductoImpuesto

    pi = (
        ProductoImpuesto.objects
        .filter(producto=producto, impuesto__activo=True)
        .select_related("impuesto")
        .first()
    )
    if not pi or pi.impuesto.porcentaje == 0:
        return {"monto_exenta": subtotal}
    tasa = pi.impuesto.porcentaje / Decimal("100")
    iva = (subtotal - (subtotal / (1 + tasa))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if pi.impuesto.nombre == "IVA 5%":
        return {"iva_5": iva}
    return {"iva_10": iva}


class VentaService:
    """
    Servicio para registrar ventas.

    Flujo completo:
    1. Bloquear stock y tarjeta con select_for_update()
    2. Validar stock disponible y saldo
    3. Crear Venta + DetalleVenta
    4. Actualizar Stock + MovimientoStock
    5. Si es a credito -> CuentaCorrienteCliente (DEBITO)
    6. Si es contado con tarjeta -> Actualizar saldo + MovimientoTarjeta
    7. Si es contado -> Crear PagoVenta + AplicacionPago automatico
    """

    @staticmethod
    def registrar_venta(
        *,
        cliente,
        cajero,
        tipo: str,
        medio_pago=None,
        tarjeta=None,
        hijo=None,
        items: list = None,
        estado_pago: str = "PENDIENTE",
        referencia: str = "",
        cierre_caja=None,
        genera_factura_legal: bool = False,
        nro_factura: str = "",
    ) -> Venta:
        """
        Registra una venta completa con sus detalles.
        """
        if not items:
            raise ValidationError({"error": "Debe incluir al menos un producto."})

        # Validar medio de pago — requerido para contado SIN tarjeta prepago
        if tipo == "CONTADO" and medio_pago is None and tarjeta is None:
            raise ValidationError({
                "error": "Las ventas al contado requieren un medio de pago o tarjeta prepago."
            })

        # Validar que el hijo pertenezca al cliente
        if hijo and hijo.cliente_responsable_id != cliente.pk:
            raise ValidationError({"error": "El hijo indicado no pertenece al cliente."})

        with transaction.atomic():
            # 0. Bloquear stocks y tarjeta para evitar race conditions
            productos_con_stock = [item["producto"] for item in items if item["producto"].requiere_stock]

            stocks_bloqueados = {}
            if productos_con_stock:
                stocks_bloqueados = {
                    s.producto_id: s
                    for s in Stock.objects.select_for_update().filter(
                        producto__in=productos_con_stock
                    )
                }

            # Bloquear tarjeta si se usa
            tarjeta_bloqueada = None
            if tipo == "CONTADO" and tarjeta:
                tarjeta_bloqueada = Tarjeta.objects.select_for_update().get(pk=tarjeta.pk)
                if tarjeta_bloqueada.estado != Tarjeta.Estado.ACTIVA:
                    raise ValidationError({"error": "La tarjeta no está activa."})

            # Bloquear cuenta corriente si es a credito
            saldo_anterior_cc = Decimal("0")
            if tipo == "CREDITO":
                ultimo_cc = (
                    CuentaCorrienteCliente.objects
                    .filter(cliente=cliente)
                    .select_for_update()
                    .order_by("-id_movimiento_cc")
                    .first()
                )
                saldo_anterior_cc = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")

            # 1. Calcular totales y validar
            # Agregar ítems con el mismo producto para respetar unique_together(venta, producto)
            merged: dict = {}
            for item in items:
                pid = item["producto"].pk
                if pid in merged:
                    merged[pid]["cantidad"] += item["cantidad"]
                else:
                    merged[pid] = dict(item)
            items = list(merged.values())

            monto_total = Decimal("0")
            limite_credito = getattr(cliente, "limite_credito", None)
            monto_gravada_10 = Decimal("0")
            monto_gravada_5 = Decimal("0")
            monto_exenta = Decimal("0")
            iva_10 = Decimal("0")
            iva_5 = Decimal("0")

            # Precargar precios de la lista asignada al cliente si no es la lista por defecto.
            # Una sola query cubre todos los productos de la venta.
            precio_overrides: dict = {}
            lista_precio_id = getattr(cliente, "lista_precio_id", None)
            if lista_precio_id:
                from apps.productos.models import PrecioPorLista
                for row in PrecioPorLista.objects.filter(
                    lista_id=lista_precio_id,
                    lista__es_por_defecto=False,
                ).values("producto_id", "precio_unitario"):
                    precio_overrides[row["producto_id"]] = row["precio_unitario"]

            detalles_data = []
            for item in items:
                producto = item["producto"]
                cantidad = item["cantidad"]
                precio = precio_overrides.get(producto.pk, item.get("precio_unitario", Decimal("0")))
                subtotal = cantidad * precio
                iva_calculado = _calcular_iva_producto(producto, subtotal)
                item_iva_10 = iva_calculado.get("iva_10", Decimal("0"))
                item_iva_5 = iva_calculado.get("iva_5", Decimal("0"))
                item_exenta = iva_calculado.get("monto_exenta", Decimal("0"))
                item_gravada_10 = subtotal - item_iva_10 if item_iva_10 else Decimal("0")
                item_gravada_5 = subtotal - item_iva_5 if item_iva_5 else Decimal("0")

                # Validar stock con el objeto bloqueado
                if producto.requiere_stock:
                    stock = stocks_bloqueados.get(producto.pk)
                    disponible = stock.cantidad if stock else Decimal("0")
                    if disponible < cantidad and not producto.permite_stock_negativo:
                        raise ValidationError({
                            "error": f"Stock insuficiente para {producto.descripcion}.",
                            "disponible": str(disponible),
                            "solicitado": str(cantidad),
                        })

                monto_total += subtotal
                monto_gravada_10 += item_gravada_10
                monto_gravada_5 += item_gravada_5
                monto_exenta += item_exenta
                iva_10 += item_iva_10
                iva_5 += item_iva_5

                detalles_data.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio_unitario": precio,
                    "subtotal": subtotal,
                    "monto_gravada_10": item_gravada_10,
                    "monto_gravada_5": item_gravada_5,
                    "monto_exenta": item_exenta,
                    "iva_10": item_iva_10,
                    "iva_5": item_iva_5,
                })

            # Validar cuenta corriente habilitada y límite de crédito
            # permite_cuenta_corriente=False → sin crédito permitido;
            # limite_credito=0 → sin límite; >0 → límite máximo.
            if tipo == "CREDITO":
                if not getattr(cliente, "permite_cuenta_corriente", False):
                    raise ValidationError({
                        "error": "El cliente no tiene habilitada la cuenta corriente.",
                    })
                if limite_credito:
                    limite_decimal = Decimal(str(limite_credito))
                    if saldo_anterior_cc + monto_total > limite_decimal:
                        raise ValidationError({
                            "error": "La venta excede el límite de crédito autorizado del cliente.",
                            "limite_credito": str(limite_decimal),
                            "saldo_deudor": str(saldo_anterior_cc),
                            "monto_venta": str(monto_total),
                        })

            # Validar saldo de tarjeta con objeto bloqueado
            if tipo == "CONTADO" and tarjeta_bloqueada:
                if tarjeta_bloqueada.saldo_actual < monto_total and not tarjeta_bloqueada.permite_saldo_negativo:
                    raise ValidationError({
                        "error": "Saldo insuficiente en la tarjeta.",
                        "saldo_actual": str(tarjeta_bloqueada.saldo_actual),
                        "monto_venta": str(monto_total),
                    })

            # 2. Crear Venta
            # Si no se pasó hijo explícitamente pero hay tarjeta de alumno, tomarlo de la tarjeta
            if hijo is None and tarjeta_bloqueada is not None and tarjeta_bloqueada.hijo_id:
                hijo = tarjeta_bloqueada.hijo

            venta = Venta.objects.create(
                cliente=cliente,
                cajero=cajero,
                tipo=tipo,
                medio_pago=medio_pago,
                hijo=hijo,
                tarjeta=tarjeta_bloqueada,
                caja=cierre_caja.caja if cierre_caja else None,
                monto_total=monto_total,
                monto_gravada_10=monto_gravada_10,
                monto_gravada_5=monto_gravada_5,
                monto_exenta=monto_exenta,
                iva_10=iva_10,
                iva_5=iva_5,
                estado_pago="PAGADO" if tipo == "CONTADO" else estado_pago,
            )

            # 3. Crear DetalleVenta y actualizar Stock
            for det in detalles_data:
                DetalleVenta.objects.create(venta=venta, **det)

                producto = det["producto"]
                if producto.requiere_stock:
                    stock = stocks_bloqueados.get(producto.pk)
                    if stock is None:
                        stock, _ = Stock.objects.get_or_create(
                            producto=producto,
                            defaults={"cantidad": Decimal("0")},
                        )
                    stock.cantidad -= det["cantidad"]
                    stock.save()

                    MovimientoStock.objects.create(
                        producto=producto,
                        tipo=MovimientoStock.Tipo.EGRESO,
                        motivo=MovimientoStock.Motivo.VENTA,
                        cantidad=det["cantidad"],
                        stock_resultante=stock.cantidad,
                        venta=venta,
                        autorizado_por=cajero,
                    )

            # 4. Si es a credito, registrar en cuenta corriente
            if tipo == "CREDITO":
                CuentaCorrienteCliente.objects.create(
                    cliente=cliente,
                    tipo=CuentaCorrienteCliente.Tipo.DEBITO,
                    monto=monto_total,
                    saldo_anterior=saldo_anterior_cc,
                    saldo_resultante=saldo_anterior_cc + monto_total,
                    venta=venta,
                    descripcion=f"Venta #{venta.pk}",
                    creado_por=cajero,
                    origen=CuentaCorrienteCliente.Origen.CANTINA,
                )

            # 5. Si es contado con medio_pago explícito, crear pago automático.
            # Las ventas con tarjeta prepago NO generan PagoVenta —
            # el pago queda registrado en MovimientoTarjeta (paso 6).
            if tipo == "CONTADO" and medio_pago is not None:
                pago = PagoVenta.objects.create(
                    cliente=cliente,
                    venta=venta,
                    monto=monto_total,
                    medio_pago=medio_pago,
                    cajero=cajero,
                    referencia=referencia or None,
                    cierre_caja=cierre_caja,
                    estado=PagoVenta.Estado.CONCILIADO,
                )
                AplicacionPago.objects.create(
                    pago=pago,
                    venta=venta,
                    monto_aplicado=monto_total,
                )
                if cierre_caja:
                    from apps.contabilidad.models import MovimientoCaja
                    MovimientoCaja.objects.create(
                        cierre=cierre_caja,
                        tipo=MovimientoCaja.Tipo.INGRESO,
                        monto=monto_total,
                        descripcion=f"Venta #{venta.pk}",
                        medio_pago=medio_pago,
                        venta=venta,
                    )

            # 6. Si es contado con tarjeta, descontar saldo
            if tipo == "CONTADO" and tarjeta_bloqueada:
                saldo_anterior_tarjeta = tarjeta_bloqueada.saldo_actual
                tarjeta_bloqueada.saldo_actual -= monto_total
                tarjeta_bloqueada.save()

                MovimientoTarjeta.objects.create(
                    tarjeta=tarjeta_bloqueada,
                    tipo=MovimientoTarjeta.Tipo.CONSUMO,
                    monto=monto_total,
                    saldo_anterior=saldo_anterior_tarjeta,
                    saldo_resultante=tarjeta_bloqueada.saldo_actual,
                    descripcion=f"Venta #{venta.pk}",
                    creado_por=cajero,
                )

                if tarjeta_bloqueada.saldo_actual < 0 and tarjeta_bloqueada.hijo_id:
                    # Notificación de saldo negativo solo para tarjetas de alumnos (tienen padre/tutor)
                    try:
                        cliente_resp = tarjeta_bloqueada.hijo.cliente_responsable
                        usuario_portal = cliente_resp.usuario_portal
                        from apps.notificaciones.models import Notificacion
                        from apps.notificaciones.services import (
                            push_ws_notificacion,
                            whatsapp_cliente,
                        )
                        nombre_hijo = str(tarjeta_bloqueada.hijo)
                        deficit = abs(int(tarjeta_bloqueada.saldo_actual))
                        msg = (
                            f"Se registro una compra de Gs. {int(monto_total):,} para "
                            f"{nombre_hijo}. Saldo actual: -Gs. {deficit:,}. "
                            f"Por favor recarga la tarjeta."
                        )
                        notif = Notificacion.objects.create(
                            usuario=usuario_portal,
                            tipo=Notificacion.Tipo.VENTA_DEUDA,
                            titulo="Venta con saldo insuficiente",
                            mensaje=msg,
                            destino=Notificacion.Destino.SISTEMA,
                        )
                        push_ws_notificacion(notif)
                        whatsapp_cliente(cliente_resp, msg)
                    except Exception:
                        logger.warning(
                            "No se pudo enviar notificación de saldo negativo para tarjeta %s",
                            tarjeta_bloqueada.pk,
                            exc_info=True,
                        )

                if cierre_caja:
                    from apps.contabilidad.models import MovimientoCaja
                    MovimientoCaja.objects.create(
                        cierre=cierre_caja,
                        tipo=MovimientoCaja.Tipo.INGRESO,
                        monto=monto_total,
                        descripcion=f"Venta #{venta.pk} - Tarjeta prepago",
                        medio_pago=None,
                        venta=venta,
                    )

            # 7. Facturación opcional (CONTADO con cualquier medio: prepago, efectivo, POS, etc.)
            # Si el cajero ingresó nro_factura → crea la Factura al instante.
            # Si solo se marcó genera_factura_legal → queda pendiente para Facturación.
            if tipo == "CONTADO" and nro_factura:
                from apps.contabilidad.services import FacturacionService
                iva_dict = {
                    "iva_10": iva_10,
                    "iva_5": iva_5,
                    "monto_exenta": monto_exenta,
                }
                factura = FacturacionService.emitir_factura(
                    cliente=cliente,
                    nro_factura=nro_factura,
                    monto_total=monto_total,
                    **iva_dict,
                )
                venta.factura = factura
                venta.nro_factura = nro_factura
                venta.genera_factura_legal = True
                venta.save(update_fields=["factura", "nro_factura", "genera_factura_legal"])
            elif tipo == "CONTADO" and genera_factura_legal:
                venta.genera_factura_legal = True
                venta.save(update_fields=["genera_factura_legal"])

            return venta

    @staticmethod
    def anular_venta(venta: "Venta", anulado_por) -> "Venta":
        """
        Anula una venta ACTIVA revirtiendo:
        - Stock (DEVOLUCION_CLIENTE por cada detalle)
        - Saldo de tarjeta (REVERSO si se pagó con tarjeta)
        - Cuenta corriente (entrada CREDITO si era CREDITO)

        Raises ValidationError si la venta ya está anulada o tiene factura EMITIDA.
        """
        if venta.estado == Venta.Estado.ANULADA:
            raise ValidationError({"error": "La venta ya está anulada."})

        # Bloquear si tiene factura emitida asociada (campo FK directo en Venta)
        if venta.factura and venta.factura.estado == "EMITIDA":
            raise ValidationError({
                "error": "La venta tiene una factura EMITIDA. Anulá primero la factura."
            })

        with transaction.atomic():
            venta = Venta.objects.select_for_update().get(pk=venta.pk)
            if venta.estado == Venta.Estado.ANULADA:
                raise ValidationError({"error": "La venta ya está anulada."})

            # 1. Revertir stock
            for detalle in venta.detalles.select_related("producto").all():
                if detalle.producto.requiere_stock:
                    stock, _ = Stock.objects.get_or_create(
                        producto=detalle.producto,
                        defaults={"cantidad": Decimal("0")},
                    )
                    stock = Stock.objects.select_for_update().get(pk=stock.pk)
                    stock.cantidad += detalle.cantidad
                    stock.save()
                    MovimientoStock.objects.create(
                        producto=detalle.producto,
                        tipo=MovimientoStock.Tipo.INGRESO,
                        motivo=MovimientoStock.Motivo.DEVOLUCION_CLIENTE,
                        cantidad=detalle.cantidad,
                        stock_resultante=stock.cantidad,
                        venta=venta,
                        autorizado_por=anulado_por,
                    )

            # 2. Revertir saldo de tarjeta (si aplica)
            if venta.tarjeta_id:
                tarjeta = Tarjeta.objects.select_for_update().get(pk=venta.tarjeta_id)
                saldo_anterior = tarjeta.saldo_actual
                tarjeta.saldo_actual += venta.monto_total
                tarjeta.save()
                MovimientoTarjeta.objects.create(
                    tarjeta=tarjeta,
                    tipo=MovimientoTarjeta.Tipo.REVERSO,
                    monto=venta.monto_total,
                    saldo_anterior=saldo_anterior,
                    descripcion=f"Anulación Venta #{venta.pk}",
                    creado_por=anulado_por,
                )

            # 3. Anular PagoVenta asociados
            PagoVenta.objects.filter(venta=venta).exclude(
                estado=PagoVenta.Estado.ANULADO
            ).update(estado=PagoVenta.Estado.ANULADO)

            # 4. Revertir cuenta corriente (si era CREDITO)
            if venta.tipo == Venta.Tipo.CREDITO:
                ultimo_cc = (
                    CuentaCorrienteCliente.objects
                    .filter(cliente=venta.cliente)
                    .select_for_update()
                    .order_by("-id_movimiento_cc")
                    .first()
                )
                saldo_anterior_cc = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")
                CuentaCorrienteCliente.objects.create(
                    cliente=venta.cliente,
                    tipo=CuentaCorrienteCliente.Tipo.CREDITO,
                    monto=venta.monto_total,
                    saldo_anterior=saldo_anterior_cc,
                    saldo_resultante=saldo_anterior_cc - venta.monto_total,
                    venta=venta,
                    descripcion=f"Anulación Venta #{venta.pk}",
                    creado_por=anulado_por,
                    origen=CuentaCorrienteCliente.Origen.CANTINA,
                )

            venta.estado = Venta.Estado.ANULADA
            venta.save(update_fields=["estado"])

        return venta

    @staticmethod
    def emitir_nota_credito(
        *,
        cliente,
        empleado,
        nro_nota_credito: str,
        motivo: str,
        venta_origen=None,
        items: list = None,
        monto_total: Decimal = None,
    ) -> NotaCredito:
        """
        Emite una nota de crédito a un cliente (devolución de mercadería o
        descuento). Con items: revierte stock (INGRESO, DEVOLUCION_CLIENTE) y
        el monto_total se calcula de la suma de líneas. Sin items: es un
        descuento/ajuste puro y monto_total debe venir explícito.

        Siempre reduce la deuda del cliente en cuenta corriente (CREDITO),
        sin importar si tenía deuda o no.
        """
        items = items or []

        if items:
            monto_total = sum(
                (i["cantidad"] * i["precio_unitario"]) for i in items
            ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        elif not monto_total or monto_total <= 0:
            raise ValidationError({"error": "Debe indicar ítems o un monto_total mayor a 0."})

        with transaction.atomic():
            if NotaCredito.objects.filter(nro_nota_credito=nro_nota_credito).exists():
                raise ValidationError({"error": f"La nota de crédito {nro_nota_credito} ya fue registrada."})

            nc = NotaCredito.objects.create(
                cliente=cliente,
                venta_origen=venta_origen,
                nro_nota_credito=nro_nota_credito,
                monto_total=monto_total,
                motivo=motivo,
                estado=NotaCredito.Estado.EMITIDA,
                empleado_autoriza=empleado,
            )

            for item in items:
                producto = item["producto"]
                cantidad = item["cantidad"]
                precio_unitario = item["precio_unitario"]
                subtotal = (cantidad * precio_unitario).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

                DetalleNotaCredito.objects.create(
                    nota_credito=nc,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                )

                if producto.requiere_stock:
                    stock, _ = Stock.objects.get_or_create(
                        producto=producto, defaults={"cantidad": Decimal("0")},
                    )
                    stock = Stock.objects.select_for_update().get(pk=stock.pk)
                    stock.cantidad += cantidad
                    stock.save()
                    MovimientoStock.objects.create(
                        producto=producto,
                        tipo=MovimientoStock.Tipo.INGRESO,
                        motivo=MovimientoStock.Motivo.DEVOLUCION_CLIENTE,
                        cantidad=cantidad,
                        stock_resultante=stock.cantidad,
                        venta=venta_origen,
                        autorizado_por=empleado,
                        observaciones=f"Devolución NC #{nro_nota_credito}",
                    )

            ultimo_cc = (
                CuentaCorrienteCliente.objects
                .filter(cliente=cliente)
                .select_for_update()
                .order_by("-id_movimiento_cc")
                .first()
            )
            saldo_anterior_cc = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")
            CuentaCorrienteCliente.objects.create(
                cliente=cliente,
                tipo=CuentaCorrienteCliente.Tipo.CREDITO,
                monto=monto_total,
                saldo_anterior=saldo_anterior_cc,
                saldo_resultante=saldo_anterior_cc - monto_total,
                nota_credito=nc,
                descripcion=f"Nota de crédito #{nro_nota_credito}",
                creado_por=empleado,
                origen=CuentaCorrienteCliente.Origen.CANTINA,
            )

        return nc

    @staticmethod
    def anular_nota_credito(nc: "NotaCredito", anulado_por) -> "NotaCredito":
        """
        Anula una NC EMITIDA revirtiendo:
        - Cuenta corriente (DEBITO que restaura la deuda reducida)
        - Stock (EGRESO por cada ítem devuelto, si tenía)
        """
        if nc.estado == NotaCredito.Estado.ANULADA:
            raise ValidationError({"error": "La nota de crédito ya está anulada."})

        with transaction.atomic():
            nc = NotaCredito.objects.select_for_update().get(pk=nc.pk)
            if nc.estado == NotaCredito.Estado.ANULADA:
                raise ValidationError({"error": "La nota de crédito ya está anulada."})

            ultimo_cc = (
                CuentaCorrienteCliente.objects
                .filter(cliente=nc.cliente)
                .select_for_update()
                .order_by("-id_movimiento_cc")
                .first()
            )
            saldo_anterior_cc = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")
            CuentaCorrienteCliente.objects.create(
                cliente=nc.cliente,
                tipo=CuentaCorrienteCliente.Tipo.DEBITO,
                monto=nc.monto_total,
                saldo_anterior=saldo_anterior_cc,
                saldo_resultante=saldo_anterior_cc + nc.monto_total,
                nota_credito=nc,
                descripcion=f"Reversión por anulación NC #{nc.nro_nota_credito}",
                creado_por=anulado_por,
                origen=CuentaCorrienteCliente.Origen.CANTINA,
            )

            for detalle in nc.detalles.select_related("producto").all():
                producto = detalle.producto
                if producto.requiere_stock:
                    stock, _ = Stock.objects.get_or_create(
                        producto=producto, defaults={"cantidad": Decimal("0")},
                    )
                    stock = Stock.objects.select_for_update().get(pk=stock.pk)
                    stock.cantidad -= detalle.cantidad
                    stock.save()
                    MovimientoStock.objects.create(
                        producto=producto,
                        tipo=MovimientoStock.Tipo.EGRESO,
                        motivo=MovimientoStock.Motivo.CORRECCION,
                        cantidad=detalle.cantidad,
                        stock_resultante=stock.cantidad,
                        venta=nc.venta_origen,
                        autorizado_por=anulado_por,
                        observaciones=f"Reversión por anulación NC #{nc.nro_nota_credito}",
                    )

            nc.estado = NotaCredito.Estado.ANULADA
            nc.save(update_fields=["estado"])

        return nc


class PagoService:
    """Servicio para registrar pagos de clientes."""

    @staticmethod
    def registrar_pago(
        *,
        cliente,
        monto: Decimal,
        medio_pago,
        cajero,
        venta=None,
        referencia: str = "",
    ) -> PagoVenta:
        """
        Registra un pago de cliente a una venta a credito.
        """
        if venta and venta.tipo != "CREDITO":
            raise ValidationError({"error": "Solo se pueden registrar pagos para ventas a credito."})

        # Rechazar pagos que excedan el saldo pendiente de la venta.
        # Para pagar más, usar venta=None (pago a cuenta corriente) y aplicar manualmente.
        if venta:
            saldo = venta.saldo_pendiente
            if monto > saldo:
                raise ValidationError({
                    "error": "El monto del pago supera el saldo pendiente de la venta.",
                    "saldo_pendiente": str(saldo),
                    "monto_pago": str(monto),
                })

        with transaction.atomic():
            # Bloquear cuenta corriente
            ultimo_cc = (
                CuentaCorrienteCliente.objects
                .filter(cliente=cliente)
                .select_for_update()
                .order_by("-id_movimiento_cc")
                .first()
            )
            saldo_anterior = ultimo_cc.saldo_resultante if ultimo_cc else Decimal("0")

            # Crear pago
            pago = PagoVenta.objects.create(
                cliente=cliente,
                venta=venta,
                monto=monto,
                medio_pago=medio_pago,
                cajero=cajero,
                referencia=referencia,
                estado=PagoVenta.Estado.PENDIENTE,
            )

            # Aplicar a la venta (monto == saldo_pendiente garantizado por la validación previa)
            if venta:
                AplicacionPago.objects.create(
                    pago=pago,
                    venta=venta,
                    monto_aplicado=monto,
                )
                venta.estado_pago = (
                    Venta.EstadoPago.PAGADO if venta.saldo_pendiente <= 0
                    else Venta.EstadoPago.PARCIAL
                )
                venta.save(update_fields=["estado_pago"])

            # Registrar en cuenta corriente (CREDITO)
            CuentaCorrienteCliente.objects.create(
                cliente=cliente,
                tipo=CuentaCorrienteCliente.Tipo.CREDITO,
                monto=monto,
                saldo_anterior=saldo_anterior,
                saldo_resultante=saldo_anterior - monto,
                pago=pago,
                descripcion=f"Pago #{pago.pk}",
                creado_por=cajero,
                origen=CuentaCorrienteCliente.Origen.CANTINA,
            )

            return pago
