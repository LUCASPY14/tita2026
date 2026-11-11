"""
Tests para apps.notificaciones.tasks.verificar_sesion_waha.

Usa LocMemCache (no DummyCache, que es lo que usan los settings de test por
defecto) porque la tarea depende de que el cache realmente persista entre
llamadas para el debounce de 15 min / 4 horas.
"""
import pytest
from unittest.mock import patch, MagicMock
from freezegun import freeze_time


@pytest.fixture(autouse=True)
def _config_waha(settings):
    """Configura settings + un cache real (LocMemCache, no la DummyCache de
    test.py) porque la tarea depende de que el cache persista entre llamadas
    para el debounce de 15 min / 4 horas."""
    from django.core.cache import cache

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-waha-session",
        }
    }
    settings.EVOLUTION_API_URL = "http://waha-test:3000"
    settings.EVOLUTION_API_INSTANCE = "default"
    settings.EVOLUTION_API_KEY = ""
    cache.clear()
    yield
    cache.clear()


def _mock_response(json_data):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


@pytest.mark.django_db
class TestVerificarSesionWaha:

    def test_sin_url_configurada_no_hace_nada(self, settings):
        from apps.notificaciones.tasks import verificar_sesion_waha
        settings.EVOLUTION_API_URL = ""
        result = verificar_sesion_waha()
        assert result == {"estado": "sin_configurar"}

    @patch("requests.get")
    def test_working_no_avisa(self, mock_get):
        from apps.notificaciones.tasks import verificar_sesion_waha
        mock_get.return_value = _mock_response({"status": "WORKING"})
        result = verificar_sesion_waha()
        assert result == {"estado": "WORKING"}

    @patch("requests.get")
    def test_error_de_red_no_rompe(self, mock_get):
        from apps.notificaciones.tasks import verificar_sesion_waha
        mock_get.side_effect = Exception("timeout")
        result = verificar_sesion_waha()
        assert result == {"estado": "error_consulta"}

    @patch("requests.get")
    def test_primera_vez_caida_no_avisa_todavia(self, mock_get, usuario_admin):
        from apps.notificaciones.tasks import verificar_sesion_waha
        from apps.notificaciones.models import Notificacion

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 10:00:00"):
            result = verificar_sesion_waha()

        assert result["estado"] == "FAILED"
        assert result.get("recien_detectado") is True
        assert Notificacion.objects.count() == 0

    @patch("requests.get")
    def test_caida_menos_de_15_min_no_avisa(self, mock_get, usuario_admin):
        from apps.notificaciones.tasks import verificar_sesion_waha
        from apps.notificaciones.models import Notificacion

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 10:00:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 10:10:00"):
            result = verificar_sesion_waha()

        assert "admins_avisados" not in result
        assert Notificacion.objects.count() == 0

    @patch("apps.notificaciones.services.EmailService.enviar_simple")
    @patch("requests.get")
    def test_caida_mas_de_15_min_avisa_admins(self, mock_get, mock_email, usuario_admin):
        from apps.notificaciones.tasks import verificar_sesion_waha
        from apps.notificaciones.models import Notificacion

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 10:00:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 10:16:00"):
            result = verificar_sesion_waha()

        assert result["admins_avisados"] == 1
        assert Notificacion.objects.filter(usuario=usuario_admin, tipo="SISTEMA").count() == 1
        mock_email.assert_called_once()

    @patch("apps.notificaciones.services.EmailService.enviar_simple")
    @patch("requests.get")
    def test_no_reavisa_antes_del_cooldown(self, mock_get, mock_email, usuario_admin):
        from apps.notificaciones.tasks import verificar_sesion_waha
        from apps.notificaciones.models import Notificacion

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 10:00:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 10:16:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 10:30:00"):
            result = verificar_sesion_waha()

        assert result.get("ya_avisado") is True
        assert Notificacion.objects.count() == 1  # no un segundo aviso
        mock_email.assert_called_once()

    @patch("apps.notificaciones.services.EmailService.enviar_simple")
    @patch("requests.get")
    def test_se_recupera_y_vuelve_a_avisar_si_cae_de_nuevo(self, mock_get, mock_email, usuario_admin):
        from apps.notificaciones.tasks import verificar_sesion_waha
        from apps.notificaciones.models import Notificacion

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 10:00:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 10:16:00"):
            verificar_sesion_waha()
        assert Notificacion.objects.count() == 1

        mock_get.return_value = _mock_response({"status": "WORKING"})
        with freeze_time("2026-11-11 10:20:00"):
            result = verificar_sesion_waha()
        assert result == {"estado": "WORKING"}

        mock_get.return_value = _mock_response({"status": "FAILED"})
        with freeze_time("2026-11-11 11:00:00"):
            verificar_sesion_waha()
        with freeze_time("2026-11-11 11:16:00"):
            result = verificar_sesion_waha()

        assert result["admins_avisados"] == 1
        assert Notificacion.objects.count() == 2
        assert mock_email.call_count == 2
