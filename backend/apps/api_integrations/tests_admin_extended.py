"""
Tests for apps/api_integrations/admin.py
Covers all custom display methods across 6 admin classes.
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from apps.api_integrations.admin import (
    ProveedoresApiAdmin,
    EndpointsApiAdmin,
    LogsLlamadasApiAdmin,
    CredencialesApiAdmin,
    LogsWebhooksAdmin,
    WebhookEndpointsAdmin,
)
from apps.api_integrations.models import (
    ProveedoresApi,
    EndpointsApi,
    LogsLlamadasApi,
    CredencialesApi,
    LogsWebhooks,
    WebhookEndpoints,
)

_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# ProveedoresApiAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class ProveedoresApiAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ProveedoresApiAdmin(ProveedoresApi, self.site)

    def test_tipo_servicio_badge_rest(self):
        obj = _mock_obj(tipo_servicio="REST")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("28a745", result)
        self.assertIn("REST", result)

    def test_tipo_servicio_badge_soap(self):
        obj = _mock_obj(tipo_servicio="SOAP")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("007bff", result)

    def test_tipo_servicio_badge_graphql(self):
        obj = _mock_obj(tipo_servicio="GraphQL")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("e83e8c", result)

    def test_tipo_servicio_badge_websocket(self):
        obj = _mock_obj(tipo_servicio="WebSocket")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("fd7e14", result)

    def test_tipo_servicio_badge_grpc(self):
        obj = _mock_obj(tipo_servicio="gRPC")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("6f42c1", result)

    def test_tipo_servicio_badge_xmlrpc(self):
        obj = _mock_obj(tipo_servicio="XML-RPC")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("20c997", result)

    def test_tipo_servicio_badge_odata(self):
        obj = _mock_obj(tipo_servicio="OData")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("6610f2", result)

    def test_tipo_servicio_badge_desconocido(self):
        obj = _mock_obj(tipo_servicio="Otro")
        result = str(self.admin.tipo_servicio_badge(obj))
        self.assertIn("6c757d", result)

    def test_tipo_auth_badge_api_key(self):
        obj = _mock_obj(tipo_auth="API_KEY")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("007bff", result)

    def test_tipo_auth_badge_oauth2(self):
        obj = _mock_obj(tipo_auth="OAuth2")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("28a745", result)

    def test_tipo_auth_badge_bearer(self):
        obj = _mock_obj(tipo_auth="Bearer")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("17a2b8", result)

    def test_tipo_auth_badge_basic(self):
        obj = _mock_obj(tipo_auth="Basic")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("ffc107", result)

    def test_tipo_auth_badge_jwt(self):
        obj = _mock_obj(tipo_auth="JWT")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("e83e8c", result)

    def test_tipo_auth_badge_none(self):
        obj = _mock_obj(tipo_auth="None")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("6c757d", result)

    def test_tipo_auth_badge_hmac(self):
        obj = _mock_obj(tipo_auth="HMAC")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("6f42c1", result)

    def test_tipo_auth_badge_custom(self):
        obj = _mock_obj(tipo_auth="Custom")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("fd7e14", result)

    def test_tipo_auth_badge_desconocido(self):
        obj = _mock_obj(tipo_auth="Otro")
        result = str(self.admin.tipo_auth_badge(obj))
        self.assertIn("6c757d", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("estado", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# EndpointsApiAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class EndpointsApiAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EndpointsApiAdmin(EndpointsApi, self.site)

    def test_metodo_badge_get(self):
        obj = _mock_obj(metodo="GET")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("28a745", result)
        self.assertIn("GET", result)

    def test_metodo_badge_post(self):
        obj = _mock_obj(metodo="POST")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("007bff", result)

    def test_metodo_badge_put(self):
        obj = _mock_obj(metodo="PUT")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("ffc107", result)

    def test_metodo_badge_delete(self):
        obj = _mock_obj(metodo="DELETE")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("dc3545", result)

    def test_metodo_badge_patch(self):
        obj = _mock_obj(metodo="PATCH")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("17a2b8", result)

    def test_metodo_badge_head(self):
        obj = _mock_obj(metodo="HEAD")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("6c757d", result)

    def test_metodo_badge_options(self):
        obj = _mock_obj(metodo="OPTIONS")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("6f42c1", result)

    def test_metodo_badge_desconocido(self):
        obj = _mock_obj(metodo="TRACE")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("6c757d", result)

    def test_requiere_auth_badge_si(self):
        obj = _mock_obj(requiere_auth=True)
        result = str(self.admin.requiere_auth_badge(obj))
        self.assertIn("dc3545", result)
        self.assertIn("Requiere Auth", result)

    def test_requiere_auth_badge_no(self):
        obj = _mock_obj(requiere_auth=False)
        result = str(self.admin.requiere_auth_badge(obj))
        self.assertIn("Público", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)

    def test_proveedor_nombre_con_proveedor(self):
        proveedor = _mock_obj(nombre="Proveedor X")
        obj = _mock_obj(id_proveedor=proveedor)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "Proveedor X")

    def test_proveedor_nombre_sin_proveedor(self):
        obj = _mock_obj(id_proveedor=None)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "-")


# =============================================================================
# LogsLlamadasApiAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class LogsLlamadasApiAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = LogsLlamadasApiAdmin(LogsLlamadasApi, self.site)

    def test_metodo_badge_get(self):
        obj = _mock_obj(metodo="GET")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("28a745", result)

    def test_metodo_badge_post(self):
        obj = _mock_obj(metodo="POST")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("007bff", result)

    def test_metodo_badge_delete(self):
        obj = _mock_obj(metodo="DELETE")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("dc3545", result)

    def test_metodo_badge_patch(self):
        obj = _mock_obj(metodo="PATCH")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("17a2b8", result)

    def test_metodo_badge_desconocido(self):
        obj = _mock_obj(metodo="OTHER")
        result = str(self.admin.metodo_badge(obj))
        self.assertIn("6c757d", result)

    def test_url_corta_corta(self):
        obj = _mock_obj(url="https://api.example.com/v1/users")
        result = self.admin.url_corta(obj)
        self.assertEqual(result, "https://api.example.com/v1/users")

    def test_url_corta_larga(self):
        obj = _mock_obj(url="https://api.example.com/v1/" + "x" * 60)
        result = self.admin.url_corta(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 50)

    def test_url_corta_exactamente_50(self):
        obj = _mock_obj(url="A" * 50)
        result = self.admin.url_corta(obj)
        self.assertEqual(result, "A" * 50)

    def test_status_badge_2xx(self):
        obj = _mock_obj(status_code=200)
        result = str(self.admin.status_badge(obj))
        self.assertIn("28a745", result)

    def test_status_badge_3xx(self):
        obj = _mock_obj(status_code=301)
        result = str(self.admin.status_badge(obj))
        self.assertIn("17a2b8", result)

    def test_status_badge_4xx(self):
        obj = _mock_obj(status_code=404)
        result = str(self.admin.status_badge(obj))
        self.assertIn("ffc107", result)

    def test_status_badge_5xx(self):
        obj = _mock_obj(status_code=500)
        result = str(self.admin.status_badge(obj))
        self.assertIn("dc3545", result)

    def test_exitoso_badge_ok(self):
        obj = _mock_obj(exitoso=True)
        result = str(self.admin.exitoso_badge(obj))
        self.assertIn("green", result)
        self.assertIn("OK", result)

    def test_exitoso_badge_error(self):
        obj = _mock_obj(exitoso=False)
        result = str(self.admin.exitoso_badge(obj))
        self.assertIn("red", result)
        self.assertIn("Error", result)

    def test_has_add_permission_false(self):
        request = MagicMock()
        result = self.admin.has_add_permission(request)
        self.assertFalse(result)

    def test_has_change_permission_false(self):
        request = MagicMock()
        result = self.admin.has_change_permission(request)
        self.assertFalse(result)

    def test_has_change_permission_with_obj_false(self):
        request = MagicMock()
        obj = MagicMock()
        result = self.admin.has_change_permission(request, obj)
        self.assertFalse(result)


# =============================================================================
# CredencialesApiAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class CredencialesApiAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CredencialesApiAdmin(CredencialesApi, self.site)

    def test_ambiente_badge_development(self):
        obj = _mock_obj(ambiente="development")
        result = str(self.admin.ambiente_badge(obj))
        self.assertIn("6c757d", result)
        self.assertIn("DEVELOPMENT", result)

    def test_ambiente_badge_staging(self):
        obj = _mock_obj(ambiente="staging")
        result = str(self.admin.ambiente_badge(obj))
        self.assertIn("ffc107", result)
        self.assertIn("STAGING", result)

    def test_ambiente_badge_production(self):
        obj = _mock_obj(ambiente="production")
        result = str(self.admin.ambiente_badge(obj))
        self.assertIn("dc3545", result)
        self.assertIn("PRODUCTION", result)

    def test_ambiente_badge_testing(self):
        obj = _mock_obj(ambiente="testing")
        result = str(self.admin.ambiente_badge(obj))
        self.assertIn("17a2b8", result)
        self.assertIn("TESTING", result)

    def test_ambiente_badge_desconocido(self):
        obj = _mock_obj(ambiente="otro")
        result = str(self.admin.ambiente_badge(obj))
        self.assertIn("6c757d", result)

    def test_tiene_api_key_si(self):
        obj = _mock_obj(api_key="mykey123")
        result = str(self.admin.tiene_api_key(obj))
        self.assertIn("green", result)

    def test_tiene_api_key_no(self):
        obj = _mock_obj(api_key=None)
        result = str(self.admin.tiene_api_key(obj))
        self.assertIn("ccc", result)

    def test_tiene_secret_si(self):
        obj = _mock_obj(secret="mysecret")
        result = str(self.admin.tiene_secret(obj))
        self.assertIn("green", result)

    def test_tiene_secret_no(self):
        obj = _mock_obj(secret="")
        result = str(self.admin.tiene_secret(obj))
        self.assertIn("ccc", result)

    def test_tiene_token_si(self):
        obj = _mock_obj(token="mytoken")
        result = str(self.admin.tiene_token(obj))
        self.assertIn("green", result)

    def test_tiene_token_no(self):
        obj = _mock_obj(token=None)
        result = str(self.admin.tiene_token(obj))
        self.assertIn("ccc", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)

    def test_proveedor_nombre_con_proveedor(self):
        proveedor = _mock_obj(nombre="Proveedor Y")
        obj = _mock_obj(id_proveedor=proveedor)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "Proveedor Y")

    def test_proveedor_nombre_sin_proveedor(self):
        obj = _mock_obj(id_proveedor=None)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "-")


# =============================================================================
# LogsWebhooksAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class LogsWebhooksAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = LogsWebhooksAdmin(LogsWebhooks, self.site)

    def test_verificacion_badge_verificado(self):
        obj = _mock_obj(verificacion_ok=True)
        result = str(self.admin.verificacion_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Verificado", result)

    def test_verificacion_badge_no_verificado(self):
        obj = _mock_obj(verificacion_ok=False)
        result = str(self.admin.verificacion_badge(obj))
        self.assertIn("red", result)
        self.assertIn("No Verificado", result)

    def test_procesado_badge_ok(self):
        obj = _mock_obj(procesado_ok=True)
        result = str(self.admin.procesado_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Procesado", result)

    def test_procesado_badge_error(self):
        obj = _mock_obj(procesado_ok=False)
        result = str(self.admin.procesado_badge(obj))
        self.assertIn("red", result)
        self.assertIn("Error", result)

    def test_has_add_permission_false(self):
        request = MagicMock()
        result = self.admin.has_add_permission(request)
        self.assertFalse(result)

    def test_has_change_permission_false(self):
        request = MagicMock()
        result = self.admin.has_change_permission(request)
        self.assertFalse(result)

    def test_has_change_permission_with_obj_false(self):
        request = MagicMock()
        obj = MagicMock()
        result = self.admin.has_change_permission(request, obj)
        self.assertFalse(result)


# =============================================================================
# WebhookEndpointsAdmin
# =============================================================================


@patch("apps.api_integrations.admin.format_html", _plain_format_html)
class WebhookEndpointsAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = WebhookEndpointsAdmin(WebhookEndpoints, self.site)

    def test_requiere_verificacion_badge_si(self):
        obj = _mock_obj(requiere_verificacion=True)
        result = str(self.admin.requiere_verificacion_badge(obj))
        self.assertIn("dc3545", result)
        self.assertIn("Verificación", result)

    def test_requiere_verificacion_badge_no(self):
        obj = _mock_obj(requiere_verificacion=False)
        result = str(self.admin.requiere_verificacion_badge(obj))
        self.assertIn("6c757d", result)
        self.assertIn("Sin Verificación", result)

    def test_eventos_count_con_lista(self):
        obj = _mock_obj(eventos=["evento1", "evento2", "evento3"])
        result = str(self.admin.eventos_count(obj))
        self.assertIn("3", result)
        self.assertIn("eventos", result)

    def test_eventos_count_lista_vacia(self):
        obj = _mock_obj(eventos=[])
        result = str(self.admin.eventos_count(obj))
        self.assertIn("0", result)

    def test_eventos_count_no_lista(self):
        obj = _mock_obj(eventos=None)
        result = self.admin.eventos_count(obj)
        self.assertEqual(result, "—")

    def test_eventos_count_dict(self):
        obj = _mock_obj(eventos={"key": "val"})
        result = self.admin.eventos_count(obj)
        self.assertEqual(result, "—")

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)

    def test_proveedor_nombre_con_proveedor(self):
        proveedor = _mock_obj(nombre="Proveedor Z")
        obj = _mock_obj(id_proveedor=proveedor)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "Proveedor Z")

    def test_proveedor_nombre_sin_proveedor(self):
        obj = _mock_obj(id_proveedor=None)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "-")
