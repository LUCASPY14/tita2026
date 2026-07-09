"""
Tests para ramas no cubiertas de send_push_to_user y enviar_whatsapp.
Cubre:
  - send_push_to_user: WebPushException 404/410 → borra suscripción,
    WebPushException otro status → no borra, Exception genérica → silenciosa
  - enviar_whatsapp: sin EVOLUTION_API_URL, con API key, sin API key,
    HTTP error, respuesta OK
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def push_sub(db, usuario_admin):
    from apps.notificaciones.models import PushSubscription
    return PushSubscription.objects.create(
        usuario=usuario_admin,
        endpoint="https://push.example.com/abc",
        p256dh="BKey123",
        auth="Auth456",
        activa=True,
    )


# ── send_push_to_user — ramas de excepción ────────────────────────────────────

@pytest.mark.django_db
class TestSendPushBranches:

    def _call(self, usuario_id, mock_webpush):
        from apps.notificaciones.services import send_push_to_user
        with patch("django.conf.settings.VAPID_PRIVATE_KEY", "fake_pk"):
            with patch("pywebpush.webpush", mock_webpush):
                send_push_to_user(usuario_id, "Título", "Cuerpo")

    def test_webpush_exception_410_borra_suscripcion(self, push_sub, usuario_admin):
        from apps.notificaciones.models import PushSubscription
        from pywebpush import WebPushException

        mock_resp = MagicMock()
        mock_resp.status_code = 410
        exc = WebPushException("Gone")
        exc.response = mock_resp

        self._call(usuario_admin.pk, MagicMock(side_effect=exc))

        assert not PushSubscription.objects.filter(pk=push_sub.pk).exists()

    def test_webpush_exception_404_borra_suscripcion(self, push_sub, usuario_admin):
        from apps.notificaciones.models import PushSubscription
        from pywebpush import WebPushException

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        exc = WebPushException("Not Found")
        exc.response = mock_resp

        self._call(usuario_admin.pk, MagicMock(side_effect=exc))

        assert not PushSubscription.objects.filter(pk=push_sub.pk).exists()

    def test_webpush_exception_otro_status_no_borra(self, push_sub, usuario_admin):
        from apps.notificaciones.models import PushSubscription
        from pywebpush import WebPushException

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        exc = WebPushException("Server Error")
        exc.response = mock_resp

        self._call(usuario_admin.pk, MagicMock(side_effect=exc))

        assert PushSubscription.objects.filter(pk=push_sub.pk).exists()

    def test_webpush_exception_sin_response_no_borra(self, push_sub, usuario_admin):
        from apps.notificaciones.models import PushSubscription
        from pywebpush import WebPushException

        exc = WebPushException("Unknown")
        exc.response = None

        self._call(usuario_admin.pk, MagicMock(side_effect=exc))

        assert PushSubscription.objects.filter(pk=push_sub.pk).exists()

    def test_exception_generica_ignorada(self, push_sub, usuario_admin):
        from apps.notificaciones.models import PushSubscription

        self._call(usuario_admin.pk, MagicMock(side_effect=RuntimeError("boom")))

        # No lanzó excepción y la suscripción sigue
        assert PushSubscription.objects.filter(pk=push_sub.pk).exists()


# ── enviar_whatsapp ───────────────────────────────────────────────────────────

class TestEnviarWhatsapp:

    def test_sin_evolution_url_lanza_runtime_error(self):
        from apps.notificaciones.services import enviar_whatsapp
        with patch("django.conf.settings.EVOLUTION_API_URL", ""):
            with pytest.raises(RuntimeError, match="EVOLUTION_API_URL"):
                enviar_whatsapp("595981234567", "hola")

    def test_envia_sin_api_key(self):
        from apps.notificaciones.services import enviar_whatsapp
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg1"}
        mock_resp.raise_for_status = MagicMock()

        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3000"):
            with patch("django.conf.settings.EVOLUTION_API_KEY", ""):
                with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                    with patch("requests.post", return_value=mock_resp) as mock_post:
                        result = enviar_whatsapp("595981234567", "test msg")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        headers = call_kwargs[1]["headers"] if call_kwargs[1] else call_kwargs.kwargs["headers"]
        assert "X-Api-Key" not in headers
        assert result == {"id": "msg1"}

    def test_envia_con_api_key_en_header(self):
        from apps.notificaciones.services import enviar_whatsapp
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg2"}
        mock_resp.raise_for_status = MagicMock()

        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3000"):
            with patch("django.conf.settings.EVOLUTION_API_KEY", "myapikey"):
                with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                    with patch("requests.post", return_value=mock_resp) as mock_post:
                        enviar_whatsapp("+595 98-123-4567", "msg con key")

        headers = mock_post.call_args[1]["headers"]
        assert headers["X-Api-Key"] == "myapikey"

    def test_normaliza_numero(self):
        from apps.notificaciones.services import enviar_whatsapp
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()

        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3000"):
            with patch("django.conf.settings.EVOLUTION_API_KEY", ""):
                with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                    with patch("requests.post", return_value=mock_resp) as mock_post:
                        enviar_whatsapp("+595 98-111-2222", "msg")

        payload = mock_post.call_args[1]["json"]
        assert payload["chatId"] == "595981112222@c.us"

    def test_http_error_se_propaga(self):
        from apps.notificaciones.services import enviar_whatsapp
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.HTTPError("401 Unauthorized")

        with patch("django.conf.settings.EVOLUTION_API_URL", "http://waha:3000"):
            with patch("django.conf.settings.EVOLUTION_API_KEY", ""):
                with patch("django.conf.settings.EVOLUTION_API_INSTANCE", "default"):
                    with patch("requests.post", return_value=mock_resp):
                        with pytest.raises(req_lib.HTTPError):
                            enviar_whatsapp("595981234567", "msg")
