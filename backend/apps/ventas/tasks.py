import logging
from celery import shared_task
from django.db import models as db_models, transaction
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.ventas.tasks.generar_resumen_diario_ventas",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def generar_resumen_diario_ventas():
    """Registra en log el resumen de ventas del día anterior."""
    from apps.ventas.models import Venta

    ayer = (timezone.now() - timedelta(days=1)).date()

    ventas = Venta.objects.filter(fecha__date=ayer)
    total = ventas.aggregate(
        cantidad=db_models.Count("id_venta"),
        monto=db_models.Sum("monto_total"),
    )

    resumen = {
        "fecha": ayer.isoformat(),
        "cantidad_ventas": total["cantidad"] or 0,
        "monto_total": int(total["monto"] or 0),
    }
    logger.info("Resumen diario ventas: %s", resumen)
    return resumen


@shared_task(
    name="apps.ventas.tasks.cerrar_cajas_automatico",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def cerrar_cajas_automatico():
    """Cierra automáticamente las cajas que quedaron abiertas del día anterior."""
    from apps.contabilidad.models import CierreCaja, MovimientoCaja
    from django.db import models as m

    hoy = timezone.now().date()

    # Obtener IDs sin bloqueo — el lock se adquiere por fila dentro de cada transacción.
    pks_abiertos = list(
        CierreCaja.objects.filter(
            estado=CierreCaja.Estado.ABIERTO,
            fecha_apertura__date__lt=hoy,
        ).values_list("pk", flat=True)
    )

    cerradas = 0
    for pk in pks_abiertos:
        with transaction.atomic():
            # Re-fetch con lock dentro de la transacción para evitar doble cierre.
            try:
                cierre = CierreCaja.objects.select_for_update().get(
                    pk=pk, estado=CierreCaja.Estado.ABIERTO
                )
            except CierreCaja.DoesNotExist:
                continue  # Otro worker ya lo cerró

            ingresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre, tipo=MovimientoCaja.Tipo.INGRESO
                ).aggregate(total=m.Sum("monto"))["total"] or 0
            )
            egresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre, tipo=MovimientoCaja.Tipo.EGRESO
                ).aggregate(total=m.Sum("monto"))["total"] or 0
            )
            monto_esperado = cierre.monto_inicial + ingresos - egresos

            cierre.monto_contado_fisico = monto_esperado
            cierre.diferencia_efectivo = 0
            cierre.fecha_cierre = timezone.now()
            cierre.estado = CierreCaja.Estado.CERRADO
            cierre.save()
            cerradas += 1
            logger.warning(
                "Cierre automático caja #%d — Monto esperado: Gs. %s",
                cierre.pk, monto_esperado,
            )

    logger.info("cerrar_cajas_automatico: %d cajas cerradas", cerradas)
    return {"cajas_cerradas": cerradas}
