"""
Extended tests for apps/usuarios/management/commands/cleanup_usuarios.py.

Missing line targets:
  83-85:   except Exception block for SessionService raise
  104-105: else block for tokens service returning success=False
  123-125: except Exception block for PasswordRecoveryService raise
  150:     verbose print inside login cleanup when cantidad > 0
  165-167: except Exception block for IntentosLogin query raise
  190:     verbose print inside 2FA cleanup when cantidad > 0
  205-207: except Exception block for Intentos2Fa query raise
"""

from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase


class CleanupSessionsExceptionTest(TestCase):
    """Lines 83-85: except block when SessionService raises."""

    def test_sessions_service_raises_covers_except_block(self):
        """Lines 83-85: SessionService.limpiar_sesiones_expiradas raises → except caught."""
        out = StringIO()
        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            side_effect=Exception("DB connection error"),
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={"success": True, "tokens_eliminados": 0, "mensaje": "ok"},
            ):
                call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Error", output)


class CleanupTokensFailureTest(TestCase):
    """Lines 104-105: else block when tokens service returns success=False."""

    def test_tokens_service_returns_failure_covers_else_block(self):
        """Lines 104-105: PasswordRecoveryService returns success=False → else branch."""
        out = StringIO()
        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={
                    "success": False,
                    "tokens_eliminados": 0,
                    "mensaje": "Error en tokens",
                },
            ):
                call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Error", output)


class CleanupTokensExceptionTest(TestCase):
    """Lines 123-125: except block when PasswordRecoveryService raises."""

    def test_tokens_service_raises_covers_except_block(self):
        """Lines 123-125: PasswordRecoveryService.limpiar_tokens_expirados raises."""
        out = StringIO()
        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                side_effect=Exception("Token DB error"),
            ):
                call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Error", output)


class CleanupLoginVerboseTest(TestCase):
    """Line 150: verbose print for login attempts when cantidad > 0."""

    def test_verbose_with_login_attempts_covers_line_150(self):
        """Line 150: when verbose=True and login count > 0, print line executes."""
        out = StringIO()
        mock_qs = MagicMock()
        mock_qs.count.return_value = 5
        mock_qs.delete.return_value = (5, {})

        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={"success": True, "tokens_eliminados": 0, "mensaje": "ok"},
            ):
                with patch(
                    "apps.usuarios.models.IntentosLogin.objects.filter",
                    return_value=mock_qs,
                ):
                    with patch(
                        "apps.usuarios.models.Intentos2Fa.objects.filter",
                        return_value=mock_qs,
                    ):
                        call_command("cleanup_usuarios", verbose=True, stdout=out)
        output = out.getvalue()
        self.assertIn("Limpieza", output)


class CleanupLoginExceptionTest(TestCase):
    """Lines 165-167: except block when IntentosLogin query raises."""

    def test_login_attempts_query_raises_covers_except_block(self):
        """Lines 165-167: IntentosLogin.objects.filter raises → except caught."""
        out = StringIO()
        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={"success": True, "tokens_eliminados": 0, "mensaje": "ok"},
            ):
                with patch(
                    "apps.usuarios.models.IntentosLogin.objects.filter",
                    side_effect=Exception("IntentosLogin table missing"),
                ):
                    call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Error", output)


class Cleanup2FAVerboseTest(TestCase):
    """Line 190: verbose print for 2FA attempts when cantidad > 0."""

    def test_verbose_with_2fa_attempts_covers_line_190(self):
        """Line 190: when verbose=True and 2FA count > 0, print line executes."""
        out = StringIO()
        mock_qs = MagicMock()
        mock_qs.count.return_value = 3
        mock_qs.delete.return_value = (3, {})

        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={"success": True, "tokens_eliminados": 0, "mensaje": "ok"},
            ):
                with patch(
                    "apps.usuarios.models.IntentosLogin.objects.filter",
                    return_value=mock_qs,
                ):
                    with patch(
                        "apps.usuarios.models.Intentos2Fa.objects.filter",
                        return_value=mock_qs,
                    ):
                        call_command("cleanup_usuarios", verbose=True, stdout=out)
        output = out.getvalue()
        self.assertIn("Limpieza", output)


class Cleanup2FAExceptionTest(TestCase):
    """Lines 205-207: except block when Intentos2Fa query raises."""

    def test_2fa_attempts_query_raises_covers_except_block(self):
        """Lines 205-207: Intentos2Fa.objects.filter raises → except caught."""
        out = StringIO()
        with patch(
            "apps.usuarios.services.SessionService.limpiar_sesiones_expiradas",
            return_value={"success": True, "sesiones_cerradas": 0, "mensaje": "ok"},
        ):
            with patch(
                "apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados",
                return_value={"success": True, "tokens_eliminados": 0, "mensaje": "ok"},
            ):
                with patch(
                    "apps.usuarios.models.IntentosLogin.objects.filter",
                    return_value=MagicMock(count=MagicMock(return_value=0),
                                          delete=MagicMock(return_value=(0, {}))),
                ):
                    with patch(
                        "apps.usuarios.models.Intentos2Fa.objects.filter",
                        side_effect=Exception("Intentos2Fa table missing"),
                    ):
                        call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Error", output)
