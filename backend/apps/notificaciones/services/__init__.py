"""
Service Layer para Sistema de Notificaciones

Este módulo contiene la lógica de negocio para:
- Envío de notificaciones (Email, SMS, Push)
- Generación de alertas de saldo bajo
- Notificaciones de transacciones
- Preferencias de notificación
- Templates de mensajes

Autor: Cantina Tita Development Team
Fecha: Marzo 2026
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

from apps.notificaciones.models import (
    NotificacionesSaldo,
    NotificacionesPortal,
    SolicitudesNotificacion,
    PreferenciasNotificacion,
    EmailsEnviados,
)
from apps.core.models import Tarjetas
from apps.clientes.models import Clientes, Hijos
from apps.usuarios.models import UsuariosPortal

logger = logging.getLogger(__name__)


class NotificacionService:
    """
    Service Layer para gestión de notificaciones multicanal.

    Métodos principales:
    - enviar_notificacion_saldo_bajo()
    - enviar_notificacion_recarga()
    - enviar_notificacion_consumo()
    - generar_alertas_automaticas()
    - crear_solicitud_notificacion()
    - obtener_preferencias_usuario()
    """

    @staticmethod
    def enviar_notificacion_saldo_bajo(
        nro_tarjeta: str,
        saldo_actual: Decimal,
        saldo_alerta: Decimal,
        email_destinatario: Optional[str] = None,
        enviar_sms: bool = True,
    ) -> Dict:
        """
        Envía notificación de saldo bajo al responsable de la tarjeta.

        Args:
            nro_tarjeta: Número de tarjeta
            saldo_actual: Saldo actual de la tarjeta
            saldo_alerta: Nivel configurado de alerta
            email_destinatario: Email opcional (si no se provee, se obtiene del cliente)
            enviar_sms: Si debe enviar SMS además de email

        Returns:
            {
                'success': bool,
                'id_notificacion': int,
                'enviada_email': bool,
                'enviada_sms': bool,
                'mensaje': str
            }

        Raises:
            ValidationError: Si la tarjeta no existe o datos inválidos
        """
        try:
            # Validar tarjeta
            tarjeta = Tarjetas.objects.select_related("id_hijo__id_cliente").get(
                numero_tarjeta=nro_tarjeta
            )

            # Obtener cliente responsable
            hijo = tarjeta.id_hijo
            cliente = hijo.id_cliente

            # Determinar email destinatario
            if not email_destinatario:
                email_destinatario = cliente.email

            # Generar mensaje personalizado
            mensaje = (
                f"⚠️ ALERTA DE SALDO BAJO\n\n"
                f"Tarjeta: {nro_tarjeta}\n"
                f"Estudiante: {hijo.nombre} {hijo.apellido}\n"
                f"Saldo actual: ₲{saldo_actual:,.2f}\n"
                f"Límite de alerta: ₲{saldo_alerta:,.2f}\n\n"
                f"El saldo está por debajo del nivel configurado. "
                f"Considere realizar una recarga para evitar inconvenientes.\n\n"
                f"Cantina Tita - Sistema de Gestión"
            )

            # Crear notificación en BD
            notificacion = NotificacionesSaldo.objects.create(
                tipo_notificacion="saldo_bajo",
                saldo_actual=saldo_actual,
                mensaje=mensaje,
                enviada_email=0,  # Pendiente
                enviada_sms=0,  # Pendiente
                leida=0,
                email_destinatario=email_destinatario,
                fecha_creacion=timezone.now(),
                nro_tarjeta=tarjeta,
            )

            # Enviar por email
            email_enviado = False
            if email_destinatario:
                try:
                    from apps.notificaciones.services.email_service import EmailService

                    resultado_email = EmailService.enviar_alerta_saldo_bajo(
                        email_destinatario=email_destinatario,
                        nombre_destinatario=f"{cliente.nombre} {cliente.apellido}",
                        nro_tarjeta=nro_tarjeta,
                        nombre_hijo=f"{hijo.nombre} {hijo.apellido}",
                        saldo_actual=saldo_actual,
                        saldo_alerta=saldo_alerta,
                    )

                    email_enviado = resultado_email.get("success", False)

                except Exception as e:
                    logger.error(f"Error enviando email saldo bajo: {str(e)}")
                    email_enviado = False

            # Enviar por SMS
            sms_enviado = False
            if enviar_sms and cliente.telefono:
                try:
                    from apps.notificaciones.services.sms_service import SMSService

                    mensaje_sms = (
                        f"CANTINA TITA - Saldo bajo en tarjeta {nro_tarjeta}. "
                        f"Saldo: ₲{saldo_actual:,.0f}. "
                        f"Estudiante: {hijo.nombre}"
                    )

                    resultado_sms = SMSService.enviar_sms(
                        telefono=cliente.telefono, mensaje=mensaje_sms
                    )

                    sms_enviado = resultado_sms.get("success", False)

                except Exception as e:
                    logger.error(f"Error enviando SMS saldo bajo: {str(e)}")
                    sms_enviado = False

            # Actualizar notificación
            notificacion.enviada_email = 1 if email_enviado else 0
            notificacion.enviada_sms = 1 if sms_enviado else 0
            notificacion.fecha_envio = timezone.now() if (email_enviado or sms_enviado) else None
            notificacion.save()

            return {
                "success": True,
                "id_notificacion": notificacion.id_notificacion,
                "enviada_email": email_enviado,
                "enviada_sms": sms_enviado,
                "mensaje": mensaje,
            }

        except Tarjetas.DoesNotExist:
            raise ValidationError(f"Tarjeta {nro_tarjeta} no existe")

        except Exception as e:
            logger.error(f"Error en enviar_notificacion_saldo_bajo: {str(e)}")
            raise ValidationError(f"Error enviando notificación: {str(e)}")

    @staticmethod
    def enviar_notificacion_recarga(
        id_recarga: int, id_usuario_portal: Optional[int] = None
    ) -> Dict:
        """
        Envía notificación de recarga exitosa al portal del usuario.

        Args:
            id_recarga: ID de la recarga completada
            id_usuario_portal: ID del usuario portal (opcional)

        Returns:
            {
                'success': bool,
                'id_notificacion': int,
                'mensaje': str
            }
        """
        from apps.core.models import CargasSaldo

        try:
            # Obtener recarga
            recarga = CargasSaldo.objects.select_related("nro_tarjeta__id_hijo__id_cliente").get(
                id_recarga=id_recarga
            )

            # Verificar que esté completada
            if recarga.estado != "completada":
                raise ValidationError("Solo se notifican recargas completadas")

            # Obtener datos
            tarjeta = recarga.nro_tarjeta
            hijo = tarjeta.id_hijo

            # Generar mensaje
            titulo = "✅ Recarga Exitosa"
            mensaje = (
                f"Se ha acreditado correctamente una recarga a la tarjeta.\n\n"
                f"Estudiante: {hijo.nombre} {hijo.apellido}\n"
                f"Tarjeta: {tarjeta.numero_tarjeta}\n"
                f"Monto acreditado: ₲{recarga.monto_cargado:,.2f}\n"
                f"Método de pago: {recarga.metodo_pago}\n"
                f"Nuevo saldo: ₲{tarjeta.saldo_actual:,.2f}\n"
                f"Fecha: {recarga.fecha_carga.strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Gracias por confiar en Cantina Tita."
            )

            # Si no hay usuario portal, intentar obtenerlo
            if not id_usuario_portal:
                try:
                    usuario_portal = UsuariosPortal.objects.get(id_cliente=hijo.id_cliente)
                    id_usuario_portal_obj = usuario_portal
                except UsuariosPortal.DoesNotExist:
                    # No hay usuario portal, solo loguear
                    logger.warning(f"Cliente {hijo.id_cliente.id_cliente} no tiene usuario portal")
                    return {
                        "success": False,
                        "error": "Cliente no tiene usuario portal configurado",
                    }
            else:
                id_usuario_portal_obj = UsuariosPortal.objects.get(
                    id_usuario_portal=id_usuario_portal
                )

            # Crear notificación en portal
            notificacion = NotificacionesPortal.objects.create(
                tipo="recarga",
                titulo=titulo,
                mensaje=mensaje,
                leida=0,
                fecha_envio=timezone.now(),
                id_usuario_portal=id_usuario_portal_obj,
                creado_en=timezone.now(),
            )

            return {
                "success": True,
                "id_notificacion": notificacion.id_notificacion,
                "mensaje": mensaje,
            }

        except CargasSaldo.DoesNotExist:
            raise ValidationError(f"Recarga {id_recarga} no existe")

        except Exception as e:
            logger.error(f"Error en enviar_notificacion_recarga: {str(e)}")
            raise ValidationError(f"Error enviando notificación: {str(e)}")

    @staticmethod
    def enviar_notificacion_consumo(
        id_consumo: int, id_usuario_portal: Optional[int] = None
    ) -> Dict:
        """
        Envía notificación de consumo realizado.

        Args:
            id_consumo: ID del consumo registrado
            id_usuario_portal: ID del usuario portal

        Returns:
            {
                'success': bool,
                'id_notificacion': int
            }
        """
        from apps.core.models import ConsumosTarjeta

        try:
            # Obtener consumo
            consumo = ConsumosTarjeta.objects.select_related(
                "nro_tarjeta__id_hijo__id_cliente"
            ).get(id_consumo=id_consumo)

            tarjeta = consumo.nro_tarjeta
            hijo = tarjeta.id_hijo

            # Generar mensaje
            titulo = "🛒 Nuevo Consumo Registrado"
            mensaje = (
                f"Se ha registrado un consumo en la tarjeta.\n\n"
                f"Estudiante: {hijo.nombre} {hijo.apellido}\n"
                f"Monto: ₲{abs(consumo.monto_consumido):,.2f}\n"
                f"Saldo anterior: ₲{consumo.saldo_anterior:,.2f}\n"
                f"Saldo nuevo: ₲{consumo.saldo_nuevo:,.2f}\n"
                f"Fecha: {consumo.fecha_consumo.strftime('%d/%m/%Y %H:%M')}"
            )

            # Obtener usuario portal
            if not id_usuario_portal:
                try:
                    usuario_portal = UsuariosPortal.objects.get(id_cliente=hijo.id_cliente)
                    id_usuario_portal_obj = usuario_portal
                except UsuariosPortal.DoesNotExist:
                    return {"success": False, "error": "Cliente no tiene usuario portal"}
            else:
                id_usuario_portal_obj = UsuariosPortal.objects.get(
                    id_usuario_portal=id_usuario_portal
                )

            # Crear notificación
            notificacion = NotificacionesPortal.objects.create(
                tipo="consumo",
                titulo=titulo,
                mensaje=mensaje,
                leida=0,
                fecha_envio=timezone.now(),
                id_usuario_portal=id_usuario_portal_obj,
                creado_en=timezone.now(),
            )

            return {"success": True, "id_notificacion": notificacion.id_notificacion}

        except ConsumosTarjeta.DoesNotExist:
            raise ValidationError(f"Consumo {id_consumo} no existe")

        except Exception as e:
            logger.error(f"Error en enviar_notificacion_consumo: {str(e)}")
            raise ValidationError(f"Error enviando notificación: {str(e)}")

    @staticmethod
    @transaction.atomic
    def generar_alertas_automaticas() -> Dict:
        """
        Genera alertas automáticas de saldo bajo para todas las tarjetas.

        Lógica:
        - Busca tarjetas con saldo_actual <= saldo_alerta
        - Verifica que no se haya enviado alerta en las últimas 24h
        - Envía notificación por email y/o SMS según preferencias

        Returns:
            {
                'success': bool,
                'alertas_generadas': int,
                'alertas_enviadas': int,
                'errores': List[str]
            }

        Esta función se ejecuta automáticamente vía Celery Beat.
        """
        try:
            # Buscar tarjetas con saldo bajo
            tarjetas_bajo = Tarjetas.objects.filter(
                estado="Activa", saldo_actual__lte=models.F("saldo_alerta")
            ).select_related("id_hijo__id_cliente")

            alertas_generadas = 0
            alertas_enviadas = 0
            errores = []

            for tarjeta in tarjetas_bajo:
                # Verificar que no se haya enviado alerta reciente
                ultima_alerta = NotificacionesSaldo.objects.filter(
                    nro_tarjeta=tarjeta,
                    tipo_notificacion="saldo_bajo",
                    fecha_creacion__gte=timezone.now() - timedelta(hours=24),
                ).exists()

                if ultima_alerta:
                    continue  # Ya se envió alerta en últimas 24h

                # Generar alerta
                try:
                    resultado = NotificacionService.enviar_notificacion_saldo_bajo(
                        nro_tarjeta=tarjeta.numero_tarjeta,
                        saldo_actual=tarjeta.saldo_actual,
                        saldo_alerta=tarjeta.saldo_alerta or Decimal("10000.00"),
                    )

                    alertas_generadas += 1
                    if resultado.get("enviada_email") or resultado.get("enviada_sms"):
                        alertas_enviadas += 1

                except Exception as e:
                    errores.append(f"Tarjeta {tarjeta.numero_tarjeta}: {str(e)}")

            return {
                "success": True,
                "alertas_generadas": alertas_generadas,
                "alertas_enviadas": alertas_enviadas,
                "errores": errores,
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error en generar_alertas_automaticas: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def obtener_preferencias_usuario(id_usuario_portal: int) -> Dict:
        """
        Obtiene las preferencias de notificación del usuario.

        Args:
            id_usuario_portal: ID del usuario portal

        Returns:
            {
                'preferencias': List[{
                    'tipo_notificacion': str,
                    'email_activo': bool,
                    'push_activo': bool
                }]
            }
        """
        try:
            preferencias = PreferenciasNotificacion.objects.filter(
                id_usuario_portal=id_usuario_portal
            )

            return {
                "preferencias": [
                    {
                        "tipo_notificacion": pref.tipo_notificacion,
                        "email_activo": bool(pref.email_activo),
                        "push_activo": bool(pref.push_activo),
                    }
                    for pref in preferencias
                ]
            }

        except Exception as e:
            logger.error(f"Error obteniendo preferencias: {str(e)}")
            return {"preferencias": []}

    @staticmethod
    @transaction.atomic
    def marcar_notificacion_leida(id_notificacion: int, tipo: str = "portal") -> Dict:
        """
        Marca una notificación como leída.

        Args:
            id_notificacion: ID de la notificación
            tipo: 'portal' o 'saldo'

        Returns:
            {
                'success': bool,
                'fecha_lectura': datetime
            }
        """
        try:
            if tipo == "portal":
                notificacion = NotificacionesPortal.objects.get(id_notificacion=id_notificacion)
            else:
                notificacion = NotificacionesSaldo.objects.get(id_notificacion=id_notificacion)

            notificacion.leida = 1
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()

            return {"success": True, "fecha_lectura": notificacion.fecha_lectura}

        except (NotificacionesPortal.DoesNotExist, NotificacionesSaldo.DoesNotExist):
            raise ValidationError(f"Notificación {id_notificacion} no existe")

        except Exception as e:
            logger.error(f"Error marcando notificación como leída: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")


# =============================================================================
# IMPORT PARA ATOMIC
# =============================================================================
from django.db import models
