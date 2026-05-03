"""
Tests de validadores del módulo API Integrations
Cobertura completa de 48 validadores con casos positivos, negativos y edge cases
"""

from datetime import datetime, timedelta, timezone

from django.core.exceptions import ValidationError
from django.test import TestCase

from .validators import *

# ============================================================================
# TESTS DE VALIDADORES DE PROVEEDORES API
# ============================================================================


class ValidarNombreProveedorTest(TestCase):
    def test_nombre_valido(self):
        self.assertEqual(validar_nombre_proveedor("Stripe API"), "Stripe API")
        self.assertEqual(validar_nombre_proveedor("   PayPal   "), "PayPal")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_proveedor("AB")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_proveedor("A" * 101)


class ValidarDescripcionProveedorTest(TestCase):
    def test_descripcion_valida(self):
        desc = "Este es un proveedor de pagos"
        self.assertEqual(validar_descripcion_proveedor(desc), desc)

    def test_descripcion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_proveedor("Corto")

    def test_descripcion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_proveedor("A" * 5001)


class ValidarTipoServicioTest(TestCase):
    def test_tipos_validos(self):
        for tipo in ["REST", "SOAP", "GraphQL", "WebSocket", "gRPC"]:
            self.assertEqual(validar_tipo_servicio(tipo), tipo)

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_servicio("HTTP")

    def test_tipo_requerido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_servicio(None)


class ValidarUrlBaseTest(TestCase):
    def test_url_valida_https(self):
        url = "https://api.stripe.com/v1"
        self.assertEqual(validar_url_base(url), url)

    def test_url_valida_http(self):
        url = "http://localhost:8000/api"
        self.assertEqual(validar_url_base(url), url)

    def test_url_sin_protocolo(self):
        with self.assertRaises(ValidationError):
            validar_url_base("api.stripe.com")

    def test_url_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_url_base("https://" + "a" * 200)


class ValidarVersionTest(TestCase):
    def test_version_semantica(self):
        self.assertEqual(validar_version("v1.0.0"), "v1.0.0")
        self.assertEqual(validar_version("2.1.3"), "2.1.3")
        self.assertEqual(validar_version("v3"), "v3")

    def test_version_invalida(self):
        with self.assertRaises(ValidationError):
            validar_version("version-1.0")

    def test_version_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_version("v" + ".".join(["1"] * 20))


class ValidarDocumentacionProveedorTest(TestCase):
    def test_documentacion_valida(self):
        url = "https://docs.stripe.com"
        self.assertEqual(validar_documentacion_proveedor(url), url)

    def test_documentacion_opcional(self):
        self.assertIsNone(validar_documentacion_proveedor(None))
        self.assertEqual(validar_documentacion_proveedor(""), "")

    def test_documentacion_invalida(self):
        with self.assertRaises(ValidationError):
            validar_documentacion_proveedor("not-a-url")


class ValidarTipoAuthTest(TestCase):
    def test_tipos_auth_validos(self):
        for tipo in ["API_KEY", "OAuth2", "Bearer", "JWT", "None"]:
            self.assertEqual(validar_tipo_auth(tipo), tipo)

    def test_tipo_auth_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_auth("CustomAuth")

    def test_tipo_auth_requerido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_auth(None)


class ValidarConfigAuthTest(TestCase):
    def test_config_valida(self):
        config = {"api_key_header": "X-API-Key", "location": "header"}
        self.assertEqual(validar_config_auth(config), config)

    def test_config_vacia(self):
        with self.assertRaises(ValidationError):
            validar_config_auth({})

    def test_config_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_config_auth(["api_key"])

    def test_config_muy_grande(self):
        config = {"data": "x" * 15000}
        with self.assertRaises(ValidationError):
            validar_config_auth(config)


class ValidarTimeoutTest(TestCase):
    def test_timeout_valido(self):
        self.assertEqual(validar_timeout(30), 30)
        self.assertEqual(validar_timeout(1), 1)
        self.assertEqual(validar_timeout(300), 300)

    def test_timeout_muy_bajo(self):
        with self.assertRaises(ValidationError):
            validar_timeout(0)

    def test_timeout_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_timeout(301)


class ValidarMaxReintentosTest(TestCase):
    def test_reintentos_validos(self):
        self.assertEqual(validar_max_reintentos(0), 0)
        self.assertEqual(validar_max_reintentos(5), 5)
        self.assertEqual(validar_max_reintentos(10), 10)

    def test_reintentos_negativos(self):
        with self.assertRaises(ValidationError):
            validar_max_reintentos(-1)

    def test_reintentos_muy_altos(self):
        with self.assertRaises(ValidationError):
            validar_max_reintentos(11)


class ValidarActivoProveedorTest(TestCase):
    def test_activo_valido(self):
        self.assertTrue(validar_activo_proveedor(True))
        self.assertFalse(validar_activo_proveedor(False))

    def test_activo_no_booleano(self):
        with self.assertRaises(ValidationError):
            validar_activo_proveedor(1)


# ============================================================================
# TESTS DE VALIDADORES DE ENDPOINTS API
# ============================================================================


class ValidarNombreEndpointTest(TestCase):
    def test_nombre_valido(self):
        self.assertEqual(validar_nombre_endpoint("Create Payment"), "Create Payment")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_endpoint("AB")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_endpoint("A" * 101)


class ValidarDescripcionEndpointTest(TestCase):
    def test_descripcion_valida(self):
        desc = "Crea un nuevo pago en Stripe"
        self.assertEqual(validar_descripcion_endpoint(desc), desc)

    def test_descripcion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_endpoint("Corta")

    def test_descripcion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_endpoint("A" * 2001)


class ValidarPathEndpointTest(TestCase):
    def test_path_valido(self):
        self.assertEqual(validar_path_endpoint("/api/v1/payments"), "/api/v1/payments")
        self.assertEqual(validar_path_endpoint("/users/{id}"), "/users/{id}")

    def test_path_sin_barra_inicial(self):
        with self.assertRaises(ValidationError):
            validar_path_endpoint("api/payments")

    def test_path_con_espacios(self):
        with self.assertRaises(ValidationError):
            validar_path_endpoint("/api /payments")

    def test_path_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_path_endpoint("/api/payments?filter=active")


class ValidarMetodoHttpTest(TestCase):
    def test_metodos_validos(self):
        for metodo in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            self.assertEqual(validar_metodo_http(metodo), metodo)

        # Debe convertir a mayúsculas
        self.assertEqual(validar_metodo_http("get"), "GET")

    def test_metodo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_metodo_http("CONNECT")


class ValidarHeadersEndpointTest(TestCase):
    def test_headers_validos(self):
        headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
        self.assertEqual(validar_headers_endpoint(headers), headers)

    def test_headers_vacios(self):
        self.assertEqual(validar_headers_endpoint({}), {})

    def test_headers_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_headers_endpoint(["Content-Type"])

    def test_headers_clave_invalida(self):
        with self.assertRaises(ValidationError):
            validar_headers_endpoint({"Invalid Header!": "value"})


class ValidarParametrosEndpointTest(TestCase):
    def test_parametros_dict(self):
        params = {"page": 1, "limit": 10}
        self.assertEqual(validar_parametros_endpoint(params), params)

    def test_parametros_list(self):
        params = ["page", "limit", "filter"]
        self.assertEqual(validar_parametros_endpoint(params), params)

    def test_parametros_vacios(self):
        self.assertEqual(validar_parametros_endpoint({}), {})
        self.assertEqual(validar_parametros_endpoint([]), [])

    def test_parametros_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_parametros_endpoint("page,limit")


class ValidarSchemaRequestTest(TestCase):
    def test_schema_valido(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        self.assertEqual(validar_schema_request(schema), schema)

    def test_schema_null(self):
        self.assertIsNone(validar_schema_request(None))

    def test_schema_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_schema_request(["type", "object"])

    def test_schema_muy_grande(self):
        schema = {"data": "x" * 60000}
        with self.assertRaises(ValidationError):
            validar_schema_request(schema)


class ValidarSchemaResponseTest(TestCase):
    def test_schema_valido(self):
        schema = {"type": "object", "properties": {"id": {"type": "number"}}}
        self.assertEqual(validar_schema_response(schema), schema)

    def test_schema_null(self):
        self.assertIsNone(validar_schema_response(None))


class ValidarCacheSegundosTest(TestCase):
    def test_cache_valido(self):
        self.assertEqual(validar_cache_segundos(0), 0)
        self.assertEqual(validar_cache_segundos(3600), 3600)
        self.assertEqual(validar_cache_segundos(86400), 86400)

    def test_cache_negativo(self):
        with self.assertRaises(ValidationError):
            validar_cache_segundos(-1)

    def test_cache_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_cache_segundos(86401)


class ValidarRequiereAuthEndpointTest(TestCase):
    def test_requiere_auth_valido(self):
        self.assertEqual(validar_requiere_auth_endpoint(0), 0)
        self.assertEqual(validar_requiere_auth_endpoint(1), 1)

    def test_requiere_auth_invalido(self):
        with self.assertRaises(ValidationError):
            validar_requiere_auth_endpoint(2)


class ValidarActivoEndpointTest(TestCase):
    def test_activo_valido(self):
        self.assertTrue(validar_activo_endpoint(True))
        self.assertFalse(validar_activo_endpoint(False))

    def test_activo_no_booleano(self):
        with self.assertRaises(ValidationError):
            validar_activo_endpoint(1)


# ============================================================================
# TESTS DE VALIDADORES DE LOGS LLAMADAS API
# ============================================================================


class ValidarTimestampLogTest(TestCase):
    def test_timestamp_valido(self):
        ahora = datetime.now(timezone.utc)
        self.assertEqual(validar_timestamp_log(ahora), ahora)

    def test_timestamp_pasado(self):
        ayer = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertEqual(validar_timestamp_log(ayer), ayer)

    def test_timestamp_futuro(self):
        futuro = datetime.now(timezone.utc) + timedelta(hours=2)
        with self.assertRaises(ValidationError):
            validar_timestamp_log(futuro)


class ValidarMetodoLogTest(TestCase):
    def test_metodo_valido(self):
        self.assertEqual(validar_metodo_log("POST"), "POST")
        self.assertEqual(validar_metodo_log("get"), "GET")

    def test_metodo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_metodo_log("TRACE")


class ValidarUrlLogTest(TestCase):
    def test_url_valida(self):
        url = "https://api.stripe.com/v1/charges"
        self.assertEqual(validar_url_log(url), url)

    def test_url_vacia(self):
        with self.assertRaises(ValidationError):
            validar_url_log("")

    def test_url_muy_larga(self):
        url = "https://api.example.com/" + "a" * 500
        with self.assertRaises(ValidationError):
            validar_url_log(url)


class ValidarHeadersLogTest(TestCase):
    def test_headers_validos(self):
        headers = {"Content-Type": "application/json"}
        self.assertEqual(validar_headers_log(headers), headers)

    def test_headers_vacios(self):
        self.assertEqual(validar_headers_log({}), {})

    def test_headers_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_headers_log(None)


class ValidarPayloadLogTest(TestCase):
    def test_payload_valido(self):
        payload = '{"amount": 1000, "currency": "USD"}'
        self.assertEqual(validar_payload_log(payload), payload)

    def test_payload_opcional(self):
        self.assertIsNone(validar_payload_log(None))
        self.assertEqual(validar_payload_log(""), "")

    def test_payload_muy_grande(self):
        payload = "x" * 1000001
        with self.assertRaises(ValidationError):
            validar_payload_log(payload)


class ValidarStatusCodeTest(TestCase):
    def test_status_codes_validos(self):
        for code in [200, 201, 400, 404, 500, 503]:
            self.assertEqual(validar_status_code(code), code)

    def test_status_code_muy_bajo(self):
        with self.assertRaises(ValidationError):
            validar_status_code(99)

    def test_status_code_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_status_code(600)


class ValidarTiempoMsTest(TestCase):
    def test_tiempo_valido(self):
        self.assertEqual(validar_tiempo_ms(0), 0)
        self.assertEqual(validar_tiempo_ms(1500), 1500)
        self.assertEqual(validar_tiempo_ms(3600000), 3600000)

    def test_tiempo_negativo(self):
        with self.assertRaises(ValidationError):
            validar_tiempo_ms(-1)

    def test_tiempo_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_tiempo_ms(3600001)


class ValidarBytesSentTest(TestCase):
    def test_bytes_validos(self):
        self.assertEqual(validar_bytes_sent(0), 0)
        self.assertEqual(validar_bytes_sent(1024), 1024)

    def test_bytes_opcional(self):
        self.assertIsNone(validar_bytes_sent(None))

    def test_bytes_negativos(self):
        with self.assertRaises(ValidationError):
            validar_bytes_sent(-1)

    def test_bytes_muy_grandes(self):
        with self.assertRaises(ValidationError):
            validar_bytes_sent(100000001)


class ValidarBytesReceivedTest(TestCase):
    def test_bytes_validos(self):
        self.assertEqual(validar_bytes_received(512), 512)

    def test_bytes_opcional(self):
        self.assertIsNone(validar_bytes_received(None))


class ValidarExitosoLogTest(TestCase):
    def test_exitoso_valido(self):
        self.assertEqual(validar_exitoso_log(0), 0)
        self.assertEqual(validar_exitoso_log(1), 1)

    def test_exitoso_invalido(self):
        with self.assertRaises(ValidationError):
            validar_exitoso_log(2)


class ValidarErrorMsgLogTest(TestCase):
    def test_error_msg_valido(self):
        msg = "Connection timeout after 30 seconds"
        self.assertEqual(validar_error_msg_log(msg), msg)

    def test_error_msg_opcional(self):
        self.assertIsNone(validar_error_msg_log(None))

    def test_error_msg_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_error_msg_log("Error: " + "x" * 5000)


class ValidarIntentoLogTest(TestCase):
    def test_intento_valido(self):
        self.assertEqual(validar_intento_log(1), 1)
        self.assertEqual(validar_intento_log(5), 5)

    def test_intento_muy_bajo(self):
        with self.assertRaises(ValidationError):
            validar_intento_log(0)

    def test_intento_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_intento_log(101)


class ValidarIpOrigenLogTest(TestCase):
    def test_ipv4_valida(self):
        self.assertEqual(validar_ip_origen_log("192.168.1.1"), "192.168.1.1")
        self.assertEqual(validar_ip_origen_log("127.0.0.1"), "127.0.0.1")

    def test_ipv6_valida(self):
        self.assertEqual(validar_ip_origen_log("2001:db8::1"), "2001:db8::1")

    def test_ip_opcional(self):
        self.assertIsNone(validar_ip_origen_log(None))
        self.assertEqual(validar_ip_origen_log(""), "")

    def test_ip_invalida(self):
        with self.assertRaises(ValidationError):
            validar_ip_origen("not-an-ip", "IP")


class ValidarContextoLogTest(TestCase):
    def test_contexto_valido(self):
        ctx = {"user_id": 123, "action": "create_payment"}
        self.assertEqual(validar_contexto_log(ctx), ctx)

    def test_contexto_vacio(self):
        self.assertEqual(validar_contexto_log({}), {})

    def test_contexto_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_contexto_log(["user_id", 123])

    def test_contexto_muy_grande(self):
        ctx = {"data": "x" * 15000}
        with self.assertRaises(ValidationError):
            validar_contexto_log(ctx)


# ============================================================================
# TESTS DE VALIDADORES DE CREDENCIALES API
# ============================================================================


class ValidarAmbienteTest(TestCase):
    def test_ambientes_validos(self):
        for amb in ["development", "staging", "production", "testing"]:
            self.assertEqual(validar_ambiente(amb), amb)

        # Debe aceptar mayúsculas/minúsculas
        self.assertEqual(validar_ambiente("PRODUCTION").lower(), "production")

    def test_ambiente_invalido(self):
        with self.assertRaises(ValidationError):
            validar_ambiente("qa")


class ValidarApiKeyTest(TestCase):
    def test_api_key_valida(self):
        key = "sk_test_1234567890abcdef"
        self.assertEqual(validar_api_key(key), key)

    def test_api_key_opcional(self):
        self.assertIsNone(validar_api_key(None))
        self.assertEqual(validar_api_key(""), "")

    def test_api_key_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_api_key("short")

    def test_api_key_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_api_key("x" * 5001)


class ValidarSecretTest(TestCase):
    def test_secret_valido(self):
        secret = "whsec_1234567890abcdef1234567890"
        self.assertEqual(validar_secret(secret), secret)

    def test_secret_opcional(self):
        self.assertIsNone(validar_secret(None))


class ValidarTokenTest(TestCase):
    def test_token_valido(self):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
        self.assertEqual(validar_token(token), token)

    def test_token_opcional(self):
        self.assertIsNone(validar_token(None))


class ValidarConfiguracionCredTest(TestCase):
    def test_configuracion_valida(self):
        config = {"webhook_secret": "whsec_123", "api_version": "2023-10-16"}
        self.assertEqual(validar_configuracion_cred(config), config)

    def test_configuracion_vacia(self):
        self.assertEqual(validar_configuracion_cred({}), {})

    def test_configuracion_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_configuracion_cred(["key", "value"])

    def test_configuracion_muy_grande(self):
        config = {"data": "x" * 25000}
        with self.assertRaises(ValidationError):
            validar_configuracion_cred(config)


class ValidarFechaExpiracionCredTest(TestCase):
    def test_fecha_futura(self):
        futura = datetime.now(timezone.utc) + timedelta(days=30)
        self.assertEqual(validar_fecha_expiracion_cred(futura), futura)

    def test_fecha_opcional(self):
        self.assertIsNone(validar_fecha_expiracion_cred(None))

    def test_fecha_pasada(self):
        pasada = datetime.now(timezone.utc) - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fecha_expiracion_cred(pasada)


class ValidarUpdatedAtCredTest(TestCase):
    def test_updated_at_valido(self):
        ahora = datetime.now(timezone.utc)
        self.assertEqual(validar_updated_at_cred(ahora), ahora)

    def test_updated_at_futuro(self):
        futuro = datetime.now(timezone.utc) + timedelta(hours=2)
        with self.assertRaises(ValidationError):
            validar_updated_at_cred(futuro)


class ValidarActivoCredencialTest(TestCase):
    def test_activo_valido(self):
        self.assertTrue(validar_activo_credencial(True))
        self.assertFalse(validar_activo_credencial(False))

    def test_activo_no_booleano(self):
        with self.assertRaises(ValidationError):
            validar_activo_credencial(1)


# ============================================================================
# TESTS DE VALIDADORES DE LOGS WEBHOOKS
# ============================================================================


class ValidarTimestampWebhookTest(TestCase):
    def test_timestamp_valido(self):
        ahora = datetime.now(timezone.utc)
        self.assertEqual(validar_timestamp_webhook(ahora), ahora)

    def test_timestamp_futuro(self):
        futuro = datetime.now(timezone.utc) + timedelta(hours=2)
        with self.assertRaises(ValidationError):
            validar_timestamp_webhook(futuro)


class ValidarHeadersWebhookTest(TestCase):
    def test_headers_validos(self):
        headers = {"X-Webhook-Signature": "sha256=abc123"}
        self.assertEqual(validar_headers_webhook(headers), headers)


class ValidarPayloadWebhookTest(TestCase):
    def test_payload_valido(self):
        payload = '{"event": "payment.success", "data": {"id": 123}}'
        self.assertEqual(validar_payload_webhook(payload), payload)

    def test_payload_vacio(self):
        with self.assertRaises(ValidationError):
            validar_payload_webhook("")

    def test_payload_muy_grande(self):
        with self.assertRaises(ValidationError):
            validar_payload_webhook("x" * 1000001)


class ValidarEventoTipoTest(TestCase):
    def test_evento_valido(self):
        self.assertEqual(validar_evento_tipo("payment.created"), "payment.created")
        self.assertEqual(validar_evento_tipo("user_signup"), "user_signup")
        self.assertEqual(validar_evento_tipo("invoice.updated"), "invoice.updated")

    def test_evento_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_evento_tipo("ok")

    def test_evento_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_evento_tipo("payment created!")


class ValidarVerificacionOkTest(TestCase):
    def test_verificacion_valida(self):
        self.assertEqual(validar_verificacion_ok(0), 0)
        self.assertEqual(validar_verificacion_ok(1), 1)

    def test_verificacion_invalida(self):
        with self.assertRaises(ValidationError):
            validar_verificacion_ok(2)


class ValidarProcesadoOkTest(TestCase):
    def test_procesado_valido(self):
        self.assertEqual(validar_procesado_ok(0), 0)
        self.assertEqual(validar_procesado_ok(1), 1)

    def test_procesado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_procesado_ok(2)


class ValidarTiempoProcMsWebhookTest(TestCase):
    def test_tiempo_valido(self):
        self.assertEqual(validar_tiempo_proc_ms_webhook(150), 150)
        self.assertEqual(validar_tiempo_proc_ms_webhook(60000), 60000)

    def test_tiempo_opcional(self):
        self.assertIsNone(validar_tiempo_proc_ms_webhook(None))

    def test_tiempo_muy_alto(self):
        with self.assertRaises(ValidationError):
            validar_tiempo_proc_ms_webhook(60001)


class ValidarErrorMsgWebhookTest(TestCase):
    def test_error_msg_valido(self):
        msg = "Signature verification failed"
        self.assertEqual(validar_error_msg_webhook(msg), msg)

    def test_error_msg_opcional(self):
        self.assertIsNone(validar_error_msg_webhook(None))


class ValidarIpOrigenWebhookTest(TestCase):
    def test_ip_valida(self):
        self.assertEqual(validar_ip_origen_webhook("54.192.1.25"), "54.192.1.25")

    def test_ip_requerida(self):
        with self.assertRaises(ValidationError):
            validar_ip_origen_webhook(None)


class ValidarUserAgentTest(TestCase):
    def test_user_agent_valido(self):
        ua = "Stripe/1.0 (+https://stripe.com/docs/webhooks)"
        self.assertEqual(validar_user_agent(ua), ua)

    def test_user_agent_opcional(self):
        self.assertIsNone(validar_user_agent(None))

    def test_user_agent_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_user_agent("x" * 501)


# ============================================================================
# TESTS DE VALIDADORES DE WEBHOOK ENDPOINTS
# ============================================================================


class ValidarNombreWebhookTest(TestCase):
    def test_nombre_valido(self):
        self.assertEqual(validar_nombre_webhook("Stripe Webhooks"), "Stripe Webhooks")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_webhook("AB")


class ValidarDescripcionWebhookTest(TestCase):
    def test_descripcion_valida(self):
        desc = "Recibe eventos de pagos desde Stripe"
        self.assertEqual(validar_descripcion_webhook(desc), desc)

    def test_descripcion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_webhook("Corta")


class ValidarPathWebhookTest(TestCase):
    def test_path_valido(self):
        self.assertEqual(validar_path_webhook("/webhooks/stripe"), "/webhooks/stripe")

    def test_path_sin_barra(self):
        with self.assertRaises(ValidationError):
            validar_path_webhook("webhooks/stripe")


class ValidarRequiereVerificacionTest(TestCase):
    def test_requiere_verificacion_valido(self):
        self.assertEqual(validar_requiere_verificacion(0), 0)
        self.assertEqual(validar_requiere_verificacion(1), 1)

    def test_requiere_verificacion_invalido(self):
        with self.assertRaises(ValidationError):
            validar_requiere_verificacion(2)


class ValidarSecretKeyWebhookTest(TestCase):
    def test_secret_key_valida(self):
        key = "whsec_" + "a" * 32
        self.assertEqual(validar_secret_key_webhook(key), key)

    def test_secret_key_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_secret_key_webhook("short_secret")

    def test_secret_key_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_secret_key_webhook("x" * 256)


class ValidarHeaderVerificacionTest(TestCase):
    def test_header_valido(self):
        self.assertEqual(validar_header_verificacion("X-Stripe-Signature"), "X-Stripe-Signature")
        self.assertEqual(validar_header_verificacion("Authorization"), "Authorization")

    def test_header_empieza_con_numero(self):
        with self.assertRaises(ValidationError):
            validar_header_verificacion("123-Header")

    def test_header_con_espacios(self):
        with self.assertRaises(ValidationError):
            validar_header_verificacion("X Stripe Signature")


class ValidarEventosWebhookTest(TestCase):
    def test_eventos_validos(self):
        eventos = ["payment.created", "payment.updated", "payment.deleted"]
        self.assertEqual(validar_eventos_webhook(eventos), eventos)

    def test_eventos_vacios(self):
        with self.assertRaises(ValidationError):
            validar_eventos_webhook([])

    def test_eventos_duplicados(self):
        with self.assertRaises(ValidationError):
            validar_eventos_webhook(["payment.created", "payment.created"])

    def test_evento_no_string(self):
        with self.assertRaises(ValidationError):
            validar_eventos_webhook([123, "payment.created"])

    def test_evento_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_eventos_webhook(["ab"])


class ValidarHandlerFuncTest(TestCase):
    def test_handler_func_valido(self):
        func = "apps.api_integrations.handlers.handle_stripe_webhook"
        self.assertEqual(validar_handler_func(func), func)

        func2 = "myapp.webhooks.process_payment"
        self.assertEqual(validar_handler_func(func2), func2)

    def test_handler_func_sin_puntos(self):
        with self.assertRaises(ValidationError):
            validar_handler_func("handle_webhook")

    def test_handler_func_empieza_con_numero(self):
        with self.assertRaises(ValidationError):
            validar_handler_func("123app.handler.func")

    def test_handler_func_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_handler_func("a.b." + "c" * 200)


class ValidarActivoWebhookTest(TestCase):
    def test_activo_valido(self):
        self.assertTrue(validar_activo_webhook(True))
        self.assertFalse(validar_activo_webhook(False))

    def test_activo_no_booleano(self):
        with self.assertRaises(ValidationError):
            validar_activo_webhook(1)


class ValidarCreatedAtWebhookTest(TestCase):
    def test_created_at_valido(self):
        ahora = datetime.now(timezone.utc)
        self.assertEqual(validar_created_at_webhook(ahora), ahora)

    def test_created_at_futuro(self):
        futuro = datetime.now(timezone.utc) + timedelta(hours=2)
        with self.assertRaises(ValidationError):
            validar_created_at_webhook(futuro)
