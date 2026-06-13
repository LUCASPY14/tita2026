"""
Tests de vistas de usuarios.
Cubre: CustomTokenObtainPairView (login), UsuarioViewSet.me,
UsuarioViewSet.cambiar_password, PortalMiHijoView, PortalHistorialCantina,
RecuperarPasswordView, TwoFAEstadoView, TwoFAConfigurarView.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def usuario_portal(db, cliente):
    """CLIENTE_WEB con cliente vinculado para tests del portal."""
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="portal@test.com",
        password="test1234",
        nombre="María",
        apellido="Portal",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente,
    )


@pytest.fixture
def api_portal(api_client, usuario_portal):
    api_client.force_authenticate(user=usuario_portal)
    return api_client


@pytest.fixture
def hijo_portal(db, cliente):
    from apps.clientes.models import Hijo, Grado
    grado, _ = Grado.objects.get_or_create(
        nombre="3er grado",
        defaults={"nivel": 3, "orden": 3, "activo": True},
    )
    return Hijo.objects.create(
        nombre="Sofía",
        apellido="Portal",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


# ── CustomTokenObtainPairView (POST /api/token/) ──────────────────────────────

@pytest.mark.django_db
class TestLogin:

    def test_login_exitoso_devuelve_tokens(self, api_client, usuario_admin):
        resp = api_client.post(
            "/api/token/",
            {"email": "admin@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert "user" in resp.data
        assert resp.data["user"]["email"] == "admin@test.com"

    def test_login_credenciales_incorrectas_401(self, api_client, usuario_admin):
        resp = api_client.post(
            "/api/token/",
            {"email": "admin@test.com", "password": "mal_password"},
            format="json",
        )
        assert resp.status_code == 401

    def test_login_con_2fa_habilitado_devuelve_pre_auth(self, api_client, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin,
            secret_key="JBSWY3DPEHPK3PXP",
            habilitado=True,
        )
        resp = api_client.post(
            "/api/token/",
            {"email": "admin@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data.get("requires_2fa") is True
        assert "pre_auth_token" in resp.data
        assert "access" not in resp.data

    def test_login_cajero_retorna_rol(self, api_client, usuario_cajero):
        resp = api_client.post(
            "/api/token/",
            {"email": "cajero@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["user"]["rol"] == "CAJERO"


# ── UsuarioViewSet.me (GET /api/v1/usuarios/usuarios/me/) ─────────────────────

@pytest.mark.django_db
class TestMe:

    def test_me_retorna_datos_usuario(self, api_admin, usuario_admin):
        resp = api_admin.get("/api/v1/usuarios/usuarios/me/")
        assert resp.status_code == 200
        assert resp.data["email"] == "admin@test.com"
        assert resp.data["rol"] == "ADMIN"
        assert "id" in resp.data
        assert "nombre" in resp.data
        assert "apellido" in resp.data

    def test_me_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/usuarios/usuarios/me/")
        assert resp.status_code in (401, 403)

    def test_me_cajero_devuelve_rol_cajero(self, api_cajero):
        resp = api_cajero.get("/api/v1/usuarios/usuarios/me/")
        assert resp.status_code == 200
        assert resp.data["rol"] == "CAJERO"

    def test_me_portal_devuelve_cliente_id(self, api_portal, cliente):
        resp = api_portal.get("/api/v1/usuarios/usuarios/me/")
        assert resp.status_code == 200
        assert resp.data["cliente_id"] == cliente.pk


# ── UsuarioViewSet.cambiar_password ───────────────────────────────────────────

@pytest.mark.django_db
class TestCambiarPassword:

    def test_cambiar_password_exitoso(self, api_admin, usuario_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/usuarios/cambiar-password/",
            {"password_actual": "test1234", "password_nuevo": "nueva_pass_999"},
            format="json",
        )
        assert resp.status_code == 200
        assert "detail" in resp.data
        usuario_admin.refresh_from_db()
        assert usuario_admin.check_password("nueva_pass_999")

    def test_password_actual_incorrecto_falla(self, api_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/usuarios/cambiar-password/",
            {"password_actual": "mal_pass", "password_nuevo": "nueva_pass_999"},
            format="json",
        )
        assert resp.status_code == 400

    def test_misma_password_falla(self, api_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/usuarios/cambiar-password/",
            {"password_actual": "test1234", "password_nuevo": "test1234"},
            format="json",
        )
        assert resp.status_code == 400

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/usuarios/cambiar-password/",
            {"password_actual": "test1234", "password_nuevo": "nueva"},
            format="json",
        )
        assert resp.status_code in (401, 403)


# ── PortalMiHijoView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalMiHijo:

    def test_retorna_estructura_base(self, api_portal, usuario_portal, cliente):
        resp = api_portal.get("/api/v1/usuarios/portal/mi-hijo/")
        assert resp.status_code == 200
        assert "cliente" in resp.data
        assert "mes" in resp.data
        assert "hijos" in resp.data
        assert resp.data["cliente"]["id"] == cliente.pk

    def test_sin_cliente_vinculado_retorna_400(self, api_cajero):
        resp = api_cajero.get("/api/v1/usuarios/portal/mi-hijo/")
        assert resp.status_code == 400

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/usuarios/portal/mi-hijo/")
        assert resp.status_code in (401, 403)

    def test_con_hijo_incluye_datos(self, api_portal, hijo_portal):
        resp = api_portal.get("/api/v1/usuarios/portal/mi-hijo/")
        assert resp.status_code == 200
        assert len(resp.data["hijos"]) == 1
        hijo_data = resp.data["hijos"][0]
        assert hijo_data["id"] == hijo_portal.pk
        assert "tarjeta" in hijo_data
        assert "consumos_mes" in hijo_data
        assert "cuenta_mensual" in hijo_data


# ── PortalHistorialCantina ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalHistorialCantina:

    def test_sin_hijo_id_retorna_400(self, api_portal):
        resp = api_portal.get("/api/v1/usuarios/portal/historial-cantina/")
        assert resp.status_code == 400

    def test_hijo_no_encontrado_retorna_404(self, api_portal):
        resp = api_portal.get(
            "/api/v1/usuarios/portal/historial-cantina/",
            {"hijo_id": 99999},
        )
        assert resp.status_code == 404

    def test_con_hijo_valido_retorna_estructura(self, api_portal, hijo_portal):
        resp = api_portal.get(
            "/api/v1/usuarios/portal/historial-cantina/",
            {"hijo_id": hijo_portal.pk},
        )
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "next" in resp.data
        assert "results" in resp.data

    def test_sin_cliente_falla(self, api_cajero):
        resp = api_cajero.get(
            "/api/v1/usuarios/portal/historial-cantina/",
            {"hijo_id": 1},
        )
        assert resp.status_code == 400


# ── RecuperarPasswordView ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecuperarPassword:

    def test_email_existente_siempre_devuelve_200(self, api_client, usuario_admin):
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/",
            {"email": "admin@test.com"},
            format="json",
        )
        assert resp.status_code == 200
        assert "detail" in resp.data

    def test_email_inexistente_tambien_200(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/",
            {"email": "noexiste@test.com"},
            format="json",
        )
        assert resp.status_code == 200

    def test_email_invalido_retorna_400(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/",
            {"email": "no_es_email"},
            format="json",
        )
        assert resp.status_code == 400


# ── TwoFAEstadoView ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFAEstado:

    def test_sin_2fa_devuelve_habilitado_false(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/2fa/estado/")
        assert resp.status_code == 200
        assert resp.data["habilitado"] is False

    def test_con_2fa_activo_devuelve_habilitado_true(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin,
            secret_key="JBSWY3DPEHPK3PXP",
            habilitado=True,
        )
        resp = api_admin.get("/api/v1/usuarios/2fa/estado/")
        assert resp.status_code == 200
        assert resp.data["habilitado"] is True

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/usuarios/2fa/estado/")
        assert resp.status_code in (401, 403)


# ── TwoFAConfigurarView ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFAConfigurar:

    def test_configurar_devuelve_uri_y_secret(self, api_admin):
        resp = api_admin.post("/api/v1/usuarios/2fa/configurar/")
        assert resp.status_code == 200
        assert "otp_uri" in resp.data
        assert "secret" in resp.data
        assert "backup_codes" in resp.data
        assert len(resp.data["backup_codes"]) == 8

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.post("/api/v1/usuarios/2fa/configurar/")
        assert resp.status_code in (401, 403)


# ── TOTP helpers (unit tests) ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestTOTPHelpers:

    def test_compute_totp_retorna_6_digitos(self):
        from apps.usuarios.views import _compute_totp, _generate_secret
        secret = _generate_secret()
        code = _compute_totp(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_totp_valida_codigo_correcto(self):
        import time
        from apps.usuarios.views import _compute_totp, _generate_secret, _verify_totp
        secret = _generate_secret()
        now = time.time()
        code = _compute_totp(secret, timestamp=now)
        assert _verify_totp(secret, code) is True

    def test_verify_totp_rechaza_codigo_incorrecto(self):
        from apps.usuarios.views import _generate_secret, _verify_totp
        secret = _generate_secret()
        assert _verify_totp(secret, "000000") is False

    def test_generate_backup_codes_8_codigos(self):
        from apps.usuarios.views import _generate_backup_codes
        codes = _generate_backup_codes()
        assert len(codes) == 8
        assert all(len(c) == 6 for c in codes)


# ── UsuarioViewSet CRUD ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUsuarioViewSetCRUD:

    def test_list_usuarios(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/usuarios/")
        assert resp.status_code == 200

    def test_create_usuario(self, api_admin):
        # Hits get_serializer_class() → UsuarioCreateSerializer (lines 142-144)
        resp = api_admin.post(
            "/api/v1/usuarios/usuarios/",
            {
                "email": "nuevo@test.com",
                "password": "nuevo_pass_123",
                "nombre": "Nuevo",
                "apellido": "Usuario",
                "rol": "CAJERO",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_requiere_admin(self, api_cajero):
        resp = api_cajero.get("/api/v1/usuarios/usuarios/")
        assert resp.status_code in (401, 403)


# ── ViewSets simples ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestViewSetsSimples:

    def test_empleados_list(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/empleados/")
        assert resp.status_code == 200

    def test_roles_list(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/roles/")
        assert resp.status_code == 200

    def test_permisos_list(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/permisos/")
        assert resp.status_code == 200

    def test_roles_permisos_list(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/roles-permisos/")
        assert resp.status_code == 200

    def test_perfiles_list(self, api_admin):
        resp = api_admin.get("/api/v1/usuarios/perfiles/")
        assert resp.status_code == 200


# ── PortalMiHijoView — con hijo+tarjeta+cuenta ───────────────────────────────

@pytest.mark.django_db
class TestPortalMiHijoConDatos:

    def test_con_tarjeta_y_cuenta_retorna_datos(self, api_portal, hijo_portal, cliente):
        from decimal import Decimal
        from datetime import date
        from apps.core.models import Tarjeta
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="PORTAL001",
            hijo=hijo_portal,
            saldo_actual=Decimal("30000"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        hoy = date.today()
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_portal, anio=hoy.year, mes=hoy.month,
            cantidad_almuerzos=3, monto_total=Decimal("45000"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        resp = api_portal.get("/api/v1/usuarios/portal/mi-hijo/")
        assert resp.status_code == 200
        hijos = resp.data["hijos"]
        assert len(hijos) == 1
        assert hijos[0]["tarjeta"]["nro_tarjeta"] == "PORTAL001"
        assert hijos[0]["cuenta_mensual"]["cantidad_almuerzos"] == 3


# ── PortalHistorialConsumos ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalHistorialConsumos:

    def test_sin_cliente_retorna_400(self, api_cajero):
        resp = api_cajero.get("/api/v1/usuarios/portal/historial-consumos/")
        assert resp.status_code == 400

    def test_hijo_no_encontrado_retorna_404(self, api_portal):
        resp = api_portal.get(
            "/api/v1/usuarios/portal/historial-consumos/",
            {"hijo_id": 99999},
        )
        assert resp.status_code == 404

    def test_con_hijo_valido_retorna_estructura(self, api_portal, hijo_portal):
        from datetime import date
        resp = api_portal.get(
            "/api/v1/usuarios/portal/historial-consumos/",
            {"hijo_id": hijo_portal.pk, "anio": str(date.today().year), "mes": str(date.today().month)},
        )
        assert resp.status_code == 200
        assert "consumos" in resp.data
        assert "total" in resp.data
        assert "hijo" in resp.data

    def test_sin_hijo_id_retorna_404(self, api_portal):
        # hijo_id=None → hijo not found (None filter returns nothing)
        resp = api_portal.get("/api/v1/usuarios/portal/historial-consumos/")
        assert resp.status_code == 404


# ── PortalMisFacturas ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalMisFacturas:

    def test_con_cliente_retorna_lista(self, api_portal):
        resp = api_portal.get("/api/v1/usuarios/portal/mis-facturas/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_sin_cliente_retorna_400(self, api_cajero):
        resp = api_cajero.get("/api/v1/usuarios/portal/mis-facturas/")
        assert resp.status_code == 400


# ── RecuperarPasswordView — CLIENTE_WEB genera enlace portal ─────────────────

@pytest.mark.django_db
class TestRecuperarPasswordClienteWeb:

    def test_cliente_web_genera_enlace_portal(self, api_client, usuario_portal):
        # Hits line 456 (portal/reset-password link for CLIENTE_WEB)
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/",
            {"email": "portal@test.com"},
            format="json",
        )
        assert resp.status_code == 200


# ── ConfirmarPasswordView ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestConfirmarPassword:

    def test_uid_invalido_retorna_400(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/confirmar/",
            {"uid": "uid_invalido", "token": "token_invalido", "password_nuevo": "nueva_pass_123"},
            format="json",
        )
        assert resp.status_code == 400

    def test_token_invalido_retorna_400(self, api_client, usuario_admin):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(usuario_admin.pk))
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/confirmar/",
            {"uid": uid, "token": "token-invalido-xxx", "password_nuevo": "nueva_pass_123"},
            format="json",
        )
        assert resp.status_code == 400

    def test_token_valido_cambia_password(self, api_client, usuario_admin):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(usuario_admin.pk))
        token = default_token_generator.make_token(usuario_admin)
        resp = api_client.post(
            "/api/v1/usuarios/recuperar-password/confirmar/",
            {"uid": uid, "token": token, "password_nuevo": "nueva_pass_segura_999"},
            format="json",
        )
        assert resp.status_code == 200
        assert "detail" in resp.data


# ── TwoFAActivarView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFAActivar:

    def test_sin_configurar_retorna_400(self, api_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/activar/",
            {"codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_codigo_invalido_retorna_400(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        from apps.usuarios.views import _generate_secret
        secret = _generate_secret()
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key=secret, habilitado=False,
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/activar/",
            {"codigo": "000000"},
            format="json",
        )
        assert resp.status_code == 400

    def test_codigo_valido_activa_2fa(self, api_admin, usuario_admin):
        import time
        from apps.usuarios.models import Autenticacion2FA
        from apps.usuarios.views import _generate_secret, _compute_totp
        secret = _generate_secret()
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key=secret, habilitado=False,
        )
        codigo = _compute_totp(secret, timestamp=time.time())
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/activar/",
            {"codigo": codigo},
            format="json",
        )
        assert resp.status_code == 200

    def test_ya_activo_retorna_400(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="JBSWY3DPEHPK3PXP", habilitado=True,
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/activar/",
            {"codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400


# ── TwoFAVerificarView ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFAVerificar:

    def test_sin_configurar_retorna_400(self, api_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/verificar/",
            {"codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_no_activo_retorna_400(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="JBSWY3DPEHPK3PXP", habilitado=False,
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/verificar/",
            {"codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_codigo_invalido_retorna_400(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="JBSWY3DPEHPK3PXP", habilitado=True,
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/verificar/",
            {"codigo": "000000"},
            format="json",
        )
        assert resp.status_code == 400

    def test_backup_code_valido_retorna_200(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin,
            secret_key="JBSWY3DPEHPK3PXP",
            habilitado=True,
            backup_codes=["AABBCC"],
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/verificar/",
            {"codigo": "aabbcc"},  # lowercase → upper en la vista
            format="json",
        )
        assert resp.status_code == 200

    def test_totp_valido_retorna_200(self, api_admin, usuario_admin):
        import time
        from apps.usuarios.models import Autenticacion2FA
        from apps.usuarios.views import _generate_secret, _compute_totp
        secret = _generate_secret()
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key=secret, habilitado=True, backup_codes=[],
        )
        codigo = _compute_totp(secret, timestamp=time.time())
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/verificar/",
            {"codigo": codigo},
            format="json",
        )
        assert resp.status_code == 200


# ── TwoFADesactivarView ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFADesactivar:

    def test_sin_configurar_retorna_400(self, api_admin):
        resp = api_admin.post("/api/v1/usuarios/2fa/desactivar/")
        assert resp.status_code == 400

    def test_desactiva_propio_2fa(self, api_admin, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="JBSWY3DPEHPK3PXP", habilitado=True,
        )
        resp = api_admin.post("/api/v1/usuarios/2fa/desactivar/")
        assert resp.status_code == 200

    def test_admin_desactiva_otro_usuario(self, api_admin, usuario_cajero):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_cajero, secret_key="JBSWY3DPEHPK3PXP", habilitado=True,
        )
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/desactivar/",
            {"usuario_id": usuario_cajero.pk},
            format="json",
        )
        assert resp.status_code == 200

    def test_admin_desactiva_usuario_inexistente_retorna_404(self, api_admin):
        resp = api_admin.post(
            "/api/v1/usuarios/2fa/desactivar/",
            {"usuario_id": 99999},
            format="json",
        )
        assert resp.status_code == 404


# ── TwoFALoginVerificarView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestTwoFALoginVerificar:

    def _get_pre_auth_token(self, user_id):
        from django.core import signing
        return signing.dumps({"user_id": user_id}, salt="2fa-pre-auth")

    def test_sin_token_retorna_400(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_token_invalido_retorna_400(self, api_client):
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"pre_auth_token": "token_invalido", "codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_sin_2fa_configurado_retorna_400(self, api_client, usuario_admin):
        token = self._get_pre_auth_token(usuario_admin.pk)
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"pre_auth_token": token, "codigo": "123456"},
            format="json",
        )
        assert resp.status_code == 400

    def test_codigo_invalido_retorna_400(self, api_client, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="JBSWY3DPEHPK3PXP", habilitado=True, backup_codes=[],
        )
        token = self._get_pre_auth_token(usuario_admin.pk)
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"pre_auth_token": token, "codigo": "000000"},
            format="json",
        )
        assert resp.status_code == 400

    def test_backup_code_valido_retorna_jwt(self, api_client, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        Autenticacion2FA.objects.create(
            usuario=usuario_admin,
            secret_key="JBSWY3DPEHPK3PXP",
            habilitado=True,
            backup_codes=["AABBCC"],
        )
        token = self._get_pre_auth_token(usuario_admin.pk)
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"pre_auth_token": token, "codigo": "AABBCC"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_totp_valido_retorna_jwt(self, api_client, usuario_admin):
        import time
        from apps.usuarios.models import Autenticacion2FA
        from apps.usuarios.views import _generate_secret, _compute_totp
        secret = _generate_secret()
        Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key=secret, habilitado=True, backup_codes=[],
        )
        codigo = _compute_totp(secret, timestamp=time.time())
        token = self._get_pre_auth_token(usuario_admin.pk)
        resp = api_client.post(
            "/api/v1/usuarios/2fa/login/",
            {"pre_auth_token": token, "codigo": codigo},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data


# ── PortalHistorialCantina — con resultados ───────────────────────────────────

@pytest.mark.django_db
class TestPortalHistorialCantinaConVentas:

    def test_con_ventas_retorna_resultados(self, api_portal, hijo_portal, usuario_cajero, cliente, producto):
        from apps.ventas.models import Venta, DetalleVenta
        from decimal import Decimal
        venta = Venta.objects.create(
            cliente=cliente,
            hijo=hijo_portal,
            estado=Venta.Estado.ACTIVA,
            monto_total=Decimal("5000"),
            cajero=usuario_cajero,
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("5000"),
            subtotal=Decimal("5000"),
        )
        resp = api_portal.get(
            "/api/v1/usuarios/portal/historial-cantina/",
            {"hijo_id": hijo_portal.pk},
        )
        assert resp.status_code == 200
        assert resp.data["count"] >= 1
