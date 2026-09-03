"""
Tests para common.utils.request_ip.get_client_ip

Nginx es el único proxy delante de Daphne (ver frontend/nginx.conf), y
reenvía la IP real del cliente en X-Real-IP en cada request proxied.
REMOTE_ADDR en Daphne es la IP interna de Docker del contenedor de Nginx,
no la del usuario — por eso X-Real-IP debe tener prioridad.
"""
from django.test import RequestFactory

from common.utils.request_ip import get_client_ip


class TestGetClientIp:

    def test_usa_x_real_ip_si_esta_presente(self):
        request = RequestFactory().get(
            "/", HTTP_X_REAL_IP="192.168.100.50", REMOTE_ADDR="172.18.0.4",
        )
        assert get_client_ip(request) == "192.168.100.50"

    def test_fallback_a_remote_addr_sin_x_real_ip(self):
        request = RequestFactory().get("/", REMOTE_ADDR="127.0.0.1")
        assert get_client_ip(request) == "127.0.0.1"

    def test_sin_ningun_dato_devuelve_string_vacio(self):
        request = RequestFactory().get("/")
        request.META.pop("REMOTE_ADDR", None)
        assert get_client_ip(request) == ""
