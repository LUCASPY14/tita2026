"""
Smoke tests del flujo de login con 2FA.

Cubre:
  1. Login sin 2FA → JWT directo.
  2. Login con 2FA habilitado → pre_auth_token, sin JWT.
  3. Segunda etapa con código TOTP válido → JWT.
  4. Segunda etapa con código TOTP inválido → 400.
  5. Segunda etapa con pre_auth_token expirado → 400.
  6. Segunda etapa con backup code válido → JWT (y el code se consume).
"""
import base64
import hashlib
import hmac as hmac_mod
import secrets
import struct
import time

import pytest
from django.core import signing
from rest_framework.test import APIClient

from apps.usuarios.models import Autenticacion2FA, Usuario

# ── Helpers ───────────────────────────────────────────────────────────────────

LOGIN_URL     = "/api/token/"
FA2_LOGIN_URL = "/api/v1/usuarios/2fa/login/"


def _generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")


def _compute_totp(secret_b32: str, timestamp: float | None = None, step: int = 30) -> str:
    """RFC 6238 TOTP — reproduce la lógica de views.py sin importarla."""
    key = base64.b32decode(secret_b32.upper(), casefold=True)
    t = int((timestamp if timestamp is not None else time.time()) // step)
    counter = struct.pack(">Q", t)
    mac = hmac_mod.new(key, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    value = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def _pre_auth_token(user: Usuario) -> str:
    return signing.dumps({"user_id": user.id}, salt="2fa-pre-auth")


def _expired_pre_auth_token(user: Usuario) -> str:
    """Token firmado hace 6 minutos → superó el TTL de 300 s."""
    from unittest.mock import patch

    six_min_ago = time.time() - 360
    with patch("django.core.signing.time") as mock_time:
        mock_time.time.return_value = six_min_ago
        return signing.dumps({"user_id": user.id}, salt="2fa-pre-auth")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_sin_2fa(db):
    return Usuario.objects.create_user(
        email="sin2fa@test.com",
        password="Test1234!",
        nombre="Sin",
        apellido="DosFa",
        rol=Usuario.Rol.CAJERO,
    )


@pytest.fixture
def user_con_2fa(db):
    user = Usuario.objects.create_user(
        email="con2fa@test.com",
        password="Test1234!",
        nombre="Con",
        apellido="DosFa",
        rol=Usuario.Rol.ADMIN,
    )
    secret = _generate_secret()
    Autenticacion2FA.objects.create(
        usuario=user,
        secret_key=secret,
        habilitado=True,
        backup_codes=["ABCDEF", "123456"],
    )
    return user


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_login_sin_2fa_retorna_jwt(client, user_sin_2fa):
    """Usuario sin 2FA: login devuelve access + refresh directamente."""
    resp = client.post(
        LOGIN_URL,
        {"email": "sin2fa@test.com", "password": "Test1234!"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access" in resp.data
    assert "refresh" in resp.data
    assert "requires_2fa" not in resp.data


@pytest.mark.django_db
def test_login_con_2fa_retorna_pre_auth_token(client, user_con_2fa):
    """Usuario con 2FA: login devuelve requires_2fa=True y pre_auth_token, sin JWT."""
    resp = client.post(
        LOGIN_URL,
        {"email": "con2fa@test.com", "password": "Test1234!"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data.get("requires_2fa") is True
    assert "pre_auth_token" in resp.data
    assert "access" not in resp.data
    assert "refresh" not in resp.data


@pytest.mark.django_db
def test_2fa_login_con_codigo_valido_retorna_jwt(client, user_con_2fa):
    """Segunda etapa con TOTP correcto → 200 con JWT."""
    pre_auth = _pre_auth_token(user_con_2fa)
    secret = user_con_2fa.auth_2fa.secret_key
    codigo = _compute_totp(secret)

    resp = client.post(
        FA2_LOGIN_URL,
        {"pre_auth_token": pre_auth, "codigo": codigo},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert "access" in resp.data
    assert "refresh" in resp.data


@pytest.mark.django_db
def test_2fa_login_con_codigo_invalido_retorna_400(client, user_con_2fa):
    """Segunda etapa con TOTP incorrecto → 400."""
    pre_auth = _pre_auth_token(user_con_2fa)

    resp = client.post(
        FA2_LOGIN_URL,
        {"pre_auth_token": pre_auth, "codigo": "000000"},
        format="json",
    )
    assert resp.status_code == 400
    assert "error" in resp.data


@pytest.mark.django_db
def test_2fa_login_token_expirado_retorna_400(client, user_con_2fa):
    """pre_auth_token expirado (> 5 min) → 400."""
    expired = _expired_pre_auth_token(user_con_2fa)
    secret = user_con_2fa.auth_2fa.secret_key
    codigo = _compute_totp(secret)

    resp = client.post(
        FA2_LOGIN_URL,
        {"pre_auth_token": expired, "codigo": codigo},
        format="json",
    )
    assert resp.status_code == 400
    assert "error" in resp.data


@pytest.mark.django_db
def test_2fa_login_con_backup_code_valido(client, user_con_2fa):
    """Backup code válido → 200 con JWT y el code se elimina de la lista."""
    pre_auth = _pre_auth_token(user_con_2fa)

    resp = client.post(
        FA2_LOGIN_URL,
        {"pre_auth_token": pre_auth, "codigo": "ABCDEF"},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert "access" in resp.data

    # El backup code debe haber sido consumido
    user_con_2fa.auth_2fa.refresh_from_db()
    assert "ABCDEF" not in user_con_2fa.auth_2fa.backup_codes


@pytest.mark.django_db
def test_2fa_login_sin_campos_retorna_400(client, user_con_2fa):
    """Body vacío → 400 con mensaje de error descriptivo."""
    resp = client.post(FA2_LOGIN_URL, {}, format="json")
    assert resp.status_code == 400
    assert "error" in resp.data


@pytest.mark.django_db
def test_login_credenciales_incorrectas(client, user_sin_2fa):
    """Password incorrecto → 401."""
    resp = client.post(
        LOGIN_URL,
        {"email": "sin2fa@test.com", "password": "wrong!"},
        format="json",
    )
    assert resp.status_code == 401
