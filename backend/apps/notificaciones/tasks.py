import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.notificaciones.tasks.generar_alertas_saldo_bajo",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
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

        msg_saldo = (
            f"La tarjeta de {tarjeta.hijo.nombre_completo} tiene un saldo de "
            f"Gs. {int(tarjeta.saldo_actual):,} por debajo del umbral configurado. "
            f"Por favor recarga la tarjeta."
        )
        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.SALDO_BAJO,
            titulo="Saldo bajo en tarjeta",
            mensaje=msg_saldo,
            destino=Notificacion.Destino.SISTEMA,
        )
        from apps.notificaciones.services import _whatsapp_cliente
        _whatsapp_cliente(tarjeta.hijo.cliente_responsable, msg_saldo)
        tarjeta.ultima_notificacion_saldo = timezone.now()
        tarjeta.save(update_fields=["ultima_notificacion_saldo"])
        creadas += 1

    logger.info("generar_alertas_saldo_bajo: %d notificaciones creadas", creadas)
    return {"notificaciones_creadas": creadas}


@shared_task(
    name="apps.notificaciones.tasks.limpiar_notificaciones_antiguas",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
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


MAX_EMAIL_INTENTOS = 3


@shared_task(
    name="apps.notificaciones.tasks.enviar_emails_pendientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def enviar_emails_pendientes():
    """
    Procesa Notificaciones con destino=EMAIL aún no leídas y envía el email.

    Retry logic:
      - Éxito:   marca leida=True.
      - Fallo:   incrementa email_intentos; NO marca leida para reintentar
                 en la próxima ejecución (cada 15 min).
      - Tras MAX_EMAIL_INTENTOS fallos: marca leida=True y loguea warning.
    """
    from apps.notificaciones.models import Notificacion
    from apps.notificaciones.services import EmailService

    pendientes = Notificacion.objects.filter(
        destino=Notificacion.Destino.EMAIL,
        leida=False,
    ).select_related("usuario")

    enviados = 0
    errores = 0
    descartados = 0

    for notif in pendientes:
        if notif.email_intentos >= MAX_EMAIL_INTENTOS:
            logger.warning(
                "enviar_emails_pendientes: notif #%d descartada tras %d intentos — %s",
                notif.pk, notif.email_intentos, notif.titulo,
            )
            notif.leida = True
            notif.fecha_lectura = timezone.now()
            notif.save(update_fields=["leida", "fecha_lectura"])
            descartados += 1
            continue

        try:
            if not notif.usuario.email:
                raise ValueError("El usuario no tiene email registrado.")
            EmailService.enviar_simple(
                destinatario_email=notif.usuario.email,
                destinatario_nombre=notif.usuario.nombre_completo,
                asunto=notif.titulo,
                cuerpo=notif.mensaje,
            )
            notif.leida = True
            notif.fecha_lectura = timezone.now()
            notif.save(update_fields=["leida", "fecha_lectura", "email_intentos"])
            enviados += 1
        except Exception as exc:
            notif.email_intentos += 1
            notif.save(update_fields=["email_intentos"])
            logger.error(
                "Error enviando email notif #%d (intento %d/%d): %s",
                notif.pk, notif.email_intentos, MAX_EMAIL_INTENTOS, exc,
            )
            errores += 1

    logger.info(
        "enviar_emails_pendientes: %d enviados, %d errores, %d descartados",
        enviados, errores, descartados,
    )
    return {"enviados": enviados, "errores": errores, "descartados": descartados}
