"""
Tests de AlmuerzoService.anular_recarga_almuerzo y el endpoint
POST /almuerzos/recargas-saldo/<id>/anular/ — mismo patrón que
core.anular_carga_saldo / ventas.anular_venta.
"""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.almuerzos.models import MovimientoSaldoAlmuerzo, RecargaSaldoAlmuerzo, SaldoAlmuerzo
from apps.almuerzos.services import AlmuerzoService
from apps.core.models import PagoBancard


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(nombre="Mía", apellido="Duré", cliente_responsable=cliente, activo=True)


@pytest.fixture
def hijo_con_recarga(db, hijo, usuario_cajero):
    recarga = AlmuerzoService.recargar_saldo(
        hijo=hijo, monto=Decimal("30000"), registrado_por=usuario_cajero,
    )
    return hijo, recarga


@pytest.mark.django_db
class TestAnularRecargaAlmuerzo:

    def test_anula_y_revierte_el_saldo(self, hijo_con_recarga, usuario_admin):
        hijo, recarga = hijo_con_recarga
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo)
        assert saldo.saldo_actual == Decimal("30000")

        resultado = AlmuerzoService.anular_recarga_almuerzo(recarga=recarga, anulado_por=usuario_admin)

        saldo.refresh_from_db()
        assert saldo.saldo_actual == Decimal("0")
        assert resultado.estado == RecargaSaldoAlmuerzo.Estado.ANULADA

        ajuste = MovimientoSaldoAlmuerzo.objects.filter(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE,
        ).first()
        assert ajuste is not None
        assert ajuste.monto == Decimal("-30000")
        assert ajuste.recarga_id == recarga.pk

    def test_no_se_puede_anular_dos_veces(self, hijo_con_recarga, usuario_admin):
        _, recarga = hijo_con_recarga
        AlmuerzoService.anular_recarga_almuerzo(recarga=recarga, anulado_por=usuario_admin)
        recarga.refresh_from_db()
        with pytest.raises(ValidationError):
            AlmuerzoService.anular_recarga_almuerzo(recarga=recarga, anulado_por=usuario_admin)

    def test_no_se_puede_anular_pendiente(self, hijo, usuario_admin):
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo, monto_cargado=Decimal("5000"), estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        with pytest.raises(ValidationError):
            AlmuerzoService.anular_recarga_almuerzo(recarga=recarga, anulado_por=usuario_admin)

    def test_bloqueada_si_viene_de_pago_bancard_aprobado(self, hijo_con_recarga, cliente, usuario_admin):
        hijo, recarga = hijo_con_recarga
        PagoBancard.objects.create(
            tipo=PagoBancard.Tipo.ALMUERZO, hijo=hijo, cliente=cliente,
            shop_process_id="shop-alm-1", monto=Decimal("30000"),
            estado=PagoBancard.Estado.APROBADO, recarga_almuerzo=recarga,
        )
        with pytest.raises(ValidationError):
            AlmuerzoService.anular_recarga_almuerzo(recarga=recarga, anulado_por=usuario_admin)


@pytest.mark.django_db
class TestAnularRecargaAlmuerzoEndpoint:

    def _login(self, email):
        client = APIClient()
        resp = client.post("/api/token/", {"email": email, "password": "test1234"}, format="json")
        assert resp.status_code == 200
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        return client

    def test_admin_puede_anular(self, hijo_con_recarga, usuario_admin):
        _, recarga = hijo_con_recarga
        client = self._login("admin@test.com")
        resp = client.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/anular/")
        assert resp.status_code == 200, resp.data
        assert resp.data["estado"] == "ANULADA"

    def test_cajero_no_puede_anular(self, hijo_con_recarga, usuario_cajero):
        _, recarga = hijo_con_recarga
        client = self._login("cajero@test.com")
        resp = client.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/anular/")
        assert resp.status_code == 403
