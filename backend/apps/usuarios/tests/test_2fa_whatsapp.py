"""
Tests del 2FA por WhatsApp (setup y segundo paso del login).

Cubre:
  1. Setup: enviar código — éxito, sin teléfono, fallo de WAHA.
  2. Setup: activar — código correcto/incorrecto, genera backup codes.
  3. Login: requires_2fa expone metodo_2fa.
  4. Login: reenvío de código durante el login.
  5. Login: verificación con código de WhatsApp (correcto/incorrecto) y backup code.
"""
from unittest.mock import patch

import pytest
from django.core import signing
from django.core.cache import cache as django_cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.usuarios.models import Autenticacion2FA, Usuario

LOGIN_URL          = "/api/token/"
FA2_LOGIN_URL       = "/api/v1/usuarios/2fa/login/"
WA_LOGIN_ENVIAR_URL = "/api/v1/usuarios/2fa/login/whatsapp/enviar/"
WA_ENVIAR_URL       = "/api/v1/usuarios/2fa/whatsapp/enviar/"
WA_ACTIVAR_URL      = "/api/v1/usuarios/2fa/whatsapp/activar/"


def _pre_auth_token(user: Usuario) -> str:
    return signing.dumps({"user_id": user.id_usuario}, salt="2fa-pre-auth")


# backend.settings.test usa DummyCache (no-op) — el código de WhatsApp SÍ
# necesita sobrevivir entre el request que lo envía y el que lo verifica,
# así que estos tests fuerzan un cache real (mismo patrón que test_webauthn.py).
@pytest.fixture(autouse=True)
def cache_real():
    with override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "test-2fa-whatsapp"}}
    ):
        django_cache.clear()
        yield


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def cliente_con_telefono(cliente):
    cliente.telefono = "0981234567"
    cliente.save(update_fields=["telefono"])
    return cliente


@pytest.fixture
def user_portal_sin_2fa(db, cliente_con_telefono):
    return Usuario.objects.create_user(
        email="padre@test.com",
        password="Test1234!",
        nombre="Padre",
        apellido="DePrueba",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente_con_telefono,
    )


@pytest.fixture
def user_portal_con_2fa_whatsapp(db, cliente_con_telefono):
    user = Usuario.objects.create_user(
        email="mama@test.com",
        password="Test1234!",
        nombre="Mama",
        apellido="DePrueba",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente_con_telefono,
    )
    Autenticacion2FA.objects.create(
        usuario=user,
        secret_key="",
        metodo=Autenticacion2FA.Metodo.WHATSAPP,
        habilitado=True,
        backup_codes=["ABCDEF"],
    )
    return user


# ── Setup: enviar código ───────────────────────────────────────────────────────

@pytest.mark.django_db
@patch("apps.notificaciones.services.enviar_whatsapp")
def test_whatsapp_enviar_ok(mock_enviar, client, user_portal_sin_2fa):
    client.force_authenticate(user=user_portal_sin_2fa)
    resp = client.post(WA_ENVIAR_URL, {}, format="json")
    assert resp.status_code == 200, resp.data
    assert "telefono" in resp.data
    mock_enviar.assert_called_once()
    numero_enviado = mock_enviar.call_args[0][0]
    assert numero_enviado == "595981234567"


@pytest.mark.django_db
def test_whatsapp_enviar_sin_telefono_retorna_400(client, db):
    user = Usuario.objects.create_user(
        email="sintelefono@test.com", password="Test1234!",
        nombre="Sin", apellido="Telefono", rol=Usuario.Rol.CAJERO,
    )
    client.force_authenticate(user=user)
    resp = client.post(WA_ENVIAR_URL, {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
@patch("apps.notificaciones.services.enviar_whatsapp", side_effect=RuntimeError("WAHA caído"))
def test_whatsapp_enviar_con_fallo_de_waha_retorna_502(mock_enviar, client, user_portal_sin_2fa):
    client.force_authenticate(user=user_portal_sin_2fa)
    resp = client.post(WA_ENVIAR_URL, {}, format="json")
    assert resp.status_code == 502


# ── Setup: activar ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
@patch("apps.notificaciones.services.enviar_whatsapp")
def test_whatsapp_activar_con_codigo_correcto(mock_enviar, client, user_portal_sin_2fa):
    client.force_authenticate(user=user_portal_sin_2fa)
    client.post(WA_ENVIAR_URL, {}, format="json")

    from apps.usuarios.views import _cache_key_whatsapp_2fa
    from django.core.cache import cache
    codigo = cache.get(_cache_key_whatsapp_2fa(user_portal_sin_2fa.id_usuario))
    assert codigo is not None

    resp = client.post(WA_ACTIVAR_URL, {"codigo": codigo}, format="json")
    assert resp.status_code == 200, resp.data
    assert len(resp.data["backup_codes"]) == 8

    user_portal_sin_2fa.auth_2fa.refresh_from_db()
    assert user_portal_sin_2fa.auth_2fa.habilitado is True
    assert user_portal_sin_2fa.auth_2fa.metodo == Autenticacion2FA.Metodo.WHATSAPP


@pytest.mark.django_db
def test_whatsapp_activar_con_codigo_incorrecto_retorna_400(client, user_portal_sin_2fa):
    client.force_authenticate(user=user_portal_sin_2fa)
    resp = client.post(WA_ACTIVAR_URL, {"codigo": "000000"}, format="json")
    assert resp.status_code == 400


# ── Login: requires_2fa expone el método ────────────────────────────────────────

@pytest.mark.django_db
def test_login_con_2fa_whatsapp_expone_metodo(client, user_portal_con_2fa_whatsapp):
    resp = client.post(
        LOGIN_URL, {"email": "mama@test.com", "password": "Test1234!"}, format="json",
    )
    assert resp.status_code == 200
    assert resp.data.get("requires_2fa") is True
    assert resp.data.get("metodo_2fa") == "WHATSAPP"


# ── Login: reenvío y verificación ───────────────────────────────────────────────

@pytest.mark.django_db
@patch("apps.notificaciones.services.enviar_whatsapp")
def test_login_whatsapp_enviar_codigo(mock_enviar, client, user_portal_con_2fa_whatsapp):
    pre_auth = _pre_auth_token(user_portal_con_2fa_whatsapp)
    resp = client.post(WA_LOGIN_ENVIAR_URL, {"pre_auth_token": pre_auth}, format="json")
    assert resp.status_code == 200, resp.data
    mock_enviar.assert_called_once()


@pytest.mark.django_db
@patch("apps.notificaciones.services.enviar_whatsapp")
def test_2fa_login_con_codigo_whatsapp_valido_retorna_jwt(mock_enviar, client, user_portal_con_2fa_whatsapp):
    pre_auth = _pre_auth_token(user_portal_con_2fa_whatsapp)
    client.post(WA_LOGIN_ENVIAR_URL, {"pre_auth_token": pre_auth}, format="json")

    from apps.usuarios.views import _cache_key_whatsapp_2fa
    from django.core.cache import cache
    codigo = cache.get(_cache_key_whatsapp_2fa(user_portal_con_2fa_whatsapp.id_usuario))

    resp = client.post(FA2_LOGIN_URL, {"pre_auth_token": pre_auth, "codigo": codigo}, format="json")
    assert resp.status_code == 200, resp.data
    assert "access" in resp.data


@pytest.mark.django_db
def test_2fa_login_con_codigo_whatsapp_invalido_retorna_400(client, user_portal_con_2fa_whatsapp):
    pre_auth = _pre_auth_token(user_portal_con_2fa_whatsapp)
    resp = client.post(FA2_LOGIN_URL, {"pre_auth_token": pre_auth, "codigo": "000000"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_2fa_login_whatsapp_con_backup_code_valido(client, user_portal_con_2fa_whatsapp):
    """El backup code sigue funcionando como red de respaldo con método WhatsApp."""
    pre_auth = _pre_auth_token(user_portal_con_2fa_whatsapp)
    resp = client.post(FA2_LOGIN_URL, {"pre_auth_token": pre_auth, "codigo": "ABCDEF"}, format="json")
    assert resp.status_code == 200, resp.data
    user_portal_con_2fa_whatsapp.auth_2fa.refresh_from_db()
    assert "ABCDEF" not in user_portal_con_2fa_whatsapp.auth_2fa.backup_codes
