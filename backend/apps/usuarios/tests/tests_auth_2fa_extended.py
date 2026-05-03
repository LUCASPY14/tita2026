"""
Extended tests for AuthenticationService and TwoFactorAuthService
Targeting uncovered lines for coverage improvement.
"""

from unittest.mock import patch

from django.test import TransactionTestCase
from django.utils import timezone

from apps.usuarios.models import (
    AuditoriaOperaciones,
    Autenticacion2Fa,
    Empleados,
    Intentos2Fa,
    Roles,
    SesionesActivas,
)
from apps.usuarios.services.auth_service import AuthenticationService
from apps.usuarios.services.two_factor_service import TwoFactorAuthService


class BaseAuthTest(TransactionTestCase):
    """Base setup for auth service tests."""

    password = "SecurePass123!@#"

    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol="TestRolAuth", descripcion="Test", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Auth",
            apellido="Test",
            usuario="authtestuser",
            email="auth@cantinatita.com",
            contrasena_hash=AuthenticationService._hash_password(self.password),
            id_rol=self.rol,
            fecha_ingreso=timezone.now(),
            estado=True,
        )
        self.ip = "10.0.0.2"

    def tearDown(self):
        SesionesActivas.objects.all().delete()
        AuditoriaOperaciones.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


# ============================================================================
# AuthenticationService - missing lines coverage
# ============================================================================


class VerifyPasswordExceptionTest(BaseAuthTest):
    """Cover exception path in _verify_password (lines 70-71)."""

    def test_verify_password_bcrypt_exception_returns_false(self):
        """When bcrypt.checkpw raises, returns False (lines 70-71)."""
        with patch("apps.usuarios.services.auth_service.bcrypt") as mock_bcrypt:
            mock_bcrypt.checkpw.side_effect = Exception("bcrypt error")
            result = AuthenticationService._verify_password("password", "$2b$invalid")
        self.assertFalse(result)


class GenerarTokensExistingUserTest(BaseAuthTest):
    """Cover is_active sync branch in _generar_tokens_jwt (lines 248-250)."""

    def test_generar_tokens_syncs_is_active_si_django_user_existente(self):
        """When django_user already exists with different is_active, syncs it (lines 249-250)."""
        from django.contrib.auth.models import User

        # Pre-create django User with is_active=False
        User.objects.filter(username=self.empleado.usuario).delete()
        User.objects.create_user(
            username=self.empleado.usuario,
            email=self.empleado.email,
            is_active=False,  # different from empleado.estado=True
        )
        tokens = AuthenticationService._generar_tokens_jwt(self.empleado)
        self.assertIn("access", tokens)
        # Django user should now be synced to active
        user = User.objects.filter(username=self.empleado.usuario).first()
        self.assertTrue(user.is_active)


class LoginExceptionTest(BaseAuthTest):
    """Cover outer exception path in login (lines 394-397)."""

    def test_login_outer_exception_returns_error(self):
        """Outer exception in login returns error dict (lines 394-397)."""
        with patch("apps.usuarios.services.auth_service.Empleados") as mock_emp:
            mock_emp.objects.filter.side_effect = Exception("DB fail")
            result = AuthenticationService.login(
                usuario="authtestuser",
                password=self.password,
                ip_address=self.ip,
                user_agent="TestAgent",
            )
        self.assertFalse(result["success"])
        self.assertEqual(result["codigo"], "ERROR_SERVIDOR")


class LogoutExceptionTest(BaseAuthTest):
    """Cover outer exception path in logout (lines 439-441)."""

    def test_logout_outer_exception_returns_error(self):
        """Outer exception in logout returns error dict (lines 439-441)."""
        with patch("apps.usuarios.services.auth_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            result = AuthenticationService.logout(
                empleado=self.empleado,
                session_key="any_key",
                ip_address=self.ip,
            )
        self.assertFalse(result["success"])


class CambiarPasswordSamePasswordTest(BaseAuthTest):
    """Cover 'same password' branch in cambiar_password (line 470)."""

    def test_cambiar_password_igual_a_actual_falla(self):
        """Same password as current → returns error (line 470)."""
        result = AuthenticationService.cambiar_password(
            empleado=self.empleado,
            password_actual=self.password,
            password_nueva=self.password,  # same!
            ip_address=self.ip,
        )
        self.assertFalse(result["success"])
        self.assertIn("diferente", result["mensaje"])


class CambiarPasswordExceptionTest(BaseAuthTest):
    """Cover outer exception in cambiar_password (lines 508-510)."""

    def test_cambiar_password_outer_exception(self):
        """Outer exception in cambiar_password returns error dict (lines 508-510)."""
        with patch("apps.usuarios.services.auth_service.AuthenticationService._verify_password") as mock_verify:
            mock_verify.side_effect = Exception("Unexpected")
            result = AuthenticationService.cambiar_password(
                empleado=self.empleado,
                password_actual=self.password,
                password_nueva="NewPass456!@#",
                ip_address=self.ip,
            )
        self.assertFalse(result["success"])
        self.assertIn("Error al cambiar", result["mensaje"])


class CrearEmpleadoTest(BaseAuthTest):
    """Cover crear_empleado exception paths (lines 586-590)."""

    def test_crear_empleado_rol_inexistente(self):
        """Rol.DoesNotExist → returns error (line 586-587)."""
        result = AuthenticationService.crear_empleado(
            nombre="Nuevo",
            apellido="Emp",
            usuario="nuevo_emp_999",
            email="nuevo999@cantinatita.com",
            password="NewPass123!@#",
            id_rol=99999,  # non-existent
            creado_por=self.empleado,
            ip_address=self.ip,
        )
        self.assertFalse(result["success"])
        self.assertIn("rol especificado no existe", result["mensaje"])

    def test_crear_empleado_outer_exception(self):
        """Outer exception in crear_empleado returns error (lines 588-590)."""
        with patch("apps.usuarios.services.auth_service.Empleados") as mock_emp:
            # Let filter().exists() pass normally for usuario/email checks, but
            # make create() raise to trigger the outer except Exception
            mock_emp.objects.filter.return_value.exists.return_value = False
            mock_emp.objects.create.side_effect = Exception("Unexpected DB error")
            # We need Roles to work, so import it separately

            with patch(
                "apps.usuarios.services.auth_service.AuthenticationService._hash_password", return_value="hashedpw"
            ):
                with patch(
                    "apps.usuarios.services.auth_service.AuthenticationService.validar_fortaleza_password",
                    return_value=(True, ""),
                ):
                    result = AuthenticationService.crear_empleado(
                        nombre="Test",
                        apellido="Emp",
                        usuario="outer_exc_user",
                        email="outer@cantinatita.com",
                        password="SomePass123!",
                        id_rol=self.rol.id_rol,
                        creado_por=self.empleado,
                        ip_address=self.ip,
                    )
        self.assertFalse(result["success"])
        self.assertIn("Error al crear empleado", result["mensaje"])


# ============================================================================
# TwoFactorAuthService - missing lines coverage
# ============================================================================


class Base2FATest(TransactionTestCase):
    """Base setup for 2FA tests."""

    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol="TestRol2FA", descripcion="Test", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="TwoFA",
            apellido="Test",
            usuario="twofatestuser",
            email="twofa@cantinatita.com",
            contrasena_hash="testhash",
            id_rol=self.rol,
            fecha_ingreso=timezone.now(),
            estado=True,
        )
        self.ip = "10.0.0.3"

    def tearDown(self):
        Intentos2Fa.objects.all().delete()
        Autenticacion2Fa.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


class Habilitar2FAExceptionTest(Base2FATest):
    """Cover exception path in habilitar_2fa_empleado (lines 153-155)."""

    def test_habilitar_2fa_outer_exception(self):
        """Outer exception in habilitar_2fa_empleado returns error (lines 153-155)."""
        with patch("apps.usuarios.services.two_factor_service.TwoFactorAuthService._generar_secret_key") as mock_key:
            mock_key.side_effect = Exception("Key gen failed")
            result = TwoFactorAuthService.habilitar_2fa_empleado(empleado=self.empleado, ip_address=self.ip)
        self.assertFalse(result["success"])
        self.assertIn("Error al habilitar 2FA", result["mensaje"])


class Verificar2FAExceptionTest(Base2FATest):
    """Cover exception path in verificar_codigo_2fa (lines 246-248)."""

    def test_verificar_2fa_outer_exception(self):
        """Outer exception in verificar_codigo_2fa returns error (lines 246-248)."""
        with patch("apps.usuarios.services.two_factor_service.Autenticacion2Fa") as mock_auth:
            mock_auth.objects.filter.side_effect = Exception("DB fail")
            result = TwoFactorAuthService.verificar_codigo_2fa(
                empleado=self.empleado,
                codigo="123456",
                ip_address=self.ip,
            )
        self.assertFalse(result["success"])
        self.assertIn("Error al verificar", result["mensaje"])


class VerificarBackupCodeTest(Base2FATest):
    """Cover _verificar_backup_code with list backup_codes (line 260) and exception (lines 279-280)."""

    def _crear_auth_2fa(self):
        return Autenticacion2Fa.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            secret_key="JBSWY3DPEHPK3PXP",
            backup_codes=["11111111", "22222222"],
            habilitado=True,
            fecha_activacion=timezone.now(),
            fecha_creacion=timezone.now(),
        )

    def test_backup_code_es_lista_no_string(self):
        """When backup_codes is already a list (not str), branch at line 260 is skipped."""
        auth_2fa = self._crear_auth_2fa()
        # backup_codes is already a list, directly test the method
        result = TwoFactorAuthService._verificar_backup_code(auth_2fa, "11111111", self.ip)
        self.assertTrue(result)

    def test_backup_code_exception_returns_false(self):
        """Exception in _verificar_backup_code returns False (lines 279-280)."""
        auth_2fa = self._crear_auth_2fa()
        # Mock backup_codes to be invalid JSON string (can't save to DB due to constraint)
        with patch.object(auth_2fa, "backup_codes", "not_json{"):
            result = TwoFactorAuthService._verificar_backup_code(auth_2fa, "11111111", self.ip)
            self.assertFalse(result)


class Deshabilitar2FAExceptionTest(Base2FATest):
    """Cover exception path in deshabilitar_2fa_empleado (lines 354-356)."""

    def test_deshabilitar_2fa_outer_exception(self):
        """Outer exception in deshabilitar_2fa_empleado returns error (lines 354-356)."""
        with patch("apps.usuarios.services.two_factor_service.Autenticacion2Fa") as mock_auth:
            mock_auth.objects.filter.side_effect = Exception("DB fail")
            result = TwoFactorAuthService.deshabilitar_2fa_empleado(empleado=self.empleado, ip_address=self.ip)
        self.assertFalse(result["success"])
        self.assertIn("Error al deshabilitar 2FA", result["mensaje"])


class RegenBackupCodesExceptionTest(Base2FATest):
    """Cover exception path in regenerar_backup_codes (lines 403-405)."""

    def test_regenerar_backup_codes_outer_exception(self):
        """Outer exception in regenerar_backup_codes returns error (lines 403-405)."""
        with patch("apps.usuarios.services.two_factor_service.Autenticacion2Fa") as mock_auth:
            mock_auth.objects.filter.side_effect = Exception("DB fail")
            result = TwoFactorAuthService.regenerar_backup_codes(empleado=self.empleado, ip_address=self.ip)
        self.assertFalse(result["success"])
        self.assertIn("Error al regenerar", result["mensaje"])


class Verificar2FAHabilitadoTest(Base2FATest):
    """Cover verificar_2fa_habilitado (line 415)."""

    def test_verificar_2fa_habilitado_true(self):
        """Returns True when 2FA is enabled (line 415)."""
        Autenticacion2Fa.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            secret_key="JBSWY3DPEHPK3PXP",
            backup_codes=[],  # Use list instead of string
            habilitado=True,
            fecha_activacion=timezone.now(),
            fecha_creacion=timezone.now(),
        )
        result = TwoFactorAuthService.verificar_2fa_habilitado(self.empleado)
        self.assertTrue(result)

    def test_verificar_2fa_habilitado_false(self):
        """Returns False when 2FA is not enabled (line 415)."""
        result = TwoFactorAuthService.verificar_2fa_habilitado(self.empleado)
        self.assertFalse(result)


class ObtenerEstadisticasBackupCodesListTest(Base2FATest):
    """Cover backup_codes as list branch in obtener_estadisticas_2fa (lines 457-460, 461-462)."""

    def test_estadisticas_backup_codes_como_lista(self):
        """When backup_codes is a list, exercises line 459 (not str branch)."""
        auth_2fa = Autenticacion2Fa.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            secret_key="JBSWY3DPEHPK3PXP",
            backup_codes=["code1", "code2", "code3"],
            habilitado=True,
            fecha_activacion=timezone.now(),
            fecha_creacion=timezone.now(),
        )
        result = TwoFactorAuthService.obtener_estadisticas_2fa(self.empleado)
        self.assertTrue(result["habilitado"])
        self.assertEqual(result["backup_codes_restantes"], 3)

    def test_estadisticas_backup_codes_json_invalido(self):
        """When backup_codes is invalid JSON, exception silenced (lines 461-462)."""
        # Create valid auth_2fa first
        auth_2fa = Autenticacion2Fa.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            secret_key="JBSWY3DPEHPK3PXP",
            backup_codes=[],  # Valid JSON
            habilitado=True,
            fecha_activacion=timezone.now(),
            fecha_creacion=timezone.now(),
        )
        # Mock the backup_codes to be invalid JSON string
        with patch.object(auth_2fa, "backup_codes", "invalid{json"):
            result = TwoFactorAuthService.obtener_estadisticas_2fa(self.empleado)
            # Should not raise, backup_codes_restantes stays 0 due to exception handling
            self.assertTrue(result["habilitado"])
            self.assertEqual(result["backup_codes_restantes"], 0)
