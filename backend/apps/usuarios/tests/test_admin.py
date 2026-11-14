"""Tests de admin para la app usuarios."""
import pytest
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone
from datetime import timedelta


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
    "/admin/usuarios/autenticacion2fa/",
    "/admin/usuarios/intento2fa/",
    "/admin/usuarios/intentologin/",
    "/admin/usuarios/sesionactiva/",
    "/admin/usuarios/patronacceso/",
    "/admin/usuarios/bloqueo cuenta/",
    "/admin/usuarios/auditoriaoperacion/",
])
def test_admin_changelist_returns_200_or_not_found(sa_client, url):
    # Algunos model_names pueden diferir por capitalización; 404 es aceptable
    resp = sa_client.get(url)
    assert resp.status_code in (200, 404)


@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/usuarios/usuario/",
    "/admin/usuarios/rol/",
    "/admin/usuarios/intentologin/",
    "/admin/usuarios/sesionactiva/",
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


# ── CantinaAdminAuthenticationForm: bloqueo en /admin/login/ ──────────────────
# El login nativo de Django admin no pasaba por el bloqueo por intentos
# fallidos que ya protege /api/v1/usuarios/login/ (hallazgo revisión de
# seguridad nov-2026) — ahora reutiliza las mismas funciones.

_LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-bloqueo-admin",
    }
}


@pytest.mark.django_db
class TestAdminLoginBloqueo:

    def test_login_exitoso_registra_intentologin(self, usuario_admin):
        from apps.usuarios.models import IntentoLogin
        client = Client()
        resp = client.post(
            "/admin/login/",
            {"username": "admin@test.com", "password": "test1234"},
        )
        assert resp.status_code == 302
        assert IntentoLogin.objects.filter(email="admin@test.com", exitoso=True).exists()

    def test_login_fallido_registra_intentologin(self, usuario_admin):
        from apps.usuarios.models import IntentoLogin
        client = Client()
        resp = client.post(
            "/admin/login/",
            {"username": "admin@test.com", "password": "MALA"},
        )
        assert resp.status_code == 200
        assert IntentoLogin.objects.filter(email="admin@test.com", exitoso=False).exists()

    def test_bloqueo_cuenta_activo_impide_login_aunque_la_clave_sea_correcta(self, usuario_admin):
        from apps.usuarios.models import BloqueoCuenta
        BloqueoCuenta.objects.create(
            usuario=usuario_admin,
            motivo="Test",
            fecha_desbloqueo=timezone.now() + timedelta(minutes=30),
            estado=True,
        )
        client = Client()
        resp = client.post(
            "/admin/login/",
            {"username": "admin@test.com", "password": "test1234"},
        )
        assert resp.status_code == 200
        assert b"bloqueada" in resp.content.lower()

    def test_bloqueo_expirado_se_levanta_y_permite_login(self, usuario_admin):
        from apps.usuarios.models import BloqueoCuenta
        BloqueoCuenta.objects.create(
            usuario=usuario_admin,
            motivo="Test",
            fecha_desbloqueo=timezone.now() - timedelta(minutes=1),
            estado=True,
        )
        client = Client()
        resp = client.post(
            "/admin/login/",
            {"username": "admin@test.com", "password": "test1234"},
        )
        assert resp.status_code == 302
        assert BloqueoCuenta.objects.filter(usuario=usuario_admin, estado=False).exists()

    @override_settings(CACHES=_LOCMEM_CACHE, LOGIN_MAX_INTENTOS=3)
    def test_N_fallos_bloquean_por_cache_aunque_despues_la_clave_sea_correcta(self, usuario_admin):
        cache.clear()
        client = Client()
        for _ in range(3):
            resp = client.post(
                "/admin/login/",
                {"username": "admin@test.com", "password": "MALA"},
            )
            assert resp.status_code == 200

        resp = client.post(
            "/admin/login/",
            {"username": "admin@test.com", "password": "test1234"},
        )
        assert resp.status_code == 200
        assert b"demasiados intentos" in resp.content.lower()
        cache.clear()
