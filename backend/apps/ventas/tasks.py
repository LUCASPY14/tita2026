import logging
from celery import shared_task
from django.utils import timezone
from django.db import models as db_models
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="apps.ventas.tasks.generar_resumen_diario_ventas")
def generar_resumen_diario_ventas():
    """Registra en log el resumen de ventas del día anterior."""
    from apps.ventas.models import Venta

    ayer = (timezone.now() - timedelta(days=1)).date()

    ventas = Venta.objects.filter(fecha__date=ayer)
    total = ventas.aggregate(
        cantidad=db_models.Count("id"),
        monto=db_models.Sum("monto_total"),
    )

    resumen = {
        "fecha": ayer.isoformat(),
        "cantidad_ventas": total["cantidad"] or 0,
        "monto_total": int(total["monto"] or 0),
    }
    logger.info("Resumen diario ventas: %s", resumen)
    return resumen


@shared_task(name="apps.ventas.tasks.cerrar_cajas_automatico")
def cerrar_cajas_automatico():
    """Cierra automáticamente las cajas que quedaron abiertas del día anterior."""
    from apps.contabilidad.models import CierreCaja, MovimientoCaja
    from django.db import models as m

    hoy = timezone.now().date()

    cierres_abiertos = CierreCaja.objects.filter(
        estado=CierreCaja.Estado.ABIERTO,
        fecha_apertura__date__lt=hoy,
    ).select_for_update()

    cerradas = 0
    for cierre in cierres_abiertos:
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
