import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="apps.core.tasks.expirar_recargas_pendientes")
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
