"""
Servicios de negocio para contabilidad
Caja y facturacion
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import models, transaction, IntegrityError
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from .models import Caja, CierreCaja, MovimientoCaja, Factura

TIPO_CARGA_SALDO = "CARGA_SALDO"
TIPO_PAGO_ALMUERZO = "PAGO_ALMUERZO"
TIPO_VENTA = "VENTA"
TIPO_PAGO_CREDITO = "PAGO_CREDITO"


class CajaService:
    """Servicio para operaciones de caja."""

    @staticmethod
    def abrir_caja(*, caja, empleado, monto_inicial: Decimal = 0) -> CierreCaja:
        """
        Abre una caja para iniciar operaciones.
        Valida que no haya otra caja abierta.
        """
        with transaction.atomic():
            caja_obj = Caja.objects.select_for_update().get(pk=caja.pk)

            if CierreCaja.objects.filter(
                caja=caja_obj, estado=CierreCaja.Estado.ABIERTO
            ).exists():
                raise ValidationError({"error": "La caja ya tiene un cierre abierto."})

            return CierreCaja.objects.create(
                caja=caja_obj,
                empleado=empleado,
                monto_inicial=monto_inicial,
                estado=CierreCaja.Estado.ABIERTO,
            )

    @staticmethod
    def cerrar_caja(*, cierre, monto_contado: Decimal) -> CierreCaja:
        """
        Cierra una caja y calcula la diferencia.

        diferencia_efectivo compara solo contra movimientos de EFECTIVO:
        el cajero cuenta los billetes del cajón, no los pagos por POS ni prepago.
        """
        with transaction.atomic():
            cierre = CierreCaja.objects.select_for_update().get(pk=cierre.pk)

            if cierre.estado != CierreCaja.Estado.ABIERTO:
                raise ValidationError({"error": "La caja no esta abierta."})

            # Efectivo físico = movimientos con medio_pago EFECTIVO +
            # egresos manuales sin medio_pago (retiros en cash sin especificar)
            efectivo_ingresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre,
                    tipo=MovimientoCaja.Tipo.INGRESO,
                    medio_pago__descripcion__iexact="efectivo",
                ).aggregate(total=models.Sum("monto"))["total"]
            ) or Decimal("0")

            efectivo_egresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre,
                    tipo=MovimientoCaja.Tipo.EGRESO,
                ).filter(
                    models.Q(medio_pago__descripcion__iexact="efectivo")
                    | models.Q(medio_pago__isnull=True)
                ).aggregate(total=models.Sum("monto"))["total"]
            ) or Decimal("0")

            efectivo_esperado = cierre.monto_inicial + efectivo_ingresos - efectivo_egresos
            diferencia = monto_contado - efectivo_esperado

            cierre.monto_contado_fisico = monto_contado
            cierre.diferencia_efectivo = diferencia
            cierre.fecha_cierre = timezone.now()
            cierre.estado = CierreCaja.Estado.CERRADO
            cierre.save()

            return cierre

    @staticmethod
    def registrar_movimiento(
        *,
        cierre,
        tipo: str,
        monto: Decimal,
        medio_pago,
        descripcion: str = "",
        venta=None,
    ) -> MovimientoCaja:
        """Registra un movimiento en un cierre de caja."""
        if monto <= 0:
            raise ValidationError({"error": "El monto debe ser mayor a 0."})

        if tipo not in (MovimientoCaja.Tipo.INGRESO, MovimientoCaja.Tipo.EGRESO):
            raise ValidationError({"error": f"Tipo invalido: {tipo}."})

        with transaction.atomic():
            cierre_obj = CierreCaja.objects.select_for_update().get(pk=cierre.pk)

            if cierre_obj.estado != CierreCaja.Estado.ABIERTO:
                raise ValidationError({"error": "La caja no esta abierta."})

            return MovimientoCaja.objects.create(
                cierre=cierre_obj,
                tipo=tipo,
                monto=monto,
                medio_pago=medio_pago,
                descripcion=descripcion,
                venta=venta,
            )


class FacturacionService:
    """Servicio para factura en papel preimpreso."""

    @staticmethod
    def emitir_factura(
        *,
        cliente,
        venta=None,
        nro_factura: str,
        monto_total: Decimal,
        iva_10: Decimal = 0,
        iva_5: Decimal = 0,
        monto_exenta: Decimal = 0,
        observaciones: str = "",
    ) -> Factura:
        """
        Registra una factura preimpresa.
        Valida que el numero no este duplicado.
        """
        with transaction.atomic():
            if Factura.objects.filter(nro_factura=nro_factura).exists():
                raise ValidationError({"error": f"La factura {nro_factura} ya fue registrada."})

            try:
                return Factura.objects.create(
                    cliente=cliente,
                    venta=venta,
                    nro_factura=nro_factura,
                    monto_total=monto_total,
                    iva_10=iva_10,
                    iva_5=iva_5,
                    monto_exenta=monto_exenta,
                    observaciones=observaciones,
                )
            except IntegrityError:
                raise ValidationError({"error": f"La factura {nro_factura} ya fue registrada."})

    @staticmethod
    def anular_factura(factura) -> Factura:
        """Anula una factura."""
        with transaction.atomic():
            factura = Factura.objects.select_for_update().get(pk=factura.pk)

            if factura.estado == Factura.Estado.ANULADA:
                raise ValidationError({"error": "La factura ya esta anulada."})

            factura.estado = Factura.Estado.ANULADA
            factura.save()
            return factura

    @staticmethod
    def _calcular_iva_10(monto: Decimal) -> dict:
        """Precio incluye IVA 10%: iva = monto * 10/110."""
        iva = (monto * Decimal("10") / Decimal("110")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return {"iva_10": iva, "iva_5": Decimal(0), "monto_exenta": Decimal(0)}

    @classmethod
    def emitir_para_origen(cls, *, tipo: str, origen_id: int, nro_factura: str) -> Factura:
        """
        Emite una factura para una CargaSaldo o PagoCuentaAlmuerzo.
        tipo: CARGA_SALDO | PAGO_ALMUERZO
        """
        from apps.core.models import CargaSaldo
        from apps.almuerzos.models import PagoCuentaAlmuerzo

        with transaction.atomic():
            if tipo == TIPO_CARGA_SALDO:
                origen = (
                    CargaSaldo.objects
                    .select_related("tarjeta__hijo__cliente_responsable", "cliente_origen")
                    .select_for_update(of=("self",))
                    .get(pk=origen_id)
                )

                if origen.estado != CargaSaldo.Estado.CONFIRMADA:
                    raise ValidationError({"error": "Solo se pueden facturar cargas confirmadas."})
                if origen.factura_id:
                    raise ValidationError({"error": "Esta carga de saldo ya tiene factura emitida."})

                cliente = origen.cliente_origen
                if not cliente and origen.tarjeta and origen.tarjeta.hijo:
                    cliente = origen.tarjeta.hijo.cliente_responsable
                if not cliente:
                    raise ValidationError({"error": "La carga no tiene cliente asociado."})

                monto = origen.monto_cargado
                iva = cls._calcular_iva_10(monto)

            elif tipo == TIPO_PAGO_ALMUERZO:
                origen = PagoCuentaAlmuerzo.objects.select_related(
                    "cuenta__hijo__cliente_responsable"
                ).select_for_update().get(pk=origen_id)

                if origen.factura_id:
                    raise ValidationError({"error": "Este pago ya tiene factura emitida."})

                cliente = origen.cuenta.hijo.cliente_responsable
                monto = origen.monto
                iva = cls._calcular_iva_10(monto)

            elif tipo == TIPO_VENTA:
                from apps.ventas.models import Venta as VentaModel
                origen = (
                    VentaModel.objects
                    .select_related("cliente")
                    .select_for_update(of=("self",))
                    .get(pk=origen_id)
                )
                if origen.estado == VentaModel.Estado.ANULADA:
                    raise ValidationError({"error": "No se puede facturar una venta anulada."})
                if not origen.genera_factura_legal:
                    raise ValidationError({"error": "La venta no está marcada para factura legal."})
                if origen.factura_id:
                    raise ValidationError({"error": "La venta ya tiene factura emitida."})

                cliente = origen.cliente
                monto = origen.monto_total
                iva = {
                    "iva_10": origen.iva_10,
                    "iva_5": origen.iva_5,
                    "monto_exenta": origen.monto_exenta,
                }

            elif tipo == TIPO_PAGO_CREDITO:
                from apps.clientes.models import CuentaCorrienteCliente as CCModel
                origen = (
                    CCModel.objects
                    .select_related("cliente")
                    .select_for_update(of=("self",))
                    .get(pk=origen_id)
                )
                if not origen.genera_factura_legal:
                    raise ValidationError({"error": "El pago no está marcado para factura legal."})
                if origen.factura_id:
                    raise ValidationError({"error": "Este pago ya tiene factura emitida."})
                cliente = origen.cliente
                monto = origen.monto
                iva = cls._calcular_iva_10(monto)

            else:
                raise ValidationError({"error": f"Tipo desconocido: {tipo}."})

            factura = FacturacionService.emitir_factura(
                cliente=cliente,
                nro_factura=nro_factura,
                monto_total=monto,
                **iva,
            )

            origen.factura = factura
            if tipo == TIPO_VENTA:
                origen.nro_factura = nro_factura
                origen.save(update_fields=["factura", "nro_factura"])
            else:
                origen.save(update_fields=["factura"])

            return factura

    @staticmethod
    def get_pendientes() -> dict:
        """Retorna cargas de saldo, pagos de almuerzo, ventas y pagos de crédito sin factura."""
        from apps.core.models import CargaSaldo
        from apps.almuerzos.models import PagoCuentaAlmuerzo
        from apps.ventas.models import Venta as VentaModel
        from apps.clientes.models import CuentaCorrienteCliente

        cargas = CargaSaldo.objects.filter(
            estado=CargaSaldo.Estado.CONFIRMADA,
            factura__isnull=True,
        ).select_related("cliente_origen", "tarjeta__hijo__cliente_responsable").order_by("-fecha_carga")

        pagos = PagoCuentaAlmuerzo.objects.filter(
            factura__isnull=True,
        ).select_related("cuenta__hijo__cliente_responsable").order_by("-fecha_pago")

        ventas = VentaModel.objects.filter(
            genera_factura_legal=True,
            factura__isnull=True,
        ).exclude(estado=VentaModel.Estado.ANULADA).select_related("cliente").order_by("-fecha")

        pagos_credito = CuentaCorrienteCliente.objects.filter(
            tipo=CuentaCorrienteCliente.Tipo.CREDITO,
            genera_factura_legal=True,
            factura__isnull=True,
        ).select_related("cliente").order_by("-fecha")

        return {"cargas": cargas, "pagos": pagos, "ventas": ventas, "pagos_credito": pagos_credito}

    @classmethod
    def emitir_lote(cls, *, tipo: str, ids: list[int], nro_factura: str) -> Factura:
        """
        Emite UNA factura agrupando varias cargas de saldo o pagos de almuerzo.
        tipo: CARGA_SALDO | PAGO_ALMUERZO
        Todos los ids deben pertenecer al mismo cliente.
        """
        from apps.core.models import CargaSaldo
        from apps.almuerzos.models import PagoCuentaAlmuerzo

        if not ids:
            raise ValidationError({"error": "Debe seleccionar al menos un ítem."})

        with transaction.atomic():
            if tipo == TIPO_CARGA_SALDO:
                origenes = list(
                    CargaSaldo.objects
                    .select_related("tarjeta__hijo__cliente_responsable", "cliente_origen")
                    .select_for_update(of=("self",))
                    .filter(pk__in=ids)
                )
                if len(origenes) != len(ids):
                    raise ValidationError({"error": "Uno o más ítems no existen."})

                clientes = set()
                for o in origenes:
                    if o.estado != CargaSaldo.Estado.CONFIRMADA:
                        raise ValidationError({"error": f"La carga #{o.pk} no está confirmada."})
                    if o.factura_id:
                        raise ValidationError({"error": f"La carga #{o.pk} ya tiene factura."})
                    c = o.cliente_origen or (o.tarjeta.hijo.cliente_responsable if o.tarjeta and o.tarjeta.hijo else None)
                    if not c:
                        raise ValidationError({"error": f"La carga #{o.pk} no tiene cliente."})
                    clientes.add(c.pk)

                if len(clientes) > 1:
                    raise ValidationError({"error": "Todos los ítems deben pertenecer al mismo cliente."})

                cliente_obj = (origenes[0].cliente_origen
                               or origenes[0].tarjeta.hijo.cliente_responsable)
                monto_total = sum(o.monto_cargado for o in origenes)
                iva = cls._calcular_iva_10(monto_total)

            elif tipo == TIPO_PAGO_ALMUERZO:
                origenes = list(
                    PagoCuentaAlmuerzo.objects
                    .select_related("cuenta__hijo__cliente_responsable")
                    .select_for_update()
                    .filter(pk__in=ids)
                )
                if len(origenes) != len(ids):
                    raise ValidationError({"error": "Uno o más ítems no existen."})

                clientes = set()
                for o in origenes:
                    if o.factura_id:
                        raise ValidationError({"error": f"El pago #{o.pk} ya tiene factura."})
                    clientes.add(o.cuenta.hijo.cliente_responsable_id)

                if len(clientes) > 1:
                    raise ValidationError({"error": "Todos los ítems deben pertenecer al mismo cliente."})

                cliente_obj = origenes[0].cuenta.hijo.cliente_responsable
                monto_total = sum(o.monto for o in origenes)
                iva = cls._calcular_iva_10(monto_total)

            elif tipo == TIPO_VENTA:
                from apps.ventas.models import Venta as VentaModel
                origenes = list(
                    VentaModel.objects
                    .select_related("cliente")
                    .select_for_update(of=("self",))
                    .filter(pk__in=ids)
                )
                if len(origenes) != len(ids):
                    raise ValidationError({"error": "Uno o más ventas no existen."})

                clientes = set()
                for o in origenes:
                    if o.estado == VentaModel.Estado.ANULADA:
                        raise ValidationError({"error": f"La venta #{o.pk} está anulada."})
                    if not o.genera_factura_legal:
                        raise ValidationError({"error": f"La venta #{o.pk} no requiere factura legal."})
                    if o.factura_id:
                        raise ValidationError({"error": f"La venta #{o.pk} ya tiene factura."})
                    clientes.add(o.cliente_id)

                if len(clientes) > 1:
                    raise ValidationError({"error": "Todas las ventas deben pertenecer al mismo cliente."})

                cliente_obj = origenes[0].cliente
                monto_total = sum(o.monto_total for o in origenes)
                iva = {
                    "iva_10": sum(o.iva_10 for o in origenes),
                    "iva_5": sum(o.iva_5 for o in origenes),
                    "monto_exenta": sum(o.monto_exenta for o in origenes),
                }

            elif tipo == TIPO_PAGO_CREDITO:
                from apps.clientes.models import CuentaCorrienteCliente as CCModel
                origenes = list(
                    CCModel.objects
                    .select_related("cliente")
                    .select_for_update(of=("self",))
                    .filter(pk__in=ids)
                )
                if len(origenes) != len(ids):
                    raise ValidationError({"error": "Uno o más pagos no existen."})

                clientes = set()
                for o in origenes:
                    if not o.genera_factura_legal:
                        raise ValidationError({"error": f"El pago #{o.pk} no requiere factura legal."})
                    if o.factura_id:
                        raise ValidationError({"error": f"El pago #{o.pk} ya tiene factura."})
                    clientes.add(o.cliente_id)

                if len(clientes) > 1:
                    raise ValidationError({"error": "Todos los pagos deben pertenecer al mismo cliente."})

                cliente_obj = origenes[0].cliente
                monto_total = sum(o.monto for o in origenes)
                iva = cls._calcular_iva_10(monto_total)

            else:
                raise ValidationError({"error": f"Tipo desconocido: {tipo}."})

            factura = FacturacionService.emitir_factura(
                cliente=cliente_obj,
                nro_factura=nro_factura,
                monto_total=monto_total,
                **iva,
            )

            for o in origenes:
                o.factura = factura
                if tipo == TIPO_VENTA:
                    o.nro_factura = nro_factura
                    o.save(update_fields=["factura", "nro_factura"])
                else:
                    o.save(update_fields=["factura"])

            return factura
