"""
Additional coverage tests for apps/usuarios/signals.py.

Missing branch/line targets:
  24->exit through 33->exit: stub functions (audit_logger, send_notification, …)
                             are defined but never called — calling each once
                             covers their single-line function branches.
  68->71:  serializar_modelo with explicit campos_excluir (else branch of
           `if campos_excluir is None:`)
  320->exit: sesion_post_save — `if not instance.activa:` is False path
             (session updated but still active)
  324-325: except block in sesion_post_save — triggered when the try body raises
"""

from unittest.mock import MagicMock

from django.test import TestCase
from django.utils import timezone

from apps.usuarios.models import Empleados, Roles, SesionesActivas
from apps.usuarios.signals import (
    audit_log,
    audit_logger,
    cleanup_user_data,
    create_user_profile,
    hash_password,
    invalidate_sessions,
    log_role_change,
    send_notification,
    send_welcome_email,
    serializar_modelo,
    sesion_post_save,
    update_last_login,
)


class SignalStubFunctionsTest(TestCase):
    """Call all 10 stub functions to cover their single-line function bodies (lines 24-33)."""

    def test_call_all_stubs(self):
        """Each stub accepts *args, **kwargs and returns None (pass)."""
        # Lines 24-33: each def has a branch 'function called → exit'
        self.assertIsNone(audit_logger("arg1", key="val"))
        self.assertIsNone(send_notification("msg"))
        self.assertIsNone(update_last_login(user=None))
        self.assertIsNone(hash_password("secret"))
        self.assertIsNone(log_role_change(role="admin"))
        self.assertIsNone(invalidate_sessions(user_id=1))
        self.assertIsNone(cleanup_user_data(1, 2, 3))
        self.assertIsNone(create_user_profile())
        self.assertIsNone(send_welcome_email(email="a@b.com"))
        self.assertIsNone(audit_log("CRUD", "Empleados", 42))


class SerializarModeloExplicitCamposExcluirTest(TestCase):
    """Branch 68->71: serializar_modelo called with an explicit campos_excluir list."""

    def setUp(self):
        self.rol = Roles.objects.create(
            nombre_rol="SerCovTest",
            descripcion="Test",
            estado=True,
        )

    def test_serializar_con_campos_excluir_explicito(self):
        """Branch 68->71: when campos_excluir is not None, the `else` branch skips assignment."""
        empleado = Empleados.objects.create(
            nombre="Cov",
            apellido="Test",
            usuario="serial_cov_user",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="sercov@test.com",
            estado=True,
            id_rol=self.rol,
        )
        # Pass campos_excluir explicitly → `if campos_excluir is None:` is False (branch 68->71)
        result = serializar_modelo(empleado, campos_excluir=["id_rol"])
        # id_rol should be excluded, but other fields are present
        self.assertIn("nombre", result)
        self.assertNotIn("id_rol", result)


class SesionPostSaveActivaTrueUpdateTest(TestCase):
    """Branch 320->exit: update a session while keeping activa=True."""

    def test_update_sesion_keeping_active_covers_320_exit(self):
        """Branch 320->exit: else block entered, if not instance.activa: is False."""
        sesion = SesionesActivas.objects.create(
            usuario="cov_active_user",
            tipo_usuario="empleado",
            session_key="cov_active_session_key",
            fecha_inicio=timezone.now(),
            ultima_actividad=timezone.now(),
            activa=True,
        )
        # Update ultima_actividad while keeping activa=True → triggers else branch
        # with `if not instance.activa:` = False → branch 320->exit
        sesion.ultima_actividad = timezone.now()
        sesion.save()
        sesion.refresh_from_db()
        self.assertTrue(sesion.activa)


class SesionPostSaveExceptBlockTest(TestCase):
    """Lines 324-325: except block in sesion_post_save (force exception in try body)."""

    def test_sesion_post_save_except_block_via_bad_instance(self):
        """Lines 324-325: when instance.activa raises AttributeError, except block runs."""
        # A mock with spec=[] has no attributes — accessing .activa raises AttributeError
        mock_instance = MagicMock(spec=[])
        # Call the signal handler directly with created=False, so the else branch
        # is entered and `if not instance.activa:` raises AttributeError → except caught
        sesion_post_save(SesionesActivas, mock_instance, created=False)
        # No exception should propagate (it is caught and printed internally)


class BloqueoPostSaveObtenerIPExceptionTest(TestCase):
    """Branch 370->exit: covers exception path AND normal success path of bloqueo_post_save."""

    def setUp(self):
        self.rol = Roles.objects.create(
            nombre_rol="BloqueoIPExcTest",
            descripcion="Test",
            estado=True,
        )

    def test_bloqueo_post_save_370_exit_via_empleado_exception(self):
        """370->exit: when obtener_empleado_actual raises, the except block catches it."""
        from unittest.mock import patch

        from apps.usuarios.models import BloqueosCuenta

        bloqueo = BloqueosCuenta.objects.create(
            usuario="ip_exc_test_user",
            tipo_usuario="empleado",
            motivo="Test motivo",
            fecha_bloqueo=timezone.now(),
            estado=True,
        )

        with patch(
            "apps.usuarios.signals.obtener_empleado_actual",
            side_effect=Exception("empleado fetch error"),
        ):
            bloqueo.estado = False
            bloqueo.save()

        bloqueo.refresh_from_db()
        self.assertFalse(bloqueo.estado)

    def test_bloqueo_post_save_normal_success_path(self):
        """370->exit (success): desbloqueo audit runs successfully — normal function exit."""
        from apps.usuarios.models import BloqueosCuenta

        bloqueo = BloqueosCuenta.objects.create(
            usuario="normal_desbloqueo_user",
            tipo_usuario="empleado",
            motivo="Bloqueo de prueba",
            fecha_bloqueo=timezone.now(),
            estado=True,
        )

        # No patches — AuditoriaOperaciones.create() runs successfully
        # empleado_actual=None → usuario="sistema", id_usuario=None → valid
        bloqueo.estado = False
        bloqueo.save()

        bloqueo.refresh_from_db()
        self.assertFalse(bloqueo.estado)
