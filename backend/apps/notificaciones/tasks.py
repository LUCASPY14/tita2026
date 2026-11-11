import logging
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta

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
        cliente = tarjeta.hijo.cliente_responsable
        from apps.notificaciones.models import PreferenciaNotificacion, SolicitudNotificacion
        wa_pref = PreferenciaNotificacion.objects.filter(
            usuario=usuario,
            tipo_notificacion="SALDO_BAJO",
            whatsapp_activo=True,
        ).exists()
        if wa_pref and getattr(cliente, "telefono", None):
            SolicitudNotificacion.objects.create(
                cliente=cliente,
                tipo="SALDO_BAJO",
                destino=Notificacion.Destino.WHATSAPP,
                mensaje=msg_saldo,
            )
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


@shared_task(
    name="apps.notificaciones.tasks.enviar_whatsapp_cliente",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def enviar_whatsapp_cliente(cliente_id, mensaje):
    """
    Envía un WhatsApp a un cliente fuera del ciclo request/response.

    whatsapp_cliente() nunca debe llamarse de forma síncrona dentro de una
    vista: con ATOMIC_REQUESTS=True la conexión a la DB queda abierta en
    transacción durante toda la llamada, y si WAHA está lento o desconectado,
    idle_in_transaction_session_timeout (10s en producción) mata la conexión
    y tira 500 la operación que originó el aviso (venta, recarga, comedor).
    Dispatchear esto con transaction.on_commit(lambda: enviar_whatsapp_cliente.delay(...))
    desacopla el envío por completo de esa transacción.
    """
    from apps.clientes.models import Cliente

    from apps.notificaciones.services import whatsapp_cliente

    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return
    whatsapp_cliente(cliente, mensaje)


@shared_task(
    name="apps.notificaciones.tasks.procesar_solicitudes_pendientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def procesar_solicitudes_pendientes():
    """Procesa SolicitudNotificacion en estado PENDIENTE (sistema/email/WhatsApp)."""
    from apps.notificaciones.services import NotificacionService

    resultado = NotificacionService.procesar_pendientes()
    logger.info(
        "procesar_solicitudes_pendientes: %d enviadas, %d fallidas",
        resultado["enviadas"], resultado["fallidas"],
    )
    return resultado


_WAHA_CACHE_CAIDA_DESDE = "waha_sesion_caida_desde"
_WAHA_CACHE_AVISADO = "waha_sesion_avisado"
_WAHA_MINUTOS_ANTES_DE_AVISAR = 15
_WAHA_SEGUNDOS_ENTRE_AVISOS = 4 * 60 * 60  # 4 horas — reavisa si sigue caída


@shared_task(
    name="apps.notificaciones.tasks.verificar_sesion_waha",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
)
def verificar_sesion_waha():
    """
    Revisa el estado de la sesión de WhatsApp (WAHA) y avisa a los ADMIN si
    quedó caída (cualquier estado distinto de WORKING) por más de
    _WAHA_MINUTOS_ANTES_DE_AVISAR minutos seguidos — no apenas un blip
    momentáneo de reconexión, que WAHA resuelve solo en segundos.

    No se reconecta sola: eso requiere escanear el QR a mano desde
    Configuración → WhatsApp (ver apps.core — botón "Conectar WhatsApp").
    El aviso usa notificación interna + email, porque WhatsApp es justo el
    canal que puede estar caído; no se repite antes de
    _WAHA_SEGUNDOS_ENTRE_AVISOS para no spamear mientras sigue caída.
    """
    import requests
    from django.conf import settings
    from django.core.cache import cache

    from apps.notificaciones.services import EmailService
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    base_url = getattr(settings, "EVOLUTION_API_URL", "").rstrip("/")
    session = getattr(settings, "EVOLUTION_API_INSTANCE", "default")
    if not base_url:
        return {"estado": "sin_configurar"}

    headers = {}
    api_key = getattr(settings, "EVOLUTION_API_KEY", "")
    if api_key:
        headers["X-Api-Key"] = api_key

    try:
        resp = requests.get(f"{base_url}/api/sessions/{session}", headers=headers, timeout=10)
        resp.raise_for_status()
        estado = resp.json().get("status", "")
    except Exception as exc:
        logger.warning("verificar_sesion_waha: no se pudo consultar WAHA: %s", exc)
        return {"estado": "error_consulta"}

    if estado == "WORKING":
        cache.delete(_WAHA_CACHE_CAIDA_DESDE)
        cache.delete(_WAHA_CACHE_AVISADO)
        return {"estado": estado}

    caida_desde = cache.get(_WAHA_CACHE_CAIDA_DESDE)
    if caida_desde is None:
        cache.set(_WAHA_CACHE_CAIDA_DESDE, timezone.now().isoformat(), timeout=None)
        return {"estado": estado, "recien_detectado": True}

    minutos_caida = (timezone.now() - datetime.fromisoformat(caida_desde)).total_seconds() / 60
    if minutos_caida < _WAHA_MINUTOS_ANTES_DE_AVISAR:
        return {"estado": estado, "minutos_caida": round(minutos_caida, 1)}

    if cache.get(_WAHA_CACHE_AVISADO):
        return {"estado": estado, "minutos_caida": round(minutos_caida, 1), "ya_avisado": True}

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    titulo = "WhatsApp desconectado"
    mensaje = (
        f"La sesión de WhatsApp quedó en estado '{estado}' hace más de "
        f"{_WAHA_MINUTOS_ANTES_DE_AVISAR} minutos y no se reconecta sola. "
        "Entrá a Configuración → WhatsApp y escaneá el código QR con el "
        "celular de la cantina lo antes posible."
    )
    for admin in admins:
        Notificacion.objects.create(
            usuario=admin,
            tipo=Notificacion.Tipo.SISTEMA,
            titulo=titulo,
            mensaje=mensaje,
            destino=Notificacion.Destino.SISTEMA,
        )
        if admin.email:
            try:
                EmailService.enviar_simple(admin.email, admin.nombre, titulo, mensaje)
            except Exception as exc:
                logger.warning("verificar_sesion_waha: no se pudo enviar email a %s: %s", admin.email, exc)

    cache.set(_WAHA_CACHE_AVISADO, True, timeout=_WAHA_SEGUNDOS_ENTRE_AVISOS)
    logger.warning(
        "verificar_sesion_waha: sesión en estado %s hace %.1f min, %d admins avisados",
        estado, minutos_caida, len(admins),
    )
    return {"estado": estado, "minutos_caida": round(minutos_caida, 1), "admins_avisados": len(admins)}
