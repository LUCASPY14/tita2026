"""
Tests para AuthenticationService.
Cubre: validar_fortaleza_password, verificar_cuenta_bloqueada, login,
       crear_empleado, cambiar_password.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.usuarios.models import BloqueosCuenta, Empleados, IntentosLogin, Roles
from apps.usuarios.services import AuthenticationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rol(nombre="Cajero"):
    rol, _ = Roles.objects.get_or_create(nombre_rol=nombre, defaults={"descripcion": nombre})
    return rol


def _make_empleado(usuario="emp_test", password_plain="Test1234!", email=None, estado=True):
    rol = _make_rol()
    hash_ = AuthenticationService._hash_password(password_plain)
    emp, _ = Empleados.objects.get_or_create(
        usuario=usuario,
        defaults={
            "nombre": "Test",
            "apellido": "User",
            "contrasena_hash": hash_,
            "fecha_ingreso": timezone.now(),
            "estado": estado,
            "email": email or f"{usuario}@test.com",
            "id_rol": rol,
        },
    )
    return emp


# ============================================================================
# 1. validar_fortaleza_password
# ============================================================================

class ValidarFortalezaPasswordTest(TestCase):
    """Tests para validacion de fortaleza de contrasena."""

    def test_password_corta(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("Ab1!")
        self.assertFalse(ok)
        self.assertIn("8", msg)

    def test_sin_mayuscula(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("abc12345!")
        self.assertFalse(ok)
        self.assertIn("may", msg.lower())

    def test_sin_minuscula(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("ABC12345!")
        self.assertFalse(ok)
        self.assertIn("min", msg.lower())

    def test_sin_numero(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("Abcdefgh!")
        self.assertFalse(ok)
        self.assertIn("n", msg.lower())

    def test_sin_especial(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("Abcde123")
        self.assertFalse(ok)
        self.assertIn("especial", msg.lower())

    def test_password_valida(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("Cantina2026!")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_password_minima_exacta(self):
        ok, msg = AuthenticationService.validar_fortaleza_password("Abc1234!")
        self.assertTrue(ok)


# ============================================================================
# 2. _hash_password / _verify_password
# ============================================================================

class HashPasswordTest(TestCase):
    """Tests para hash y verificacion de contrasenas."""

    def test_hash_es_diferente_al_plain(self):
        plain = "Prueba123!"
        hashed = AuthenticationService._hash_password(plain)
        self.assertNotEqual(plain, hashed)

    def test_verificacion_correcta(self):
        plain = "Cantina2026!"
        hashed = AuthenticationService._hash_password(plain)
        self.assertTrue(AuthenticationService._verify_password(plain, hashed))

    def test_verificacion_incorrecta(self):
        plain = "Cantina2026!"
        hashed = AuthenticationService._hash_password(plain)
        self.assertFalse(AuthenticationService._verify_password("Otro2026!", hashed))

    def test_verify_con_hash_invalido(self):
        resultado = AuthenticationService._verify_password("algo", "no_es_bcrypt")
        self.assertFalse(resultado)


# ============================================================================
# 3. verificar_cuenta_bloqueada
# ============================================================================

class VerificarCuentaBloqueadaTest(TestCase):
    """Tests para verificacion de bloqueo de cuenta."""

    def setUp(self):
        self.empleado = _make_empleado("bloq_test")

    def test_empleado_inactivo_bloqueado(self):
        self.empleado.estado = False
        self.empleado.save()
        bloqueada, motivo = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)
        self.assertTrue(bloqueada)
        self.assertIn("inactiv", motivo.lower())

    def test_sin_bloqueos_activos(self):
        bloqueada, motivo = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)
        self.assertFalse(bloqueada)
        self.assertIsNone(motivo)

    def test_bloqueo_activo_sin_expiracion(self):
        BloqueosCuenta.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            motivo="Demasiados intentos",
            bloqueado_por="sistema",
            ip_address="127.0.0.1",
            fecha_bloqueo=timezone.now(),
            fecha_desbloqueo=None,
            estado=True,
        )
        bloqueada, motivo = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)
        self.assertTrue(bloqueada)
        self.assertIn("Demasiados intentos", motivo)

    def test_bloqueo_temporal_expirado(self):
        BloqueosCuenta.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            motivo="Temporal expirado",
            bloqueado_por="sistema",
            ip_address="127.0.0.1",
            fecha_bloqueo=timezone.now() - timedelta(hours=2),
            fecha_desbloqueo=timezone.now() - timedelta(hours=1),  # ya expiró
            estado=True,
        )
        bloqueada, motivo = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)
        self.assertFalse(bloqueada)
        self.assertIsNone(motivo)


# ============================================================================
# 4. login
# ============================================================================

class LoginTest(TestCase):
    """Tests para el flujo de login completo."""

    def setUp(self):
        self.empleado = _make_empleado("login_user", "Login2026!")

    def test_usuario_no_existe(self):
        resultado = AuthenticationService.login("no_existe", "pass", "127.0.0.1")
        self.assertFalse(resultado["success"])
        self.assertIn("CREDENCIALES", resultado["codigo"])

    def test_password_incorrecta(self):
        resultado = AuthenticationService.login(self.empleado.usuario, "WrongPass!", "127.0.0.1")
        self.assertFalse(resultado["success"])
        self.assertEqual(resultado["codigo"], "CREDENCIALES_INVALIDAS")

    def test_login_exitoso(self):
        resultado = AuthenticationService.login(self.empleado.usuario, "Login2026!", "127.0.0.1")
        self.assertTrue(resultado["success"])
        self.assertIn("access", resultado)
        self.assertIn("refresh", resultado)
        self.assertEqual(resultado["codigo"], "LOGIN_EXITOSO")

    def test_login_registra_intento_exitoso(self):
        AuthenticationService.login(self.empleado.usuario, "Login2026!", "127.0.0.1")
        intentos = IntentosLogin.objects.filter(usuario=self.empleado.usuario, exitoso=1)
        self.assertGreaterEqual(intentos.count(), 1)

    def test_login_registra_intento_fallido(self):
        AuthenticationService.login(self.empleado.usuario, "BadPass!", "127.0.0.1")
        intentos = IntentosLogin.objects.filter(usuario=self.empleado.usuario, exitoso=0)
        self.assertGreaterEqual(intentos.count(), 1)

    def test_cuenta_bloqueada_no_puede_login(self):
        BloqueosCuenta.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            motivo="Test bloqueo",
            bloqueado_por="sistema",
            ip_address="127.0.0.1",
            fecha_bloqueo=timezone.now(),
            estado=True,
        )
        resultado = AuthenticationService.login(self.empleado.usuario, "Login2026!", "127.0.0.1")
        self.assertFalse(resultado["success"])
        self.assertEqual(resultado["codigo"], "CUENTA_BLOQUEADA")

    def test_bloqueo_automatico_por_intentos(self):
        for _ in range(AuthenticationService.MAX_LOGIN_INTENTOS - 1):
            AuthenticationService.login(self.empleado.usuario, "BadPass!", "127.0.0.1")
        bloqueos = BloqueosCuenta.objects.filter(usuario=self.empleado.usuario, estado=True)
        self.assertGreaterEqual(bloqueos.count(), 1)

    def test_login_empleado_inactivo(self):
        self.empleado.estado = False
        self.empleado.save()
        resultado = AuthenticationService.login(self.empleado.usuario, "Login2026!", "127.0.0.1")
        self.assertFalse(resultado["success"])


# ============================================================================
# 5. crear_empleado
# ============================================================================

class CrearEmpleadoTest(TestCase):
    """Tests para crear_empleado."""

    def setUp(self):
        self.rol = _make_rol("Vendedor")

    def test_crear_empleado_exitoso(self):
        resultado = AuthenticationService.crear_empleado(
            nombre="Maria",
            apellido="Lopez",
            usuario="mlopez_test",
            email="mlopez@test.com",
            password="MariaTita2026!",
            id_rol=self.rol.id_rol,
            creado_por=None,
            ip_address="127.0.0.1",
        )
        self.assertTrue(resultado["success"])
        self.assertIn("empleado", resultado)
        emp = Empleados.objects.get(usuario="mlopez_test")
        self.assertEqual(emp.nombre, "Maria")

    def test_crear_empleado_usuario_duplicado(self):
        _make_empleado("dup_user")
        resultado = AuthenticationService.crear_empleado(
            nombre="Otro",
            apellido="Apellido",
            usuario="dup_user",
            email="otro@test.com",
            password="Otro2026!",
            id_rol=self.rol.id_rol,
            creado_por=None,
            ip_address="127.0.0.1",
        )
        self.assertFalse(resultado["success"])

    def test_crear_empleado_password_debil(self):
        resultado = AuthenticationService.crear_empleado(
            nombre="Test",
            apellido="Debil",
            usuario="pwd_debil",
            email="debil@test.com",
            password="1234",
            id_rol=self.rol.id_rol,
            creado_por=None,
            ip_address="127.0.0.1",
        )
        self.assertFalse(resultado["success"])


# ============================================================================
# 6. cambiar_password
# ============================================================================

class CambiarPasswordTest(TestCase):
    """Tests para cambiar_password."""

    def setUp(self):
        self.empleado = _make_empleado("cambio_pwd", "Vieja2026!")

    def test_cambio_exitoso(self):
        resultado = AuthenticationService.cambiar_password(
            self.empleado, "Vieja2026!", "Nueva2026!", "127.0.0.1"
        )
        self.assertTrue(resultado["success"])
        self.empleado.refresh_from_db()
        self.assertTrue(AuthenticationService._verify_password("Nueva2026!", self.empleado.contrasena_hash))

    def test_password_actual_incorrecta(self):
        resultado = AuthenticationService.cambiar_password(
            self.empleado, "WrongPass!", "Nueva2026!", "127.0.0.1"
        )
        self.assertFalse(resultado["success"])

    def test_nueva_password_debil(self):
        resultado = AuthenticationService.cambiar_password(
            self.empleado, "Vieja2026!", "corta", "127.0.0.1"
        )
        self.assertFalse(resultado["success"])

    def test_nueva_igual_a_vieja_rechazada(self):
        resultado = AuthenticationService.cambiar_password(
            self.empleado, "Vieja2026!", "Vieja2026!", "127.0.0.1"
        )
        self.assertFalse(resultado["success"])
