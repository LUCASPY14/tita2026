"""
Servicio para procesar y enviar notificaciones.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import EmailEnviado, Notificacion, SolicitudNotificacion


def _whatsapp_cliente(cliente, mensaje: str) -> None:
    """
    Envía WhatsApp a un cliente si tiene teléfono configurado y las
    notificaciones están activas. Silencioso ante cualquier error.
    """
    if not getattr(settings, "NOTIFICACIONES_ACTIVAS", False):
        return
    telefono = getattr(cliente, "telefono", None)
    if not telefono:
        return
    try:
        enviar_whatsapp(telefono, mensaje)
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "WhatsApp no enviado a cliente %s: fallo silencioso", cliente.pk
        )


def crear_solicitudes_cobro(hijos_con_deuda, mensaje_template=None):
    """
    Crea SolicitudNotificacion para todos los responsables que reciben notificaciones
    de cobro de los alumnos indicados, en orden de prioridad (orden_cobro).

    Args:
        hijos_con_deuda: QuerySet o lista de Hijo con deuda.
        mensaje_template: Callable(hijo, responsable) -> str, o None para usar el
                          mensaje por defecto.

    Returns:
        int: cantidad de solicitudes creadas.
    """
    from apps.clientes.models import AlumnoResponsable

    solicitudes = []
    for hijo in hijos_con_deuda:
        responsables = (
            AlumnoResponsable.objects
            .filter(hijo=hijo, activo=True, recibe_notificaciones=True)
            .select_related("cliente")
            .order_by("orden_cobro")
        )
        for resp in responsables:
            if not resp.cliente.email and not resp.cliente.activo:
                continue
            if mensaje_template:
                mensaje = mensaje_template(hijo, resp)
            else:
                mensaje = (
                    f"Estimado/a {resp.cliente.nombre_completo}, "
                    f"le informamos que el alumno/a {hijo.nombre_completo} "
                    f"tiene saldo pendiente en la cantina. "
                    f"Por favor regularice su situacion. Gracias."
                )
            solicitudes.append(
                SolicitudNotificacion(
                    cliente=resp.cliente,
                    tipo="COBRO_PENDIENTE",
                    destino=Notificacion.Destino.EMAIL,
                    mensaje=mensaje,
                )
            )
            from .models import PreferenciaNotificacion
            tiene_whatsapp = PreferenciaNotificacion.objects.filter(
                usuario=resp.cliente.usuario_portal,
                tipo_notificacion="COBRO_PENDIENTE",
                whatsapp_activo=True,
            ).exists() if getattr(resp.cliente, "usuario_portal", None) else False
            if tiene_whatsapp and getattr(resp.cliente, "telefono", None):
                solicitudes.append(
                    SolicitudNotificacion(
                        cliente=resp.cliente,
                        tipo="COBRO_PENDIENTE",
                        destino=Notificacion.Destino.WHATSAPP,
                        mensaje=mensaje,
                    )
                )
    if solicitudes:
        SolicitudNotificacion.objects.bulk_create(solicitudes)

    return len(solicitudes)


class NotificacionService:

    @staticmethod
    def procesar_pendientes(solicitud_ids=None):
        """
        Procesa SolicitudNotificacion en estado PENDIENTE.
        Si se pasan solicitud_ids solo procesa esas.
        """
        qs = SolicitudNotificacion.objects.filter(
            estado=SolicitudNotificacion.Estado.PENDIENTE
        ).select_related("cliente").select_for_update(skip_locked=True)

        if solicitud_ids:
            qs = qs.filter(pk__in=solicitud_ids)

        resultados = {"enviadas": 0, "fallidas": 0, "ids_enviadas": [], "ids_fallidas": []}

        with transaction.atomic():
            for solicitud in qs:
                try:
                    if solicitud.destino == Notificacion.Destino.SISTEMA:
                        NotificacionService._enviar_sistema(solicitud)
                    elif solicitud.destino == Notificacion.Destino.EMAIL:
                        NotificacionService._enviar_email(solicitud)
                    elif solicitud.destino == Notificacion.Destino.WHATSAPP:
                        NotificacionService._enviar_whatsapp(solicitud)

                    solicitud.estado = SolicitudNotificacion.Estado.ENVIADA
                    solicitud.fecha_envio = timezone.now()
                    solicitud.save(update_fields=["estado", "fecha_envio"])
                    resultados["enviadas"] += 1
                    resultados["ids_enviadas"].append(solicitud.pk)
                except Exception as exc:
                    solicitud.estado = SolicitudNotificacion.Estado.FALLIDA
                    solicitud.save(update_fields=["estado"])
                    resultados["fallidas"] += 1
                    resultados["ids_fallidas"].append({"id": solicitud.pk, "error": str(exc)})

        return resultados

    @staticmethod
    def _enviar_sistema(solicitud):
        try:
            usuario = solicitud.cliente.usuario_portal
        except Exception:
            raise ValueError(f"Cliente {solicitud.cliente} no tiene cuenta de usuario vinculada.")

        tipos_validos = {t[0] for t in Notificacion.Tipo.choices}
        tipo = solicitud.tipo if solicitud.tipo in tipos_validos else Notificacion.Tipo.SISTEMA

        notif = Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=solicitud.tipo.replace("_", " ").capitalize(),
            mensaje=solicitud.mensaje,
            destino=Notificacion.Destino.SISTEMA,
        )
        push_ws_notificacion(notif)

    @staticmethod
    def _enviar_whatsapp(solicitud):
        cliente = solicitud.cliente
        telefono = getattr(cliente, "telefono", None)
        if not telefono:
            raise ValueError(f"Cliente {cliente} no tiene teléfono registrado.")
        enviar_whatsapp(telefono, solicitud.mensaje)

    @staticmethod
    def _enviar_email(solicitud):
        cliente = solicitud.cliente
        if not cliente.email:
            raise ValueError(f"Cliente {cliente} no tiene email registrado.")

        asunto = solicitud.tipo.replace("_", " ").capitalize()

        send_mail(
            subject=asunto,
            message=solicitud.mensaje,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "cantina@tita.edu.py"),
            recipient_list=[cliente.email],
            fail_silently=False,
        )

        EmailEnviado.objects.create(
            destinatario_email=cliente.email,
            destinatario_nombre=cliente.nombre_completo,
            asunto=asunto,
            cuerpo=solicitud.mensaje,
            estado=EmailEnviado.Estado.ENVIADO,
        )


def push_ws_notificacion(notificacion) -> None:
    """Envía la notificación recién creada al WebSocket del usuario en tiempo real."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        group = f"notificaciones_{notificacion.usuario_id}"
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "notificacion.nueva",
                "data": {
                    "id": notificacion.pk,
                    "tipo": notificacion.tipo,
                    "titulo": notificacion.titulo,
                    "mensaje": notificacion.mensaje,
                    "destino": notificacion.destino,
                    "leida": notificacion.leida,
                    "fecha_envio": notificacion.fecha_envio.isoformat(),
                },
            },
        )
    except Exception:
        pass


def send_push_to_user(usuario_id: int, title: str, body: str, url: str = "/", icon: str = "/logo_tita.png") -> None:
    """
    Envía una Web Push notification a todas las suscripciones activas de un usuario.
    Si VAPID_PRIVATE_KEY no está configurada, retorna silenciosamente.
    """
    from django.conf import settings

    vapid_pk    = getattr(settings, "VAPID_PRIVATE_KEY", "")
    vapid_email = getattr(settings, "VAPID_ADMIN_EMAIL", "admin@cantinatita.com")
    if not vapid_pk:
        return

    try:
        import json
        from pywebpush import webpush, WebPushException
        from .models import PushSubscription

        subs = list(PushSubscription.objects.filter(usuario_id=usuario_id, activa=True))
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                    },
                    data=json.dumps({"title": title, "body": body, "url": url, "icon": icon}),
                    vapid_private_key=vapid_pk,
                    vapid_claims={"sub": f"mailto:{vapid_email}"},
                )
            except WebPushException as exc:
                resp = getattr(exc, "response", None)
                if resp is not None and resp.status_code in (404, 410):
                    sub.delete()
            except Exception:
                pass
    except Exception:
        pass


class EmailService:
    """Envío directo de emails transaccionales (no ligados a SolicitudNotificacion)."""

    @staticmethod
    def enviar_simple(destinatario_email, destinatario_nombre, asunto, cuerpo):
        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "cantina@tita.edu.py"),
            recipient_list=[destinatario_email],
            fail_silently=False,
        )
        EmailEnviado.objects.create(
            destinatario_email=destinatario_email,
            destinatario_nombre=destinatario_nombre,
            asunto=asunto,
            cuerpo=cuerpo,
            estado=EmailEnviado.Estado.ENVIADO,
        )


def enviar_whatsapp(numero: str, mensaje: str) -> dict:
    """
    Envía un mensaje de WhatsApp usando WAHA (WhatsApp HTTP API, self-hosted).

    Args:
        numero: Número en formato internacional sin '+', ej. "595981234567"
        mensaje: Texto plano del mensaje

    Returns:
        dict con la respuesta de WAHA

    Raises:
        RuntimeError si EVOLUTION_API_URL no está configurada
        requests.HTTPError si la API responde con error HTTP
    """
    import requests

    base_url = getattr(settings, "EVOLUTION_API_URL", "").rstrip("/")
    session  = getattr(settings, "EVOLUTION_API_INSTANCE", "default")

    if not base_url:
        raise RuntimeError(
            "EVOLUTION_API_URL no está configurada en .env. "
            "Iniciá WAHA con: docker run -d --name waha -p 3000:3000 devlikeapro/waha:latest"
        )

    # Normalizar: quitar espacios, guiones y '+' inicial
    numero_limpio = numero.strip().lstrip("+").replace(" ", "").replace("-", "")
    # WAHA usa el formato E.164 con sufijo @c.us para contactos individuales
    chat_id = f"{numero_limpio}@c.us"

    url = f"{base_url}/api/sendText"
    headers = {"Content-Type": "application/json"}

    # WAHA CORE no requiere auth; si se configura API key se agrega aquí
    api_key = getattr(settings, "EVOLUTION_API_KEY", "")
    if api_key:
        headers["X-Api-Key"] = api_key

    payload = {
        "session": session,
        "chatId": chat_id,
        "text": mensaje,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()
