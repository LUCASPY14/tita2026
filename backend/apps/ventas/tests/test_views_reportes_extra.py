"""
Tests para ReporteMediosPagoView y ReporteNotasCreditoVentaView.
Cubre: parámetros faltantes (400), JSON OK, CSV, filtro por estado.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.fixture
def api_admin(usuario_admin):
    client = APIClient()
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Reporte Extra", activo=True)


@pytest.fixture
def cierre_cajero(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def venta_activa(db, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, cierre_cajero):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=usuario_cajero,
        tipo="CONTADO",
        medio_pago=medio_pago_efectivo,
        items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        cierre_caja=cierre_cajero,
    )


@pytest.fixture
def pago_venta(db, cliente, venta_activa, medio_pago_efectivo, usuario_cajero):
    from apps.ventas.models import PagoVenta
    return PagoVenta.objects.create(
        cliente=cliente,
        venta=venta_activa,
        monto=Decimal("3000"),
        medio_pago=medio_pago_efectivo,
        cajero=usuario_cajero,
        estado=PagoVenta.Estado.CONCILIADO,
    )


@pytest.fixture
def nota_credito_venta(db, cliente, venta_activa, usuario_admin):
    from apps.ventas.models import NotaCredito
    return NotaCredito.objects.create(
        cliente=cliente,
        venta_origen=venta_activa,
        nro_nota_credito="NC-TEST-001",
        monto_total=Decimal("3000"),
        motivo="Devolución test",
        estado=NotaCredito.Estado.EMITIDA,
        empleado_autoriza=usuario_admin,
    )


# ── ReporteMediosPagoView ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteMediosPago:

    URL = "/api/v1/ventas/reporte-medios-pago/"

    def test_sin_parametros_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_solo_desde_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01"})
        assert resp.status_code == 400

    def test_json_sin_pagos(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 200
        assert "por_medio_pago" in resp.data
        assert "resumen" in resp.data

    def test_json_con_pago(self, api_admin, pago_venta):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy})
        assert resp.status_code == 200
        assert resp.data["resumen"]["total_pagos"] >= 1
        assert len(resp.data["por_medio_pago"]) >= 1

    def test_csv_retorna_content_type(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "csv",
        })
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE MEDIOS DE PAGO" in resp.content

    def test_csv_con_pago_incluye_medio(self, api_admin, pago_venta, medio_pago_efectivo):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy, "formato": "csv"})
        assert resp.status_code == 200
        assert medio_pago_efectivo.descripcion.encode() in resp.content

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code in (401, 403)


# ── ReporteNotasCreditoVentaView ──────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteNotasCreditoVenta:

    URL = "/api/v1/ventas/reporte-notas-credito/"

    def test_sin_parametros_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_json_sin_notas(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 200
        assert "detalle" in resp.data
        assert "resumen" in resp.data

    def test_json_con_nota_credito(self, api_admin, nota_credito_venta):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy})
        assert resp.status_code == 200
        assert resp.data["resumen"]["total_emitidas"] >= 1
        assert len(resp.data["detalle"]) >= 1

    def test_filtro_por_estado(self, api_admin, nota_credito_venta):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {
            "desde": hoy, "hasta": hoy, "estado": "EMITIDA",
        })
        assert resp.status_code == 200
        for fila in resp.data["detalle"]:
            assert fila["estado"] == "EMITIDA"

    def test_filtro_estado_excluye_otros(self, api_admin, nota_credito_venta):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {
            "desde": hoy, "hasta": hoy, "estado": "ANULADA",
        })
        assert resp.status_code == 200
        assert len(resp.data["detalle"]) == 0

    def test_csv_retorna_content_type(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "csv",
        })
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert "NOTAS DE CR" in resp.content.decode("utf-8-sig")

    def test_csv_con_nota_incluye_datos(self, api_admin, nota_credito_venta):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy, "formato": "csv"})
        assert resp.status_code == 200
        assert b"NC-TEST-001" in resp.content

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code in (401, 403)
