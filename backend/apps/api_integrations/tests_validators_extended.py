"""
Extended tests for apps/api_integrations/validators.py covering previously missing lines.

Missing lines: 20, 34, 61, 77, 85, 109, 121, 144, 161, 169, 173-174, 187, 191-192,
218, 232, 246, 264, 272, 287, 297, 310, 335, 353, 357-358, 371, 375-376, 400, 403,
418, 438, 446-447, 458, 469, 481, 485-486, 497, 501-502, 519-520, 545, 549-550,
564, 575, 579-580, 598, 612, 617, 631, 642, 655, 673, 704, 715, 726, 741, 744,
786, 798, 804, 819, 823-824, 835, 839-840, 855-856, 859, 882, 913, 917-918, 929,
945, 960, 968, 971, 986, 1001, 1031, 1034
"""

from datetime import datetime, timezone, timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.api_integrations.validators import (
    validar_nombre_proveedor,
    validar_descripcion_proveedor,
    validar_url_base,
    validar_version,
    validar_documentacion_proveedor,
    validar_config_auth,
    validar_timeout,
    validar_max_reintentos,
    validar_nombre_endpoint,
    validar_descripcion_endpoint,
    validar_path_endpoint,
    validar_metodo_http,
    validar_headers_endpoint,
    validar_parametros_endpoint,
    validar_schema_json,
    validar_cache_segundos,
    validar_requiere_auth_endpoint,
    validar_timestamp_log,
    validar_metodo_log,
    validar_url_log,
    validar_headers_log,
    validar_payload_log,
    validar_status_code,
    validar_tiempo_ms,
    validar_bytes_transferidos,
    validar_exitoso_log,
    validar_error_msg_log,
    validar_intento_log,
    validar_ip_origen,
    validar_contexto_log,
    validar_ambiente,
    validar_credencial_opcional,
    validar_configuracion_cred,
    validar_fecha_expiracion_cred,
    validar_updated_at_cred,
    validar_payload_webhook,
    validar_evento_tipo,
    validar_verificacion_ok,
    validar_procesado_ok,
    validar_tiempo_proc_ms_webhook,
    validar_user_agent,
    validar_requiere_verificacion,
    validar_secret_key_webhook,
    validar_header_verificacion,
    validar_eventos_webhook,
    validar_handler_func,
)


def _future_dt():
    return datetime.now(timezone.utc) + timedelta(days=365)


def _past_dt():
    return datetime.now(timezone.utc) - timedelta(hours=6)


# ==============================================================================
# Proveedor validators
# ==============================================================================


class ValidarNombreProveedorExtendedTest(TestCase):
    """Line 20: None/empty nombre raises."""

    def test_nombre_none(self):
        with self.assertRaises(ValidationError):
            validar_nombre_proveedor(None)

    def test_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            validar_nombre_proveedor("")

    def test_nombre_valido(self):
        validar_nombre_proveedor("Bancard API")  # No raise


class ValidarDescripcionProveedorExtendedTest(TestCase):
    """Line 34: None raises."""

    def test_descripcion_none(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_proveedor(None)

    def test_descripcion_valida(self):
        validar_descripcion_proveedor("Servicio de pagos electrónicos del Paraguay")


class ValidarUrlBaseExtendedTest(TestCase):
    """Lines 61, 77."""

    def test_url_none(self):
        """Line 61: None raises."""
        with self.assertRaises(ValidationError):
            validar_url_base(None)

    def test_url_vacia(self):
        """Line 61: empty raises."""
        with self.assertRaises(ValidationError):
            validar_url_base("")

    def test_url_muy_larga(self):
        """Line 77: URL > 200 chars raises."""
        url = "https://example.com/" + "a" * 190
        with self.assertRaises(ValidationError) as ctx:
            validar_url_base(url)
        self.assertIn("200", str(ctx.exception))

    def test_url_valida(self):
        validar_url_base("https://api.bancard.com.py")


class ValidarVersionExtendedTest(TestCase):
    """Line 85: None raises."""

    def test_version_none(self):
        with self.assertRaises(ValidationError):
            validar_version(None)

    def test_version_valida(self):
        validar_version("v1.0.0")


class ValidarDocumentacionExtendedTest(TestCase):
    """Lines 109, 121: non-string and too long."""

    def test_documentacion_no_string(self):
        """Line 109: numeric value raises."""
        with self.assertRaises(ValidationError):
            validar_documentacion_proveedor(12345)

    def test_documentacion_muy_larga(self):
        """Line 121: > 200 chars raises."""
        url = "https://docs.example.com/" + "a" * 185
        with self.assertRaises(ValidationError) as ctx:
            validar_documentacion_proveedor(url)
        self.assertIn("200", str(ctx.exception))

    def test_documentacion_none_ok(self):
        """None is optional -- returns without error."""
        validar_documentacion_proveedor(None)


class ValidarConfigAuthExtendedTest(TestCase):
    """Lines 144, 161: None and JSON error."""

    def test_config_auth_none(self):
        """Line 144: None raises."""
        with self.assertRaises(ValidationError):
            validar_config_auth(None)

    def test_config_auth_valida(self):
        validar_config_auth({"api_key": "my-key"})


class ValidarTimeoutExtendedTest(TestCase):
    """Lines 169, 173-174: None and non-integer."""

    def test_timeout_none(self):
        """Line 169: None raises."""
        with self.assertRaises(ValidationError):
            validar_timeout(None)

    def test_timeout_no_entero(self):
        """Lines 173-174: non-numeric string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_timeout("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_timeout_valido(self):
        validar_timeout(30)


class ValidarMaxReintentosExtendedTest(TestCase):
    """Lines 187, 191-192: None and non-integer."""

    def test_max_reintentos_none(self):
        """Line 187: None raises."""
        with self.assertRaises(ValidationError):
            validar_max_reintentos(None)

    def test_max_reintentos_no_entero(self):
        """Lines 191-192: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_max_reintentos("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_max_reintentos_valido(self):
        validar_max_reintentos(3)


# ==============================================================================
# Endpoint validators
# ==============================================================================


class ValidarNombreEndpointExtendedTest(TestCase):
    """Line 218."""

    def test_nombre_none(self):
        with self.assertRaises(ValidationError):
            validar_nombre_endpoint(None)

    def test_nombre_valido(self):
        validar_nombre_endpoint("crear-pago")


class ValidarDescripcionEndpointExtendedTest(TestCase):
    """Line 232."""

    def test_descripcion_none(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_endpoint(None)

    def test_descripcion_valida(self):
        validar_descripcion_endpoint("Endpoint para iniciar transacciones de pago")


class ValidarPathEndpointExtendedTest(TestCase):
    """Lines 246, 264."""

    def test_path_none(self):
        """Line 246: None raises."""
        with self.assertRaises(ValidationError):
            validar_path_endpoint(None)

    def test_path_muy_largo(self):
        """Line 264: > 200 chars raises."""
        path = "/" + "a" * 210
        with self.assertRaises(ValidationError) as ctx:
            validar_path_endpoint(path)
        self.assertIn("200", str(ctx.exception))

    def test_path_valido(self):
        validar_path_endpoint("/api/v1/payments")


class ValidarMetodoHttpLogExtendedTest(TestCase):
    """Line 272 (metodo_http), Line 418 (metodo_log)."""

    def test_metodo_none(self):
        with self.assertRaises(ValidationError):
            validar_metodo_http(None)

    def test_metodo_valido(self):
        validar_metodo_http("POST")

    def test_metodo_log_none(self):
        with self.assertRaises(ValidationError):
            validar_metodo_log(None)

    def test_metodo_log_valido(self):
        validar_metodo_log("GET")


class ValidarHeadersEndpointExtendedTest(TestCase):
    """Lines 287, 297."""

    def test_headers_none(self):
        """Line 287: None raises."""
        with self.assertRaises(ValidationError):
            validar_headers_endpoint(None)

    def test_headers_clave_no_string(self):
        """Line 297: non-string key raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_headers_endpoint({1: "valor"})
        self.assertIn("strings", str(ctx.exception).lower())

    def test_headers_validos(self):
        validar_headers_endpoint({"Content-Type": "application/json"})


class ValidarParametrosExtendedTest(TestCase):
    """Line 310."""

    def test_parametros_none(self):
        with self.assertRaises(ValidationError):
            validar_parametros_endpoint(None)

    def test_parametros_validos(self):
        validar_parametros_endpoint({"page": 1})


class ValidarSchemaJSONExtendedTest(TestCase):
    """Line 335."""

    def test_schema_muy_grande(self):
        """Large non-serializable dict raises."""
        # Create a dict with a non-JSON-serializable value (set) to trigger TypeError
        import unittest

        # Instead trigger the "too large" check with a large dict
        big_dict = {str(i): "x" * 100 for i in range(600)}
        with self.assertRaises(ValidationError) as ctx:
            validar_schema_json(big_dict)
        self.assertIn("grande", str(ctx.exception).lower())

    def test_schema_none_ok(self):
        """None is valid (optional schema)."""
        validar_schema_json(None)

    def test_schema_valido(self):
        validar_schema_json({"type": "object", "properties": {}})


class ValidarCacheSegundosExtendedTest(TestCase):
    """Lines 353, 357-358."""

    def test_cache_none(self):
        """Line 353: None raises."""
        with self.assertRaises(ValidationError):
            validar_cache_segundos(None)

    def test_cache_no_entero(self):
        """Lines 357-358: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cache_segundos("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_cache_valido(self):
        validar_cache_segundos(300)


class ValidarRequiereAuthExtendedTest(TestCase):
    """Lines 371, 375-376."""

    def test_requiere_auth_none(self):
        """Line 371: None raises."""
        with self.assertRaises(ValidationError):
            validar_requiere_auth_endpoint(None)

    def test_requiere_auth_no_entero(self):
        """Lines 375-376: string raises."""
        with self.assertRaises(ValidationError):
            validar_requiere_auth_endpoint("si")

    def test_requiere_auth_valido(self):
        validar_requiere_auth_endpoint(1)
        validar_requiere_auth_endpoint(0)


# ==============================================================================
# Log validators
# ==============================================================================


class ValidarTimestampLogExtendedTest(TestCase):
    """Lines 400, 403."""

    def test_timestamp_none(self):
        """Line 400: None raises."""
        with self.assertRaises(ValidationError):
            validar_timestamp_log(None)

    def test_timestamp_no_datetime(self):
        """Line 403: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_timestamp_log("2024-01-15")
        self.assertIn("datetime", str(ctx.exception).lower())

    def test_timestamp_valido(self):
        validar_timestamp_log(_past_dt())


class ValidarUrlLogExtendedTest(TestCase):
    """Lines 438, 446-447."""

    def test_url_none(self):
        """Line 438: None raises."""
        with self.assertRaises(ValidationError):
            validar_url_log(None)

    def test_url_invalida(self):
        """Lines 446-447: invalid URL raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_url_log("not-a-valid-url")
        self.assertIn("formato", str(ctx.exception).lower())

    def test_url_valida(self):
        validar_url_log("https://api.bancard.com/payments")


class ValidarHeadersLogExtendedTest(TestCase):
    """Line 458."""

    def test_headers_no_dict(self):
        """Line 458: non-dict raises."""
        with self.assertRaises(ValidationError):
            validar_headers_log("not-a-dict")

    def test_headers_validos(self):
        validar_headers_log({"Authorization": "Bearer token"})


class ValidarPayloadLogExtendedTest(TestCase):
    """Line 469."""

    def test_payload_no_string(self):
        """Line 469: non-string (e.g. list) raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_payload_log(["list", "item"])
        self.assertIn("texto", str(ctx.exception).lower())

    def test_payload_none_ok(self):
        """None is optional -- returns without error."""
        validar_payload_log(None)

    def test_payload_valido(self):
        validar_payload_log('{"monto": 50000}')


class ValidarStatusCodeExtendedTest(TestCase):
    """Lines 481, 485-486."""

    def test_status_code_none(self):
        """Line 481: None raises."""
        with self.assertRaises(ValidationError):
            validar_status_code(None)

    def test_status_code_no_entero(self):
        """Lines 485-486: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_status_code("ok")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_status_code_valido(self):
        validar_status_code(200)


class ValidarTiempoMsExtendedTest(TestCase):
    """Lines 497, 501-502."""

    def test_tiempo_none(self):
        """Line 497: None raises."""
        with self.assertRaises(ValidationError):
            validar_tiempo_ms(None)

    def test_tiempo_no_entero(self):
        """Lines 501-502: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_tiempo_ms("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_tiempo_valido(self):
        validar_tiempo_ms(350)


class ValidarBytesTransferidosExtendedTest(TestCase):
    """Lines 519-520."""

    def test_bytes_no_entero(self):
        """Lines 519-520: non-numeric string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_bytes_transferidos("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_bytes_none_ok(self):
        """None returns without error (optional)."""
        validar_bytes_transferidos(None)

    def test_bytes_valido(self):
        validar_bytes_transferidos(1024)


class ValidarExitosoLogExtendedTest(TestCase):
    """Lines 545, 549-550."""

    def test_exitoso_none(self):
        """Line 545: None raises."""
        with self.assertRaises(ValidationError):
            validar_exitoso_log(None)

    def test_exitoso_no_entero(self):
        """Lines 549-550: string raises."""
        with self.assertRaises(ValidationError):
            validar_exitoso_log("si")

    def test_exitoso_valido(self):
        validar_exitoso_log(1)
        validar_exitoso_log(0)


class ValidarErrorMsgLogExtendedTest(TestCase):
    """Line 564."""

    def test_error_msg_no_string(self):
        """Line 564: list raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_error_msg_log(["error"])
        self.assertIn("texto", str(ctx.exception).lower())

    def test_error_msg_none_ok(self):
        validar_error_msg_log(None)


class ValidarIntentoLogExtendedTest(TestCase):
    """Lines 575, 579-580."""

    def test_intento_none(self):
        """Line 575: None raises."""
        with self.assertRaises(ValidationError):
            validar_intento_log(None)

    def test_intento_no_entero(self):
        """Lines 579-580: string raises."""
        with self.assertRaises(ValidationError):
            validar_intento_log("abc")

    def test_intento_valido(self):
        validar_intento_log(1)


class ValidarIpOrigenExtendedTest(TestCase):
    """Lines 598, 612, 617."""

    def test_ip_no_string(self):
        """Line 598: non-string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_ip_origen(12345)
        self.assertIn("texto", str(ctx.exception).lower())

    def test_ipv4_octeto_invalido(self):
        """Line 612: IPv4 with octeto > 255 raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_ip_origen("256.0.0.1")
        self.assertIn("octeto", str(ctx.exception).lower())

    def test_ipv6_muy_larga(self):
        """Line 617: IPv6 too long raises."""
        long_ipv6 = "2001:db8::" + "a" * 30
        with self.assertRaises(ValidationError) as ctx:
            validar_ip_origen(long_ipv6)
        self.assertIn("larga", str(ctx.exception).lower())

    def test_ipv4_valida(self):
        validar_ip_origen("192.168.1.100")


class ValidarContextoLogExtendedTest(TestCase):
    """Lines 631, 642."""

    def test_contexto_none(self):
        """Line 631: None raises."""
        with self.assertRaises(ValidationError):
            validar_contexto_log(None)

    def test_contexto_valido(self):
        validar_contexto_log({"user_id": 5, "action": "pay"})


class ValidarAmbienteExtendedTest(TestCase):
    """Line 655."""

    def test_ambiente_none(self):
        with self.assertRaises(ValidationError):
            validar_ambiente(None)

    def test_ambiente_valido(self):
        validar_ambiente("production")


class ValidarCredencialOpcionalExtendedTest(TestCase):
    """Line 673."""

    def test_cred_no_string(self):
        """Line 673: numeric raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_credencial_opcional(12345)
        self.assertIn("texto", str(ctx.exception).lower())

    def test_cred_none_ok(self):
        validar_credencial_opcional(None)

    def test_cred_valida(self):
        validar_credencial_opcional("my-api-key-12345")


class ValidarConfiguracionCredExtendedTest(TestCase):
    """Lines 704, 715."""

    def test_config_none(self):
        """Line 704: None raises."""
        with self.assertRaises(ValidationError):
            validar_configuracion_cred(None)

    def test_config_valida(self):
        validar_configuracion_cred({"endpoint": "https://api.example.com"})


class ValidarFechaExpiracionCredExtendedTest(TestCase):
    """Line 726: non-datetime raises."""

    def test_fecha_no_datetime(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_expiracion_cred("2025-01-01")
        self.assertIn("datetime", str(ctx.exception).lower())

    def test_fecha_none_ok(self):
        validar_fecha_expiracion_cred(None)

    def test_fecha_futura_ok(self):
        validar_fecha_expiracion_cred(_future_dt())


class ValidarUpdatedAtCredExtendedTest(TestCase):
    """Lines 741, 744: None and non-datetime."""

    def test_updated_at_none(self):
        """Line 741: None raises."""
        with self.assertRaises(ValidationError):
            validar_updated_at_cred(None)

    def test_updated_at_no_datetime(self):
        """Line 744: string raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_updated_at_cred("2024-01-01")
        self.assertIn("datetime", str(ctx.exception).lower())

    def test_updated_at_valido(self):
        validar_updated_at_cred(_past_dt())


# ==============================================================================
# Webhook validators
# ==============================================================================


class ValidarPayloadWebhookExtendedTest(TestCase):
    """Line 786."""

    def test_payload_vacio(self):
        """Line 786: empty string raises."""
        with self.assertRaises(ValidationError):
            validar_payload_webhook("")

    def test_payload_none(self):
        """Line 786: None raises."""
        with self.assertRaises(ValidationError):
            validar_payload_webhook(None)

    def test_payload_valido(self):
        validar_payload_webhook('{"event": "payment.created"}')


class ValidarEventoTipoExtendedTest(TestCase):
    """Lines 798, 804."""

    def test_evento_none(self):
        """Line 798: None raises."""
        with self.assertRaises(ValidationError):
            validar_evento_tipo(None)

    def test_evento_muy_largo(self):
        """Line 804: > 100 chars raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_evento_tipo("payment." + "x" * 100)
        self.assertIn("100", str(ctx.exception))

    def test_evento_valido(self):
        validar_evento_tipo("payment.created")


class ValidarVerificacionOkExtendedTest(TestCase):
    """Lines 819, 823-824."""

    def test_verificacion_none(self):
        """Line 819: None raises."""
        with self.assertRaises(ValidationError):
            validar_verificacion_ok(None)

    def test_verificacion_no_entero(self):
        """Lines 823-824: string raises."""
        with self.assertRaises(ValidationError):
            validar_verificacion_ok("yes")

    def test_verificacion_valido(self):
        validar_verificacion_ok(1)
        validar_verificacion_ok(0)


class ValidarProcesadoOkExtendedTest(TestCase):
    """Lines 835, 839-840."""

    def test_procesado_none(self):
        """Line 835: None raises."""
        with self.assertRaises(ValidationError):
            validar_procesado_ok(None)

    def test_procesado_no_entero(self):
        """Lines 839-840: string raises."""
        with self.assertRaises(ValidationError):
            validar_procesado_ok("yes")

    def test_procesado_valido(self):
        validar_procesado_ok(0)


class ValidarTiempoProcMsExtendedTest(TestCase):
    """Lines 855-856, 859."""

    def test_tiempo_no_entero(self):
        """Lines 855-856: string raises."""
        with self.assertRaises(ValidationError):
            validar_tiempo_proc_ms_webhook("abc")

    def test_tiempo_negativo(self):
        """Line 859: negative raises."""
        with self.assertRaises(ValidationError):
            validar_tiempo_proc_ms_webhook(-1)

    def test_tiempo_none_ok(self):
        """None returns without error (optional)."""
        validar_tiempo_proc_ms_webhook(None)

    def test_tiempo_valido(self):
        validar_tiempo_proc_ms_webhook(500)


class ValidarUserAgentExtendedTest(TestCase):
    """Line 882."""

    def test_user_agent_no_string(self):
        """Line 882: list raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_user_agent(["Mozilla", "Chrome"])
        self.assertIn("texto", str(ctx.exception).lower())

    def test_user_agent_none_ok(self):
        validar_user_agent(None)

    def test_user_agent_valido(self):
        validar_user_agent("Mozilla/5.0 (Windows NT 10.0)")


class ValidarRequiereVerificacionExtendedTest(TestCase):
    """Lines 913, 917-918."""

    def test_requiere_verificacion_none(self):
        """Line 913: None raises."""
        with self.assertRaises(ValidationError):
            validar_requiere_verificacion(None)

    def test_requiere_verificacion_no_entero(self):
        """Lines 917-918: string raises."""
        with self.assertRaises(ValidationError):
            validar_requiere_verificacion("si")

    def test_requiere_verificacion_valido(self):
        validar_requiere_verificacion(1)
        validar_requiere_verificacion(0)


class ValidarSecretKeyExtendedTest(TestCase):
    """Line 929: None/empty raises."""

    def test_secret_none(self):
        with self.assertRaises(ValidationError):
            validar_secret_key_webhook(None)

    def test_secret_vacio(self):
        with self.assertRaises(ValidationError):
            validar_secret_key_webhook("")

    def test_secret_valido(self):
        validar_secret_key_webhook("a" * 32)


class ValidarHeaderVerificacionExtendedTest(TestCase):
    """Lines 945, 960."""

    def test_header_none(self):
        """Line 945: None raises."""
        with self.assertRaises(ValidationError):
            validar_header_verificacion(None)

    def test_header_muy_largo(self):
        """Line 960: > 100 chars raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_header_verificacion("X-" + "A" * 105)
        self.assertIn("100", str(ctx.exception))

    def test_header_valido(self):
        validar_header_verificacion("X-Signature")


class ValidarEventosWebhookExtendedTest(TestCase):
    """Lines 968, 971, 986."""

    def test_eventos_none(self):
        """Line 968: None raises."""
        with self.assertRaises(ValidationError):
            validar_eventos_webhook(None)

    def test_eventos_no_lista(self):
        """Line 971: non-list raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_eventos_webhook("payment.created")
        self.assertIn("list", str(ctx.exception).lower())

    def test_evento_formato_invalido(self):
        """Line 986: evento with spaces raises."""
        with self.assertRaises(ValidationError):
            validar_eventos_webhook(["payment created"])  # Space not allowed

    def test_eventos_validos(self):
        validar_eventos_webhook(["payment.created", "payment.updated"])


class ValidarHandlerFuncExtendedTest(TestCase):
    """Line 1001: None/empty raises."""

    def test_handler_none(self):
        with self.assertRaises(ValidationError):
            validar_handler_func(None)

    def test_handler_vacio(self):
        with self.assertRaises(ValidationError):
            validar_handler_func("")

    def test_handler_valido(self):
        validar_handler_func("apps.api_integrations.handlers.handle_payment")
