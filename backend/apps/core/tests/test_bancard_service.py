"""Tests unitarios para apps.core.bancard_service."""

import hashlib
import time
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import override_settings


_SANDBOX_URL = "https://vpos.infonet.com.py:8888"
_PROD_URL    = "https://vpos.infonet.com.py"


# ─── _base_url ────────────────────────────────────────────────────────────────

class TestBaseUrl:

    @override_settings(BANCARD_SANDBOX=True)
    def test_sandbox_true_devuelve_sandbox_url(self):
        from apps.core.bancard_service import _base_url
        assert _base_url() == _SANDBOX_URL

    @override_settings(BANCARD_SANDBOX=False)
    def test_sandbox_false_devuelve_prod_url(self):
        from apps.core.bancard_service import _base_url
        assert _base_url() == _PROD_URL


# ─── Keys ─────────────────────────────────────────────────────────────────────

class TestKeys:

    @override_settings(BANCARD_PUBLIC_KEY="pub-key-test")
    def test_public_key_lee_de_settings(self):
        from apps.core.bancard_service import _public_key
        assert _public_key() == "pub-key-test"

    @override_settings(BANCARD_PRIVATE_KEY="priv-key-test")
    def test_private_key_lee_de_settings(self):
        from apps.core.bancard_service import _private_key
        assert _private_key() == "priv-key-test"

    def test_keys_devuelven_str_si_no_estan_configuradas(self):
        from apps.core.bancard_service import _public_key, _private_key
        assert isinstance(_public_key(), str)
        assert isinstance(_private_key(), str)


# ─── Tokens por operación (single_buy, confirm, get_confirmation, rollback) ────
# _token(shop_id, suffix) fue reemplazada por una función dedicada por operación,
# ya que cada una concatena un orden de campos distinto (ver bancard_service.py).

class TestTokensPorOperacion:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_single_buy_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token_single_buy
        expected = hashlib.md5("mysecret1234510000.00PYG".encode(), usedforsecurity=False).hexdigest()
        assert _token_single_buy("12345", 10000) == expected

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_confirm_webhook_incluye_sufijo_confirm(self):
        from apps.core.bancard_service import _token_confirm_webhook, _token_single_buy
        # Mismo shop_process_id y monto, pero confirm agrega el sufijo "confirm"
        # entre el shop_process_id y el amount — el token debe diferir.
        assert _token_confirm_webhook("12345", 10000) != _token_single_buy("12345", 10000)
        expected = hashlib.md5("mysecret12345confirm10000.00PYG".encode(), usedforsecurity=False).hexdigest()
        assert _token_confirm_webhook("12345", 10000) == expected

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_get_confirmation_no_depende_del_monto(self):
        from apps.core.bancard_service import _token_get_confirmation
        expected = hashlib.md5("mysecret12345get_confirmation".encode(), usedforsecurity=False).hexdigest()
        assert _token_get_confirmation("12345") == expected

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_rollback_usa_monto_fijo_0_00(self):
        from apps.core.bancard_service import _token_rollback
        expected = hashlib.md5("mysecret12345rollback0.00".encode(), usedforsecurity=False).hexdigest()
        assert _token_rollback("12345") == expected

    @override_settings(BANCARD_PRIVATE_KEY="")
    def test_tokens_con_clave_vacia_no_lanzan_excepcion(self):
        from apps.core.bancard_service import (
            _token_single_buy, _token_confirm_webhook, _token_get_confirmation, _token_rollback,
        )
        for token in (
            _token_single_buy("0", 0),
            _token_confirm_webhook("0", 0),
            _token_get_confirmation("0"),
            _token_rollback("0"),
        ):
            assert len(token) == 32  # MD5 = 32 hex chars

    @override_settings(BANCARD_PRIVATE_KEY="abc")
    def test_token_single_buy_distinto_por_shop_process_id(self):
        from apps.core.bancard_service import _token_single_buy
        assert _token_single_buy("111", 1000) != _token_single_buy("222", 1000)


# ─── pago_url ─────────────────────────────────────────────────────────────────

class TestPagoUrl:

    @override_settings(BANCARD_SANDBOX=True)
    def test_pago_url_sandbox_incluye_process_id(self):
        from apps.core.bancard_service import pago_url
        url = pago_url("proc-abc")
        assert url == f"{_SANDBOX_URL}/payment-card?process_id=proc-abc"

    @override_settings(BANCARD_SANDBOX=False)
    def test_pago_url_produccion_incluye_process_id(self):
        from apps.core.bancard_service import pago_url
        url = pago_url("proc-xyz")
        assert url == f"{_PROD_URL}/payment-card?process_id=proc-xyz"

    @override_settings(BANCARD_SANDBOX=True)
    def test_pago_url_diferentes_process_ids(self):
        from apps.core.bancard_service import pago_url
        assert pago_url("aaa") != pago_url("bbb")


# ─── iniciar_pago ─────────────────────────────────────────────────────────────

class TestIniciarPago:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_json_de_bancard(self, mock_post):
        from apps.core.bancard_service import iniciar_pago
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "pid-001"}
        result = iniciar_pago(
            shop_process_id="SP001",
            monto=100000,
            descripcion="Recarga saldo",
            return_url="https://example.com/retorno",
            cancel_url="https://example.com/cancelar",
        )
        assert result["status"] == "success"
        assert result["process_id"] == "pid-001"
        mock_post.assert_called_once()

    @patch("apps.core.bancard_service.http_client.post")
    def test_descripcion_truncada_a_20_chars(self, mock_post):
        from apps.core.bancard_service import iniciar_pago
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "p"}
        iniciar_pago(
            shop_process_id="SP002",
            monto=50000,
            descripcion="Una descripcion muy larga que supera los veinte caracteres permitidos",
            return_url="https://r.com",
            cancel_url="https://c.com",
        )
        payload = mock_post.call_args[1]["json"]
        assert len(payload["operation"]["description"]) <= 20

    @patch("apps.core.bancard_service.http_client.post")
    def test_payload_contiene_campos_requeridos(self, mock_post):
        from apps.core.bancard_service import iniciar_pago
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "p"}
        with override_settings(BANCARD_PUBLIC_KEY="pubk"):
            iniciar_pago(
                shop_process_id="SP003",
                monto=75000,
                descripcion="Test pago",
                return_url="https://r.com",
                cancel_url="https://c.com",
            )
        payload = mock_post.call_args[1]["json"]
        assert payload["public_key"] == "pubk"
        assert payload["operation"]["shop_process_id"] == "SP003"
        assert payload["operation"]["amount"] == "75000.00"
        assert payload["operation"]["currency"] == "PYG"
        assert payload["operation"]["return_url"] == "https://r.com"
        assert payload["operation"]["cancel_url"] == "https://c.com"

    @patch("apps.core.bancard_service.http_client.post")
    def test_monto_formateado_con_dos_decimales(self, mock_post):
        from apps.core.bancard_service import iniciar_pago
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "p"}
        iniciar_pago(
            shop_process_id="SP004",
            monto=200000,
            descripcion="Test",
            return_url="https://r.com",
            cancel_url="https://c.com",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["operation"]["amount"] == "200000.00"

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_status_error(self, mock_post):
        from apps.core.bancard_service import iniciar_pago
        mock_post.side_effect = Exception("Connection timeout")
        result = iniciar_pago(
            shop_process_id="SP005",
            monto=100000,
            descripcion="Test",
            return_url="https://r.com",
            cancel_url="https://c.com",
        )
        assert result["status"] == "error"
        assert "Connection timeout" in result["messages"][0]["dsc"]

    def test_circuit_breaker_open_devuelve_error_temporalmente(self):
        from apps.core import bancard_service
        from common.circuit_breaker import _State
        cb = bancard_service._bancard_cb
        original_state = cb._state
        original_count = cb._failure_count
        original_opened = cb._opened_at
        try:
            cb._state = _State.OPEN
            cb._opened_at = time.monotonic()  # recién abierto, no se recupera
            result = bancard_service.iniciar_pago(
                shop_process_id="SP006",
                monto=100000,
                descripcion="Test",
                return_url="https://r.com",
                cancel_url="https://c.com",
            )
            assert result["status"] == "error"
            assert "temporalmente" in result["messages"][0]["dsc"].lower()
        finally:
            cb._state = original_state
            cb._failure_count = original_count
            cb._opened_at = original_opened


# ─── get_confirmation ─────────────────────────────────────────────────────────
# (antes "confirmar_pago" — renombrada porque no confirma nada, sólo consulta si
# Bancard ya confirmó un pago; se usa como fallback en bancard_retorno cuando el
# webhook todavía no llegó.)

class TestGetConfirmation:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_confirmation(self, mock_post):
        from apps.core.bancard_service import get_confirmation
        mock_post.return_value.json.return_value = {
            "status": "success",
            "confirmation": {"response_code": "00", "payment_id": "12345"},
        }
        result = get_confirmation("SP010")
        assert result["status"] == "success"
        assert result["confirmation"]["response_code"] == "00"

    @patch("apps.core.bancard_service.http_client.post")
    def test_url_post_apunta_a_single_buy_confirmations(self, mock_post):
        from apps.core.bancard_service import get_confirmation
        mock_post.return_value.json.return_value = {"status": "success"}
        get_confirmation("SP013")
        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/vpos/api/0.3/single_buy/confirmations")

    @patch("apps.core.bancard_service.http_client.post")
    def test_payload_incluye_shop_process_id(self, mock_post):
        from apps.core.bancard_service import get_confirmation
        mock_post.return_value.json.return_value = {"status": "success"}
        get_confirmation("SP013")
        payload = mock_post.call_args[1]["json"]
        assert payload["operation"]["shop_process_id"] == "SP013"

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_error(self, mock_post):
        from apps.core.bancard_service import get_confirmation
        mock_post.side_effect = ConnectionError("timeout")
        result = get_confirmation("SP012")
        assert result["status"] == "error"
        assert len(result["messages"]) > 0

    @patch("apps.core.bancard_service.http_client.post")
    def test_error_de_bancard_se_propaga(self, mock_post):
        from apps.core.bancard_service import get_confirmation
        mock_post.return_value.json.return_value = {
            "status": "error",
            "messages": [{"dsc": "Transacción no encontrada"}],
        }
        result = get_confirmation("SP011")
        assert result["status"] == "error"

    def test_circuit_breaker_open_devuelve_error_temporalmente(self):
        from apps.core import bancard_service
        from common.circuit_breaker import _State
        cb = bancard_service._bancard_cb
        original_state = cb._state
        original_count = cb._failure_count
        original_opened = cb._opened_at
        try:
            cb._state = _State.OPEN
            cb._opened_at = time.monotonic()
            result = bancard_service.get_confirmation("SP014")
            assert result["status"] == "error"
            assert "temporalmente" in result["messages"][0]["dsc"].lower()
        finally:
            cb._state = original_state
            cb._failure_count = original_count
            cb._opened_at = original_opened


# ─── rollback ─────────────────────────────────────────────────────────────────
# Sin cobertura previa — la agregamos de paso, mismo patrón que get_confirmation.

class TestRollback:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_status_success(self, mock_post):
        from apps.core.bancard_service import rollback
        mock_post.return_value.json.return_value = {"status": "success"}
        result = rollback("SP020")
        assert result["status"] == "success"

    @patch("apps.core.bancard_service.http_client.post")
    def test_url_post_apunta_a_single_buy_rollback(self, mock_post):
        from apps.core.bancard_service import rollback
        mock_post.return_value.json.return_value = {"status": "success"}
        rollback("SP021")
        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/vpos/api/0.3/single_buy/rollback")

    @patch("apps.core.bancard_service.http_client.post")
    def test_transaccion_ya_confirmada_devuelve_error(self, mock_post):
        from apps.core.bancard_service import rollback
        mock_post.return_value.json.return_value = {
            "status": "error",
            "messages": [{"key": "TransactionAlreadyConfirmed", "dsc": "Transacción Cuponada"}],
        }
        result = rollback("SP022")
        assert result["status"] == "error"

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_status_error(self, mock_post):
        from apps.core.bancard_service import rollback
        mock_post.side_effect = ConnectionError("timeout")
        result = rollback("SP023")
        assert result["status"] == "error"


# ─── acreditar_saldo ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAcreditarSaldo:

    def _setup_pago(self, suffix: str, monto: Decimal):
        """Crea el mínimo de objetos necesarios para un PagoBancard."""
        from apps.clientes.models import Cliente, Hijo, TipoCliente
        from apps.core.models import PagoBancard, Tarjeta
        from apps.productos.models import ListaPrecio

        tipo = TipoCliente.objects.create(nombre=f"Padre {suffix}")
        lista = ListaPrecio.objects.create(nombre=f"General {suffix}", activo=True)
        cliente = Cliente.objects.create(
            nombres="Test", apellidos=suffix, ruc_ci=f"CI{suffix}",
            tipo_cliente=tipo, lista_precio=lista,
        )
        hijo = Hijo.objects.create(
            nombre="Test", apellido=suffix,
            cliente_responsable=cliente, activo=True,
        )
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta=f"T{suffix}", hijo=hijo,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        pago = PagoBancard.objects.create(
            tarjeta=tarjeta, cliente=cliente,
            monto=monto,
            shop_process_id=f"SP-{suffix}",
            process_id=f"proc-{suffix}",
            estado=PagoBancard.Estado.PENDIENTE,
        )
        return pago, tarjeta

    def test_pago_queda_en_estado_aprobado(self):
        from apps.core import bancard_service
        from apps.core.models import PagoBancard
        pago, _ = self._setup_pago("BS01", Decimal("150000"))
        bancard_service.acreditar_saldo(pago)
        pago.refresh_from_db()
        assert pago.estado == PagoBancard.Estado.APROBADO

    def test_saldo_se_acredita_en_tarjeta(self):
        from apps.core import bancard_service
        pago, tarjeta = self._setup_pago("BS02", Decimal("200000"))
        bancard_service.acreditar_saldo(pago)
        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == Decimal("200000")

    def test_carga_saldo_vinculada_al_pago(self):
        from apps.core import bancard_service
        pago, _ = self._setup_pago("BS03", Decimal("50000"))
        bancard_service.acreditar_saldo(pago)
        pago.refresh_from_db()
        assert pago.carga_saldo is not None

    def test_fecha_confirmacion_se_actualiza(self):
        from apps.core import bancard_service
        pago, _ = self._setup_pago("BS04", Decimal("75000"))
        assert pago.fecha_confirmacion is None
        bancard_service.acreditar_saldo(pago)
        pago.refresh_from_db()
        assert pago.fecha_confirmacion is not None

    def test_carga_tiene_metodo_tarjeta_bancard(self):
        from apps.core import bancard_service
        from apps.core.models import CargaSaldo
        pago, tarjeta = self._setup_pago("BS05", Decimal("100000"))
        bancard_service.acreditar_saldo(pago)
        carga = CargaSaldo.objects.get(tarjeta=tarjeta)
        assert carga.metodo_pago == "TARJETA_BANCARD"
        assert carga.referencia == "SP-BS05"


# ─── Tokens: tarjetas guardadas ────────────────────────────────────────────────

class TestTokenCardsNew:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token_cards_new
        expected = hashlib.md5("mysecret2100request_new_card".encode(), usedforsecurity=False).hexdigest()
        assert _token_cards_new(card_id=2, user_id=100) == expected

    @override_settings(BANCARD_PRIVATE_KEY="k")
    def test_token_distinto_por_card_id(self):
        from apps.core.bancard_service import _token_cards_new
        assert _token_cards_new(1, 100) != _token_cards_new(2, 100)


class TestTokenUsersCards:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token_users_cards
        expected = hashlib.md5("mysecret100request_user_cards".encode(), usedforsecurity=False).hexdigest()
        assert _token_users_cards(user_id=100) == expected


class TestTokenCharge:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token_charge
        expected = hashlib.md5(
            "mysecretSP001charge130.00PYGalias-abc".encode(), usedforsecurity=False
        ).hexdigest()
        assert _token_charge("SP001", 130, "alias-abc") == expected

    @override_settings(BANCARD_PRIVATE_KEY="k")
    def test_token_distinto_por_alias_token(self):
        from apps.core.bancard_service import _token_charge
        assert _token_charge("SP001", 100, "alias-1") != _token_charge("SP001", 100, "alias-2")


class TestTokenDeleteCard:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token_delete_card
        expected = hashlib.md5(
            "mysecretdelete_card100alias-abc".encode(), usedforsecurity=False
        ).hexdigest()
        assert _token_delete_card(user_id=100, card_token="alias-abc") == expected


# ─── catastro_tarjeta ───────────────────────────────────────────────────────────

class TestCatastroTarjeta:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_process_id(self, mock_post):
        from apps.core.bancard_service import catastro_tarjeta
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "pid-cat-1"}
        result = catastro_tarjeta(
            card_id=1, user_id=42, user_cell_phone="0981123456",
            user_mail="test@test.com", return_url="https://r.com",
        )
        assert result["status"] == "success"
        assert result["process_id"] == "pid-cat-1"

    @patch("apps.core.bancard_service.http_client.post")
    def test_payload_contiene_card_id_y_user_id(self, mock_post):
        from apps.core.bancard_service import catastro_tarjeta
        mock_post.return_value.json.return_value = {"status": "success", "process_id": "p"}
        catastro_tarjeta(
            card_id=3, user_id=99, user_cell_phone="0981000000",
            user_mail="a@a.com", return_url="https://r.com",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["operation"]["card_id"] == 3
        assert payload["operation"]["user_id"] == 99
        assert payload["operation"]["return_url"] == "https://r.com"

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_status_error(self, mock_post):
        from apps.core.bancard_service import catastro_tarjeta
        mock_post.side_effect = Exception("timeout")
        result = catastro_tarjeta(
            card_id=1, user_id=1, user_cell_phone="", user_mail="", return_url="https://r.com",
        )
        assert result["status"] == "error"


# ─── listar_tarjetas ────────────────────────────────────────────────────────────

class TestListarTarjetas:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_cards(self, mock_post):
        from apps.core.bancard_service import listar_tarjetas
        mock_post.return_value.json.return_value = {
            "status": "success",
            "cards": [{"card_id": 1, "alias_token": "alias-1", "card_masked_number": "5418********0014"}],
        }
        result = listar_tarjetas(user_id=42)
        assert result["status"] == "success"
        assert result["cards"][0]["card_id"] == 1

    @patch("apps.core.bancard_service.http_client.post")
    def test_payload_incluye_extra_response_attributes(self, mock_post):
        from apps.core.bancard_service import listar_tarjetas
        mock_post.return_value.json.return_value = {"status": "success", "cards": []}
        listar_tarjetas(user_id=42)
        payload = mock_post.call_args[1]["json"]
        assert payload["operation"]["extra_response_attributes"] == ["cards.bancard_proccesed"]

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_status_error(self, mock_post):
        from apps.core.bancard_service import listar_tarjetas
        mock_post.side_effect = Exception("timeout")
        result = listar_tarjetas(user_id=1)
        assert result["status"] == "error"


# ─── pagar_con_token ────────────────────────────────────────────────────────────

class TestPagarConToken:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_operation(self, mock_post):
        from apps.core.bancard_service import pagar_con_token
        mock_post.return_value.json.return_value = {
            "operation": {"response_code": "00", "process_id": None},
        }
        result = pagar_con_token(
            shop_process_id="SP001", monto=100000, alias_token="alias-1",
            descripcion="Recarga", return_url="https://r.com",
        )
        assert result["operation"]["response_code"] == "00"

    @patch("apps.core.bancard_service.http_client.post")
    def test_payload_incluye_alias_token_y_sin_extra_response_attributes(self, mock_post):
        from apps.core.bancard_service import pagar_con_token
        mock_post.return_value.json.return_value = {"operation": {}}
        pagar_con_token(
            shop_process_id="SP002", monto=50000, alias_token="alias-xyz",
            descripcion="Test", return_url="https://r.com",
        )
        payload = mock_post.call_args[1]["json"]
        assert payload["operation"]["alias_token"] == "alias-xyz"
        assert payload["operation"]["number_of_payments"] == 1
        # Bancard confirmó (ago-2026) que extra_response_attributes no está habilitado
        # para este comercio en /charge — no enviarlo (sí sigue permitido en /cards).
        assert "extra_response_attributes" not in payload["operation"]
        # El manual lo marca opcional, pero Bancard rechaza el charge sin este campo
        # ("The parameter additional_data is missing.") — confirmado contra sandbox real.
        assert payload["operation"]["additional_data"] == ""

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_status_error(self, mock_post):
        from apps.core.bancard_service import pagar_con_token
        mock_post.side_effect = Exception("timeout")
        result = pagar_con_token(
            shop_process_id="SP003", monto=1000, alias_token="a",
            descripcion="d", return_url="https://r.com",
        )
        assert result["status"] == "error"


# ─── eliminar_tarjeta ───────────────────────────────────────────────────────────

class TestEliminarTarjeta:

    @patch("apps.core.bancard_service.http_client.request")
    def test_exito_devuelve_success(self, mock_request):
        from apps.core.bancard_service import eliminar_tarjeta
        mock_request.return_value.json.return_value = {"status": "success"}
        result = eliminar_tarjeta(user_id=42, alias_token="alias-1")
        assert result["status"] == "success"
        assert mock_request.call_args[0][0] == "DELETE"

    @patch("apps.core.bancard_service.http_client.request")
    def test_excepcion_de_red_devuelve_status_error(self, mock_request):
        from apps.core.bancard_service import eliminar_tarjeta
        mock_request.side_effect = Exception("timeout")
        result = eliminar_tarjeta(user_id=1, alias_token="a")
        assert result["status"] == "error"


# ─── procesar_resultado_pago ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProcesarResultadoPago:

    def _setup_pago(self, suffix: str, monto: Decimal):
        from apps.clientes.models import Cliente, Hijo, TipoCliente
        from apps.core.models import PagoBancard, Tarjeta
        from apps.productos.models import ListaPrecio

        tipo = TipoCliente.objects.create(nombre=f"Padre {suffix}")
        lista = ListaPrecio.objects.create(nombre=f"General {suffix}", activo=True)
        cliente = Cliente.objects.create(
            nombres="Test", apellidos=suffix, ruc_ci=f"CI{suffix}",
            tipo_cliente=tipo, lista_precio=lista,
        )
        hijo = Hijo.objects.create(
            nombre="Test", apellido=suffix,
            cliente_responsable=cliente, activo=True,
        )
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta=f"T{suffix}", hijo=hijo,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        pago = PagoBancard.objects.create(
            tarjeta=tarjeta, cliente=cliente,
            monto=monto,
            shop_process_id=f"SP-{suffix}",
            estado=PagoBancard.Estado.PENDIENTE,
        )
        return pago, tarjeta

    def test_response_code_00_acredita_y_aprueba(self):
        from apps.core import bancard_service
        from apps.core.models import PagoBancard
        pago, tarjeta = self._setup_pago("PR01", Decimal("100000"))
        bancard_service.procesar_resultado_pago(pago, "00")
        pago.refresh_from_db()
        tarjeta.refresh_from_db()
        assert pago.estado == PagoBancard.Estado.APROBADO
        assert tarjeta.saldo_actual == Decimal("100000")

    def test_response_code_distinto_rechaza(self):
        from apps.core import bancard_service
        from apps.core.models import PagoBancard
        pago, tarjeta = self._setup_pago("PR02", Decimal("100000"))
        saldo_inicial = tarjeta.saldo_actual
        bancard_service.procesar_resultado_pago(pago, "05")
        pago.refresh_from_db()
        tarjeta.refresh_from_db()
        assert pago.estado == PagoBancard.Estado.RECHAZADO
        assert pago.fecha_confirmacion is not None
        assert tarjeta.saldo_actual == saldo_inicial

    def test_excepcion_al_acreditar_marca_error(self):
        from apps.core import bancard_service
        from apps.core.models import PagoBancard
        pago, _ = self._setup_pago("PR03", Decimal("100000"))
        with patch("apps.core.bancard_service.acreditar_saldo", side_effect=Exception("boom")):
            bancard_service.procesar_resultado_pago(pago, "00")
        pago.refresh_from_db()
        assert pago.estado == PagoBancard.Estado.ERROR


# ─── proxima_tarjeta_guardada_disponible ────────────────────────────────────────

class TestProximaTarjetaGuardadaDisponible:

    @patch("apps.core.bancard_service.listar_tarjetas")
    def test_sin_tarjetas_devuelve_1(self, mock_listar):
        from apps.core.bancard_service import proxima_tarjeta_guardada_disponible
        mock_listar.return_value = {"status": "success", "cards": []}
        assert proxima_tarjeta_guardada_disponible(42) == 1

    @patch("apps.core.bancard_service.listar_tarjetas")
    def test_devuelve_cantidad_actual_mas_uno(self, mock_listar):
        # Bancard no devuelve en users_cards el card_id que nosotros elegimos (usa su
        # propio id interno), así que la disponibilidad se calcula por cantidad, no
        # por matching de ids.
        from apps.core.bancard_service import proxima_tarjeta_guardada_disponible
        mock_listar.return_value = {
            "status": "success",
            "cards": [{"card_id": 173738}, {"card_id": 991204}],
        }
        assert proxima_tarjeta_guardada_disponible(42) == 3

    @patch("apps.core.bancard_service.listar_tarjetas")
    def test_cinco_tarjetas_devuelve_none(self, mock_listar):
        from apps.core.bancard_service import proxima_tarjeta_guardada_disponible
        mock_listar.return_value = {
            "status": "success",
            "cards": [{"card_id": i * 111111} for i in range(1, 6)],
        }
        assert proxima_tarjeta_guardada_disponible(42) is None

    @patch("apps.core.bancard_service.listar_tarjetas")
    def test_status_error_devuelve_1(self, mock_listar):
        from apps.core.bancard_service import proxima_tarjeta_guardada_disponible
        mock_listar.return_value = {"status": "error", "messages": []}
        assert proxima_tarjeta_guardada_disponible(42) == 1
