"""
Tests para serializers de api_integrations
Cubre serialización y validación de datos de APIs externas
"""

from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APITestCase
from django.utils import timezone
from decimal import Decimal
import json

from apps.api_integrations.models import (
    ProveedoresApi,
    EndpointsApi,
    LogsLlamadasApi,
    CredencialesApi,
    LogsWebhooks,
    WebhookEndpoints,
)
from apps.usuarios.models import Empleados, Roles


class BaseApiIntegrationsSerializer(serializers.ModelSerializer):
    """Serializer base para pruebas de api_integrations"""

    class Meta:
        abstract = True


class ProveedoresApiSerializer(BaseApiIntegrationsSerializer):
    """Serializer para ProveedoresApi (creado para testing)"""

    class Meta:
        model = ProveedoresApi
        fields = "__all__"
        read_only_fields = ("id_proveedor", "created_at")

    def validate_url_base(self, value):
        """Validar que URL base tenga formato correcto"""
        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("URL debe comenzar con http:// o https://")
        return value

    def validate_timeout(self, value):
        """Validar timeout razonable"""
        if value <= 0 or value > 300:
            raise serializers.ValidationError("Timeout debe estar entre 1 y 300 segundos")
        return value

    def validate_max_reintentos(self, value):
        """Validar número de reintentos"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("Max reintentos debe estar entre 0 y 10")
        return value


class EndpointsApiSerializer(BaseApiIntegrationsSerializer):
    """Serializer para EndpointsApi (creado para testing)"""

    proveedor_nombre = serializers.CharField(source="id_proveedor.nombre", read_only=True)

    class Meta:
        model = EndpointsApi
        fields = "__all__"
        read_only_fields = ("id_endpoint",)

    def validate_metodo(self, value):
        """Validar método HTTP"""
        metodos_validos = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if value.upper() not in metodos_validos:
            raise serializers.ValidationError(f"Método debe ser uno de: {', '.join(metodos_validos)}")
        return value.upper()

    def validate_path(self, value):
        """Validar formato de path"""
        if not value.startswith("/"):
            raise serializers.ValidationError("Path debe comenzar con /")
        return value

    def validate_cache_segundos(self, value):
        """Validar cache_segundos"""
        if value < -1:
            raise serializers.ValidationError("Cache segundos no puede ser menor a -1")
        return value


class LogsLlamadasApiSerializer(BaseApiIntegrationsSerializer):
    """Serializer para LogsLlamadasApi (creado para testing)"""

    endpoint_nombre = serializers.CharField(source="id_endpoint.nombre", read_only=True)
    empleado_usuario = serializers.CharField(source="id_empleado.usuario", read_only=True)

    class Meta:
        model = LogsLlamadasApi
        fields = "__all__"
        read_only_fields = ("id_log", "timestamp")


class WebhookDataSerializer(serializers.Serializer):
    """Serializer para datos de webhook (creado para testing)"""

    operation = serializers.JSONField()
    shop_process_id = serializers.CharField(max_length=100)
    signature = serializers.CharField(max_length=255)

    def validate_operation(self, value):
        """Validar estructura de operation"""
        required_fields = ["response", "amount", "currency"]
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' requerido en operation")
        return value

    def validate_shop_process_id(self, value):
        """Validar formato de shop_process_id"""
        if not value.startswith("REC-"):
            raise serializers.ValidationError("shop_process_id debe comenzar con 'REC-'")
        return value


class ProveedoresApiSerializerTest(TestCase):
    """Tests para ProveedoresApiSerializer"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.valid_data = {
            "nombre": "TestProvider",
            "descripcion": "Proveedor de prueba",
            "tipo_servicio": "payment",
            "url_base": "https://api.test.com",
            "version": "1.0",
            "documentacion": "https://docs.test.com",
            "tipo_auth": "api_key",
            "config_auth": {"api_key": "test_key"},
            "timeout": 30,
            "max_reintentos": 3,
            "estado": True,
            "created_at": timezone.now(),
        }

    def test_serializer_valid_data(self):
        """Debe serializar datos válidos correctamente"""
        serializer = ProveedoresApiSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        proveedor = serializer.save()

        self.assertEqual(proveedor.nombre, "TestProvider")
        self.assertEqual(proveedor.url_base, "https://api.test.com")
        self.assertEqual(proveedor.timeout, 30)

    def test_serializer_url_base_validation(self):
        """Debe validar URL base correctamente"""
        # URL sin protocolo
        invalid_data = self.valid_data.copy()
        invalid_data["url_base"] = "api.test.com"

        serializer = ProveedoresApiSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("url_base", serializer.errors)
        self.assertIn("http", str(serializer.errors["url_base"][0]))

    def test_serializer_timeout_validation(self):
        """Debe validar timeout dentro de rangos válidos"""
        test_cases = [
            (0, False),  # Timeout 0 inválido
            (-1, False),  # Timeout negativo inválido
            (301, False),  # Timeout muy alto inválido
            (30, True),  # Timeout válido
            (1, True),  # Timeout mínimo válido
            (300, True),  # Timeout máximo válido
        ]

        for timeout, should_be_valid in test_cases:
            with self.subTest(timeout=timeout):
                data = self.valid_data.copy()
                data["timeout"] = timeout

                serializer = ProveedoresApiSerializer(data=data)
                if should_be_valid:
                    self.assertTrue(serializer.is_valid(), f"Timeout {timeout} debería ser válido")
                else:
                    self.assertFalse(serializer.is_valid(), f"Timeout {timeout} debería ser inválido")

    def test_serializer_max_reintentos_validation(self):
        """Debe validar max_reintentos dentro de rangos válidos"""
        test_cases = [
            (-1, False),  # Negativo inválido
            (11, False),  # Muy alto inválido
            (0, True),  # Cero válido
            (5, True),  # Medio válido
            (10, True),  # Máximo válido
        ]

        for reintentos, should_be_valid in test_cases:
            with self.subTest(reintentos=reintentos):
                data = self.valid_data.copy()
                data["max_reintentos"] = reintentos

                serializer = ProveedoresApiSerializer(data=data)
                if should_be_valid:
                    self.assertTrue(serializer.is_valid())
                else:
                    self.assertFalse(serializer.is_valid())
                    self.assertIn("max_reintentos", serializer.errors)

    def test_serializer_config_auth_json_field(self):
        """Debe manejar config_auth como JSON correctamente"""
        complex_config = {
            "auth_type": "oauth2",
            "client_id": "test_client",
            "client_secret": "secret",
            "scopes": ["read", "write"],
            "token_endpoint": "https://auth.provider.com/token",
        }

        data = self.valid_data.copy()
        data["config_auth"] = complex_config

        serializer = ProveedoresApiSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        proveedor = serializer.save()
        self.assertEqual(proveedor.config_auth["auth_type"], "oauth2")
        self.assertIn("read", proveedor.config_auth["scopes"])

    def test_serializer_read_only_fields(self):
        """Debe manejar campos read-only correctamente"""
        data = self.valid_data.copy()
        data["id_proveedor"] = 999  # Campo read-only que debe ser ignorado

        serializer = ProveedoresApiSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        proveedor = serializer.save()
        self.assertNotEqual(proveedor.id_proveedor, 999)

    def test_serializer_partial_update(self):
        """Debe manejar updates parciales correctamente"""
        # Crear proveedor
        proveedor = ProveedoresApi.objects.create(**self.valid_data)

        # Update parcial
        update_data = {"timeout": 60, "estado": False}

        serializer = ProveedoresApiSerializer(proveedor, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_proveedor = serializer.save()
        self.assertEqual(updated_proveedor.timeout, 60)
        self.assertFalse(updated_proveedor.estado)
        # Otros campos deben mantenerse
        self.assertEqual(updated_proveedor.nombre, "TestProvider")


class EndpointsApiSerializerTest(TestCase):
    """Tests para EndpointsApiSerializer"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="EndpointTestProvider",
            descripcion="Proveedor para endpoints test",
            tipo_servicio="api",
            url_base="https://api.endpoint.test",
            version="1.0",
            tipo_auth="none",
            config_auth={},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now(),
        )

        self.valid_data = {
            "nombre": "Test Endpoint",
            "descripcion": "Endpoint de prueba",
            "path": "/api/test",
            "metodo": "POST",
            "headers": {"Content-Type": "application/json"},
            "parametros": {"param1": "string", "param2": "number"},
            "schema_request": {"type": "object"},
            "schema_response": {"type": "object"},
            "cache_segundos": 300,
            "requiere_auth": 1,
            "estado": True,
            "id_proveedor": self.proveedor.id_proveedor,
        }

    def test_serializer_valid_endpoint_data(self):
        """Debe serializar endpoint válido correctamente"""
        serializer = EndpointsApiSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        endpoint = serializer.save()

        self.assertEqual(endpoint.nombre, "Test Endpoint")
        self.assertEqual(endpoint.metodo, "POST")
        self.assertEqual(endpoint.path, "/api/test")

    def test_serializer_metodo_validation(self):
        """Debe validar métodos HTTP correctamente"""
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

        for method in valid_methods:
            with self.subTest(method=method):
                data = self.valid_data.copy()
                data["metodo"] = method.lower()  # Probar minúsculas

                serializer = EndpointsApiSerializer(data=data)
                self.assertTrue(serializer.is_valid())
                self.assertEqual(serializer.validated_data["metodo"], method.upper())

        # Método inválido
        data = self.valid_data.copy()
        data["metodo"] = "INVALID"

        serializer = EndpointsApiSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("metodo", serializer.errors)

    def test_serializer_path_validation(self):
        """Debe validar formato de path correctamente"""
        # Path sin / inicial
        data = self.valid_data.copy()
        data["path"] = "api/test"

        serializer = EndpointsApiSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("path", serializer.errors)

        # Path válido
        data["path"] = "/api/test"
        serializer = EndpointsApiSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_cache_segundos_validation(self):
        """Debe validar cache_segundos correctamente"""
        test_cases = [
            (-2, False),  # Menor a -1 inválido
            (-1, True),  # -1 válido (sin cache)
            (0, True),  # 0 válido (sin cache)
            (300, True),  # Valor positivo válido
            (86400, True),  # Valor grande válido
        ]

        for cache, should_be_valid in test_cases:
            with self.subTest(cache=cache):
                data = self.valid_data.copy()
                data["cache_segundos"] = cache

                serializer = EndpointsApiSerializer(data=data)
                if should_be_valid:
                    self.assertTrue(serializer.is_valid())
                else:
                    self.assertFalse(serializer.is_valid())
                    self.assertIn("cache_segundos", serializer.errors)

    def test_serializer_proveedor_nombre_read_only(self):
        """Debe incluir nombre del proveedor como read-only"""
        # Crear endpoint (usando objeto proveedor, no ID)
        create_data = self.valid_data.copy()
        create_data["id_proveedor"] = self.proveedor
        endpoint = EndpointsApi.objects.create(**create_data)

        # Serializar para lectura
        serializer = EndpointsApiSerializer(endpoint)
        data = serializer.data

        self.assertIn("proveedor_nombre", data)
        self.assertEqual(data["proveedor_nombre"], "EndpointTestProvider")

    def test_serializer_json_fields(self):
        """Debe manejar campos JSON correctamente"""
        complex_data = self.valid_data.copy()
        complex_data["headers"] = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}",
            "X-API-Version": "1.0",
        }
        complex_data["schema_request"] = {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "minimum": 0},
                "currency": {"type": "string", "enum": ["PYG", "USD"]},
            },
            "required": ["amount", "currency"],
        }

        serializer = EndpointsApiSerializer(data=complex_data)
        self.assertTrue(serializer.is_valid())

        endpoint = serializer.save()
        self.assertEqual(endpoint.headers["X-API-Version"], "1.0")
        self.assertIn("properties", endpoint.schema_request)


class LogsLlamadasApiSerializerTest(TestCase):
    """Tests para LogsLlamadasApiSerializer"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear empleado
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
            nombre="LogTestProvider",
            descripcion="Proveedor para logs",
            tipo_servicio="test",
            url_base="https://api.logtest.com",
            version="1.0",
            tipo_auth="none",
            config_auth={},
            timeout=30,
            max_reintentos=1,
            created_at=timezone.now(),
        )

        self.endpoint = EndpointsApi.objects.create(
            nombre="Log Test Endpoint",
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

    def test_serializer_log_with_relationships(self):
        """Debe serializar log con relaciones correctamente"""
        log_data = {
            "timestamp": timezone.now(),
            "metodo": "POST",
            "url": "https://api.logtest.com/endpoint",
            "headers_req": {"Content-Type": "application/json"},
            "payload_req": '{"test": "data"}',
            "status_code": 200,
            "headers_res": {"Content-Type": "application/json"},
            "payload_res": '{"success": true}',
            "tiempo_ms": 150,
            "exitoso": 1,
            "intento": 1,
            "contexto": {"test": True},
            "id_endpoint": self.endpoint.id_endpoint,
            "id_empleado": self.empleado.id_empleado,
        }

        serializer = LogsLlamadasApiSerializer(data=log_data)
        self.assertTrue(serializer.is_valid())

        log = serializer.save()
        self.assertEqual(log.metodo, "POST")
        self.assertEqual(log.id_endpoint, self.endpoint)
        self.assertEqual(log.id_empleado, self.empleado)

    def test_serializer_read_only_relationships(self):
        """Debe incluir nombres de relaciones como read-only"""
        # Crear log
        log = LogsLlamadasApi.objects.create(
            timestamp=timezone.now(),
            metodo="GET",
            url="https://api.test.com",
            headers_req={},
            status_code=200,
            headers_res={},
            tiempo_ms=100,
            exitoso=1,
            intento=1,
            contexto={},
            id_endpoint=self.endpoint,
            id_empleado=self.empleado,
        )

        # Serializar para lectura
        serializer = LogsLlamadasApiSerializer(log)
        data = serializer.data

        self.assertIn("endpoint_nombre", data)
        self.assertIn("empleado_usuario", data)
        self.assertEqual(data["endpoint_nombre"], "Log Test Endpoint")
        self.assertEqual(data["empleado_usuario"], "testuser")


class WebhookDataSerializerTest(TestCase):
    """Tests para WebhookDataSerializer"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.valid_webhook_data = {
            "operation": {"response": "S", "amount": "50000.00", "currency": "PYG", "authorization_number": "123456"},
            "shop_process_id": "REC-123-1234567890",
            "signature": "abc123def456",
        }

    def test_serializer_valid_webhook_data(self):
        """Debe validar datos de webhook correctos"""
        serializer = WebhookDataSerializer(data=self.valid_webhook_data)

        self.assertTrue(serializer.is_valid())
        validated = serializer.validated_data

        self.assertEqual(validated["shop_process_id"], "REC-123-1234567890")
        self.assertIn("response", validated["operation"])

    def test_serializer_operation_validation(self):
        """Debe validar estructura de operation"""
        # Operation sin campos requeridos
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["operation"] = {"response": "S"}  # Falta amount y currency

        serializer = WebhookDataSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("operation", serializer.errors)

    def test_serializer_shop_process_id_validation(self):
        """Debe validar formato de shop_process_id"""
        # shop_process_id sin prefijo REC-
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["shop_process_id"] = "INVALID-123-456"

        serializer = WebhookDataSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("shop_process_id", serializer.errors)

        # shop_process_id válido
        valid_data = self.valid_webhook_data.copy()
        valid_data["shop_process_id"] = "REC-999-VALID"

        serializer = WebhookDataSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_missing_fields(self):
        """Debe rechazar datos con campos faltantes"""
        required_fields = ["operation", "shop_process_id", "signature"]

        for field in required_fields:
            with self.subTest(field=field):
                incomplete_data = self.valid_webhook_data.copy()
                del incomplete_data[field]

                serializer = WebhookDataSerializer(data=incomplete_data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_serializer_complex_operation(self):
        """Debe manejar operation compleja correctamente"""
        complex_operation = {
            "response": "S",
            "amount": "75000.00",
            "currency": "PYG",
            "authorization_number": "AUTH789",
            "ticket_number": "TICKET123",
            "response_code": "00",
            "response_description": "Transacción aprobada",
            "security_information": {
                "customer_ip": "192.168.1.100",
                "card_source": "I",
                "card_country": "PY",
                "risk_score": "LOW",
            },
        }

        data = self.valid_webhook_data.copy()
        data["operation"] = complex_operation

        serializer = WebhookDataSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated = serializer.validated_data
        self.assertIn("security_information", validated["operation"])
        self.assertEqual(validated["operation"]["security_information"]["risk_score"], "LOW")


class ApiIntegrationsSerializerIntegrationTest(TestCase):
    """Tests de integración entre serializers"""

    def setUp(self):
        """Configurar datos completos para integración"""
        self.proveedor = ProveedoresApi.objects.create(
            nombre="IntegrationProvider",
            descripcion="Proveedor para tests de integración",
            tipo_servicio="payment",
            url_base="https://api.integration.test",
            version="2.0",
            tipo_auth="oauth2",
            config_auth={"client_id": "test_client"},
            timeout=45,
            max_reintentos=5,
            created_at=timezone.now(),
        )

    def test_serializers_chain_interaction(self):
        """Debe permitir interacción en cadena entre serializers"""
        # 1. Crear proveedor
        proveedor_data = {
            "nombre": "ChainProvider",
            "descripcion": "Proveedor para cadena",
            "tipo_servicio": "api",
            "url_base": "https://api.chain.test",
            "version": "1.0",
            "tipo_auth": "api_key",
            "config_auth": {"key": "chain_key"},
            "timeout": 30,
            "max_reintentos": 3,
            "created_at": timezone.now(),
        }

        proveedor_serializer = ProveedoresApiSerializer(data=proveedor_data)
        self.assertTrue(proveedor_serializer.is_valid())
        proveedor = proveedor_serializer.save()

        # 2. Crear endpoint para ese proveedor
        endpoint_data = {
            "nombre": "Chain Endpoint",
            "descripcion": "Endpoint en cadena",
            "path": "/api/chain",
            "metodo": "POST",
            "headers": {},
            "parametros": {},
            "schema_request": {},
            "schema_response": {},
            "cache_segundos": 0,
            "requiere_auth": 1,
            "id_proveedor": proveedor.id_proveedor,
        }

        endpoint_serializer = EndpointsApiSerializer(data=endpoint_data)
        self.assertTrue(endpoint_serializer.is_valid())
        endpoint = endpoint_serializer.save()

        # 3. Verificar relación
        self.assertEqual(endpoint.id_proveedor, proveedor)

    def test_serializer_error_handling_consistency(self):
        """Debe manejar errores consistentemente entre serializers"""
        # Error en proveedor
        invalid_proveedor_data = {
            "nombre": "Invalid",
            "url_base": "invalid_url",  # Sin protocolo
            "timeout": -1,  # Inválido
        }

        proveedor_serializer = ProveedoresApiSerializer(data=invalid_proveedor_data)
        self.assertFalse(proveedor_serializer.is_valid())
        self.assertIn("url_base", proveedor_serializer.errors)
        self.assertIn("timeout", proveedor_serializer.errors)

        # Error en endpoint
        invalid_endpoint_data = {
            "nombre": "Invalid Endpoint",
            "path": "no_slash",  # Sin /
            "metodo": "INVALID",  # Método inválido
            "cache_segundos": -2,  # Inválido
        }

        endpoint_serializer = EndpointsApiSerializer(data=invalid_endpoint_data)
        self.assertFalse(endpoint_serializer.is_valid())
        self.assertIn("path", endpoint_serializer.errors)
        self.assertIn("metodo", endpoint_serializer.errors)
        self.assertIn("cache_segundos", endpoint_serializer.errors)
