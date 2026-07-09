"""
Tests para gaps de cobertura en usuarios/views.py.
Cubre: LogoutView (con y sin session_key/refresh_token),
       login por CI/RUC (CustomTokenObtainPairSerializer),
       ReporteAuditoriaView, ReporteIntentosLoginView, ReportePersonalInactivoView.
"""
import pytest
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


# ── ReporteIntentosLoginView ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteIntentosLogin:

    URL = "/api/v1/usuarios/reporte-intentos-login/"

    def test_json_sin_datos(self, api_admin):
        resp = api_admin.get(self.URL)
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert resp.data["resumen"]["total"] == 0

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
        assert len(resp.data["por_ip"]) >= 1
        assert len(resp.data["por_email"]) >= 1

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

    def test_no_admin_retorna_403(self, api_cajero):
        resp = api_cajero.get(self.URL)
        assert resp.status_code == 403

    def test_requiere_autenticacion(self):
        resp = APIClient().get(self.URL)
        assert resp.status_code in (401, 403)
