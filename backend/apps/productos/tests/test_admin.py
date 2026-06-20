"""Tests de admin para la app productos."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_productos@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/productos/categoria/",
    "/admin/productos/producto/",
    "/admin/productos/unidadmedida/",
    "/admin/productos/listaprecio/",
    "/admin/productos/precioporlista/",
    "/admin/productos/historicoprecio/",
    "/admin/productos/impuesto/",
    "/admin/productos/productoimpuesto/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_producto_changelist_con_datos(sa_client, producto):
    """Changelist con un Producto ejercita todos los list_display methods."""
    resp = sa_client.get('/admin/productos/producto/')
    assert resp.status_code == 200
    assert 'Agua mineral'.encode() in resp.content
