"""Tests para apps.notificaciones.consumers — NotificacionConsumer."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_consumer(query: str = ""):
    from apps.notificaciones.consumers import NotificacionConsumer
    consumer = NotificacionConsumer()
    consumer.scope = {"query_string": query.encode()}
    consumer.channel_name = "test_channel"
    consumer.close = AsyncMock()
    consumer.accept = AsyncMock()
    consumer.send = AsyncMock()
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    return consumer


# ── _parse_token ───────────────────────────────────────────────────────────────

class TestParseToken:
    def test_extrae_token_simple(self):
        from apps.notificaciones.consumers import NotificacionConsumer
        assert NotificacionConsumer._parse_token("token=abc123") == "abc123"

    def test_token_entre_otros_params(self):
        from apps.notificaciones.consumers import NotificacionConsumer
        assert NotificacionConsumer._parse_token("user=x&token=xyz&foo=bar") == "xyz"

    def test_sin_token_retorna_vacio(self):
        from apps.notificaciones.consumers import NotificacionConsumer
        assert NotificacionConsumer._parse_token("other=value") == ""

    def test_querystring_vacia(self):
        from apps.notificaciones.consumers import NotificacionConsumer
        assert NotificacionConsumer._parse_token("") == ""


# ── _authenticate ──────────────────────────────────────────────────────────────

class TestAuthenticate:
    def test_token_invalido_retorna_none(self):
        consumer = _make_consumer()
        result = asyncio.run(consumer._authenticate("not_a_token"))
        assert result is None

    @pytest.mark.django_db
    def test_token_valido_user_inexistente_retorna_none(self):
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken()
        token["user_id"] = 9_999_999
        consumer = _make_consumer()
        result = asyncio.run(consumer._authenticate(str(token)))
        assert result is None

    @pytest.mark.django_db(transaction=True)
    def test_token_valido_user_existente_retorna_usuario(self):
        from apps.usuarios.models import Usuario
        from rest_framework_simplejwt.tokens import AccessToken
        usuario = Usuario.objects.create_user(
            email="ws_auth@test.com", password="test1234",
            nombre="WS", apellido="Test", rol=Usuario.Rol.CAJERO,
        )
        token = AccessToken.for_user(usuario)
        consumer = _make_consumer()
        result = asyncio.run(consumer._authenticate(str(token)))
        assert result is not None
        assert result.pk == usuario.pk


# ── connect ────────────────────────────────────────────────────────────────────

class TestConnect:
    def test_token_invalido_cierra_con_4001(self):
        consumer = _make_consumer(query="token=bad_token")
        asyncio.run(consumer.connect())
        consumer.close.assert_called_once_with(code=4001)
        consumer.accept.assert_not_called()

    def test_token_valido_acepta_y_une_al_grupo(self):
        consumer = _make_consumer(query="token=good")
        mock_user = MagicMock()
        mock_user.pk = 42
        with patch.object(consumer, "_authenticate", new=AsyncMock(return_value=mock_user)):
            asyncio.run(consumer.connect())
        consumer.accept.assert_called_once()
        consumer.channel_layer.group_add.assert_called_once_with("notificaciones_42", "test_channel")
        assert consumer.group_name == "notificaciones_42"


# ── disconnect ─────────────────────────────────────────────────────────────────

class TestDisconnect:
    def test_sin_group_name_no_falla(self):
        consumer = _make_consumer()
        asyncio.run(consumer.disconnect(1000))
        consumer.channel_layer.group_discard.assert_not_called()

    def test_con_group_name_llama_group_discard(self):
        consumer = _make_consumer()
        consumer.group_name = "notificaciones_7"
        asyncio.run(consumer.disconnect(1000))
        consumer.channel_layer.group_discard.assert_called_once_with("notificaciones_7", "test_channel")


# ── receive & notificacion_nueva ───────────────────────────────────────────────

class TestReceive:
    def test_receive_no_hace_nada(self):
        consumer = _make_consumer()
        asyncio.run(consumer.receive(text_data="{}"))
        consumer.send.assert_not_called()


class TestNotificacionNueva:
    def test_envia_datos_como_json(self):
        import json
        consumer = _make_consumer()
        event = {"data": {"tipo": "SALDO_BAJO", "mensaje": "test"}}
        asyncio.run(consumer.notificacion_nueva(event))
        consumer.send.assert_called_once_with(text_data=json.dumps(event["data"]))
