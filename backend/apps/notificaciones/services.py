"""
Servicio para procesar y enviar notificaciones.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import EmailEnviado, Notificacion, SolicitudNotificacion


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
            usuario = solicitud.cliente.usuario
        except Exception:
            raise ValueError(f"Cliente {solicitud.cliente} no tiene cuenta de usuario vinculada.")

        tipos_validos = {t[0] for t in Notificacion.Tipo.choices}
        tipo = solicitud.tipo if solicitud.tipo in tipos_validos else Notificacion.Tipo.SISTEMA

        Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=solicitud.tipo.replace("_", " ").capitalize(),
            mensaje=solicitud.mensaje,
            destino=Notificacion.Destino.SISTEMA,
        )

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
