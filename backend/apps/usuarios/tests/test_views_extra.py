"""
Tests para gaps de cobertura en usuarios/views.py.
Cubre: LogoutView (con y sin session_key/refresh_token),
       login por CI/RUC (CustomTokenObtainPairSerializer),
       ReporteAuditoriaView, ReporteIntentosLoginView, ReportePersonalInactivoView,
       bloqueo automático de cuenta (BloqueoCuenta + cache).
"""
import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


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


# ── LogoutView ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutView:

    def test_logout_sin_body_retorna_200(self, api_cajero):
        resp = api_cajero.post("/api/v1/usuarios/logout/", {}, format="json")
        # La view retorna None implícitamente (no hay return Response al final
        # del bloque principal) — DRF devuelve 200 con body vacío
        assert resp.status_code == 200

    def test_logout_con_session_key_inactiva_sesion(self, db, usuario_cajero):
        from apps.usuarios.models import SesionActiva
        sesion = SesionActiva.objects.create(
            usuario=usuario_cajero,
            session_key="test-session-key-abc",
            ip_address="127.0.0.1",
            activa=True,
        )
        client = APIClient()
        client.force_authenticate(user=usuario_cajero)
        resp = client.post(
            "/api/v1/usuarios/logout/",
            {"session_key": "test-session-key-abc"},
            format="json",
        )
        assert resp.status_code == 200
        sesion.refresh_from_db()
        assert sesion.activa is False

    def test_logout_con_refresh_token_valido(self, usuario_cajero):
        refresh = RefreshToken.for_user(usuario_cajero)
        client = APIClient()
        client.force_authenticate(user=usuario_cajero)
        resp = client.post(
            "/api/v1/usuarios/logout/",
            {"refresh_token": str(refresh)},
            format="json",
        )
        assert resp.status_code == 200

    def test_logout_con_refresh_token_invalido_no_falla(self, api_cajero):
        resp = api_cajero.post(
            "/api/v1/usuarios/logout/",
            {"refresh_token": "token.invalido.xyz"},
            format="json",
        )
        # El except silencia el error — no debe lanzar 500
        assert resp.status_code == 200

    def test_logout_requiere_autenticacion(self):
        resp = APIClient().post("/api/v1/usuarios/logout/", {}, format="json")
        assert resp.status_code in (401, 403)


# ── Login por CI/RUC ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginCiRuc:

    def test_login_por_ci_resuelve_a_email_portal(self, cliente):
        from apps.usuarios.models import Usuario
        usuario_portal = Usuario.objects.create_user(
            email="portal_ci@test.com",
            password="Test1234!",
            nombre="Portal",
            apellido="CI",
            rol=Usuario.Rol.CLIENTE_WEB,
            cliente=cliente,
        )
        # cliente.ruc_ci == "1234567" (del conftest global)
        resp = APIClient().post(
            "/api/token/",
            {"email": "1234567", "password": "Test1234!"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_login_por_ci_inexistente_falla(self):
        resp = APIClient().post(
            "/api/token/",
            {"email": "9999999", "password": "cualquiera"},
            format="json",
        )
        assert resp.status_code == 401

    def test_login_normal_por_email_sigue_funcionando(self, usuario_cajero):
        resp = APIClient().post(
            "/api/token/",
            {"email": "cajero@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data


# ── ReporteAuditoriaView ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteAuditoria:

    URL = "/api/v1/usuarios/reporte-auditoria/"

    def test_json_sin_datos(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert "detalle" in resp.data

    def test_con_filtros_fecha(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-12-31"})
        assert resp.status_code == 200

    def test_con_filtros_operacion_y_tabla(self, api_admin):
        resp = api_admin.get(self.URL, {
            "operacion": "LOGIN", "tabla": "usuarios", "resultado": "EXITO",
        })
        assert resp.status_code == 200

    def test_no_admin_retorna_403(self, api_cajero):
        resp = api_cajero.get(self.URL)
        assert resp.status_code == 403

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL)
        assert resp.status_code in (401, 403)


# ── AuditoriaOpcionesView ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuditoriaOpciones:

    URL = "/api/v1/usuarios/reporte-auditoria/opciones/"

    def test_devuelve_valores_distintos_y_ordenados(self, api_admin, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion

        AuditoriaOperacion.objects.create(
            usuario=usuario_admin, operacion="LOGIN", resultado="EXITO",
        )
        AuditoriaOperacion.objects.create(
            usuario=usuario_admin, operacion="LOGIN", resultado="EXITO",
        )
        AuditoriaOperacion.objects.create(
            usuario=usuario_admin, operacion="CREAR_USUARIO", resultado="FALLA",
        )

        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["operaciones"] == ["CREAR_USUARIO", "LOGIN"]
        assert resp.data["resultados"] == ["EXITO", "FALLA"]

    def test_sin_datos_devuelve_listas_vacias(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["operaciones"] == []
        assert resp.data["resultados"] == []

    def test_no_admin_retorna_403(self, api_cajero):
        resp = api_cajero.get(self.URL)
        assert resp.status_code == 403

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL)
        assert resp.status_code in (401, 403)


# ── ReporteIntentosLoginView ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteIntentosLogin:

    URL = "/api/v1/usuarios/reporte-intentos-login/"

    def test_json_sin_datos(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert resp.data["resumen"]["total_intentos"] == 0
        assert resp.data["resumen"]["ips_bloqueadas"] == 0

    def test_con_intento_fallido(self, db, api_admin):
        from apps.usuarios.models import IntentoLogin
        IntentoLogin.objects.create(
            email="atacante@evil.com",
            exitoso=False,
            ip_address="1.2.3.4",
            motivo_fallo="Contraseña incorrecta",
        )
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["resumen"]["fallidos"] >= 1
        assert len(resp.data["top_ips"]) >= 1
        assert len(resp.data["top_emails"]) >= 1
        # Verificar shape de top_ips
        ip_row = resp.data["top_ips"][0]
        assert "ip" in ip_row
        assert "exitosos" in ip_row
        assert "fallidos" in ip_row
        assert "bloqueada" in ip_row
        # Verificar shape de top_emails
        email_row = resp.data["top_emails"][0]
        assert "email" in email_row
        assert "fallidos" in email_row
        assert "ultimo_intento" in email_row

    def test_por_motivo_shape(self, db, api_admin):
        from apps.usuarios.models import IntentoLogin
        IntentoLogin.objects.create(
            email="a@b.com", exitoso=False, ip_address="1.1.1.1",
            motivo_fallo="Contraseña incorrecta",
        )
        resp = api_admin.get(self.URL)
        assert len(resp.data["por_motivo"]) >= 1
        m = resp.data["por_motivo"][0]
        assert "motivo" in m
        assert "n" in m

    def test_ip_bloqueada_aparece_en_reporte(self, db, api_admin, usuario_cajero):
        from apps.usuarios.models import IntentoLogin, BloqueoCuenta
        IntentoLogin.objects.create(
            email=usuario_cajero.email, exitoso=False, ip_address="9.9.9.9",
        )
        BloqueoCuenta.objects.create(
            usuario=usuario_cajero, motivo="Test", ip_address="9.9.9.9", estado=True,
        )
        resp = api_admin.get(self.URL)
        assert resp.data["resumen"]["ips_bloqueadas"] >= 1
        fila_bloqueada = next(
            (r for r in resp.data["top_ips"] if r["ip"] == "9.9.9.9"), None
        )
        assert fila_bloqueada is not None
        assert fila_bloqueada["bloqueada"] is True

    def test_filtro_fecha_desde_hasta(self, api_admin):
        resp = api_admin.get(self.URL, {"desde": "2026-01-01", "hasta": "2026-12-31"})
        assert resp.status_code == 200
        assert "tendencia" in resp.data

    def test_tasa_fallo_cero_sin_datos(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.data["resumen"]["tasa_fallo"] == 0

    def test_no_admin_retorna_403(self, api_cajero):
        resp = api_cajero.get(self.URL)
        assert resp.status_code == 403


# ── ReportePersonalInactivoView ───────────────────────────────────────────────

@pytest.mark.django_db
class TestReportePersonalInactivo:

    URL = "/api/v1/usuarios/reporte-personal-inactivo/"

    def test_json_estructura(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert "por_rol" in resp.data
        assert "detalle" in resp.data

    def test_parametro_dias_personalizado(self, api_admin):
        resp = api_admin.get(self.URL, {"dias": "7"})
        assert resp.status_code == 200
        assert resp.data["resumen"]["n_dias"] == 7

    def test_parametro_dias_invalido_usa_default(self, api_admin):
        resp = api_admin.get(self.URL, {"dias": "no-es-numero"})
        assert resp.status_code == 200
        assert resp.data["resumen"]["n_dias"] == 30

    def test_cajero_sin_acceso_aparece_en_detalle(self, api_admin, usuario_cajero):
        resp = api_admin.get(self.URL, {"dias": "1"})
        assert resp.status_code == 200
        emails_detalle = [d["email"] for d in resp.data["detalle"]]
        assert usuario_cajero.email in emails_detalle

    def test_calcula_dias_inactivo_y_resumen(self, api_admin, usuario_cajero):
        from datetime import timedelta
        from django.utils import timezone

        usuario_cajero.ultimo_acceso = timezone.now() - timedelta(days=45)
        usuario_cajero.save(update_fields=["ultimo_acceso"])

        resp = api_admin.get(self.URL, {"dias": "30"})
        assert resp.status_code == 200

        fila = next(d for d in resp.data["detalle"] if d["email"] == usuario_cajero.email)
        assert fila["dias_inactivo"] == 45
        assert fila["usuario_id"] == usuario_cajero.id
        assert fila["nombre"] == "Cajero Test"

        assert resp.data["resumen"]["total_inactivos"] >= 1
        assert resp.data["resumen"]["max_dias_inactivo"] >= 45
        assert resp.data["resumen"]["promedio_dias_inactivo"] >= 0

        fila_rol = next(r for r in resp.data["por_rol"] if r["rol"] == "CAJERO")
        assert fila_rol["n"] >= 1

    def test_no_admin_retorna_403(self, api_cajero):
        resp = api_cajero.get(self.URL)
        assert resp.status_code == 403

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL)
        assert resp.status_code in (401, 403)


# ── Bloqueo automático de cuenta ──────────────────────────────────────────────

_LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-bloqueo",
    }
}
_LOGIN_URL = "/api/token/"


@pytest.mark.django_db
class TestBloqueoCuentaManual:
    """BloqueoCuenta creado a mano → el login lo detecta y devuelve 403."""

    def test_login_rechazado_con_bloqueo_activo(self, usuario_cajero):
        from apps.usuarios.models import BloqueoCuenta
        from django.utils import timezone
        from datetime import timedelta
        BloqueoCuenta.objects.create(
            usuario=usuario_cajero,
            motivo="Bloqueo manual de test",
            fecha_desbloqueo=timezone.now() + timedelta(hours=1),
            estado=True,
        )
        resp = APIClient().post(
            _LOGIN_URL,
            {"email": usuario_cajero.email, "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 403
        assert "bloqueada" in resp.data["detail"].lower()

    def test_bloqueo_expirado_se_limpia_y_permite_login(self, usuario_cajero):
        from apps.usuarios.models import BloqueoCuenta
        from django.utils import timezone
        from datetime import timedelta
        BloqueoCuenta.objects.create(
            usuario=usuario_cajero,
            motivo="Bloqueo vencido",
            fecha_desbloqueo=timezone.now() - timedelta(minutes=1),
            estado=True,
        )
        resp = APIClient().post(
            _LOGIN_URL,
            {"email": usuario_cajero.email, "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        # El bloqueo expirado se marcó como estado=False inline
        assert BloqueoCuenta.objects.filter(usuario=usuario_cajero, estado=False).exists()


@pytest.mark.django_db
class TestBloqueoCuentaAutomatico:
    """N fallos consecutivos → bloqueo automático vía cache."""

    @override_settings(
        CACHES=_LOCMEM_CACHE,
        LOGIN_MAX_INTENTOS=3,
        LOGIN_VENTANA_MINUTOS=15,
        LOGIN_BLOQUEO_MINUTOS=30,
    )
    def test_N_fallos_crean_bloqueo_y_devuelven_429(self, db, usuario_cajero):
        from apps.usuarios.models import BloqueoCuenta
        cache.clear()
        client = APIClient()
        payload = {"email": usuario_cajero.email, "password": "MALA"}

        for i in range(3):
            resp = client.post(_LOGIN_URL, payload, format="json")
            assert resp.status_code == 401, f"Intento {i+1} debería ser 401"

        # El 4° intento debe ser bloqueado por cache (429)
        resp = client.post(_LOGIN_URL, payload, format="json")
        assert resp.status_code == 429

        # Y se creó BloqueoCuenta en DB
        assert BloqueoCuenta.objects.filter(usuario=usuario_cajero, estado=True).exists()
        cache.clear()

    @override_settings(
        CACHES=_LOCMEM_CACHE,
        LOGIN_MAX_INTENTOS=3,
        LOGIN_VENTANA_MINUTOS=15,
        LOGIN_BLOQUEO_MINUTOS=30,
    )
    def test_login_exitoso_limpia_contador(self, db, usuario_cajero):
        """Dos fallos + login exitoso → el contador se borra → otro fallo no bloquea."""
        from apps.usuarios.models import BloqueoCuenta
        cache.clear()
        client = APIClient()
        email = usuario_cajero.email

        # Dos fallos
        for _ in range(2):
            client.post(_LOGIN_URL, {"email": email, "password": "MALA"}, format="json")

        # Login exitoso → limpia contadores
        resp = client.post(_LOGIN_URL, {"email": email, "password": "test1234"}, format="json")
        assert resp.status_code == 200

        # Un fallo después del login exitoso → no bloquea (contador fue borrado)
        resp = client.post(_LOGIN_URL, {"email": email, "password": "MALA"}, format="json")
        assert resp.status_code == 401
        assert not BloqueoCuenta.objects.filter(usuario=usuario_cajero, estado=True).exists()
        cache.clear()
