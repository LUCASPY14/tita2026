import logging
from celery import shared_task
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.usuarios.tasks.limpiar_audit_logs",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def limpiar_audit_logs():
    """
    Elimina registros de auditoría y logs de seguridad con más de los días configurados.

    Política de retención:
      - auditoria_operaciones → 365 días
      - intentos_login        →  90 días
      - intentos_2fa          →  90 días
    """
    from django.utils import timezone
    from apps.usuarios.models import (
        AuditoriaOperacion,
        IntentoLogin,
        Intento2FA,
    )

    ahora = timezone.now()

    targets = [
        ("auditoria_operaciones", AuditoriaOperacion, "fecha_operacion", ahora - timedelta(days=365)),
        ("intentos_login",        IntentoLogin,        "fecha_intento",   ahora - timedelta(days=90)),
        ("intentos_2fa",          Intento2FA,          "fecha_intento",   ahora - timedelta(days=90)),
    ]

    resultado = {}
    total = 0
    for nombre, modelo, campo_fecha, corte in targets:
        eliminados, _ = modelo.objects.filter(**{f"{campo_fecha}__lt": corte}).delete()
        resultado[nombre] = eliminados
        total += eliminados
        logger.info("limpiar_audit_logs: %s — %d eliminados (antes de %s)", nombre, eliminados, corte.date())

    logger.info("limpiar_audit_logs: total %d registros eliminados", total)
    return resultado
