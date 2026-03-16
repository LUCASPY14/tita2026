"""
Service Layer para Envío de SMS

Soporta múltiples providers:
- Twilio
- AWS SNS
- Infobip (Paraguay)

Configuración en settings.py:
- SMS_PROVIDER = 'twilio' | 'aws_sns' | 'infobip'
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
- INFOBIP_API_KEY, INFOBIP_BASE_URL, INFOBIP_SENDER

Autor: Cantina Tita Development Team
"""

from decimal import Decimal
from typing import Dict, Optional
import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service Layer para envío de SMS multicanal.

    Métodos principales:
    - enviar_sms()
    - enviar_sms_twilio()
    - enviar_sms_infobip()
    """

    @staticmethod
    def enviar_sms(telefono: str, mensaje: str, prioridad: str = "normal") -> Dict:
        """
        Envía SMS usando el provider configurado.

        Args:
            telefono: Número de teléfono (formato: +595981234567)
            mensaje: Texto del mensaje
            prioridad: 'alta' | 'normal' | 'baja'

        Returns:
            {
                'success': bool,
                'message_id': str,
                'provider': str,
                'costo': Decimal (opcional)
            }
        """
        # Validar que SMS esté estado
        sms_activo = getattr(settings, "SMS_ENABLED", True)
        solo_produccion = getattr(settings, "SMS_SOLO_PRODUCCION", False)

        if not sms_activo:
            logger.warning("SMS desactivado en settings")
            return {"success": False, "error": "SMS desactivado"}

        if solo_produccion and settings.DEBUG:
            logger.warning("SMS solo en producción")
            return {"success": False, "error": "SMS solo habilitado en producción"}

        # Normalizar teléfono
        telefono_limpio = SMSService._normalizar_telefono(telefono)

        # Obtener provider configurado
        provider = getattr(settings, "SMS_PROVIDER", "twilio")

        # Enviar según provider
        if provider == "twilio":
            return SMSService.enviar_sms_twilio(telefono_limpio, mensaje)

        elif provider == "infobip":
            return SMSService.enviar_sms_infobip(telefono_limpio, mensaje)

        elif provider == "aws_sns":
            return SMSService.enviar_sms_aws(telefono_limpio, mensaje)

        else:
            logger.error(f"Provider SMS '{provider}' no soportado")
            return {"success": False, "error": f"Provider '{provider}' no configurado"}

    @staticmethod
    def enviar_sms_twilio(telefono: str, mensaje: str) -> Dict:
        """
        Envía SMS via Twilio.

        Requiere configuración:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER

        Args:
            telefono: Número destino (+595981234567)
            mensaje: Texto del SMS

        Returns:
            {
                'success': bool,
                'message_id': str,
                'provider': 'twilio'
            }
        """
        try:
            # Intentar importar Twilio
            try:
                from twilio.rest import Client  # type: ignore
            except ImportError:
                logger.error("Paquete 'twilio' no instalado. Run: pip install twilio")
                return {"success": False, "error": "Twilio no instalado"}

            # Obtener credenciales
            account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
            auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
            from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "")

            if not all([account_sid, auth_token, from_number]):
                logger.error("Credenciales Twilio incompletas")
                return {"success": False, "error": "Credenciales Twilio no configuradas"}

            # Crear cliente Twilio
            client = Client(account_sid, auth_token)

            # Enviar SMS
            message = client.messages.create(body=mensaje, from_=from_number, to=telefono)

            logger.info(f"SMS Twilio enviado: {message.sid}")

            return {
                "success": True,
                "message_id": message.sid,
                "provider": "twilio",
                "status": message.status,
            }

        except Exception as e:
            logger.error(f"Error enviando SMS Twilio: {str(e)}")
            return {"success": False, "error": str(e), "provider": "twilio"}

    @staticmethod
    def enviar_sms_infobip(telefono: str, mensaje: str) -> Dict:
        """
        Envía SMS via Infobip (provider popular en Paraguay).

        Requiere configuración:
        - INFOBIP_API_KEY
        - INFOBIP_BASE_URL (api.infobip.com)
        - INFOBIP_SENDER (nombre del remitente)

        Args:
            telefono: Número destino (+595981234567)
            mensaje: Texto del SMS

        Returns:
            {
                'success': bool,
                'message_id': str,
                'provider': 'infobip'
            }
        """
        try:
            # Obtener credenciales
            api_key = getattr(settings, "INFOBIP_API_KEY", "")
            base_url = getattr(settings, "INFOBIP_BASE_URL", "https://api.infobip.com")
            sender = getattr(settings, "INFOBIP_SENDER", "Cantina Tita")

            if not api_key:
                logger.error("INFOBIP_API_KEY no configurada")
                return {"success": False, "error": "API Key Infobip no configurada"}

            # Construir request
            url = f"{base_url}/sms/2/text/advanced"

            headers = {
                "Authorization": f"App {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            payload = {
                "messages": [{"from": sender, "destinations": [{"to": telefono}], "text": mensaje}]
            }

            # Enviar request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            # Parsear respuesta
            data = response.json()

            if data.get("messages") and len(data["messages"]) > 0:
                message_id = data["messages"][0].get("messageId")
                status = data["messages"][0].get("status", {}).get("name")

                logger.info(f"SMS Infobip enviado: {message_id}")

                return {
                    "success": True,
                    "message_id": message_id,
                    "provider": "infobip",
                    "status": status,
                }
            else:
                return {
                    "success": False,
                    "error": "Respuesta Infobip inválida",
                    "provider": "infobip",
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error HTTP Infobip: {str(e)}")
            return {"success": False, "error": str(e), "provider": "infobip"}

        except Exception as e:
            logger.error(f"Error enviando SMS Infobip: {str(e)}")
            return {"success": False, "error": str(e), "provider": "infobip"}

    @staticmethod
    def enviar_sms_aws(telefono: str, mensaje: str) -> Dict:
        """
        Envía SMS via AWS SNS.

        Requiere:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION (us-east-1)

        Args:
            telefono: Número destino
            mensaje: Texto del SMS

        Returns:
            {
                'success': bool,
                'message_id': str
            }
        """
        try:
            # Intentar importar boto3
            try:
                import boto3  # type: ignore
            except ImportError:
                logger.error("Paquete 'boto3' no instalado. Run: pip install boto3")
                return {"success": False, "error": "boto3 no instalado"}

            # Crear cliente SNS
            sns_client = boto3.client(
                "sns",
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", ""),
                region_name=getattr(settings, "AWS_REGION", "us-east-1"),
            )

            # Enviar SMS
            response = sns_client.publish(
                PhoneNumber=telefono,
                Message=mensaje,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",  # O 'Promotional'
                    }
                },
            )

            message_id = response.get("MessageId")

            logger.info(f"SMS AWS SNS enviado: {message_id}")

            return {"success": True, "message_id": message_id, "provider": "aws_sns"}

        except Exception as e:
            logger.error(f"Error enviando SMS AWS: {str(e)}")
            return {"success": False, "error": str(e), "provider": "aws_sns"}

    @staticmethod
    def _normalizar_telefono(telefono: str) -> str:
        """
        Normaliza número de teléfono a formato internacional.

        Ejemplos:
        - '0981234567' → '+595981234567'
        - '981234567' → '+595981234567'
        - '+595981234567' → '+595981234567'

        Args:
            telefono: Número de teléfono

        Returns:
            Número en formato internacional (+595...)
        """
        # Limpiar espacios y guiones
        telefono_limpio = telefono.replace(" ", "").replace("-", "")

        # Si ya tiene código país, retornar
        if telefono_limpio.startswith("+"):
            return telefono_limpio

        # Si empieza con 0, quitar el 0
        if telefono_limpio.startswith("0"):
            telefono_limpio = telefono_limpio[1:]

        # Agregar código país Paraguay (+595)
        return f"+595{telefono_limpio}"

    @staticmethod
    def validar_formato_telefono(telefono: str) -> bool:
        """
        Valida que el teléfono tenga formato válido.

        Args:
            telefono: Número de teléfono

        Returns:
            True si es válido, False si no
        """
        telefono_limpio = SMSService._normalizar_telefono(telefono)

        # Verificar longitud
        # +595 + 9 dígitos = 13 caracteres
        if len(telefono_limpio) != 13:
            return False

        # Verificar que empiece con +595
        if not telefono_limpio.startswith("+595"):
            return False

        # Verificar que el resto sean dígitos
        if not telefono_limpio[1:].isdigit():
            return False

        return True
