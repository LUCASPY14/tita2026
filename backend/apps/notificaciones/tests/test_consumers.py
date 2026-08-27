"""Tests para apps.notificaciones.consumers — NotificacionConsumer."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from asgiref.sync import sync_to_async


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

    @pytest.mark.anyio
    @pytest.mark.django_db(transaction=True)
    async def test_token_valido_user_existente_retorna_usuario(self):
        from apps.usuarios.models import Usuario
        from rest_framework_simplejwt.tokens import AccessToken
        usuario = await sync_to_async(Usuario.objects.create_user)(
            email="ws_auth@test.com", password="test1234",
            nombre="WS", apellido="Test", rol=Usuario.Rol.CAJERO,
        )
        token = AccessToken.for_user(usuario)
        consumer = _make_consumer()
        result = await consumer._authenticate(str(token))
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


# ── DashboardConsumer ──────────────────────────────────────────────────────────

def _make_dashboard_consumer(query: str = ""):
    from apps.notificaciones.consumers import DashboardConsumer
    consumer = DashboardConsumer()
    consumer.scope = {"query_string": query.encode()}
    consumer.channel_name = "test_dash_channel"
    consumer.close = AsyncMock()
    consumer.accept = AsyncMock()
    consumer.send = AsyncMock()
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    return consumer


class TestDashboardConsumer:

    def test_token_invalido_cierra_con_4001(self):
        consumer = _make_dashboard_consumer(query="token=bad_token")
        asyncio.run(consumer.connect())
        consumer.close.assert_called_once_with(code=4001)
        consumer.accept.assert_not_called()

    def test_token_valido_acepta_y_une_al_grupo_dashboard_kpi(self):
        consumer = _make_dashboard_consumer(query="token=good")
        mock_user = MagicMock()
        with patch.object(consumer, "_authenticate", new=AsyncMock(return_value=mock_user)):
            with patch.object(consumer, "_get_kpis", new=AsyncMock(return_value={})):
                asyncio.run(consumer.connect())
        consumer.accept.assert_called_once()
        consumer.channel_layer.group_add.assert_called_once_with("dashboard_kpi", "test_dash_channel")

    def test_send_kpi_snapshot_on_connect(self):
        import json
        consumer = _make_dashboard_consumer(query="token=good")
        mock_user = MagicMock()
        kpis = {"ventasHoy": 5, "montoHoy": 25000, "clientes": 10, "productos": 3, "stockBajo": 0, "cajasAbiertas": 1}
        with patch.object(consumer, "_authenticate", new=AsyncMock(return_value=mock_user)):
            with patch.object(consumer, "_get_kpis", new=AsyncMock(return_value=kpis)):
                asyncio.run(consumer.connect())
        consumer.send.assert_called_once()
        payload = json.loads(consumer.send.call_args[1]["text_data"])
        assert payload["type"] == "kpi_snapshot"
        assert payload["ventasHoy"] == 5
        assert payload["montoHoy"] == 25000

    def test_disconnect_llama_group_discard(self):
        consumer = _make_dashboard_consumer()
        asyncio.run(consumer.disconnect(1000))
        consumer.channel_layer.group_discard.assert_called_once_with("dashboard_kpi", "test_dash_channel")

    def test_kpi_update_envia_data(self):
        import json
        consumer = _make_dashboard_consumer()
        event = {"data": {"ventasHoy": 10, "montoHoy": 50000}}
        asyncio.run(consumer.kpi_update(event))
        consumer.send.assert_called_once_with(text_data=json.dumps(event["data"]))

    @pytest.mark.django_db
    def test_get_kpis_retorna_estructura_correcta(self):
        consumer = _make_dashboard_consumer()
        result = asyncio.run(consumer._get_kpis())
        for campo in [
            "ventasHoy", "montoHoy", "clientes", "productos", "stockBajo", "cajasAbiertas",
            "recargasHoy", "montoRecargasHoy", "almuerzoHoy", "tarjetasEnAlerta", "cumpleanosHoy",
            "cumpleanosPersonalHoy",
        ]:
            assert campo in result, f"Campo '{campo}' ausente en _get_kpis()"
            assert isinstance(result[campo], int), f"Campo '{campo}' debería ser int"
        assert isinstance(result["cumpleaneros"], list)
        assert isinstance(result["cumpleanerosPersonal"], list)

    @pytest.mark.django_db(transaction=True)
    def test_get_kpis_incluye_cumpleanero_del_dia(self):
        # transaction=True: database_sync_to_async corre _get_kpis en otro hilo
        # con su propia conexión — sin esto, no vería el Hijo creado en la
        # transacción (no comiteada) del hilo principal del test.
        # freeze_time tampoco cruza ese límite de forma confiable, así que en vez
        # de congelar "hoy" se usa el "hoy" real (localdate) para la fecha de
        # nacimiento.
        from datetime import date
        from django.utils.timezone import localdate
        from apps.clientes.models import Cliente, Hijo, TipoCliente
        from apps.productos.models import ListaPrecio

        tipo = TipoCliente.objects.create(nombre="Familia WS")
        lista = ListaPrecio.objects.create(nombre="General WS", activo=True)
        cliente = Cliente.objects.create(
            nombres="Ana", apellidos="Gómez", ruc_ci="9998887",
            tipo_cliente=tipo, lista_precio=lista,
        )
        hoy = localdate()
        Hijo.objects.create(
            cliente_responsable=cliente, nombre="Sofía", apellido="Gómez",
            fecha_nacimiento=date(hoy.year - 10, hoy.month, hoy.day),
        )
        consumer = _make_dashboard_consumer()
        result = asyncio.run(consumer._get_kpis())

        assert result["cumpleanosHoy"] == 1
        assert result["cumpleaneros"][0]["nombre"] == "Sofía Gómez"

    @pytest.mark.django_db(transaction=True)
    def test_get_kpis_incluye_cumpleanero_personal_del_dia(self):
        from datetime import date
        from django.utils.timezone import localdate
        from apps.usuarios.models import Usuario

        hoy = localdate()
        Usuario.objects.create_user(
            email="ws_cumple_personal@test.com", password="test1234",
            nombre="Marta", apellido="Ruiz", rol=Usuario.Rol.CAJERO,
            fecha_nacimiento=date(hoy.year - 30, hoy.month, hoy.day),
        )
        consumer = _make_dashboard_consumer()
        result = asyncio.run(consumer._get_kpis())

        assert result["cumpleanosPersonalHoy"] == 1
        assert result["cumpleanerosPersonal"][0]["nombre"] == "Marta Ruiz"
        assert result["cumpleanerosPersonal"][0]["rol"] == "CAJERO"
