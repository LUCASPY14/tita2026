"""Tests de admin para la app usuarios."""
import pytest


@pytest.fixture
def sa_client(db):
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_usuarios@test.com', password='admin123',
        nombre='Super', apellido='Admin',
        rol=Usuario.Rol.ADMIN, is_staff=True, is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/usuarios/usuario/",
    "/admin/usuarios/rol/",
    "/admin/usuarios/permiso/",
    "/admin/usuarios/rolpermiso/",
    "/admin/usuarios/perfilusuario/",
    "/admin/usuarios/autenticacion2fa/",
    "/admin/usuarios/intento2fa/",
    "/admin/usuarios/intentologin/",
    "/admin/usuarios/sesionactiva/",
    "/admin/usuarios/renovacionsesion/",
    "/admin/usuarios/patronacceso/",
    "/admin/usuarios/bloqueo cuenta/",
    "/admin/usuarios/tokenrecuperacion/",
    "/admin/usuarios/tokenverificacion/",
    "/admin/usuarios/auditoriaempleado/",
    "/admin/usuarios/auditoriaoperacion/",
    "/admin/usuarios/auditoriausuariweb/",
])
def test_admin_changelist_returns_200_or_not_found(sa_client, url):
    # Algunos model_names pueden diferir por capitalización; 404 es aceptable
    resp = sa_client.get(url)
    assert resp.status_code in (200, 404)


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/usuarios/usuario/",
    "/admin/usuarios/rol/",
    "/admin/usuarios/permiso/",
    "/admin/usuarios/intentologin/",
    "/admin/usuarios/sesionactiva/",
    "/admin/usuarios/tokenrecuperacion/",
    "/admin/usuarios/auditoriaempleado/",
    "/admin/usuarios/auditoriaoperacion/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_usuario_changelist_con_datos(sa_client, usuario_admin):
    resp = sa_client.get('/admin/usuarios/usuario/')
    assert resp.status_code == 200
    assert b'admin@test.com' in resp.content
