"""
Tests de WebAuthn (huella / Face ID) — portal de padres.
Cubre: registrar-opciones, registrar-verificar, login-opciones,
login-verificar, desactivar, y los flags tiene_webauthn en login/me/serializer.

Las respuestas del navegador (RegistrationCredential/AuthenticationCredential)
no se pueden generar en un test sin un authenticator real, así que se mockean
las funciones verify_* de la librería — se testea la lógica de la vista
(challenge en cache, guardado del modelo, permisos, errores), no la
criptografía de la librería en sí (eso ya lo prueba su propio test suite).
"""
import types
from unittest.mock import patch

import pytest
from django.core.cache import cache as django_cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.usuarios.models import Usuario, CredencialWebAuthn

WEBAUTHN_BASE = "/api/v1/usuarios/webauthn/"


# backend.settings.test usa DummyCache (no-op) — acá el challenge SÍ necesita
# sobrevivir entre el request de "opciones" y el de "verificar", así que estos
# tests fuerzan un cache real en vez del que usa el resto de la suite. Se limpia
# antes de cada uso para que el contador de LoginRateThrottle (también en cache)
# no se acumule entre tests y termine devolviendo 429.
@pytest.fixture
def cache_real():
    with override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "test-webauthn"}}
    ):
        django_cache.clear()
        yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def usuario_portal(db):
    return Usuario.objects.create_user(
        email="mama@test.com",
        password="test1234",
        nombre="Marta",
        apellido="Portal",
        rol=Usuario.Rol.CLIENTE_WEB,
    )


@pytest.fixture
def usuario_admin(db):
    return Usuario.objects.create_user(
        email="admin@test.com",
        password="test1234",
        nombre="Admin",
        apellido="Tita",
        rol=Usuario.Rol.ADMIN,
    )


@pytest.fixture
def api_portal(api_client, usuario_portal):
    api_client.force_authenticate(user=usuario_portal)
    return api_client


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def credencial(db, usuario_portal):
    return CredencialWebAuthn.objects.create(
        usuario=usuario_portal,
        credential_id="Y3JlZGVudGlhbC1pZC0x",  # base64url arbitrario
        public_key="cHVibGljLWtleS0x",
        sign_count=5,
        nombre_dispositivo="iPhone de prueba",
    )


def _pre_auth_token(user):
    from django.core import signing
    return signing.dumps({"user_id": user.id_usuario}, salt="2fa-pre-auth")


# ── WebAuthnRegistrarOpcionesView ──────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarOpciones:

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.post(f"{WEBAUTHN_BASE}registrar-opciones/")
        assert resp.status_code in (401, 403)

    def test_devuelve_opciones_validas(self, api_portal):
        resp = api_portal.post(f"{WEBAUTHN_BASE}registrar-opciones/")
        assert resp.status_code == 200
        assert "challenge" in resp.data
        assert "rp" in resp.data
        assert resp.data["rp"]["id"]

    def test_excluye_credenciales_existentes(self, api_portal, credencial):
        resp = api_portal.post(f"{WEBAUTHN_BASE}registrar-opciones/")
        assert resp.status_code == 200
        ids_excluidos = [c["id"] for c in resp.data.get("excludeCredentials", [])]
        assert credencial.credential_id in ids_excluidos


# ── WebAuthnRegistrarVerificarView ─────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarVerificar:

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.post(f"{WEBAUTHN_BASE}registrar-verificar/", {}, format="json")
        assert resp.status_code in (401, 403)

    def test_sin_challenge_previo_retorna_400(self, api_portal):
        resp = api_portal.post(
            f"{WEBAUTHN_BASE}registrar-verificar/",
            {"credential": {"id": "x"}},
            format="json",
        )
        assert resp.status_code == 400

    def test_credencial_valida_se_guarda(self, cache_real, api_portal, usuario_portal):
        api_portal.post(f"{WEBAUTHN_BASE}registrar-opciones/")  # setea el challenge en cache

        fake_verified = types.SimpleNamespace(
            credential_id=b"nuevo-id-binario",
            credential_public_key=b"nueva-clave-binaria",
            sign_count=0,
        )
        with patch("apps.usuarios.views.webauthn.verify_registration_response", return_value=fake_verified):
            resp = api_portal.post(
                f"{WEBAUTHN_BASE}registrar-verificar/",
                {"credential": {"id": "abc", "rawId": "abc", "response": {}, "type": "public-key"}},
                format="json",
            )
        assert resp.status_code == 200, resp.data
        assert CredencialWebAuthn.objects.filter(usuario=usuario_portal).count() == 1

    def test_verificacion_fallida_no_guarda_credencial(self, cache_real, api_portal, usuario_portal):
        api_portal.post(f"{WEBAUTHN_BASE}registrar-opciones/")

        with patch("apps.usuarios.views.webauthn.verify_registration_response", side_effect=Exception("boom")):
            resp = api_portal.post(
                f"{WEBAUTHN_BASE}registrar-verificar/",
                {"credential": {"id": "abc"}},
                format="json",
            )
        assert resp.status_code == 400
        assert CredencialWebAuthn.objects.filter(usuario=usuario_portal).count() == 0


# ── WebAuthnLoginOpcionesView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginOpciones:

    def test_token_invalido_retorna_400(self, api_client):
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": "token-trucho"},
            format="json",
        )
        assert resp.status_code == 400

    def test_usuario_sin_credenciales_retorna_400(self, api_client, usuario_portal):
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": _pre_auth_token(usuario_portal)},
            format="json",
        )
        assert resp.status_code == 400

    def test_usuario_con_credencial_devuelve_opciones(self, api_client, usuario_portal, credencial):
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": _pre_auth_token(usuario_portal)},
            format="json",
        )
        assert resp.status_code == 200
        ids_permitidos = [c["id"] for c in resp.data.get("allowCredentials", [])]
        assert credencial.credential_id in ids_permitidos


# ── WebAuthnLoginVerificarView ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginVerificar:

    def test_token_invalido_retorna_400(self, api_client):
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-verificar/",
            {"pre_auth_token": "trucho", "credential": {"id": "x"}},
            format="json",
        )
        assert resp.status_code == 400

    def test_sin_challenge_previo_retorna_400(self, api_client, usuario_portal, credencial):
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-verificar/",
            {"pre_auth_token": _pre_auth_token(usuario_portal), "credential": {"id": credencial.credential_id}},
            format="json",
        )
        assert resp.status_code == 400

    def test_credencial_no_reconocida_retorna_400(self, cache_real, api_client, usuario_portal, credencial):
        api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": _pre_auth_token(usuario_portal)},
            format="json",
        )
        resp = api_client.post(
            f"{WEBAUTHN_BASE}login-verificar/",
            {
                "pre_auth_token": _pre_auth_token(usuario_portal),
                "credential": {"id": "id-que-no-existe"},
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_login_exitoso_devuelve_jwt_y_actualiza_sign_count(self, cache_real, api_client, usuario_portal, credencial):
        api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": _pre_auth_token(usuario_portal)},
            format="json",
        )
        fake_verified = types.SimpleNamespace(new_sign_count=99)
        with patch("apps.usuarios.views.webauthn.verify_authentication_response", return_value=fake_verified):
            resp = api_client.post(
                f"{WEBAUTHN_BASE}login-verificar/",
                {
                    "pre_auth_token": _pre_auth_token(usuario_portal),
                    "credential": {"id": credencial.credential_id, "rawId": credencial.credential_id, "response": {}},
                },
                format="json",
            )
        assert resp.status_code == 200, resp.data
        assert "access" in resp.data
        assert "refresh" in resp.data
        credencial.refresh_from_db()
        assert credencial.sign_count == 99
        assert credencial.ultimo_uso is not None

    def test_verificacion_fallida_retorna_400(self, cache_real, api_client, usuario_portal, credencial):
        api_client.post(
            f"{WEBAUTHN_BASE}login-opciones/",
            {"pre_auth_token": _pre_auth_token(usuario_portal)},
            format="json",
        )
        with patch("apps.usuarios.views.webauthn.verify_authentication_response", side_effect=Exception("boom")):
            resp = api_client.post(
                f"{WEBAUTHN_BASE}login-verificar/",
                {
                    "pre_auth_token": _pre_auth_token(usuario_portal),
                    "credential": {"id": credencial.credential_id},
                },
                format="json",
            )
        assert resp.status_code == 400


# ── WebAuthnDesactivarView ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDesactivar:

    def test_sin_credenciales_retorna_400(self, api_portal):
        resp = api_portal.post(f"{WEBAUTHN_BASE}desactivar/")
        assert resp.status_code == 400

    def test_desactiva_propia_credencial(self, api_portal, usuario_portal, credencial):
        resp = api_portal.post(f"{WEBAUTHN_BASE}desactivar/")
        assert resp.status_code == 200
        assert CredencialWebAuthn.objects.filter(usuario=usuario_portal).count() == 0

    def test_admin_usuario_id_inexistente_retorna_404(self, api_admin):
        resp = api_admin.post(
            f"{WEBAUTHN_BASE}desactivar/",
            {"usuario_id": 999999},
            format="json",
        )
        assert resp.status_code == 404

    def test_admin_desactiva_credencial_de_otro_usuario(self, api_admin, usuario_portal, credencial):
        resp = api_admin.post(
            f"{WEBAUTHN_BASE}desactivar/",
            {"usuario_id": usuario_portal.pk},
            format="json",
        )
        assert resp.status_code == 200
        assert CredencialWebAuthn.objects.filter(usuario=usuario_portal).count() == 0

    def test_no_admin_no_puede_desactivar_de_otro(self, api_portal, usuario_admin, credencial):
        # usuario_portal (no admin) intenta pasar usuario_id de otro usuario —
        # el usuario_id se ignora y solo se borran sus PROPIAS credenciales
        resp = api_portal.post(
            f"{WEBAUTHN_BASE}desactivar/",
            {"usuario_id": usuario_admin.pk},
            format="json",
        )
        assert resp.status_code == 200
        # La credencial de usuario_portal se borró (era la única que tenía permiso de tocar)
        assert not CredencialWebAuthn.objects.filter(pk=credencial.pk).exists()


# ── Flags tiene_webauthn en login / me / serializer ─────────────────────────────

@pytest.mark.django_db
class TestFlagsTieneWebauthn:

    def test_login_sin_ningun_2fa_no_requiere_paso_extra(self, api_client, usuario_portal):
        resp = api_client.post(
            "/api/token/",
            {"email": "mama@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert "requires_2fa" not in resp.data
        assert resp.data["user"]["tiene_webauthn"] is False

    def test_login_con_solo_webauthn_requiere_paso_extra(self, api_client, usuario_portal, credencial):
        resp = api_client.post(
            "/api/token/",
            {"email": "mama@test.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data.get("requires_2fa") is True
        assert resp.data.get("tiene_webauthn") is True
        assert "access" not in resp.data

    def test_me_incluye_tiene_webauthn(self, api_portal, credencial):
        resp = api_portal.get("/api/v1/usuarios/usuarios/me/")
        assert resp.status_code == 200
        assert resp.data["tiene_webauthn"] is True

    def test_serializer_lista_incluye_tiene_webauthn(self, api_admin, usuario_portal, credencial):
        resp = api_admin.get("/api/v1/usuarios/usuarios/", {"rol": "CLIENTE_WEB"})
        assert resp.status_code == 200
        data = resp.data["results"] if isinstance(resp.data, dict) else resp.data
        row = next(r for r in data if r["id_usuario"] == usuario_portal.pk)
        assert row["tiene_webauthn"] is True
