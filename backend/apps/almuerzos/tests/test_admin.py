"""Tests de admin para la app almuerzos."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_almuerzos@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/almuerzos/precioalmuerzo/",
    "/admin/almuerzos/tipoalmuerzo/",
    "/admin/almuerzos/planalmuerzo/",
    "/admin/almuerzos/suscripcionalmuerzo/",
    "/admin/almuerzos/registroconsumoalmuerzo/",
    "/admin/almuerzos/cuentaalmuerzomensual/",
    "/admin/almuerzos/pagocuentaalmuerzo/",
    "/admin/almuerzos/alergeno/",
    "/admin/almuerzos/productoalergeno/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200
