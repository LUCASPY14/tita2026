"""
Tests para WAHAEstadoView (GET estado sesión WAHA, POST mensaje de prueba).
Cubre las líneas 148-213 de notificaciones/views.py.

Estrategia de mock:
  - GET: se mockea requests.get (llamada a /api/sessions de WAHA)
  - POST: se mockea apps.notificaciones.services.enviar_whatsapp
"""
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient


URL = "/api/v1/notificaciones/whatsapp-estado/"


@pytest.fixture
def api_admin(usuario_admin):
    client = APIClient()
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def api_cajero(usuario_cajero):
    client = APIClient()
    client.force_authenticate(user=usuario_cajero)
    return client


# ── GET ───────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWAHAEstadoViewGet:

    def test_sin_url_configurada_retorna_no_configurado(self, api_admin):
        """Si EVOLUTION_API_URL no está definida, retorna configurado=False sin llamar a WAHA."""
        with patch("apps.notificaciones.views.WAHAEstadoView._waha_headers", return_value={}):
            with patch("django.conf.settings.EVOLUTION_API_URL", ""):
                resp = api_admin.get(URL)
        assert resp.status_code == 200
        assert resp.data["configurado"] is False
        assert resp.data["conectado"] is False
        assert "mensaje" in resp.data

    def test_sesion_working_retorna_conectado(self, api_admin):
        """Cuando WAHA responde con la sesión en estado WORKING → conectado=True."""
        sesion = "default"
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": sesion, "status": "WORKING"}]
        mock_resp.raise_for_status.return_value = None

        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", sesion):
                with patch("requests.get", return_value=mock_resp):
                    resp = api_admin.get(URL)

        assert resp.status_code == 200
        assert resp.data["configurado"] is True
        assert resp.data["conectado"] is True
        assert resp.data["estado"] == "WORKING"
        assert resp.data["session"] == sesion

    def test_sesion_not_found_retorna_desconectado(self, api_admin):
        """Cuando la sesión no existe en la lista de WAHA → conectado=False, estado=NOT_FOUND."""
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                mock_resp = MagicMock()
                mock_resp.json.return_value = []  # lista vacía — sesión no encontrada
                mock_resp.raise_for_status.return_value = None
                with patch("requests.get", return_value=mock_resp):
                    resp = api_admin.get(URL)

        assert resp.status_code == 200
        assert resp.data["configurado"] is True
        assert resp.data["conectado"] is False
        assert resp.data["estado"] == "NOT_FOUND"

    def test_sesion_stopped_retorna_desconectado(self, api_admin):
        """Estado distinto de WORKING → conectado=False."""
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                mock_resp = MagicMock()
                mock_resp.json.return_value = [{"name": "default", "status": "STOPPED"}]
                mock_resp.raise_for_status.return_value = None
                with patch("requests.get", return_value=mock_resp):
                    resp = api_admin.get(URL)

        assert resp.status_code == 200
        assert resp.data["conectado"] is False
        assert resp.data["estado"] == "STOPPED"

    def test_waha_timeout_retorna_503(self, api_admin):
        """Si WAHA no responde (timeout u otro RequestException) → 503 con campo 'error'."""
        import requests
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.get", side_effect=requests.exceptions.Timeout("timeout")):
                    resp = api_admin.get(URL)

        assert resp.status_code == 503
        assert resp.data["configurado"] is True
        assert resp.data["conectado"] is False
        assert "error" in resp.data

    def test_waha_connection_error_retorna_503(self, api_admin):
        """ConnectionError también devuelve 503."""
        import requests
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.get", side_effect=requests.exceptions.ConnectionError("refused")):
                    resp = api_admin.get(URL)

        assert resp.status_code == 503

    def test_solo_admin_puede_acceder(self, api_cajero):
        """Un cajero (no ADMIN) recibe 403."""
        resp = api_cajero.get(URL)
        assert resp.status_code == 403

    def test_anonimo_recibe_401(self):
        """Sin autenticación → 401."""
        resp = APIClient().get(URL)
        assert resp.status_code == 401


# ── POST ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWAHAEstadoViewPost:

    def test_sin_telefono_retorna_400(self, api_admin):
        """POST sin campo 'telefono' → 400."""
        resp = api_admin.post(URL, {"mensaje": "Hola"}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_telefono_vacio_retorna_400(self, api_admin):
        """POST con telefono='' → 400."""
        resp = api_admin.post(URL, {"telefono": "  ", "mensaje": "Hola"}, format="json")
        assert resp.status_code == 400

    def test_envio_exitoso_retorna_200(self, api_admin):
        """POST con teléfono válido y servicio disponible → 200 con ok=True."""
        waha_mock_response = {"id": "msg-123", "status": "sent"}
        with patch("apps.notificaciones.services.enviar_whatsapp", return_value=waha_mock_response):
            resp = api_admin.post(URL, {"telefono": "595981234567", "mensaje": "Prueba"}, format="json")

        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert resp.data["waha_response"] == waha_mock_response

    def test_usa_mensaje_por_defecto_si_no_se_envia(self, api_admin):
        """Si no se pasa 'mensaje', usa el texto de prueba por defecto."""
        with patch("apps.notificaciones.services.enviar_whatsapp", return_value={}) as mock_send:
            api_admin.post(URL, {"telefono": "595981234567"}, format="json")
        _, kwargs_or_args = mock_send.call_args[0], mock_send.call_args
        # verificar que se llamó — el mensaje por defecto no es vacío
        assert mock_send.called
        args = mock_send.call_args[0]
        assert args[0] == "595981234567"
        assert len(args[1]) > 0

    def test_runtime_error_retorna_503(self, api_admin):
        """Si enviar_whatsapp lanza RuntimeError (WAHA no configurado) → 503."""
        with patch("apps.notificaciones.services.enviar_whatsapp", side_effect=RuntimeError("WAHA no disponible")):
            resp = api_admin.post(URL, {"telefono": "595981234567", "mensaje": "Test"}, format="json")

        assert resp.status_code == 503
        assert resp.data["ok"] is False
        assert "error" in resp.data

    def test_exception_generica_retorna_502(self, api_admin):
        """Si enviar_whatsapp lanza Exception genérica → 502."""
        with patch("apps.notificaciones.services.enviar_whatsapp", side_effect=Exception("unexpected")):
            resp = api_admin.post(URL, {"telefono": "595981234567", "mensaje": "Test"}, format="json")

        assert resp.status_code == 502
        assert resp.data["ok"] is False

    def test_solo_admin_puede_enviar(self, api_cajero):
        """Un cajero recibe 403 al intentar enviar mensajes de prueba."""
        resp = api_cajero.post(URL, {"telefono": "595981234567", "mensaje": "x"}, format="json")
        assert resp.status_code == 403

    def test_anonimo_recibe_401_en_post(self):
        """Sin autenticación → 401."""
        resp = APIClient().post(URL, {"telefono": "595981234567"}, format="json")
        assert resp.status_code == 401


# ── WAHASesionView (iniciar/cerrar sesión) ─────────────────────────────────────

URL_SESION = "/api/v1/notificaciones/whatsapp-sesion/"


@pytest.mark.django_db
class TestWAHASesionViewPost:

    def test_sin_url_configurada_retorna_503(self, api_admin):
        with patch("django.conf.settings.EVOLUTION_API_URL", ""):
            resp = api_admin.post(URL_SESION)
        assert resp.status_code == 503

    def test_crea_sesion_nueva(self, api_admin):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"name": "default", "status": "STARTING"}
        mock_resp.raise_for_status.return_value = None
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    resp = api_admin.post(URL_SESION)
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        mock_post.assert_called_once()

    def test_sesion_existente_reintenta_con_start(self, api_admin):
        """Si /api/sessions responde 422 (ya existe), reintenta con /start."""
        mock_422 = MagicMock()
        mock_422.status_code = 422
        mock_started = MagicMock()
        mock_started.status_code = 200
        mock_started.json.return_value = {"name": "default", "status": "STARTING"}
        mock_started.raise_for_status.return_value = None
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.post", side_effect=[mock_422, mock_started]) as mock_post:
                    resp = api_admin.post(URL_SESION)
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert mock_post.call_count == 2

    def test_waha_error_retorna_502(self, api_admin):
        import requests
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.post", side_effect=requests.exceptions.ConnectionError("refused")):
                    resp = api_admin.post(URL_SESION)
        assert resp.status_code == 502
        assert resp.data["ok"] is False

    def test_solo_admin_puede_iniciar(self, api_cajero):
        resp = api_cajero.post(URL_SESION)
        assert resp.status_code == 403

    def test_anonimo_recibe_401(self):
        resp = APIClient().post(URL_SESION)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestWAHASesionViewDelete:

    def test_sin_url_configurada_retorna_503(self, api_admin):
        with patch("django.conf.settings.EVOLUTION_API_URL", ""):
            resp = api_admin.delete(URL_SESION)
        assert resp.status_code == 503

    def test_cierra_sesion(self, api_admin):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    resp = api_admin.delete(URL_SESION)
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        mock_post.assert_called_once()
        assert "/logout" in mock_post.call_args[0][0]

    def test_waha_error_retorna_502(self, api_admin):
        import requests
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.post", side_effect=requests.exceptions.Timeout("timeout")):
                    resp = api_admin.delete(URL_SESION)
        assert resp.status_code == 502

    def test_solo_admin_puede_cerrar(self, api_cajero):
        resp = api_cajero.delete(URL_SESION)
        assert resp.status_code == 403

    def test_anonimo_recibe_401(self):
        resp = APIClient().delete(URL_SESION)
        assert resp.status_code == 401


# ── WAHAQRView (imagen del código QR) ──────────────────────────────────────────

URL_QR = "/api/v1/notificaciones/whatsapp-qr/"


@pytest.mark.django_db
class TestWAHAQRView:

    def test_sin_url_configurada_retorna_503(self, api_admin):
        with patch("django.conf.settings.EVOLUTION_API_URL", ""):
            resp = api_admin.get(URL_QR)
        assert resp.status_code == 503

    def test_devuelve_imagen_png(self, api_admin):
        mock_resp = MagicMock()
        mock_resp.content = b"\x89PNG\r\n\x1a\n"
        mock_resp.headers = {"content-type": "image/png"}
        mock_resp.raise_for_status.return_value = None
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.get", return_value=mock_resp):
                    resp = api_admin.get(URL_QR)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"
        assert resp.content == b"\x89PNG\r\n\x1a\n"

    def test_waha_error_retorna_502(self, api_admin):
        import requests
        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3001"):
            with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                with patch("requests.get", side_effect=requests.exceptions.Timeout("timeout")):
                    resp = api_admin.get(URL_QR)
        assert resp.status_code == 502

    def test_solo_admin_puede_ver_qr(self, api_cajero):
        resp = api_cajero.get(URL_QR)
        assert resp.status_code == 403

    def test_anonimo_recibe_401(self):
        resp = APIClient().get(URL_QR)
        assert resp.status_code == 401
