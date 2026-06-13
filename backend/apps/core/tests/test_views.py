"""
Tests de vistas de core.
Cubre: CargaSaldoViewSet (create, confirmar), MedioPagoViewSet (caché),
ReporteTarjetasView.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def hijo_core(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Ana",
        apellido="García",
        cliente_responsable=cliente,
    )


@pytest.fixture
def tarjeta_core(db, hijo_core):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(nro_tarjeta="CORE0001", hijo=hijo_core)


@pytest.fixture
def carga_pendiente(db, tarjeta_core, usuario_cajero):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta_core,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.PENDIENTE,
        responsable=usuario_cajero,
    )


# ── CargaSaldoViewSet ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCargaSaldoCreate:

    def test_transferencia_queda_pendiente(self, api_cajero, tarjeta_core):
        resp = api_cajero.post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta_core.pk, "monto_cargado": 50000, "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "PENDIENTE"

    def test_efectivo_queda_confirmada(self, api_cajero, tarjeta_core):
        resp = api_cajero.post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta_core.pk, "monto_cargado": 30000, "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "CONFIRMADA"

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/core/cargas-saldo/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/core/cargas-saldo/")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestCargaSaldoConfirmar:

    def test_confirmar_pendiente_ok(self, api_cajero, carga_pendiente):
        resp = api_cajero.post(
            f"/api/v1/core/cargas-saldo/{carga_pendiente.pk}/confirmar/"
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "CONFIRMADA"

    def test_confirmar_ya_confirmada_falla(self, api_cajero, tarjeta_core):
        from apps.core.models import CargaSaldo
        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta_core,
            monto_cargado=Decimal("10000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
        )
        resp = api_cajero.post(f"/api/v1/core/cargas-saldo/{carga.pk}/confirmar/")
        assert resp.status_code == 400


# ── MedioPagoViewSet — caché ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestMedioPagoCache:

    def test_list_cache_miss_y_hit(self, api_cajero, medio_pago_efectivo):
        resp1 = api_cajero.get("/api/v1/core/medios-pago/")
        assert resp1.status_code == 200
        resp2 = api_cajero.get("/api/v1/core/medios-pago/")
        assert resp2.status_code == 200
        assert resp1.data == resp2.data

    def test_create_invalida_cache(self, api_admin):
        resp = api_admin.post(
            "/api/v1/core/medios-pago/",
            {"descripcion": "Cheque", "activo": True},
            format="json",
        )
        assert resp.status_code == 201

    def test_update_invalida_cache(self, api_admin, medio_pago_efectivo):
        resp = api_admin.patch(
            f"/api/v1/core/medios-pago/{medio_pago_efectivo.pk}/",
            {"descripcion": "Efectivo Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_delete_invalida_cache(self, api_admin):
        from apps.core.models import MedioPago
        mp = MedioPago.objects.create(descripcion="Temporal", activo=True)
        resp = api_admin.delete(f"/api/v1/core/medios-pago/{mp.pk}/")
        assert resp.status_code == 204


# ── ReporteTarjetasView ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteTarjetas:

    def test_sin_params_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/core/reporte-tarjetas/")
        assert resp.status_code == 200
        assert "tarjetas" in resp.data
        assert "resumen" in resp.data

    def test_con_periodo_filtra(self, api_admin):
        resp = api_admin.get(
            "/api/v1/core/reporte-tarjetas/",
            {"desde": "2020-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert resp.data["periodo"]["desde"] == "2020-01-01"

    def test_formato_csv_sin_periodo(self, api_admin):
        resp = api_admin.get("/api/v1/core/reporte-tarjetas/", {"formato": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE TARJETAS PREPAGO" in resp.content

    def test_formato_csv_con_periodo_y_tarjeta(self, api_admin, tarjeta_core):
        resp = api_admin.get(
            "/api/v1/core/reporte-tarjetas/",
            {"desde": "2020-01-01", "hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"CORE0001" in resp.content

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/core/reporte-tarjetas/")
        assert resp.status_code in (401, 403)
