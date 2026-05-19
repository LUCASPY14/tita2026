import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="apps.notificaciones.tasks.generar_alertas_saldo_bajo")
def generar_alertas_saldo_bajo():
    """Genera notificaciones de saldo bajo para tarjetas que superaron el umbral."""
    from apps.core.models import Tarjeta
    from apps.notificaciones.models import Notificacion

    tarjetas = Tarjeta.objects.filter(
        estado=Tarjeta.Estado.ACTIVA,
        notificar_saldo_bajo=True,
        saldo_alerta__isnull=False,
    ).select_related("hijo__cliente_responsable__usuario_portal")

    creadas = 0
    for tarjeta in tarjetas:
        if not tarjeta.esta_en_alerta:
            continue

        # Evitar spam: solo una notificación cada 24h por tarjeta
        if tarjeta.ultima_notificacion_saldo:
            hace_24h = timezone.now() - timedelta(hours=24)
            if tarjeta.ultima_notificacion_saldo > hace_24h:
                continue

        try:
            usuario = tarjeta.hijo.cliente_responsable.usuario_portal
        except AttributeError:
            continue

        if not usuario:
            continue

        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.SALDO_BAJO,
            titulo="Saldo bajo en tarjeta",
            mensaje=(
                f"La tarjeta de {tarjeta.hijo.nombre_completo} tiene un saldo de "
                f"Gs. {int(tarjeta.saldo_actual):,} — por debajo del umbral configurado."
            ),
            destino=Notificacion.Destino.SISTEMA,
        )
        tarjeta.ultima_notificacion_saldo = timezone.now()
        tarjeta.save(update_fields=["ultima_notificacion_saldo"])
        creadas += 1

    logger.info("generar_alertas_saldo_bajo: %d notificaciones creadas", creadas)
    return {"notificaciones_creadas": creadas}


@shared_task(name="apps.notificaciones.tasks.limpiar_notificaciones_antiguas")
def limpiar_notificaciones_antiguas():
    """Elimina notificaciones leídas con más de 90 días."""
    from apps.notificaciones.models import Notificacion

    limite = timezone.now() - timedelta(days=90)
    eliminadas, _ = Notificacion.objects.filter(
        leida=True,
        fecha_creacion__lt=limite,
    ).delete()

    logger.info("limpiar_notificaciones_antiguas: %d eliminadas", eliminadas)
    return {"eliminadas": eliminadas}


@shared_task(name="apps.notificaciones.tasks.enviar_emails_pendientes")
def enviar_emails_pendientes():
    """
    Procesa Notificaciones con destino=EMAIL aún no leídas y envía el email.
    Marca como leída cada una tras el intento (exitoso o fallido con error registrado).
    Se ejecuta cada 15 minutos.
    """
    from apps.notificaciones.models import Notificacion
    from apps.notificaciones.services import EmailService

    pendientes = Notificacion.objects.filter(
        destino=Notificacion.Destino.EMAIL,
        leida=False,
    ).select_related("usuario")

    enviados = 0
    errores = 0
    for notif in pendientes:
        ok = EmailService.enviar_notificacion(notif)
        # Marcar leída independientemente del resultado para no reintentar indefinidamente
        notif.leida = True
        notif.fecha_lectura = timezone.now()
        notif.save(update_fields=["leida", "fecha_lectura"])
        if ok:
            enviados += 1
        else:
            errores += 1

    logger.info(
        "enviar_emails_pendientes: %d enviados, %d errores",
        enviados, errores,
    )
    return {"enviados": enviados, "errores": errores}
