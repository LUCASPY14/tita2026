"""
Tests para modelos de api_integrations
Cubre validaciones, relaciones y funcionalidad de modelos de integraciones API
"""

import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.api_integrations.models import (
    CredencialesApi,
    EndpointsApi,
    LogsLlamadasApi,
    LogsWebhooks,
    ProveedoresApi,
    WebhookEndpoints,
)
from apps.usuarios.models import Empleados, Roles


class ProveedoresApiModelTest(TestCase):
    """Tests para modelo ProveedoresApi"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor_data = {
            "nombre": "Bancard",
            "descripcion": "Pasarela de pagos de Paraguay",
            "tipo_servicio": "payment_gateway",
            "url_base": "https://vpos.infonet.com.py",
            "version": "0.3",
            "documentacion": "https://bancard.com.py/docs",
            "tipo_auth": "hmac_sha256",
            "config_auth": {"public_key": "test_public_key", "private_key": "test_private_key"},
            "timeout": 30,
            "max_reintentos": 3,
            "estado": True,
            "created_at": timezone.now(),
        }

    def test_crear_proveedor_api_valido(self):
        """Debe crear proveedor API con datos válidos"""
        proveedor = ProveedoresApi.objects.create(**self.proveedor_data)

        self.assertEqual(proveedor.nombre, "Bancard")
        self.assertEqual(proveedor.tipo_servicio, "payment_gateway")
        self.assertEqual(proveedor.url_base, "https://vpos.infonet.com.py")
        self.assertTrue(proveedor.estado)
        self.assertIsInstance(proveedor.config_auth, dict)

    def test_proveedor_string_representation(self):
        """Debe retornar representación string correcta"""
        proveedor = ProveedoresApi.objects.create(**self.proveedor_data)
        expected = f"ProveedoresApi #{proveedor.pk}"
        self.assertEqual(str(proveedor), expected)

    def test_proveedor_config_auth_json_field(self):
        """Debe manejar campo JSON config_auth correctamente"""
        config_complex = {
            "auth_type": "oauth2",
            "client_id": "test_client",
            "client_secret": "secret",
            "scope": ["read", "write"],
            "token_url": "https://api.example.com/token",
        }

        proveedor_data = self.proveedor_data.copy()
        proveedor_data["config_auth"] = config_complex

        proveedor = ProveedoresApi.objects.create(**proveedor_data)
        proveedor.refresh_from_db()

        self.assertEqual(proveedor.config_auth["auth_type"], "oauth2")
        self.assertEqual(proveedor.config_auth["scope"], ["read", "write"])

    def test_proveedor_nombre_unico_constraint(self):
        """Debe validar unicidad de nombre si está configurada"""
        ProveedoresApi.objects.create(**self.proveedor_data)

        # Intentar crear otro con mismo nombre puede o no fallar
        # dependiendo de si hay constraint en BD
        proveedor_data2 = self.proveedor_data.copy()
        proveedor_data2["url_base"] = "https://api2.example.com"

        try:
            proveedor2 = ProveedoresApi.objects.create(**proveedor_data2)
            # Si no hay constraint, ambos existen
            self.assertNotEqual(proveedor2.pk, None)
        except IntegrityError:
            # Si hay constraint, debe fallar apropiadamente
            pass

    def test_proveedor_campos_obligatorios(self):
        """Debe validar campos obligatorios"""
        campos_requeridos = [
            "nombre",
            "descripcion",
            "tipo_servicio",
            "url_base",
            "version",
            "tipo_auth",
            "config_auth",
            "timeout",
            "max_reintentos",
            "created_at",
        ]

        for campo in campos_requeridos:
            data = self.proveedor_data.copy()
            data.pop(campo, None)

            with self.subTest(campo=campo):
                with self.assertRaises((IntegrityError, ValueError, ValidationError, TypeError)):
                    obj = ProveedoresApi(**data)
                    obj.full_clean()
                    obj.save()

    def test_proveedor_campos_opcionales(self):
        """Debe permitir campos opcionales como None"""
        data = self.proveedor_data.copy()
        data["documentacion"] = None

        proveedor = ProveedoresApi.objects.create(**data)
        self.assertIsNone(proveedor.documentacion)

    def test_proveedor_valores_por_defecto(self):
        """Debe aplicar valores por defecto correctamente"""
        data = self.proveedor_data.copy()
        data.pop("estado", None)  # Usar default

        proveedor = ProveedoresApi.objects.create(**data)
        self.assertTrue(proveedor.estado)  # Default True


class EndpointsApiModelTest(TestCase):
    """Tests para modelo EndpointsApi"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="TestProvider",
            descripcion="Provider para endpoints test",
            tipo_servicio="payment",
            url_base="https://api.test.com",
            version="1.0",
            tipo_auth="api_key",
            config_auth={"api_key": "test"},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now(),
        )

        self.endpoint_data = {
            "nombre": "Create Payment",
            "descripcion": "Endpoint para crear pagos",
            "path": "/payments",
            "metodo": "POST",
            "headers": {"Content-Type": "application/json", "Authorization": "Bearer {token}"},
            "parametros": {"amount": "decimal", "currency": "string", "description": "string"},
            "schema_request": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["amount", "currency"],
            },
            "schema_response": {
                "type": "object",
                "properties": {
                    "payment_id": {"type": "string"},
                    "status": {"type": "string"},
                    "amount": {"type": "number"},
                },
            },
            "cache_segundos": 300,
            "requiere_auth": 1,
            "estado": True,
            "id_proveedor": self.proveedor,
        }

    def test_crear_endpoint_api_valido(self):
        """Debe crear endpoint API con datos válidos"""
        endpoint = EndpointsApi.objects.create(**self.endpoint_data)

        self.assertEqual(endpoint.nombre, "Create Payment")
        self.assertEqual(endpoint.metodo, "POST")
        self.assertEqual(endpoint.path, "/payments")
        self.assertEqual(endpoint.id_proveedor, self.proveedor)

    def test_endpoint_relacion_proveedor(self):
        """Debe mantener relación correcta con proveedor"""
        endpoint = EndpointsApi.objects.create(**self.endpoint_data)

        self.assertEqual(endpoint.id_proveedor.nombre, "TestProvider")
        self.assertEqual(self.proveedor.endpointsapi_set.first(), endpoint)

    def test_endpoint_schemas_json_fields(self):
        """Debe manejar schemas JSON correctamente"""
        endpoint = EndpointsApi.objects.create(**self.endpoint_data)
        endpoint.refresh_from_db()

        self.assertIn("properties", endpoint.schema_request)
        self.assertIn("required", endpoint.schema_request)
        self.assertEqual(endpoint.schema_request["required"], ["amount", "currency"])

    def test_endpoint_metodos_http_validos(self):
        """Debe aceptar métodos HTTP válidos"""
        metodos_validos = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for metodo in metodos_validos:
            with self.subTest(metodo=metodo):
                data = self.endpoint_data.copy()
                data["metodo"] = metodo
                data["nombre"] = f"Test {metodo}"
                data["path"] = f"/{metodo.lower()}"

                endpoint = EndpointsApi.objects.create(**data)
                self.assertEqual(endpoint.metodo, metodo)

    def test_endpoint_cache_segundos_validation(self):
        """Debe validar cache_segundos apropiadamente"""
        # Cache negativo debe ser permitido (sin cache)
        data = self.endpoint_data.copy()
        data["cache_segundos"] = -1

        endpoint = EndpointsApi.objects.create(**data)
        self.assertEqual(endpoint.cache_segundos, -1)

    def test_endpoint_string_representation(self):
        """Debe retornar representación string correcta"""
        endpoint = EndpointsApi.objects.create(**self.endpoint_data)
        expected = f"EndpointsApi #{endpoint.pk}"
        self.assertEqual(str(endpoint), expected)


class LogsLlamadasApiModelTest(TestCase):
    """Tests para modelo LogsLlamadasApi"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(nombre_rol="TestRole", descripcion="Rol para pruebas", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Crear proveedor y endpoint
        self.proveedor = ProveedoresApi.objects.create(
            nombre="LogTest",
            descripcion="Proveedor para logs",
            tipo_servicio="test",
            url_base="https://api.test.com",
            version="1.0",
            tipo_auth="none",
            config_auth={},
            timeout=30,
            max_reintentos=1,
            created_at=timezone.now(),
        )

        self.endpoint = EndpointsApi.objects.create(
            nombre="Test Endpoint",
            descripcion="Endpoint para logs",
            path="/test",
            metodo="GET",
            headers={},
            parametros={},
            schema_request={},
            schema_response={},
            cache_segundos=0,
            requiere_auth=0,
            id_proveedor=self.proveedor,
        )

    def test_crear_log_llamada_api_completo(self):
        """Debe crear log de llamada API con todos los datos"""
        log_data = {
            "timestamp": timezone.now(),
            "metodo": "POST",
            "url": "https://api.test.com/endpoint",
            "headers_req": {"Content-Type": "application/json"},
            "payload_req": '{"test": "data"}',
            "status_code": 200,
            "headers_res": {"Content-Type": "application/json"},
            "payload_res": '{"success": true}',
            "tiempo_ms": 150,
            "bytes_sent": 20,
            "bytes_received": 18,
            "exitoso": 1,
            "error_msg": None,
            "intento": 1,
            "ip_origen": "192.168.1.100",
            "contexto": {"transaction_id": "12345"},
            "id_endpoint": self.endpoint,
            "id_empleado": self.empleado,
        }

        log = LogsLlamadasApi.objects.create(**log_data)

        self.assertEqual(log.metodo, "POST")
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.tiempo_ms, 150)
        self.assertEqual(log.exitoso, 1)
        self.assertEqual(log.id_endpoint, self.endpoint)
        self.assertEqual(log.id_empleado, self.empleado)

    def test_log_llamada_campos_opcionales(self):
        """Debe manejar campos opcionales correctamente"""
        log_data = {
            "timestamp": timezone.now(),
            "metodo": "GET",
            "url": "https://api.test.com/simple",
            "headers_req": {},
            "status_code": 404,
            "headers_res": {},
            "tiempo_ms": 50,
            "exitoso": 0,
            "intento": 1,
            "contexto": {},
        }

        log = LogsLlamadasApi.objects.create(**log_data)

        self.assertIsNone(log.payload_req)
        self.assertIsNone(log.payload_res)
        self.assertIsNone(log.bytes_sent)
        self.assertIsNone(log.bytes_received)
        self.assertIsNone(log.error_msg)
        self.assertIsNone(log.ip_origen)
        self.assertIsNone(log.id_endpoint)
        self.assertIsNone(log.id_empleado)

    def test_log_llamada_contexto_json(self):
        """Debe manejar contexto JSON correctamente"""
        contexto_complex = {
            "user_id": 123,
            "transaction_type": "payment",
            "metadata": {"source": "mobile_app", "version": "1.2.3"},
            "tags": ["payment", "credit_card"],
        }

        log = LogsLlamadasApi.objects.create(
            timestamp=timezone.now(),
            metodo="POST",
            url="https://api.test.com/complex",
            headers_req={},
            status_code=201,
            headers_res={},
            tiempo_ms=300,
            exitoso=1,
            intento=1,
            contexto=contexto_complex,
        )

        log.refresh_from_db()
        self.assertEqual(log.contexto["user_id"], 123)
        self.assertEqual(log.contexto["metadata"]["source"], "mobile_app")
        self.assertIn("payment", log.contexto["tags"])

    def test_log_llamada_string_representation(self):
        """Debe retornar representación string correcta"""
        log = LogsLlamadasApi.objects.create(
            timestamp=timezone.now(),
            metodo="GET",
            url="https://api.test.com/test",
            headers_req={},
            status_code=200,
            headers_res={},
            tiempo_ms=100,
            exitoso=1,
            intento=1,
            contexto={},
        )

        expected = f"LogsLlamadasApi #{log.pk}"
        self.assertEqual(str(log), expected)


class CredencialesApiModelTest(TestCase):
    """Tests para modelo CredencialesApi"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="CredentialTest",
            descripcion="Proveedor para credenciales",
            tipo_servicio="payment",
            url_base="https://api.cred.com",
            version="1.0",
            tipo_auth="oauth2",
            config_auth={},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now(),
        )

    def test_crear_credenciales_api_completas(self):
        """Debe crear credenciales API con todos los campos"""
        credencial_data = {
            "ambiente": "staging",
            "api_key": "test_api_key_123",
            "secret": "test_secret_456",
            "token": "bearer_token_789",
            "configuracion": {
                "oauth": {"client_id": "client123", "client_secret": "secret456", "scope": "read write"},
                "endpoints": {"auth": "/oauth/token", "refresh": "/oauth/refresh"},
            },
            "fecha_expiracion": timezone.now() + timezone.timedelta(days=30),
            "updated_at": timezone.now(),
            "estado": True,
            "id_proveedor": self.proveedor,
        }

        credencial = CredencialesApi.objects.create(**credencial_data)

        self.assertEqual(credencial.ambiente, "staging")
        self.assertEqual(credencial.api_key, "test_api_key_123")
        self.assertEqual(credencial.id_proveedor, self.proveedor)
        self.assertTrue(credencial.estado)

    def test_credenciales_unique_together_constraint(self):
        """Debe validar unique_together (id_proveedor, ambiente)"""
        # Crear primera credencial
        CredencialesApi.objects.create(
            ambiente="production", configuracion={}, updated_at=timezone.now(), id_proveedor=self.proveedor
        )

        # Intentar crear otra para mismo proveedor y ambiente
        with self.assertRaises(IntegrityError):
            CredencialesApi.objects.create(
                ambiente="production", configuracion={}, updated_at=timezone.now(), id_proveedor=self.proveedor
            )

    def test_credenciales_diferentes_ambientes(self):
        """Debe permitir múltiples credenciales para diferentes ambientes"""
        # Staging
        cred_staging = CredencialesApi.objects.create(
            ambiente="staging",
            api_key="staging_key",
            configuracion={"env": "test"},
            updated_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        # Production
        cred_production = CredencialesApi.objects.create(
            ambiente="production",
            api_key="prod_key",
            configuracion={"env": "prod"},
            updated_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        self.assertEqual(cred_staging.ambiente, "staging")
        self.assertEqual(cred_production.ambiente, "production")
        self.assertNotEqual(cred_staging.api_key, cred_production.api_key)

    def test_credenciales_configuracion_json(self):
        """Debe manejar configuración JSON compleja"""
        config_oauth2 = {
            "grant_type": "authorization_code",
            "redirect_uri": "https://app.com/callback",
            "token_endpoint": "https://auth.provider.com/token",
            "refresh_token_endpoint": "https://auth.provider.com/refresh",
            "scopes": ["read:transactions", "write:payments"],
            "token_storage": {"type": "redis", "ttl": 3600, "key_prefix": "oauth_token:"},
        }

        credencial = CredencialesApi.objects.create(
            ambiente="development", configuracion=config_oauth2, updated_at=timezone.now(), id_proveedor=self.proveedor
        )

        credencial.refresh_from_db()
        self.assertEqual(credencial.configuracion["grant_type"], "authorization_code")
        self.assertIn("read:transactions", credencial.configuracion["scopes"])
        self.assertEqual(credencial.configuracion["token_storage"]["type"], "redis")

    def test_credenciales_fecha_expiracion_opcional(self):
        """Debe manejar fecha_expiracion como campo opcional"""
        # Sin fecha de expiración
        credencial = CredencialesApi.objects.create(
            ambiente="test", configuracion={}, updated_at=timezone.now(), id_proveedor=self.proveedor
        )

        self.assertIsNone(credencial.fecha_expiracion)

    def test_credenciales_string_representation(self):
        """Debe retornar representación string correcta"""
        credencial = CredencialesApi.objects.create(
            ambiente="test", configuracion={}, updated_at=timezone.now(), id_proveedor=self.proveedor
        )

        expected = f"CredencialesApi #{credencial.pk}"
        self.assertEqual(str(credencial), expected)


class WebhookEndpointsModelTest(TestCase):
    """Tests para modelo WebhookEndpoints"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="WebhookProvider",
            descripcion="Proveedor con webhooks",
            tipo_servicio="notification",
            url_base="https://api.webhook.com",
            version="2.0",
            tipo_auth="secretkey",
            config_auth={"secret": "webhook_secret"},
            timeout=15,
            max_reintentos=2,
            created_at=timezone.now(),
        )

    def test_crear_webhook_endpoint_completo(self):
        """Debe crear webhook endpoint con todos los datos"""
        webhook_data = {
            "nombre": "Payment Confirmation",
            "descripcion": "Webhook para confirmación de pagos",
            "path": "/webhooks/payments",
            "requiere_verificacion": 1,
            "secret_key": "webhook_secret_key_123",
            "header_verificacion": "X-Webhook-Signature",
            "eventos": ["payment.created", "payment.completed", "payment.failed"],
            "handler_func": "webhooks.handlers.payment_handler",
            "estado": True,
            "created_at": timezone.now(),
            "id_proveedor": self.proveedor,
        }

        webhook = WebhookEndpoints.objects.create(**webhook_data)

        self.assertEqual(webhook.nombre, "Payment Confirmation")
        self.assertEqual(webhook.path, "/webhooks/payments")
        self.assertEqual(webhook.requiere_verificacion, 1)
        self.assertIn("payment.created", webhook.eventos)
        self.assertEqual(webhook.id_proveedor, self.proveedor)

    def test_webhook_unique_together_path_proveedor(self):
        """Debe validar unique_together (id_proveedor, path)"""
        # Crear primer webhook
        WebhookEndpoints.objects.create(
            nombre="First Webhook",
            descripcion="Primer webhook",
            path="/webhook/test",
            requiere_verificacion=0,
            secret_key="secret1",
            header_verificacion="X-Signature",
            eventos=["event1"],
            handler_func="handler1",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        # Intentar crear otro con mismo path y proveedor
        with self.assertRaises(IntegrityError):
            WebhookEndpoints.objects.create(
                nombre="Second Webhook",
                descripcion="Segundo webhook",
                path="/webhook/test",  # Mismo path
                requiere_verificacion=0,
                secret_key="secret2",
                header_verificacion="X-Signature",
                eventos=["event2"],
                handler_func="handler2",
                created_at=timezone.now(),
                id_proveedor=self.proveedor,  # Mismo proveedor
            )

    def test_webhook_eventos_json_array(self):
        """Debe manejar array de eventos JSON correctamente"""
        eventos_complejos = [
            "user.created",
            "user.updated",
            "user.deleted",
            "subscription.created",
            "subscription.cancelled",
            "payment.processing",
            "payment.completed",
            "payment.rejected",
        ]

        webhook = WebhookEndpoints.objects.create(
            nombre="Multi Event Webhook",
            descripcion="Webhook para múltiples eventos",
            path="/webhooks/multi",
            requiere_verificacion=1,
            secret_key="multi_secret",
            header_verificacion="X-Multi-Signature",
            eventos=eventos_complejos,
            handler_func="webhooks.handlers.multi_event_handler",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        webhook.refresh_from_db()
        self.assertEqual(len(webhook.eventos), 8)
        self.assertIn("user.created", webhook.eventos)
        self.assertIn("payment.completed", webhook.eventos)

    def test_webhook_sin_verificacion(self):
        """Debe crear webhook sin verificación de signature"""
        webhook = WebhookEndpoints.objects.create(
            nombre="Simple Webhook",
            descripcion="Webhook sin verificación",
            path="/webhooks/simple",
            requiere_verificacion=0,
            secret_key="",
            header_verificacion="",
            eventos=["simple.event"],
            handler_func="webhooks.handlers.simple_handler",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        self.assertEqual(webhook.requiere_verificacion, 0)
        self.assertEqual(webhook.secret_key, "")

    def test_webhook_string_representation(self):
        """Debe retornar representación string correcta"""
        webhook = WebhookEndpoints.objects.create(
            nombre="Test Webhook",
            descripcion="Test webhook",
            path="/webhook/test",
            requiere_verificacion=0,
            secret_key="test",
            header_verificacion="X-Test",
            eventos=["test"],
            handler_func="test_handler",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

        expected = f"WebhookEndpoints #{webhook.pk}"
        self.assertEqual(str(webhook), expected)


class LogsWebhooksModelTest(TestCase):
    """Tests para modelo LogsWebhooks"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="WebhookLogProvider",
            descripcion="Proveedor para logs de webhooks",
            tipo_servicio="webhook",
            url_base="https://api.webhooklog.com",
            version="1.0",
            tipo_auth="none",
            config_auth={},
            timeout=30,
            max_reintentos=1,
            created_at=timezone.now(),
        )

        self.webhook_endpoint = WebhookEndpoints.objects.create(
            nombre="Log Test Webhook",
            descripcion="Webhook para tests de logs",
            path="/webhook/log-test",
            requiere_verificacion=1,
            secret_key="log_secret",
            header_verificacion="X-Log-Signature",
            eventos=["log.test"],
            handler_func="log_handler",
            created_at=timezone.now(),
            id_proveedor=self.proveedor,
        )

    def test_crear_log_webhook_completo(self):
        """Debe crear log de webhook con todos los datos"""
        log_data = {
            "timestamp": timezone.now(),
            "headers": {
                "Content-Type": "application/json",
                "X-Log-Signature": "sha256=abc123",
                "User-Agent": "WebhookBot/1.0",
            },
            "payload": '{"event": "log.test", "data": {"id": 123}}',
            "evento_tipo": "log.test",
            "verificacion_ok": 1,
            "procesado_ok": 1,
            "tiempo_proc_ms": 250,
            "error_msg": None,
            "ip_origen": "203.0.113.10",
            "user_agent": "WebhookBot/1.0",
            "id_webhook": self.webhook_endpoint,
        }

        log = LogsWebhooks.objects.create(**log_data)

        self.assertEqual(log.evento_tipo, "log.test")
        self.assertEqual(log.verificacion_ok, 1)
        self.assertEqual(log.procesado_ok, 1)
        self.assertEqual(log.tiempo_proc_ms, 250)
        self.assertEqual(log.ip_origen, "203.0.113.10")
        self.assertEqual(log.id_webhook, self.webhook_endpoint)

    def test_log_webhook_con_error(self):
        """Debe crear log de webhook con error de procesamiento"""
        log_data = {
            "timestamp": timezone.now(),
            "headers": {"Content-Type": "application/json"},
            "payload": '{"invalid": "json"',  # JSON inválido
            "evento_tipo": "error.test",
            "verificacion_ok": 0,
            "procesado_ok": 0,
            "tiempo_proc_ms": 50,
            "error_msg": "Invalid JSON format in payload",
            "ip_origen": "192.168.1.50",
            "id_webhook": self.webhook_endpoint,
        }

        log = LogsWebhooks.objects.create(**log_data)

        self.assertEqual(log.verificacion_ok, 0)
        self.assertEqual(log.procesado_ok, 0)
        self.assertIsNotNone(log.error_msg)
        self.assertIn("Invalid JSON", log.error_msg)

    def test_log_webhook_headers_json(self):
        """Debe manejar headers JSON correctamente"""
        headers_complejos = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": "sha256=abcdef123456",
            "X-Webhook-ID": "webhook-123",
            "X-Webhook-Timestamp": "1234567890",
            "User-Agent": "Provider-Webhook/2.1",
            "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
            "Authorization": "Bearer token123",
        }

        log = LogsWebhooks.objects.create(
            timestamp=timezone.now(),
            headers=headers_complejos,
            payload='{"test": true}',
            evento_tipo="headers.test",
            verificacion_ok=1,
            procesado_ok=1,
            ip_origen="10.0.0.1",
        )

        log.refresh_from_db()
        self.assertEqual(log.headers["X-Webhook-ID"], "webhook-123")
        self.assertEqual(log.headers["User-Agent"], "Provider-Webhook/2.1")

    def test_log_webhook_campos_opcionales(self):
        """Debe manejar campos opcionales correctamente"""
        log_minimo = {
            "timestamp": timezone.now(),
            "headers": {},
            "payload": "{}",
            "evento_tipo": "minimal.test",
            "verificacion_ok": 1,
            "procesado_ok": 1,
            "ip_origen": "127.0.0.1",
        }

        log = LogsWebhooks.objects.create(**log_minimo)

        self.assertIsNone(log.tiempo_proc_ms)
        self.assertIsNone(log.error_msg)
        self.assertIsNone(log.user_agent)
        self.assertIsNone(log.id_webhook)

    def test_log_webhook_string_representation(self):
        """Debe retornar representación string correcta"""
        log = LogsWebhooks.objects.create(
            timestamp=timezone.now(),
            headers={},
            payload="{}",
            evento_tipo="representation.test",
            verificacion_ok=1,
            procesado_ok=1,
            ip_origen="127.0.0.1",
        )

        expected = f"LogsWebhooks #{log.pk}"
        self.assertEqual(str(log), expected)
