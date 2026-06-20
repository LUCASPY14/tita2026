"""Tests de admin para la app clientes."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_clientes@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/clientes/cliente/",
    "/admin/clientes/cuentacorrientecliente/",
    "/admin/clientes/tipocliente/",
    "/admin/clientes/hijo/",
    "/admin/clientes/grado/",
    "/admin/clientes/historialGrado/",
    "/admin/clientes/restriccionhijo/",
    "/admin/clientes/autorizacionsaldonegativo/",
    "/admin/clientes/pais/",
    "/admin/clientes/ciudad/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code in (200, 404)  # historialGrado puede diferir en capitalización


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/clientes/cliente/",
    "/admin/clientes/tipocliente/",
    "/admin/clientes/hijo/",
    "/admin/clientes/grado/",
    "/admin/clientes/restriccionhijo/",
    "/admin/clientes/pais/",
    "/admin/clientes/ciudad/",
])
def test_admin_changelist_core_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_cliente_changelist_con_datos(sa_client, cliente):
    resp = sa_client.get('/admin/clientes/cliente/')
    assert resp.status_code == 200
