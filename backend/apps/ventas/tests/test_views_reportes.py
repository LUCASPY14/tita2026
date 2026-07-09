"""
Tests para ReporteVentasProductoView y ReporteVentasCajeroView.
Cubre: parámetros faltantes (400), JSON OK, formatos CSV y PDF.
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
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Reportes Test", activo=True)


@pytest.fixture
def medio_pago(db):
    from apps.core.models import MedioPago
    return MedioPago.objects.create(descripcion="Efectivo Test", activo=True)


@pytest.fixture
def venta_hoy(db, cliente, producto, usuario_cajero, caja, medio_pago):
    """Crea una venta activa de hoy para que aparezca en los reportes."""
    from apps.ventas.models import Venta, DetalleVenta
    venta = Venta.objects.create(
        cliente=cliente,
        caja=caja,
        cajero=usuario_cajero,
        medio_pago=medio_pago,
        monto_total=Decimal("10000"),
        estado=Venta.Estado.ACTIVA,
    )
    DetalleVenta.objects.create(
        venta=venta,
        producto=producto,
        cantidad=Decimal("2"),
        precio_unitario=Decimal("5000"),
        subtotal=Decimal("10000"),
    )
    return venta


# ── ReporteVentasProductoView ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteVentasProducto:

    URL = "/api/v1/ventas/reporte-productos/"

    def test_sin_parametros_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_solo_desde_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01"})
        assert resp.status_code == 400

    def test_json_sin_ventas(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 200
        assert "productos" in resp.data
        assert "total_monto" in resp.data

    def test_json_con_venta(self, api_admin, venta_hoy):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy})
        assert resp.status_code == 200
        assert resp.data["total_monto"] >= 0

    def test_csv_retorna_content_type_csv(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "csv"
        })
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE VENTAS POR PRODUCTO" in resp.content

    def test_csv_con_venta_incluye_producto(self, api_admin, venta_hoy, producto):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {
            "desde": hoy, "hasta": hoy, "formato": "csv"
        })
        assert resp.status_code == 200
        assert producto.descripcion.encode() in resp.content

    def test_pdf_retorna_content_type_pdf(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "pdf"
        })
        assert resp.status_code == 200
        assert "application/pdf" in resp["Content-Type"]

    def test_no_staff_no_puede_acceder(self, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="cliente_reporte@test.com", password="x",
            nombre="C", apellido="W",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 403


# ── ReporteVentasCajeroView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteVentasCajero:

    URL = "/api/v1/ventas/reporte-cajeros/"

    def test_sin_parametros_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_solo_hasta_retorna_400(self, api_admin):
        resp = api_admin.get(self.URL, {"hasta": "2026-12-31"})
        assert resp.status_code == 400

    def test_json_sin_ventas(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 200
        assert "cajeros" in resp.data
        assert "total_monto" in resp.data

    def test_json_con_venta(self, api_admin, venta_hoy):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {"desde": hoy, "hasta": hoy})
        assert resp.status_code == 200
        assert len(resp.data["cajeros"]) >= 1

    def test_csv_retorna_content_type_csv(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "csv"
        })
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE VENTAS POR CAJERO" in resp.content

    def test_csv_con_venta_incluye_cajero(self, api_admin, venta_hoy, usuario_cajero):
        from django.utils import timezone
        hoy = timezone.now().date().isoformat()
        resp = api_admin.get(self.URL, {
            "desde": hoy, "hasta": hoy, "formato": "csv"
        })
        assert resp.status_code == 200
        assert usuario_cajero.email.encode() in resp.content

    def test_pdf_retorna_content_type_pdf(self, api_admin):
        resp = api_admin.get(self.URL, {
            "desde": "2026-01-01", "hasta": "2026-01-31", "formato": "pdf"
        })
        assert resp.status_code == 200
        assert "application/pdf" in resp["Content-Type"]

    def test_cliente_web_no_puede_acceder(self, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="cliente_cajero@test.com", password="x",
            nombre="C", apellido="W",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-01-31"})
        assert resp.status_code == 403
