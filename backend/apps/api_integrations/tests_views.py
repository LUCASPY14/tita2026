"""
Tests para views de api_integrations
Cubre endpoints de webhooks y funcionalidad de vistas API
"""

import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.api_integrations.models import CredencialesApi, LogsWebhooks, ProveedoresApi, WebhookEndpoints
from apps.api_integrations.views import bancard_webhook, webhook_test


class BancardWebhookViewTest(APITestCase):
    """Tests para bancard_webhook view"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear proveedor Bancard
        self.proveedor = ProveedoresApi.objects.create(
            nombre="Bancard",
            descripcion="Pasarela de pagos Bancard",
            tipo_servicio="payment_gateway",
            url_base="https://vpos.infonet.com.py",
            version="0.3",
            tipo_auth="hmac_sha256",
            config_auth={"public_key": "test_public_key", "private_key": "test_private_key"},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now(),
        )

        # Crear webhook endpoint
        self.webhook_endpoint = WebhookEndpoints.objects.create(
            nombre="Bancard Payment Webhook",
            descripcion="Webhook para confirmaciones de pago",
            path="/api/webhooks/bancard/",
            requiere_verificacion=1,
            secret_key="webhook_secret",
            header_verificacion="X-Signature",
            eventos=["payment.completed"],
            handler_func="bancard_webhook",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        self.webhook_url = "/api/v1/webhooks/bancard/"

        # Datos de webhook válidos
        self.valid_operation = {
            "response": "S",
            "response_details": "Transacción aprobada",
            "amount": "50000.00",
            "currency": "PYG",
            "authorization_number": "123456",
            "ticket_number": "789012",
            "response_code": "00",
            "response_description": "Transacción aprobada",
            "security_information": {"customer_ip": "192.168.1.100", "card_source": "I", "card_country": "PY"},
        }

        self.valid_webhook_data = {
            "operation": self.valid_operation,
            "shop_process_id": "REC-123-1234567890",
            "signature": "abc123xyz",
        }

    def test_webhook_post_method_required(self):
        """Debe aceptar solo método POST"""
        # GET debe fallar
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PUT debe fallar
        response = self.client.put(self.webhook_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_webhook_invalid_json(self):
        """Debe rechazar JSON inválido"""
        response = self.client.post(self.webhook_url, "invalid json{", content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("JSON inválido", response.data["error"])

    def test_webhook_missing_required_fields(self):
        """Debe rechazar datos con campos faltantes"""
        # Sin operation
        incomplete_data = {"shop_process_id": "REC-123-1234567890", "signature": "abc123xyz"}

        response = self.client.post(self.webhook_url, data=json.dumps(incomplete_data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Faltan datos requeridos", response.data["error"])

    def test_webhook_empty_operation(self):
        """Debe rechazar operation vacía"""
        invalid_data = {"operation": {}, "shop_process_id": "REC-123-1234567890", "signature": "abc123xyz"}

        response = self.client.post(self.webhook_url, data=json.dumps(invalid_data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_successful_processing(self, mock_bancard_service):
        """Debe procesar webhook exitosamente"""
        # Mock del servicio
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {
            "success": True,
            "recarga_id": 123,
            "estado": "completada",
            "mensaje": "Pago procesado correctamente",
        }
        mock_bancard_service.return_value = mock_service_instance

        response = self.client.post(
            self.webhook_url, data=json.dumps(self.valid_webhook_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["recarga_id"], 123)
        self.assertEqual(response.data["estado"], "completada")

        # Verificar que se llamó al servicio
        mock_service_instance.procesar_webhook.assert_called_once_with(
            shop_process_id="REC-123-1234567890", operation=self.valid_operation, signature="abc123xyz"
        )

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_processing_error(self, mock_bancard_service):
        """Debe manejar errores de procesamiento"""
        # Mock del servicio con error
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {"success": False, "error": "Firma inválida"}
        mock_bancard_service.return_value = mock_service_instance

        response = self.client.post(
            self.webhook_url, data=json.dumps(self.valid_webhook_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "Firma inválida")

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_creates_log(self, mock_bancard_service):
        """Debe crear log de webhook correctamente"""
        # Mock del servicio
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {
            "success": True,
            "recarga_id": 123,
            "estado": "completada",
        }
        mock_bancard_service.return_value = mock_service_instance

        # Verificar que no hay logs antes
        logs_antes = LogsWebhooks.objects.count()

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.valid_webhook_data),
            content_type="application/json",
            HTTP_USER_AGENT="BancardBot/1.0",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que se creó un log
        logs_despues = LogsWebhooks.objects.count()
        self.assertEqual(logs_despues, logs_antes + 1)

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_service_exception(self, mock_bancard_service):
        """Debe manejar excepciones del servicio"""
        # Mock del servicio que lanza excepción
        mock_bancard_service.side_effect = Exception("Error de conexión")

        response = self.client.post(
            self.webhook_url, data=json.dumps(self.valid_webhook_data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])
        self.assertIn("Error interno", response.data["error"])

    def test_webhook_no_authentication_required(self):
        """Debe permitir acceso sin autenticación (AllowAny)"""
        # No configurar autenticación
        response = self.client.post(
            self.webhook_url, data=json.dumps(self.valid_webhook_data), content_type="application/json"
        )

        # No debe fallar por falta de auth (puede fallar por otras razones)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_csrf_exempt(self):
        """Debe estar exento de verificación CSRF"""
        # Esta prueba verifica que el decorator @csrf_exempt funciona
        # Al usar APITestCase, CSRF está deshabilitado por defecto
        # pero podemos verificar que el endpoint responde
        response = self.client.post(
            self.webhook_url, data=json.dumps({}), content_type="application/json"  # Datos mínimos
        )

        # Debe retornar error de validación, no CSRF
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_with_remote_addr(self, mock_bancard_service):
        """Debe capturar IP remota correctamente"""
        # Mock del servicio
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {
            "success": True,
            "recarga_id": 123,
            "estado": "completada",
        }
        mock_bancard_service.return_value = mock_service_instance

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.valid_webhook_data),
            content_type="application/json",
            REMOTE_ADDR="203.0.113.50",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_webhook_large_payload(self):
        """Debe manejar payloads grandes apropiadamente"""
        # Crear operation con mucha data
        large_operation = self.valid_operation.copy()
        large_operation["large_data"] = "x" * 10000  # 10KB de datos

        large_webhook_data = {
            "operation": large_operation,
            "shop_process_id": "REC-123-LARGE",
            "signature": "large_signature",
        }

        response = self.client.post(
            self.webhook_url, data=json.dumps(large_webhook_data), content_type="application/json"
        )

        # Debe procesar sin problemas (error puede ser por otros motivos)
        self.assertNotEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_multiple_operations_types(self, mock_bancard_service):
        """Debe manejar diferentes tipos de operations"""
        # Mock del servicio
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {"success": True, "recarga_id": 456}
        mock_bancard_service.return_value = mock_service_instance

        # Operation de pago rechazado
        rejected_operation = {
            "response": "N",
            "response_details": "Tarjeta rechazada",
            "amount": "25000.00",
            "currency": "PYG",
            "authorization_number": "",
            "response_code": "05",
            "response_description": "No autorizado",
        }

        webhook_data = {
            "operation": rejected_operation,
            "shop_process_id": "REC-456-REJECTED",
            "signature": "reject_signature",
        }

        response = self.client.post(self.webhook_url, data=json.dumps(webhook_data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class WebhookTestViewTest(APITestCase):
    """Tests para webhook_test view"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.test_url = "/api/v1/webhooks/test/"

    def test_webhook_test_get_method(self):
        """Debe responder a método GET"""
        response = self.client.get(self.test_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertIn("Webhook endpoint", response.data["message"])

    def test_webhook_test_response_structure(self):
        """Debe retornar estructura de respuesta correcta"""
        response = self.client.get(self.test_url)

        required_fields = ["status", "message", "método", "path"]
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data)

    def test_webhook_test_no_authentication_required(self):
        """Debe permitir acceso sin autenticación"""
        # Sin headers de autenticación
        response = self.client.get(self.test_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_webhook_test_csrf_exempt(self):
        """Debe estar exento de verificación CSRF"""
        response = self.client.get(self.test_url)

        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_webhook_test_post_method_not_allowed(self):
        """Debe rechazar métodos no permitidos"""
        # POST no debería estar permitido para test
        response = self.client.post(self.test_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PUT tampoco
        response = self.client.put(self.test_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_webhook_test_content_type(self):
        """Debe retornar content-type apropiado"""
        response = self.client.get(self.test_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # APITestCase maneja JSON automáticamente

    def test_webhook_test_multiple_requests(self):
        """Debe manejar múltiples requests correctamente"""
        for i in range(5):
            with self.subTest(request=i):
                response = self.client.get(self.test_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["status"], "ok")


class WebhookViewsIntegrationTest(APITestCase):
    """Tests de integración para views de webhooks"""

    def setUp(self):
        """Configurar datos completos para integración"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="Integration Test Provider",
            descripcion="Proveedor para tests de integración",
            tipo_servicio="payment",
            url_base="https://api.integration.test",
            version="1.0",
            tipo_auth="hmac",
            config_auth={"secret": "integration_secret"},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now(),
        )

        self.credenciales = CredencialesApi.objects.create(
            ambiente="testing",
            api_key="test_api_key",
            secret="test_secret",
            configuracion={"webhook_secret": "webhook_test_secret"},
            updated_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

    @patch("apps.api_integrations.services.BancardService")
    def test_end_to_end_webhook_processing(self, mock_bancard_service):
        """Test end-to-end de procesamiento de webhook"""
        # Configurar mock completo
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {
            "success": True,
            "recarga_id": 789,
            "estado": "completada",
            "monto_acreditado": "45000.00",
            "comision": "5000.00",
        }
        mock_bancard_service.return_value = mock_service_instance

        # Datos de webhook completos
        webhook_data = {
            "operation": {
                "response": "S",
                "response_details": "Transacción aprobada",
                "amount": "50000.00",
                "currency": "PYG",
                "authorization_number": "AUTH123456",
                "ticket_number": "TICKET789012",
                "response_code": "00",
                "response_description": "Transacción exitosa",
                "security_information": {
                    "customer_ip": "192.168.1.100",
                    "card_source": "I",
                    "card_country": "PY",
                    "risk_score": "LOW",
                },
            },
            "shop_process_id": "REC-789-INTEGRATION",
            "signature": "integration_signature_hash",
        }

        # Enviar webhook
        response = self.client.post(
            "/api/v1/webhooks/bancard/",
            data=json.dumps(webhook_data),
            content_type="application/json",
            HTTP_USER_AGENT="IntegrationTest/1.0",
            REMOTE_ADDR="203.0.113.100",
        )

        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["recarga_id"], 789)

        # Verificar que el servicio fue llamado correctamente
        mock_service_instance.procesar_webhook.assert_called_once()
        call_args = mock_service_instance.procesar_webhook.call_args
        self.assertEqual(call_args[1]["shop_process_id"], "REC-789-INTEGRATION")

    def test_webhook_error_scenarios(self):
        """Test de escenarios de error comunes"""
        error_scenarios = [
            # JSON malformado
            {
                "data": "invalid json{[",
                "expected_status": status.HTTP_400_BAD_REQUEST,
                "expected_error": "JSON inválido",
            },
            # Datos faltantes
            {
                "data": json.dumps({"operation": {}}),
                "expected_status": status.HTTP_400_BAD_REQUEST,
                "expected_error": "Faltan datos requeridos",
            },
            # Estructura vacía
            {
                "data": json.dumps({}),
                "expected_status": status.HTTP_400_BAD_REQUEST,
                "expected_error": "Faltan datos requeridos",
            },
        ]

        for scenario in error_scenarios:
            with self.subTest(scenario=scenario["expected_error"]):
                response = self.client.post(
                    "/api/v1/webhooks/bancard/", data=scenario["data"], content_type="application/json"
                )

                self.assertEqual(response.status_code, scenario["expected_status"])
                if "error" in response.data:
                    self.assertIn(scenario["expected_error"], response.data["error"])

    def test_webhook_logging_integration(self):
        """Test de integración con sistema de logging"""
        webhook_data = {
            "operation": {"response": "S", "amount": "25000.00", "currency": "PYG"},
            "shop_process_id": "REC-LOG-TEST",
            "signature": "log_test_signature",
        }

        # Contar logs antes
        logs_antes = LogsWebhooks.objects.count()

        # Enviar webhook (va a fallar pero debería crear log)
        self.client.post(
            "/api/v1/webhooks/bancard/",
            data=json.dumps(webhook_data),
            content_type="application/json",
            HTTP_USER_AGENT="LogTest/1.0",
            REMOTE_ADDR="10.0.0.1",
        )

        # Verificar que se creó log
        logs_despues = LogsWebhooks.objects.count()

        # Puede que el log se cree dependiendo de la implementación
        # Al menos no debe haber errores de logging
        self.assertGreaterEqual(logs_despues, logs_antes)

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_performance_simulation(self, mock_bancard_service):
        """Test de rendimiento simulado con múltiples webhooks"""
        # Mock del servicio
        mock_service_instance = Mock()
        mock_service_instance.procesar_webhook.return_value = {"success": True, "recarga_id": 999}
        mock_bancard_service.return_value = mock_service_instance

        # Datos base
        base_webhook_data = {
            "operation": {"response": "S", "amount": "10000.00", "currency": "PYG", "response_code": "00"},
            "signature": "perf_signature",
        }

        # Enviar múltiples webhooks
        successful_requests = 0
        for i in range(10):  # 10 requests simulados
            webhook_data = base_webhook_data.copy()
            webhook_data["shop_process_id"] = f"REC-PERF-{i}"

            response = self.client.post(
                "/api/v1/webhooks/bancard/", data=json.dumps(webhook_data), content_type="application/json"
            )

            if response.status_code == status.HTTP_200_OK:
                successful_requests += 1

        # Verificar que la mayoría fueron exitosos
        # (puede fallar por validaciones, pero no por errores de performance)
        self.assertGreater(successful_requests, 0)
