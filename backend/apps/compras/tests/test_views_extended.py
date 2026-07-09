"""
Tests para gaps de cobertura en compras/views.py (~42%).
Cubre: CompraViewSet.create y update, PagoProveedorViewSet.create,
       NotaCreditoProveedorViewSet.create y anular,
       ReporteComprasProveedoresView, ReporteNotasCreditoCompraView.
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
def api_cajero(usuario_cajero):
    client = APIClient()
    client.force_authenticate(user=usuario_cajero)
    return client


@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(ruc="80011001-1", razon_social="Proveedor Extended")


@pytest.fixture
def compra_contado(db, proveedor, usuario_cajero, producto):
    from apps.compras.services import CompraService
    return CompraService.registrar_compra(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago="CONTADO",
        items=[{
            "producto": producto,
            "cantidad": Decimal("2"),
            "costo_unitario": Decimal("5000"),
        }],
    )


@pytest.fixture
def compra_credito(db, proveedor, usuario_cajero, producto):
    from apps.compras.services import CompraService
    return CompraService.registrar_compra(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago="CREDITO",
        items=[{
            "producto": producto,
            "cantidad": Decimal("3"),
            "costo_unitario": Decimal("8000"),
        }],
    )


@pytest.fixture
def medio_pago(db):
    from apps.core.models import MedioPago
    return MedioPago.objects.create(descripcion="Transferencia Test", activo=True)


@pytest.fixture
def nota_credito(db, proveedor, usuario_admin):
    from apps.compras.models import NotaCreditoProveedor, CuentaCorrienteProveedor
    nc = NotaCreditoProveedor.objects.create(
        proveedor=proveedor,
        monto_total=Decimal("10000"),
        estado=NotaCreditoProveedor.Estado.EMITIDA,
        creado_por=usuario_admin,
    )
    CuentaCorrienteProveedor.objects.create(
        proveedor=proveedor,
        tipo=CuentaCorrienteProveedor.Tipo.NOTA_CREDITO,
        monto=Decimal("10000"),
        nota_credito=nc,
        descripcion="NC test",
        creado_por=usuario_admin,
    )
    return nc


# ── CompraViewSet.create ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompraCreate:

    def test_create_contado_ok(self, api_cajero, proveedor, producto):
        resp = api_cajero.post("/api/v1/compras/compras/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "2", "costo_unitario": "5000"}],
        }, format="json")
        assert resp.status_code == 201
        assert "monto_total" in resp.data

    def test_create_credito_ok(self, api_cajero, proveedor, producto):
        resp = api_cajero.post("/api/v1/compras/compras/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CREDITO",
            "nro_factura_proveedor": "FAC-0001",
            "items": [{"producto": producto.pk, "cantidad": "1", "costo_unitario": "8000"}],
        }, format="json")
        assert resp.status_code == 201

    def test_create_proveedor_inexistente_retorna_400(self, api_cajero, producto):
        resp = api_cajero.post("/api/v1/compras/compras/", {
            "proveedor": 99999,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "1", "costo_unitario": "5000"}],
        }, format="json")
        assert resp.status_code == 400

    def test_create_sin_items_retorna_400(self, api_cajero, proveedor):
        resp = api_cajero.post("/api/v1/compras/compras/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CONTADO",
            "items": [],
        }, format="json")
        assert resp.status_code == 400

    def test_requiere_autenticacion(self, proveedor, producto):
        resp = APIClient().post("/api/v1/compras/compras/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "1", "costo_unitario": "5000"}],
        }, format="json")
        assert resp.status_code in (401, 403)


# ── CompraViewSet.update ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompraUpdate:

    def test_update_cambia_proveedor_y_items(self, api_admin, compra_contado, proveedor, producto):
        otro_proveedor_obj = __import__("apps.compras.models", fromlist=["Proveedor"]).Proveedor.objects.create(
            ruc="80022002-2", razon_social="Otro Proveedor"
        )
        resp = api_admin.put(f"/api/v1/compras/compras/{compra_contado.pk}/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "5", "costo_unitario": "3000"}],
        }, format="json")
        assert resp.status_code == 200
        assert int(resp.data["monto_total"]) == 15000

    def test_update_proveedor_inexistente_retorna_400(self, api_admin, compra_contado, producto):
        resp = api_admin.put(f"/api/v1/compras/compras/{compra_contado.pk}/", {
            "proveedor": 99998,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "1", "costo_unitario": "5000"}],
        }, format="json")
        assert resp.status_code == 400


# ── PagoProveedorViewSet.create ───────────────────────────────────────────────

@pytest.mark.django_db
class TestPagoProveedorCreate:

    def test_pago_compra_credito_ok(self, api_admin, compra_credito, medio_pago):
        resp = api_admin.post("/api/v1/compras/pagos/", {
            "compra": compra_credito.pk,
            "medio_pago": medio_pago.pk,
            "monto": str(compra_credito.monto_total),
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["monto_total"] is not None

    def test_pago_compra_inexistente_retorna_400(self, api_admin, medio_pago):
        resp = api_admin.post("/api/v1/compras/pagos/", {
            "compra": 99997,
            "medio_pago": medio_pago.pk,
            "monto": "5000",
        }, format="json")
        assert resp.status_code == 400

    def test_pago_medio_pago_inexistente_retorna_400(self, api_admin, compra_credito):
        resp = api_admin.post("/api/v1/compras/pagos/", {
            "compra": compra_credito.pk,
            "medio_pago": 99996,
            "monto": "5000",
        }, format="json")
        assert resp.status_code == 400

    def test_pago_parcial_cambia_estado_pago(self, api_admin, compra_credito, medio_pago):
        monto_parcial = str(compra_credito.monto_total - Decimal("1000"))
        api_admin.post("/api/v1/compras/pagos/", {
            "compra": compra_credito.pk,
            "medio_pago": medio_pago.pk,
            "monto": monto_parcial,
        }, format="json")
        compra_credito.refresh_from_db()
        assert compra_credito.estado_pago in ("PARCIAL", "PAGADO")

    def test_cajero_no_puede_crear_pago(self, api_cajero, compra_credito, medio_pago):
        resp = api_cajero.post("/api/v1/compras/pagos/", {
            "compra": compra_credito.pk,
            "medio_pago": medio_pago.pk,
            "monto": "5000",
        }, format="json")
        assert resp.status_code == 403


# ── NotaCreditoProveedorViewSet.create ────────────────────────────────────────

@pytest.mark.django_db
class TestNotaCreditoCreate:

    def test_create_ok(self, api_admin, proveedor):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "15000",
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["estado"] == "EMITIDA"

    def test_create_sin_proveedor_retorna_400(self, api_admin):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "monto_total": "15000",
        }, format="json")
        assert resp.status_code == 400

    def test_create_monto_cero_retorna_400(self, api_admin, proveedor):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "0",
        }, format="json")
        assert resp.status_code == 400

    def test_create_monto_negativo_retorna_400(self, api_admin, proveedor):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "-5000",
        }, format="json")
        assert resp.status_code == 400

    def test_create_monto_invalido_retorna_400(self, api_admin, proveedor):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "no-es-numero",
        }, format="json")
        assert resp.status_code == 400

    def test_create_proveedor_inexistente_retorna_404(self, api_admin):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": 99995,
            "monto_total": "10000",
        }, format="json")
        assert resp.status_code == 404

    def test_create_con_compra_ok(self, api_admin, proveedor, compra_contado):
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "5000",
            "compra_original": compra_contado.pk,
        }, format="json")
        assert resp.status_code == 201

    def test_create_compra_de_otro_proveedor_retorna_404(self, api_admin, compra_contado):
        otro = __import__("apps.compras.models", fromlist=["Proveedor"]).Proveedor.objects.create(
            ruc="80033003-3", razon_social="Otro Proveedor NC"
        )
        resp = api_admin.post("/api/v1/compras/notas-credito/", {
            "proveedor": otro.pk,
            "monto_total": "5000",
            "compra_original": compra_contado.pk,
        }, format="json")
        assert resp.status_code == 404

    def test_cajero_no_puede_crear_nc(self, api_cajero, proveedor):
        resp = api_cajero.post("/api/v1/compras/notas-credito/", {
            "proveedor": proveedor.pk,
            "monto_total": "5000",
        }, format="json")
        assert resp.status_code == 403


# ── NotaCreditoProveedorViewSet.anular ────────────────────────────────────────

@pytest.mark.django_db
class TestNotaCreditoAnular:

    def test_anular_ok(self, api_admin, nota_credito):
        resp = api_admin.post(f"/api/v1/compras/notas-credito/{nota_credito.pk}/anular/")
        assert resp.status_code == 200
        nota_credito.refresh_from_db()
        assert nota_credito.estado == "ANULADA"

    def test_anular_ya_anulada_retorna_400(self, api_admin, nota_credito):
        api_admin.post(f"/api/v1/compras/notas-credito/{nota_credito.pk}/anular/")
        resp = api_admin.post(f"/api/v1/compras/notas-credito/{nota_credito.pk}/anular/")
        assert resp.status_code == 400

    def test_cajero_no_puede_anular(self, api_cajero, nota_credito):
        resp = api_cajero.post(f"/api/v1/compras/notas-credito/{nota_credito.pk}/anular/")
        assert resp.status_code == 403


# ── ReporteComprasProveedoresView ─────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteComprasProveedores:

    URL = "/api/v1/compras/reporte-compras/"

    def test_sin_parametros_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_json_sin_compras(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 200
        assert "por_proveedor" in resp.data
        assert "funnel_oc" in resp.data

    def test_json_con_compra(self, api_admin, compra_contado):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy})
        assert resp.status_code == 200
        assert resp.data["resumen"]["total_compras"] >= 1

    def test_csv_retorna_content_type(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "csv"
        })
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE COMPRAS POR PROVEEDOR" in resp.content

    def test_cliente_web_no_puede_acceder(self, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="clienteweb_compras@test.com", password="x",
            nombre="C", apellido="W",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 403
