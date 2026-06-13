"""Tests para apps.usuarios.middleware — AuditContextMiddleware."""
from unittest.mock import MagicMock


def _mw():
    from apps.usuarios.middleware import AuditContextMiddleware
    return AuditContextMiddleware(get_response=lambda r: None)


def _req(*, auth=True, fwd=None, addr="192.168.1.100"):
    user = MagicMock()
    user.is_authenticated = auth
    request = MagicMock()
    request.user = user
    request.META = {"REMOTE_ADDR": addr}
    if fwd:
        request.META["HTTP_X_FORWARDED_FOR"] = fwd
    return request


class TestGetHelpers:
    def test_get_current_usuario_none_sin_request(self):
        from apps.usuarios.middleware import get_current_usuario
        _mw().process_response(_req(), MagicMock())
        assert get_current_usuario() is None

    def test_get_current_ip_default_sin_atributo(self):
        from apps.usuarios.middleware import get_current_ip, _local
        if hasattr(_local, "ip"):
            del _local.ip
        assert get_current_ip() == "127.0.0.1"


class TestProcessRequest:
    def test_usuario_autenticado_setea_local_usuario(self):
        from apps.usuarios.middleware import get_current_usuario
        req = _req(auth=True, addr="10.0.0.5")
        _mw().process_request(req)
        assert get_current_usuario() == req.user

    def test_usuario_anonimo_local_usuario_es_none(self):
        from apps.usuarios.middleware import get_current_usuario
        _mw().process_request(_req(auth=False))
        assert get_current_usuario() is None

    def test_ip_desde_remote_addr(self):
        from apps.usuarios.middleware import get_current_ip
        _mw().process_request(_req(auth=False, addr="172.16.0.1"))
        assert get_current_ip() == "172.16.0.1"

    def test_ip_desde_x_forwarded_for_primer_valor(self):
        from apps.usuarios.middleware import get_current_ip
        _mw().process_request(_req(fwd="203.0.113.1, 10.0.0.1", addr="127.0.0.1"))
        assert get_current_ip() == "203.0.113.1"


class TestProcessResponse:
    def test_limpia_usuario_y_ip(self):
        from apps.usuarios.middleware import get_current_usuario
        mw = _mw()
        mw.process_request(_req(auth=True))
        assert get_current_usuario() is not None
        mw.process_response(_req(), MagicMock())
        assert get_current_usuario() is None

    def test_retorna_response_original(self):
        response = MagicMock()
        assert _mw().process_response(_req(), response) is response
