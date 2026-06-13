"""
Tests de vistas de inventario.
Cubre: StockViewSet, MovimientoStockViewSet (CSV), AjusteInventarioViewSet
(aprobar/rechazar), ViewSets simples, ReporteStockView, StockCriticoView.
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
def ajuste_pendiente_aumento(db, producto, usuario_cajero):
    from apps.inventario.models import AjusteInventario, DetalleAjuste
    ajuste = AjusteInventario.objects.create(
        tipo=AjusteInventario.TipoAjuste.AUMENTO,
        motivo="Reposición de stock",
        solicitado_por=usuario_cajero,
    )
    DetalleAjuste.objects.create(ajuste=ajuste, producto=producto, cantidad=Decimal("10"))
    return ajuste


@pytest.fixture
def ajuste_pendiente_merma(db, producto, usuario_cajero, stock_producto):
    from apps.inventario.models import AjusteInventario, DetalleAjuste
    ajuste = AjusteInventario.objects.create(
        tipo=AjusteInventario.TipoAjuste.MERMA,
        motivo="Merma por vencimiento",
        solicitado_por=usuario_cajero,
    )
    DetalleAjuste.objects.create(ajuste=ajuste, producto=producto, cantidad=Decimal("5"))
    return ajuste


# ── ViewSets simples (solo list) ──────────────────────────────────────────────

@pytest.mark.django_db
class TestViewSetsSimples:

    def test_stock_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/stock/")
        assert resp.status_code == 200

    def test_movimientos_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/movimientos/")
        assert resp.status_code == 200

    def test_ajustes_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/ajustes/")
        assert resp.status_code == 200

    def test_detalles_ajuste_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/detalles-ajuste/")
        assert resp.status_code == 200

    def test_costos_historicos_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/costos-historicos/")
        assert resp.status_code == 200

    def test_alertas_stock_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/alertas-stock/")
        assert resp.status_code == 200

    def test_lotes_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/lotes/")
        assert resp.status_code == 200

    def test_alertas_vencimiento_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/alertas-vencimiento/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/inventario/stock/")
        assert resp.status_code in (401, 403)


# ── MovimientoStockViewSet — export CSV ───────────────────────────────────────

@pytest.mark.django_db
class TestMovimientoCSV:

    def test_export_csv(self, api_cajero):
        resp = api_cajero.get("/api/v1/inventario/movimientos/", {"formato": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]


# ── AjusteInventarioViewSet ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestAjusteAprobar:

    def test_aprobar_aumento_ok(self, api_admin, ajuste_pendiente_aumento, stock_producto):
        resp = api_admin.post(
            f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/aprobar/"
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "APROBADO"

    def test_aprobar_merma_ok(self, api_admin, ajuste_pendiente_merma):
        resp = api_admin.post(
            f"/api/v1/inventario/ajustes/{ajuste_pendiente_merma.pk}/aprobar/"
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "APROBADO"

    def test_aprobar_merma_sin_stock_falla(self, api_admin, producto, usuario_cajero):
        from apps.inventario.models import AjusteInventario, DetalleAjuste
        ajuste = AjusteInventario.objects.create(
            tipo=AjusteInventario.TipoAjuste.MERMA,
            motivo="Sin stock",
            solicitado_por=usuario_cajero,
        )
        DetalleAjuste.objects.create(ajuste=ajuste, producto=producto, cantidad=Decimal("9999"))
        resp = api_admin.post(f"/api/v1/inventario/ajustes/{ajuste.pk}/aprobar/")
        assert resp.status_code == 400

    def test_aprobar_ya_aprobado_falla(self, api_admin, ajuste_pendiente_aumento, stock_producto):
        api_admin.post(f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/aprobar/")
        resp = api_admin.post(f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/aprobar/")
        assert resp.status_code == 400

    def test_requiere_admin(self, api_cajero, ajuste_pendiente_aumento):
        resp = api_cajero.post(
            f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/aprobar/"
        )
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestAjusteRechazar:

    def test_rechazar_pendiente_ok(self, api_admin, ajuste_pendiente_aumento):
        resp = api_admin.post(
            f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/rechazar/"
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "RECHAZADO"

    def test_rechazar_ya_rechazado_falla(self, api_admin, ajuste_pendiente_aumento):
        api_admin.post(f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/rechazar/")
        resp = api_admin.post(
            f"/api/v1/inventario/ajustes/{ajuste_pendiente_aumento.pk}/rechazar/"
        )
        assert resp.status_code == 400


# ── ReporteStockView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteStock:

    def test_json_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/inventario/reporte-stock/")
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert "productos" in resp.data

    def test_solo_activos_false(self, api_admin):
        resp = api_admin.get("/api/v1/inventario/reporte-stock/", {"solo_activos": "0"})
        assert resp.status_code == 200

    def test_formato_csv(self, api_admin):
        resp = api_admin.get("/api/v1/inventario/reporte-stock/", {"formato": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE INVENTARIO" in resp.content

    def test_csv_con_stock(self, api_admin, stock_producto):
        resp = api_admin.get("/api/v1/inventario/reporte-stock/", {"formato": "csv"})
        assert resp.status_code == 200
        assert b"Agua mineral" in resp.content

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/inventario/reporte-stock/")
        assert resp.status_code in (401, 403)


# ── StockCriticoView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStockCritico:

    def test_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/inventario/stock-critico/")
        assert resp.status_code == 200
        assert "total" in resp.data
        assert "productos" in resp.data

    def test_sin_stock_filter(self, api_admin):
        resp = api_admin.get("/api/v1/inventario/stock-critico/", {"sin_stock": "1"})
        assert resp.status_code == 200

    def test_con_stock_critico_muestra_producto(self, api_admin, categoria, unidad_medida):
        from apps.productos.models import Producto
        from apps.inventario.models import Stock
        p = Producto.objects.create(
            descripcion="Stock Bajo Test",
            categoria=categoria,
            unidad_medida=unidad_medida,
            activo=True,
            requiere_stock=True,
            permite_stock_negativo=False,
            stock_minimo=Decimal("10"),
        )
        Stock.objects.create(producto=p, cantidad=Decimal("2"))
        resp = api_admin.get("/api/v1/inventario/stock-critico/")
        assert resp.status_code == 200
        assert resp.data["total"] >= 1

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/inventario/stock-critico/")
        assert resp.status_code in (401, 403)


# ── ReporteStock con movimientos (días de stock) ──────────────────────────────

@pytest.mark.django_db
class TestReporteStockConMovimientos:

    def test_csv_incluye_dias_stock(self, api_admin, stock_producto, producto, usuario_cajero):
        from apps.inventario.models import MovimientoStock
        MovimientoStock.objects.create(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.VENTA,
            cantidad=Decimal("5"),
            stock_resultante=Decimal("45"),
            autorizado_por=usuario_cajero,
        )
        resp = api_admin.get("/api/v1/inventario/reporte-stock/", {"formato": "csv"})
        assert resp.status_code == 200
        assert b"Agua mineral" in resp.content
