"""
Celery Tasks para Sistema de Notificaciones

Este módulo contiene tasks asíncronas para:
- Alertas de saldo bajo
- Envío diferido de emails
- Envío masivo de notificaciones
- Limpieza de notificaciones antiguas

Se ejecutan vía Celery Beat (programadas) o manual
"""

from celery import shared_task
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
import logging

from apps.notificaciones.services import NotificacionService
from apps.notificaciones.services.email_service import EmailService
from apps.notificaciones.services.sms_service import SMSService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generar_alertas_saldo_bajo(self):
    """
    Task programada: Genera alertas de saldo bajo.

    Se ejecuta diariamente a las 8 AM (configurado en celery.py)

    Returns:
        {
            'success': bool,
            'alertas_generadas': int,
            'alertas_enviadas': int,
            'errores': List[str]
        }
    """
    try:
        logger.info("Iniciando generación de alertas de saldo bajo")

        resultado = NotificacionService.generar_alertas_automaticas()

        logger.info(
            f"Alertas completadas - Generadas: {resultado.get('alertas_generadas', 0)}, "
            f"Enviadas: {resultado.get('alertas_enviadas', 0)}"
        )

        return resultado

    except Exception as e:
        logger.error(f"Error en generar_alertas_saldo_bajo: {str(e)}")
        # Retry automático
        raise self.retry(exc=e, countdown=300)  # Retry en 5 min


@shared_task
def enviar_email_async(email_destinatario: str, nombre_destinatario: str, asunto: str, mensaje: str):
    """
    Task para enviar email de forma asíncrona.

    Args:
        email_destinatario: Email del destinatario
        nombre_destinatario: Nombre del destinatario
        asunto: Asunto del email
        mensaje: Cuerpo del mensaje

    Returns:
        {
            'success': bool,
            'id_email': int
        }
    """
    try:
        resultado = EmailService.enviar_email_generico(
            email_destinatario=email_destinatario,
            nombre_destinatario=nombre_destinatario,
            asunto=asunto,
            mensaje=mensaje,
        )

        return resultado

    except Exception as e:
        logger.error(f"Error en enviar_email_async: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def enviar_sms_async(telefono: str, mensaje: str):
    """
    Task para enviar SMS de forma asíncrona.

    Args:
        telefono: Número de teléfono destino
        mensaje: Texto del SMS

    Returns:
        {
            'success': bool,
            'message_id': str
        }
    """
    try:
        resultado = SMSService.enviar_sms(telefono=telefono, mensaje=mensaje)

        return resultado

    except Exception as e:
        logger.error(f"Error en enviar_sms_async: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=2)
def limpiar_notificaciones_antiguas(self):
    """
    Task programada: Limpia notificaciones leídas >30 días.

    Se ejecuta semanalmente.

    Returns:
        {
            'success': bool,
            'notificaciones_eliminadas': int
        }
    """
    try:
        from apps.notificaciones.models import NotificacionesPortal, NotificacionesSaldo

        # Fecha límite: 30 días atrás
        fecha_limite = timezone.now() - timedelta(days=30)

        # Eliminar notificaciones portal leídas antiguas
        portal_eliminadas = NotificacionesPortal.objects.filter(leida=1, fecha_lectura__lt=fecha_limite).delete()[0]

        # Eliminar notificaciones saldo leídas antiguas
        saldo_eliminadas = NotificacionesSaldo.objects.filter(leida=1, fecha_lectura__lt=fecha_limite).delete()[0]

        total_eliminadas = portal_eliminadas + saldo_eliminadas

        logger.info(f"Notificaciones antiguas eliminadas: {total_eliminadas}")

        return {
            "success": True,
            "notificaciones_eliminadas": total_eliminadas,
            "portal": portal_eliminadas,
            "saldo": saldo_eliminadas,
        }

    except Exception as e:
        logger.error(f"Error en limpiar_notificaciones_antiguas: {str(e)}")
        raise self.retry(exc=e, countdown=600)


@shared_task
def notificar_recarga_exitosa(id_recarga: int, id_usuario_portal: int = None):
    """
    Task para enviar notificación de recarga exitosa.

    Args:
        id_recarga: ID de la recarga
        id_usuario_portal: ID del usuario portal (opcional)

    Returns:
        {
            'success': bool,
            'id_notificacion': int
        }
    """
    try:
        resultado = NotificacionService.enviar_notificacion_recarga(
            id_recarga=id_recarga, id_usuario_portal=id_usuario_portal
        )

        return resultado

    except Exception as e:
        logger.error(f"Error en notificar_recarga_exitosa: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def notificar_consumo_realizado(id_consumo: int, id_usuario_portal: int = None):
    """
    Task para enviar notificación de consumo.

    Args:
        id_consumo: ID del consumo
        id_usuario_portal: ID del usuario portal

    Returns:
        {
            'success': bool
        }
    """
    try:
        resultado = NotificacionService.enviar_notificacion_consumo(
            id_consumo=id_consumo, id_usuario_portal=id_usuario_portal
        )

        return resultado

    except Exception as e:
        logger.error(f"Error en notificar_consumo_realizado: {str(e)}")
        return {"success": False, "error": str(e)}
