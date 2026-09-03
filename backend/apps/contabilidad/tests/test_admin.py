"""Tests de admin para la app contabilidad."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_contabilidad@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/contabilidad/caja/",
    "/admin/contabilidad/cierrecaja/",
    "/admin/contabilidad/movimientocaja/",
    "/admin/contabilidad/factura/",
    "/admin/contabilidad/datosempresa/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_factura_admin_no_permite_agregar(sa_client):
    """No se crean facturas a mano: deben salir de /facturas/emitir/ con IVA calculado."""
    resp = sa_client.get("/admin/contabilidad/factura/add/")
    assert resp.status_code == 403
