import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.core.tasks.crear_particion_anio_siguiente",
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
)
def crear_particion_anio_siguiente():
    """
    Crea las particiones del año siguiente para tablas históricas particionadas.
    Se ejecuta automáticamente el 1 de diciembre de cada año (via Celery Beat).
    Equivalente a: python manage.py create_year_partition --year <año+1>
    """
    from django.core.management import call_command
    from io import StringIO

    siguiente = timezone.now().year + 1
    out = StringIO()
    try:
        call_command("create_year_partition", year=siguiente, stdout=out)
        resultado = out.getvalue()
        logger.info("crear_particion_anio_siguiente: año=%d\n%s", siguiente, resultado)
        return {"año": siguiente, "resultado": resultado}
    except Exception as exc:
        logger.error("crear_particion_anio_siguiente: fallo para año=%d: %s", siguiente, exc)
        raise


@shared_task(
    name="apps.core.tasks.expirar_recargas_pendientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def expirar_recargas_pendientes():
    """Expira cargas de saldo PENDIENTE con más de 24 horas sin confirmar."""
    from .models import CargaSaldo

    limite = timezone.now() - timedelta(hours=24)
    actualizadas = CargaSaldo.objects.filter(
        estado=CargaSaldo.Estado.PENDIENTE,
        fecha_carga__lt=limite,
    ).update(estado=CargaSaldo.Estado.RECHAZADA)

    logger.info("expirar_recargas_pendientes: %d cargas expiradas", actualizadas)
    return {"expiradas": actualizadas}
