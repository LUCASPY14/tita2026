"""Tests de admin para la app ventas."""
import pytest
from decimal import Decimal


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_ventas@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/ventas/venta/",
    "/admin/ventas/pagoventa/",
    "/admin/ventas/aplicacionpago/",
    "/admin/ventas/notacredito/",
    "/admin/ventas/detallenotacredito/",
    "/admin/ventas/condicionventa/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
class TestVentaAdminDisplay:

    def test_estado_badge_activa(self, sa_client):
        from apps.ventas.admin import VentaAdmin
        from apps.ventas.models import Venta
        from django.contrib import admin as dj_admin
        a = VentaAdmin(Venta, dj_admin.site)
        venta = Venta(estado=Venta.Estado.ACTIVA, monto_total=Decimal('10000'))
        result = str(a.estado_badge(venta))
        assert result  # devuelve algo (HTML o string)

    def test_monto_total_display_format(self, sa_client):
        from apps.ventas.admin import VentaAdmin
        from apps.ventas.models import Venta
        from django.contrib import admin as dj_admin
        a = VentaAdmin(Venta, dj_admin.site)
        venta = Venta(monto_total=Decimal('25000'))
        result = a.monto_total_display(venta)
        assert '₲' in result or '25' in result
