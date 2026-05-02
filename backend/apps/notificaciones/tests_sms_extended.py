"""
Extended tests for notificaciones/services/sms_service.py
Targeting missing lines: 75, 78, 117-142, 218-220, 251-278, 330
"""

import sys
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from apps.notificaciones.services.sms_service import SMSService


@override_settings(
    SMS_ENABLED=True,
    SMS_PROVIDER="infobip",
    INFOBIP_API_KEY="test-key",
    INFOBIP_BASE_URL="https://api.infobip.com",
    INFOBIP_SENDER="CantinaTest",
)
class SMSEnviarViaInfobipTest(TestCase):
    """Cover line 75: provider == 'infobip' branch in enviar_sms()."""

    @patch("apps.notificaciones.services.sms_service.requests.post")
    def test_enviar_sms_usando_provider_infobip(self, mock_post):
        """enviar_sms() with provider=infobip routes to enviar_sms_infobip (line 75)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messages": [{"messageId": "IB001", "status": {"name": "PENDING"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = SMSService.enviar_sms("+595981234567", "Hola via infobip")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "infobip")


@override_settings(
    SMS_ENABLED=True,
    SMS_PROVIDER="aws_sns",
    AWS_ACCESS_KEY_ID="fake",
    AWS_SECRET_ACCESS_KEY="fake",
    AWS_REGION="us-east-1",
)
class SMSEnviarViaAWSTest(TestCase):
    """Cover line 78: provider == 'aws_sns' branch in enviar_sms()."""

    def test_enviar_sms_usando_provider_aws_sns(self):
        """enviar_sms() with provider=aws_sns routes to enviar_sms_aws (line 78)."""
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.publish.return_value = {"MessageId": "AWS-MSG-001"}

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            result = SMSService.enviar_sms("+595981234567", "Hola via AWS")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "aws_sns")


@override_settings(
    SMS_ENABLED=True,
    SMS_PROVIDER="twilio",
    TWILIO_ACCOUNT_SID="ACtest123",
    TWILIO_AUTH_TOKEN="authtest",
    TWILIO_PHONE_NUMBER="+15551234567",
)
class SMSTwilioSuccessTest(TestCase):
    """Cover lines 117-142: Twilio success path."""

    def test_twilio_envio_exitoso(self):
        """Successful Twilio send returns success dict (lines 125-142)."""
        mock_twilio = MagicMock()
        mock_client_instance = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456"
        mock_message.status = "queued"
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio.Client.return_value = mock_client_instance

        with patch.dict(sys.modules, {"twilio": mock_twilio, "twilio.rest": mock_twilio}):
            result = SMSService.enviar_sms_twilio("+595981234567", "Test twilio")

        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "SM123456")
        self.assertEqual(result["provider"], "twilio")
        self.assertEqual(result["status"], "queued")

    def test_twilio_exception_path(self):
        """Twilio raises generic exception → returns error dict (lines 140-142)."""
        mock_twilio = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.side_effect = RuntimeError("Connection refused")
        mock_twilio.Client.return_value = mock_client_instance

        with patch.dict(sys.modules, {"twilio": mock_twilio, "twilio.rest": mock_twilio}):
            result = SMSService.enviar_sms_twilio("+595981234567", "Test error")

        self.assertFalse(result["success"])
        self.assertIn("Connection refused", result["error"])
        self.assertEqual(result["provider"], "twilio")


@override_settings(
    SMS_ENABLED=True, SMS_PROVIDER="infobip", INFOBIP_API_KEY="test-key", INFOBIP_BASE_URL="https://api.infobip.com"
)
class SMSInfobipGenericExceptionTest(TestCase):
    """Cover lines 218-220: generic Exception handler in enviar_sms_infobip."""

    @patch("apps.notificaciones.services.sms_service.requests.post")
    def test_infobip_json_parse_error(self, mock_post):
        """response.json() raises Exception → caught by generic except (lines 218-220)."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        result = SMSService.enviar_sms_infobip("+595981234567", "Test")

        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "infobip")


@override_settings(
    SMS_ENABLED=True,
    SMS_PROVIDER="aws_sns",
    AWS_ACCESS_KEY_ID="fake",
    AWS_SECRET_ACCESS_KEY="fake",
    AWS_REGION="us-east-1",
)
class SMSAWSSuccessTest(TestCase):
    """Cover lines 251-278: AWS SNS success path."""

    def test_aws_envio_exitoso(self):
        """Successful AWS SNS send returns success dict (lines 261-278)."""
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.publish.return_value = {"MessageId": "AWS-MSG-42"}

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            result = SMSService.enviar_sms_aws("+595981234567", "Test AWS SNS")

        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "AWS-MSG-42")
        self.assertEqual(result["provider"], "aws_sns")

    def test_aws_exception_path(self):
        """AWS SNS raises generic exception → returns error dict (lines 277-278)."""
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.publish.side_effect = RuntimeError("AWS connection error")

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            result = SMSService.enviar_sms_aws("+595981234567", "Test error")

        self.assertFalse(result["success"])
        self.assertIn("AWS connection error", result["error"])
        self.assertEqual(result["provider"], "aws_sns")


class SMSValidarFormatoTelefonoExtendedTest(TestCase):
    """Cover line 330: starts with +595 check in validar_formato_telefono."""

    def test_numero_correcto_longitud_pero_pais_incorrecto(self):
        """Number that is 13 chars but doesn't start with +595 fails (line 330)."""
        # +44 12 345 678 XY → needs to be 13 chars not starting with +595
        # +44123456789 = 12... let's use a number that is 13 long but has +591 prefix
        # _normalizar_telefono('+591123456789') → '+591123456789' (already has +)
        result = SMSService.validar_formato_telefono("+591123456789")
        # +591123456789 is 13 chars and starts with +591 (not +595) → line 330 → False
        self.assertFalse(result)


@override_settings(
    SMS_ENABLED=True,
    SMS_PROVIDER="twilio",
    TWILIO_ACCOUNT_SID="ACtest123",
    TWILIO_AUTH_TOKEN="authtest",
    TWILIO_PHONE_NUMBER="+15551234567",
)
class SMSEnviarViaTwilioDispatchTest(TestCase):
    """Cover line 75: provider=='twilio' branch in enviar_sms() dispatcher."""

    def test_enviar_sms_usando_provider_twilio(self):
        """enviar_sms() with SMS_PROVIDER=twilio routes to enviar_sms_twilio (line 75)."""
        mock_twilio = MagicMock()
        mock_client_instance = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM_dispatch123"
        mock_message.status = "queued"
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio.Client.return_value = mock_client_instance

        with patch.dict(sys.modules, {"twilio": mock_twilio, "twilio.rest": mock_twilio}):
            result = SMSService.enviar_sms("+595981234567", "Mensaje dispatch twilio")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "twilio")


@override_settings(
    SMS_ENABLED=True, SMS_PROVIDER="twilio", TWILIO_ACCOUNT_SID="", TWILIO_AUTH_TOKEN="", TWILIO_PHONE_NUMBER=""
)
class SMSTwilioCredencialesIncompletasTest(TestCase):
    """Cover lines 122-123: Twilio credentials missing → error dict."""

    def test_twilio_credenciales_incompletas(self):
        """Lines 122-123: empty credentials → returns error without sending."""
        mock_twilio = MagicMock()
        with patch.dict(sys.modules, {"twilio": mock_twilio, "twilio.rest": mock_twilio}):
            result = SMSService.enviar_sms_twilio("+595981234567", "Test sin credenciales")
        self.assertFalse(result["success"])
        self.assertIn("Credenciales", result["error"])
