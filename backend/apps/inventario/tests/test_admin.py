"""Tests de admin para la app inventario."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_inventario@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/inventario/stock/",
    "/admin/inventario/movimientostock/",
    "/admin/inventario/ajusteinventario/",
    "/admin/inventario/detalleajuste/",
    "/admin/inventario/costohistorico/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_stock_changelist_con_datos(sa_client, stock_producto):
    """Changelist de Stock con un objeto ejercita display methods."""
    resp = sa_client.get('/admin/inventario/stock/')
    assert resp.status_code == 200
