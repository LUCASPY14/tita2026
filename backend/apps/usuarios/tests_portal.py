"""
Tests para el portal de clientes (PortalAuthViewSet, PortalAuthService,
PortalJWTAuthentication, IsPortalAuthenticated).

Cubre:
  - PortalAuthService: login, _generar_token, verificar_token
  - PortalJWTAuthentication: token correcto, incorrecto, ausente, expirado
  - IsPortalAuthenticated: usuario portal vs usuario empleado
  - POST /portal-auth/login/: credenciales válidas e inválidas
  - GET  /portal-auth/perfil/
  - GET  /portal-auth/dashboard/
  - POST /portal-auth/cambiar_password/
"""

from datetime import timedelta
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.clientes.models import Clientes
from apps.usuarios.authentication import PortalJWTAuthentication, PortalUserProxy
from apps.usuarios.models import UsuariosPortal
from apps.usuarios.permissions import IsPortalAuthenticated
from apps.usuarios.services.portal_service import (
    PORTAL_TOKEN_LIFETIME,
    PORTAL_TOKEN_TYPE,
    PortalAuthService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cliente(**kwargs):
    defaults = dict(
        nombres="Juan",
        apellidos="Perez",
        ruc_ci="111111-1",
        email="juan@test.com",
        estado=True,
    )
    defaults.update(kwargs)
    return Clientes.objects.create(**defaults)


def _make_portal_user(cliente, email="juan@portal.com", raw_password="Pass1234!", **kwargs):
    defaults = dict(estado=True, email_verificado=True)
    defaults.update(kwargs)
    pu = UsuariosPortal(email=email, id_cliente=cliente, **defaults)
    pu.set_password(raw_password)
    pu.save()
    return pu


# ---------------------------------------------------------------------------
# PortalAuthService
# ---------------------------------------------------------------------------

class PortalAuthServiceLoginTest(TestCase):

    def setUp(self):
        self.cliente = _make_cliente()
        self.password = "Pass1234!"
        self.portal_user = _make_portal_user(self.cliente, raw_password=self.password)

    def test_login_exitoso(self):
        result = PortalAuthService.login(self.portal_user.email, self.password)
        self.assertIn("token", result)
        self.assertIn("portal_user", result)
        pu_data = result["portal_user"]
        self.assertEqual(pu_data["email"], self.portal_user.email)
        self.assertEqual(pu_data["id_cliente"], self.cliente.id_cliente)
        self.assertEqual(pu_data["nombre_completo"], self.cliente.nombre_completo)

    def test_login_actualiza_ultimo_acceso(self):
        before = timezone.now()
        PortalAuthService.login(self.portal_user.email, self.password)
        self.portal_user.refresh_from_db()
        self.assertIsNotNone(self.portal_user.ultimo_acceso)
        self.assertGreaterEqual(self.portal_user.ultimo_acceso, before)

    def test_login_email_case_insensitive(self):
        result = PortalAuthService.login(self.portal_user.email.upper(), self.password)
        self.assertIn("token", result)

    def test_login_password_incorrecta(self):
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.login(self.portal_user.email, "wrong")
        self.assertIn("Credenciales", str(ctx.exception))

    def test_login_email_inexistente(self):
        with self.assertRaises(ValueError):
            PortalAuthService.login("noexiste@test.com", self.password)

    def test_login_cuenta_inactiva(self):
        self.portal_user.estado = False
        self.portal_user.save()
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.login(self.portal_user.email, self.password)
        self.assertIn("desactivada", str(ctx.exception))


class PortalAuthServiceTokenTest(TestCase):

    def setUp(self):
        self.cliente = _make_cliente(ruc_ci="222222-2")
        self.portal_user = _make_portal_user(self.cliente, email="tok@test.com")

    def test_token_contiene_claims_correctos(self):
        token = PortalAuthService._generar_token(self.portal_user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(payload["token_type"], PORTAL_TOKEN_TYPE)
        self.assertEqual(payload["id_usuario_portal"], self.portal_user.id_usuario_portal)
        self.assertEqual(payload["id_cliente"], self.portal_user.id_cliente_id)
        self.assertEqual(payload["email"], self.portal_user.email)

    def test_token_expiracion_correcta(self):
        import time as _time
        before_ts = _time.time()
        token = PortalAuthService._generar_token(self.portal_user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        delta_seconds = payload["exp"] - before_ts
        # Should be within a few seconds of PORTAL_TOKEN_LIFETIME
        self.assertAlmostEqual(delta_seconds, PORTAL_TOKEN_LIFETIME.total_seconds(), delta=5)

    def test_verificar_token_valido(self):
        token = PortalAuthService._generar_token(self.portal_user)
        result = PortalAuthService.verificar_token(token)
        self.assertEqual(result.id_usuario_portal, self.portal_user.id_usuario_portal)

    def test_verificar_token_expirado(self):
        # Create an expired token directly with a past exp timestamp
        import time as _time
        expired_payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": self.portal_user.id_usuario_portal,
            "id_cliente": self.portal_user.id_cliente_id,
            "email": self.portal_user.email,
            "exp": int(_time.time()) - 10,
            "iat": int(_time.time()) - int(PORTAL_TOKEN_LIFETIME.total_seconds()) - 10,
        }
        token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.verificar_token(token)
        self.assertIn("expirado", str(ctx.exception))

    def test_verificar_token_firma_invalida(self):
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.verificar_token("not.a.valid.token")
        self.assertIn("inválido", str(ctx.exception))

    def test_verificar_token_tipo_incorrecto(self):
        # A token with a different token_type claim
        # Use integer timestamps to avoid PyJWT naive/aware comparison issues
        import time as _time
        payload = {
            "token_type": "access",
            "id_usuario_portal": self.portal_user.id_usuario_portal,
            "exp": int(_time.time()) + 3600,
            "iat": int(_time.time()),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.verificar_token(token)
        self.assertIn("inválido", str(ctx.exception))

    def test_verificar_token_usuario_inactivo(self):
        token = PortalAuthService._generar_token(self.portal_user)
        # Deactivate user after token was generated
        self.portal_user.estado = False
        self.portal_user.save()
        with self.assertRaises(ValueError) as ctx:
            PortalAuthService.verificar_token(token)
        self.assertIn("no encontrado", str(ctx.exception))


# ---------------------------------------------------------------------------
# PortalJWTAuthentication
# ---------------------------------------------------------------------------

class PortalJWTAuthenticationTest(TestCase):

    def setUp(self):
        self.cliente = _make_cliente(ruc_ci="333333-3")
        self.portal_user = _make_portal_user(self.cliente, email="auth@test.com")
        self.auth = PortalJWTAuthentication()

    def _make_request(self, token=None):
        from rest_framework.request import Request
        from django.test import RequestFactory
        factory = RequestFactory()
        req = factory.get("/")
        if token:
            req.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return req

    def test_autentica_token_portal_valido(self):
        token = PortalAuthService._generar_token(self.portal_user)
        request = self._make_request(token)
        user, auth_token = self.auth.authenticate(request)
        self.assertIsInstance(user, PortalUserProxy)
        self.assertEqual(user.portal_user.id_usuario_portal, self.portal_user.id_usuario_portal)
        self.assertTrue(user.is_authenticated)

    def test_retorna_none_sin_header(self):
        request = self._make_request()
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_retorna_none_token_tipo_access(self):
        # Employee-style token (token_type=access) should be passed through
        payload = {
            "token_type": "access",
            "user_id": 1,
            "exp": timezone.now() + timedelta(hours=1),
            "iat": timezone.now(),
        }
        employee_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        request = self._make_request(employee_token)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_lanza_error_token_portal_expirado(self):
        from rest_framework.exceptions import AuthenticationFailed
        import time as _time
        # Create an expired portal token directly
        expired_payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": self.portal_user.id_usuario_portal,
            "id_cliente": self.portal_user.id_cliente_id,
            "email": self.portal_user.email,
            "exp": int(_time.time()) - 10,
            "iat": int(_time.time()) - int(PORTAL_TOKEN_LIFETIME.total_seconds()) - 10,
        }
        token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
        request = self._make_request(token)
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_authenticate_header(self):
        self.assertEqual(self.auth.authenticate_header(None), "Bearer")


# ---------------------------------------------------------------------------
# IsPortalAuthenticated
# ---------------------------------------------------------------------------

class IsPortalAuthenticatedTest(TestCase):

    def setUp(self):
        self.permission = IsPortalAuthenticated()
        self.cliente = _make_cliente(ruc_ci="444444-4")
        self.portal_user = _make_portal_user(self.cliente, email="perm@test.com")

    def _make_request(self, user):
        from django.test import RequestFactory
        factory = RequestFactory()
        req = factory.get("/")
        req.user = user
        return req

    def test_permite_usuario_portal(self):
        proxy = PortalUserProxy(self.portal_user)
        request = self._make_request(proxy)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_rechaza_usuario_anonimo(self):
        from django.contrib.auth.models import AnonymousUser
        request = self._make_request(AnonymousUser())
        self.assertFalse(self.permission.has_permission(request, None))

    def test_rechaza_usuario_django(self):
        from django.contrib.auth.models import User
        user = User(username="emp")
        # Django User.is_authenticated is always True for authenticated users but
        # it is NOT a PortalUserProxy, so IsPortalAuthenticated must reject it.
        request = self._make_request(user)
        self.assertFalse(self.permission.has_permission(request, None))


# ---------------------------------------------------------------------------
# POST /portal-auth/login/
# ---------------------------------------------------------------------------

class PortalLoginEndpointTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.cliente = _make_cliente(ruc_ci="555555-5")
        self.password = "Portal1234!"
        self.portal_user = _make_portal_user(
            self.cliente, email="login_test@portal.com", raw_password=self.password
        )
        self.url = "/api/v1/portal-auth/login/"

    def test_login_exitoso_devuelve_token_y_usuario(self):
        resp = self.client.post(
            self.url,
            {"email": self.portal_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)
        self.assertIn("usuario", resp.data)
        self.assertEqual(resp.data["usuario"]["email"], self.portal_user.email)

    def test_login_password_incorrecta_devuelve_401(self):
        resp = self.client.post(
            self.url,
            {"email": self.portal_user.email, "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_inexistente_devuelve_401(self):
        resp = self.client.post(
            self.url,
            {"email": "noexiste@portal.com", "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_sin_campos_devuelve_400(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_solo_email_devuelve_400(self):
        resp = self.client.post(self.url, {"email": self.portal_user.email}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_usuario_inactivo_devuelve_401(self):
        self.portal_user.estado = False
        self.portal_user.save()
        resp = self.client.post(
            self.url,
            {"email": self.portal_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_token_contiene_tipo_portal(self):
        resp = self.client.post(
            self.url,
            {"email": self.portal_user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payload = jwt.decode(resp.data["token"], settings.SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(payload["token_type"], PORTAL_TOKEN_TYPE)


# ---------------------------------------------------------------------------
# GET /portal-auth/perfil/
# ---------------------------------------------------------------------------

class PortalPerfilEndpointTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.cliente = _make_cliente(ruc_ci="666666-6", email="perfil_c@test.com")
        self.portal_user = _make_portal_user(
            self.cliente, email="perfil@portal.com", raw_password="Pass1234!"
        )
        self.url = "/api/v1/portal-auth/perfil/"
        token = PortalAuthService._generar_token(self.portal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_perfil_autenticado(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], self.portal_user.email)
        self.assertIn("cliente", resp.data)
        self.assertEqual(resp.data["cliente"]["ruc_ci"], self.cliente.ruc_ci)

    def test_perfil_contiene_campos_cliente(self):
        resp = self.client.get(self.url)
        cliente_data = resp.data["cliente"]
        for field in ["id_cliente", "nombre_completo", "ruc_ci", "email", "limite_credito", "credito_disponible"]:
            self.assertIn(field, cliente_data)

    def test_perfil_sin_token_devuelve_401(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_perfil_token_empleado_devuelve_401(self):
        # Token con tipo "access" (empleado) debe rechazarse
        payload = {
            "token_type": "access",
            "user_id": 99,
            "exp": timezone.now() + timedelta(hours=1),
            "iat": timezone.now(),
        }
        emp_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# GET /portal-auth/dashboard/
# ---------------------------------------------------------------------------

class PortalDashboardEndpointTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.cliente = _make_cliente(ruc_ci="777777-7")
        self.portal_user = _make_portal_user(
            self.cliente, email="dash@portal.com", raw_password="Pass1234!"
        )
        self.url = "/api/v1/portal-auth/dashboard/"
        token = PortalAuthService._generar_token(self.portal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_dashboard_autenticado_devuelve_estructura(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("cliente", resp.data)
        self.assertIn("hijos", resp.data)

    def test_dashboard_cliente_contiene_credito(self):
        resp = self.client.get(self.url)
        c = resp.data["cliente"]
        self.assertIn("limite_credito", c)
        self.assertIn("credito_disponible", c)
        self.assertIn("nombre_completo", c)

    def test_dashboard_sin_hijos_lista_vacia(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["hijos"], [])

    def test_dashboard_sin_token_devuelve_401(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# POST /portal-auth/cambiar_password/
# ---------------------------------------------------------------------------

class PortalCambiarPasswordEndpointTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.cliente = _make_cliente(ruc_ci="888888-8")
        self.password_original = "Original1!"
        self.portal_user = _make_portal_user(
            self.cliente, email="cambiar@portal.com", raw_password=self.password_original
        )
        self.url = "/api/v1/portal-auth/cambiar_password/"
        token = PortalAuthService._generar_token(self.portal_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_cambiar_password_exitoso(self):
        resp = self.client.post(
            self.url,
            {"password_actual": self.password_original, "password_nuevo": "NuevaClave1!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Nuevo password funciona
        self.portal_user.refresh_from_db()
        self.assertTrue(self.portal_user.check_password("NuevaClave1!"))

    def test_cambiar_password_actual_incorrecta(self):
        resp = self.client.post(
            self.url,
            {"password_actual": "wrongpass", "password_nuevo": "NuevaClave1!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_nueva_muy_corta(self):
        resp = self.client.post(
            self.url,
            {"password_actual": self.password_original, "password_nuevo": "abc"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_campos_faltantes(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_sin_token_devuelve_401(self):
        self.client.credentials()
        resp = self.client.post(
            self.url,
            {"password_actual": self.password_original, "password_nuevo": "NuevaClave1!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cambiar_password_old_password_ya_no_funciona(self):
        self.client.post(
            self.url,
            {"password_actual": self.password_original, "password_nuevo": "NuevaClave1!"},
            format="json",
        )
        self.portal_user.refresh_from_db()
        self.assertFalse(self.portal_user.check_password(self.password_original))


# ---------------------------------------------------------------------------
# UsuariosPortal model
# ---------------------------------------------------------------------------

class UsuariosPortalModelTest(TestCase):

    def setUp(self):
        self.cliente = _make_cliente(ruc_ci="999999-9")

    def test_set_password_hashea(self):
        pu = UsuariosPortal(email="hash@test.com", id_cliente=self.cliente)
        pu.set_password("secret")
        self.assertNotEqual(pu.password_hash, "secret")
        # Hash format is hasher_id$... (e.g. md5$, pbkdf2_sha256$) depending on PASSWORD_HASHERS
        self.assertIn("$", pu.password_hash)

    def test_check_password_correcto(self):
        pu = UsuariosPortal(email="chk@test.com", id_cliente=self.cliente)
        pu.set_password("secret")
        self.assertTrue(pu.check_password("secret"))

    def test_check_password_incorrecto(self):
        pu = UsuariosPortal(email="chk2@test.com", id_cliente=self.cliente)
        pu.set_password("secret")
        self.assertFalse(pu.check_password("bad"))

    def test_str(self):
        pu = UsuariosPortal(email="str@test.com", id_cliente=self.cliente)
        self.assertIn("str@test.com", str(pu))
