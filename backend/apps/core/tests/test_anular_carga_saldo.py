"""
Tests de TarjetaService.anular_carga_saldo y el endpoint
POST /core/cargas-saldo/<id>/anular/ — mismo patrón que anular_venta.
"""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import CargaSaldo, MovimientoTarjeta, PagoBancard, Tarjeta
from apps.core.services import TarjetaService


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(nombre="Ana", apellido="Soler", cliente_responsable=cliente, activo=True)


@pytest.fixture
def tarjeta_con_carga(db, hijo, cliente, usuario_cajero):
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="T100", hijo=hijo, saldo_actual=Decimal("0"),
        limite_credito=Decimal("0"), estado=Tarjeta.Estado.ACTIVA,
    )
    carga = TarjetaService.cargar_saldo(
        tarjeta=tarjeta, monto=Decimal("20000"),
        cliente_origen=cliente, responsable=usuario_cajero,
    )
    tarjeta.refresh_from_db()
    return tarjeta, carga


@pytest.mark.django_db
class TestAnularCargaSaldo:

    def test_anula_y_revierte_el_saldo(self, tarjeta_con_carga, usuario_admin):
        tarjeta, carga = tarjeta_con_carga
        assert tarjeta.saldo_actual == Decimal("20000")

        resultado = TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)

        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == Decimal("0")
        assert resultado.estado == CargaSaldo.Estado.ANULADA

        reverso = MovimientoTarjeta.objects.filter(tarjeta=tarjeta, tipo=MovimientoTarjeta.Tipo.REVERSO).first()
        assert reverso is not None
        assert reverso.monto == Decimal("-20000")
        assert reverso.carga_id == carga.pk

    def test_no_se_puede_anular_dos_veces(self, tarjeta_con_carga, usuario_admin):
        _, carga = tarjeta_con_carga
        TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)
        carga.refresh_from_db()
        with pytest.raises(ValidationError):
            TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)

    def test_no_se_puede_anular_pendiente(self, hijo, cliente, usuario_admin):
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="T101", hijo=hijo, saldo_actual=Decimal("0"),
            limite_credito=Decimal("0"), estado=Tarjeta.Estado.ACTIVA,
        )
        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta, monto_cargado=Decimal("5000"), estado=CargaSaldo.Estado.PENDIENTE,
        )
        with pytest.raises(ValidationError):
            TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)

    def test_bloqueada_si_viene_de_pago_bancard_aprobado(self, tarjeta_con_carga, cliente, usuario_admin):
        tarjeta, carga = tarjeta_con_carga
        PagoBancard.objects.create(
            tipo=PagoBancard.Tipo.TARJETA, tarjeta=tarjeta, cliente=cliente,
            shop_process_id="shop-1", monto=Decimal("20000"),
            estado=PagoBancard.Estado.APROBADO, carga_saldo=carga,
        )
        with pytest.raises(ValidationError):
            TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)

    def test_permite_si_el_pago_bancard_ya_esta_cancelado(self, tarjeta_con_carga, cliente, usuario_admin):
        tarjeta, carga = tarjeta_con_carga
        PagoBancard.objects.create(
            tipo=PagoBancard.Tipo.TARJETA, tarjeta=tarjeta, cliente=cliente,
            shop_process_id="shop-2", monto=Decimal("20000"),
            estado=PagoBancard.Estado.CANCELADO, carga_saldo=carga,
        )
        resultado = TarjetaService.anular_carga_saldo(carga=carga, anulado_por=usuario_admin)
        assert resultado.estado == CargaSaldo.Estado.ANULADA


@pytest.mark.django_db
class TestAnularCargaSaldoEndpoint:

    def _login(self, email):
        client = APIClient()
        resp = client.post("/api/token/", {"email": email, "password": "test1234"}, format="json")
        assert resp.status_code == 200
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        return client

    def test_admin_puede_anular(self, tarjeta_con_carga, usuario_admin):
        _, carga = tarjeta_con_carga
        client = self._login("admin@test.com")
        resp = client.post(f"/api/v1/core/cargas-saldo/{carga.pk}/anular/")
        assert resp.status_code == 200, resp.data
        assert resp.data["estado"] == "ANULADA"

    def test_cajero_no_puede_anular(self, tarjeta_con_carga, usuario_cajero):
        _, carga = tarjeta_con_carga
        client = self._login("cajero@test.com")
        resp = client.post(f"/api/v1/core/cargas-saldo/{carga.pk}/anular/")
        assert resp.status_code == 403
