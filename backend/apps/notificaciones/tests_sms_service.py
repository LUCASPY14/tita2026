"""
Tests para notificaciones/services/sms_service.py
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.notificaciones.services.sms_service import SMSService


class SMSServiceNormalizarTelefonoTest(TestCase):
    """Tests para _normalizar_telefono"""

    def test_numero_local_con_cero(self):
        result = SMSService._normalizar_telefono("0981234567")
        self.assertEqual(result, "+595981234567")

    def test_numero_sin_cero(self):
        result = SMSService._normalizar_telefono("981234567")
        self.assertEqual(result, "+595981234567")

    def test_numero_con_codigo_pais(self):
        result = SMSService._normalizar_telefono("+595981234567")
        self.assertEqual(result, "+595981234567")

    def test_numero_con_espacios(self):
        result = SMSService._normalizar_telefono("098 123 4567")
        self.assertEqual(result, "+595981234567")

    def test_numero_con_guiones(self):
        result = SMSService._normalizar_telefono("0981-234-567")
        self.assertEqual(result, "+595981234567")


class SMSServiceValidarFormatoTest(TestCase):
    """Tests para validar_formato_telefono"""

    def test_numero_valido(self):
        self.assertTrue(SMSService.validar_formato_telefono("0981234567"))

    def test_numero_valido_con_codigo(self):
        self.assertTrue(SMSService.validar_formato_telefono("+595981234567"))

    def test_numero_muy_corto(self):
        self.assertFalse(SMSService.validar_formato_telefono("12345"))

    def test_numero_con_codigo_incorrecto(self):
        self.assertFalse(SMSService.validar_formato_telefono("+1234567890"))

    def test_numero_con_letras(self):
        self.assertFalse(SMSService.validar_formato_telefono("+595ABCDEFGHI"))


@override_settings(SMS_ENABLED=False)
class SMSServiceDesactivadoTest(TestCase):
    """Tests cuando SMS está desactivado"""

    def test_sms_desactivado_retorna_error(self):
        result = SMSService.enviar_sms("+595981234567", "Test")
        self.assertFalse(result["success"])
        self.assertIn("desactivado", result["error"])


@override_settings(SMS_ENABLED=True, SMS_SOLO_PRODUCCION=True, DEBUG=True)
class SMSServiceSoloProduccionTest(TestCase):
    """Tests cuando SMS solo está habilitado en producción"""

    def test_sms_solo_produccion_con_debug_retorna_error(self):
        result = SMSService.enviar_sms("+595981234567", "Test")
        self.assertFalse(result["success"])
        self.assertIn("producción", result["error"])


@override_settings(
    SMS_ENABLED=True, SMS_PROVIDER="twilio", TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", TWILIO_PHONE_NUMBER=""
)
class SMSServiceTwilioSinCredencialesTest(TestCase):
    """Tests de Twilio sin credenciales"""

    def test_twilio_sin_credenciales(self):
        try:
            from twilio.rest import Client  # type: ignore[import-untyped]

            # Si Twilio está instalado, faltarán credenciales
            result = SMSService.enviar_sms_twilio("+595981234567", "Test")
            self.assertFalse(result["success"])
        except ImportError:
            # Twilio no instalado, el método retorna error de importación
            result = SMSService.enviar_sms_twilio("+595981234567", "Test")
            self.assertFalse(result["success"])


@override_settings(SMS_ENABLED=True, SMS_PROVIDER="infobip", INFOBIP_API_KEY="")
class SMSServiceInfobipSinCredencialesTest(TestCase):
    """Tests de Infobip sin credenciales"""

    def test_infobip_sin_api_key(self):
        result = SMSService.enviar_sms_infobip("+595981234567", "Test")
        self.assertFalse(result["success"])
        self.assertIn("API Key", result["error"])


@override_settings(
    SMS_ENABLED=True, SMS_PROVIDER="infobip", INFOBIP_API_KEY="test-key", INFOBIP_BASE_URL="https://api.infobip.com"
)
class SMSServiceInfobipTest(TestCase):
    """Tests de Infobip con credenciales"""

    @patch("apps.notificaciones.services.sms_service.requests.post")
    def test_infobip_exitoso(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"messages": [{"messageId": "MSG123", "status": {"name": "PENDING"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = SMSService.enviar_sms_infobip("+595981234567", "Hola")
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "MSG123")
        self.assertEqual(result["provider"], "infobip")

    @patch("apps.notificaciones.services.sms_service.requests.post")
    def test_infobip_respuesta_vacia(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"messages": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = SMSService.enviar_sms_infobip("+595981234567", "Hola")
        self.assertFalse(result["success"])

    @patch("apps.notificaciones.services.sms_service.requests.post")
    def test_infobip_error_http(self, mock_post):
        import requests as req

        mock_post.side_effect = req.exceptions.RequestException("Timeout")
        result = SMSService.enviar_sms_infobip("+595981234567", "Hola")
        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "infobip")


@override_settings(SMS_ENABLED=True, SMS_PROVIDER="aws_sns")
class SMSServiceAWSTest(TestCase):
    """Tests de AWS SNS"""

    def test_aws_sin_boto3(self):
        """Sin boto3 instalado debe retornar error"""
        with patch.dict("sys.modules", {"boto3": None}):
            result = SMSService.enviar_sms_aws("+595981234567", "Test")
            self.assertFalse(result["success"])

    @patch("apps.notificaciones.services.sms_service.requests")
    def test_aws_provider_seleccionado(self, mock_requests):
        """El proveedor aws_sns debe ser seleccionado correctamente"""
        # Mockear el provider AWS SNS directamente
        with patch.object(
            SMSService, "enviar_sms_aws", return_value={"success": True, "message_id": "A", "provider": "aws_sns"}
        ) as mock_aws:
            SMSService.enviar_sms("+595981234567", "Test")
            mock_aws.assert_called_once()


@override_settings(SMS_ENABLED=True, SMS_PROVIDER="provider_invalido")
class SMSServiceProviderInvalidoTest(TestCase):
    """Tests con provider no soportado"""

    def test_provider_invalido(self):
        result = SMSService.enviar_sms("+595981234567", "Test")
        self.assertFalse(result["success"])
        self.assertIn("provider", result["error"].lower())
