"""
Servicios de negocio para ventas
"""

from decimal import Decimal

from django.db import transaction

from rest_framework.exceptions import ValidationError

from apps.clientes.models import CuentaCorrienteCliente
from apps.inventario.models import Stock, MovimientoStock
from apps.core.models import Tarjeta, MovimientoTarjeta
from .models import Venta, DetalleVenta, PagoVenta, AplicacionPago


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
        pin_autorizacion: str = "",
        referencia: str = "",
        cierre_caja=None,
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
                    .order_by("-id")
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

            detalles_data = []
            for item in items:
                producto = item["producto"]
                cantidad = item["cantidad"]
                precio = item.get("precio_unitario", Decimal("0"))
                subtotal = cantidad * precio
                item_iva_10 = item.get("iva_10", Decimal("0"))
                item_iva_5 = item.get("iva_5", Decimal("0"))
                item_exenta = item.get("monto_exenta", Decimal("0"))
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

            # Validar límite de crédito
            # limite_credito=0 → sin crédito permitido; None → sin límite; >0 → límite máximo.
            if tipo == "CREDITO" and limite_credito is not None:
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
                    if pin_autorizacion:
                        # PIN de padre/tutor: verificar y validar límite de crédito
                        cliente_responsable = tarjeta_bloqueada.hijo.cliente_responsable
                        if not cliente_responsable.check_pin(pin_autorizacion):
                            raise ValidationError({"error": "PIN de autorización incorrecto."})
                        deficit = monto_total - tarjeta_bloqueada.saldo_actual
                        if deficit > tarjeta_bloqueada.limite_credito:
                            raise ValidationError({
                                "error": "La compra excede el límite de crédito autorizado.",
                                "limite_credito": str(tarjeta_bloqueada.limite_credito),
                                "deficit": str(deficit),
                            })
                        # PIN válido y dentro del límite — se permite saldo negativo para esta operación
                    else:
                        raise ValidationError({
                            "error": "Saldo insuficiente en la tarjeta.",
                            "saldo_actual": str(tarjeta_bloqueada.saldo_actual),
                            "monto_venta": str(monto_total),
                        })

            # 2. Crear Venta
            # Si no se pasó hijo explícitamente pero hay tarjeta, tomarlo de la tarjeta
            if hijo is None and tarjeta_bloqueada is not None:
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

                if tarjeta_bloqueada.saldo_actual < 0:
                    try:
                        cliente_resp = tarjeta_bloqueada.hijo.cliente_responsable
                        usuario_portal = cliente_resp.usuario_portal
                        from apps.notificaciones.models import Notificacion
                        from apps.notificaciones.services import (
                            push_ws_notificacion,
                            _whatsapp_cliente,
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
                        _whatsapp_cliente(cliente_resp, msg)
                    except Exception:
                        pass

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
                    .order_by("-id")
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
                )

            venta.estado = Venta.Estado.ANULADA
            venta.save(update_fields=["estado"])

        return venta


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
                .order_by("-id")
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
            )

            return pago
