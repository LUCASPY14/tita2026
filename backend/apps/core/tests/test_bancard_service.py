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


# ─── _token ───────────────────────────────────────────────────────────────────

class TestToken:

    @override_settings(BANCARD_PRIVATE_KEY="mysecret")
    def test_token_es_md5_de_concatenacion(self):
        from apps.core.bancard_service import _token
        shop_id = "12345"
        suffix = "request"
        expected = hashlib.md5(f"mysecret{shop_id}{suffix}".encode(), usedforsecurity=False).hexdigest()
        assert _token(shop_id, suffix) == expected

    @override_settings(BANCARD_PRIVATE_KEY="k")
    def test_sufijo_request_distinto_de_confirmacion(self):
        from apps.core.bancard_service import _token
        assert _token("999", "request") != _token("999", "confirmacion")

    @override_settings(BANCARD_PRIVATE_KEY="")
    def test_token_con_clave_vacia_no_lanza_excepcion(self):
        from apps.core.bancard_service import _token
        result = _token("0", "request")
        assert len(result) == 32  # MD5 = 32 hex chars

    @override_settings(BANCARD_PRIVATE_KEY="abc")
    def test_token_distinto_por_shop_process_id(self):
        from apps.core.bancard_service import _token
        assert _token("111", "request") != _token("222", "request")


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


# ─── confirmar_pago ───────────────────────────────────────────────────────────

class TestConfirmarPago:

    @patch("apps.core.bancard_service.http_client.post")
    def test_exito_devuelve_confirmation(self, mock_post):
        from apps.core.bancard_service import confirmar_pago
        mock_post.return_value.json.return_value = {
            "status": "success",
            "confirmation": {"response_code": "00", "payment_id": "12345"},
        }
        result = confirmar_pago("SP010")
        assert result["status"] == "success"
        assert result["confirmation"]["response_code"] == "00"

    @patch("apps.core.bancard_service.http_client.post")
    def test_url_post_incluye_shop_process_id(self, mock_post):
        from apps.core.bancard_service import confirmar_pago
        mock_post.return_value.json.return_value = {"status": "success"}
        confirmar_pago("SP013")
        call_url = mock_post.call_args[0][0]
        assert "SP013" in call_url

    @patch("apps.core.bancard_service.http_client.post")
    def test_excepcion_de_red_devuelve_error(self, mock_post):
        from apps.core.bancard_service import confirmar_pago
        mock_post.side_effect = ConnectionError("timeout")
        result = confirmar_pago("SP012")
        assert result["status"] == "error"
        assert len(result["messages"]) > 0

    @patch("apps.core.bancard_service.http_client.post")
    def test_error_de_bancard_se_propaga(self, mock_post):
        from apps.core.bancard_service import confirmar_pago
        mock_post.return_value.json.return_value = {
            "status": "error",
            "messages": [{"dsc": "Transacción no encontrada"}],
        }
        result = confirmar_pago("SP011")
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
            result = bancard_service.confirmar_pago("SP014")
            assert result["status"] == "error"
            assert "temporalmente" in result["messages"][0]["dsc"].lower()
        finally:
            cb._state = original_state
            cb._failure_count = original_count
            cb._opened_at = original_opened


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
