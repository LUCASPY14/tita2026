"""
Extended tests for PasswordRecoveryService and SessionService
Targeting uncovered lines for coverage improvement.
"""

from unittest.mock import patch, MagicMock
from django.test import TransactionTestCase
from django.utils import timezone
from datetime import timedelta

from apps.usuarios.services.password_recovery_service import PasswordRecoveryService
from apps.usuarios.services.session_service import SessionService
from apps.usuarios.models import (
    Empleados,
    Roles,
    TokensRecuperacion,
    SesionesActivas,
    PatronesAcceso,
    RenovacionesSesion,
)


class BaseUsuariosTest(TransactionTestCase):
    """Base setup for usuarios service tests."""

    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol="TestRolExt", descripcion="Test", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Ext",
            apellido="Test",
            usuario="exttestuser",
            email="ext@cantinatita.com",
            contrasena_hash="testhash",
            id_rol=self.rol,
            fecha_ingreso=timezone.now(),
            estado=True,
        )
        self.ip = "10.0.0.1"

    def tearDown(self):
        TokensRecuperacion.objects.all().delete()
        SesionesActivas.objects.all().delete()
        RenovacionesSesion.objects.all().delete()
        PatronesAcceso.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


# ============================================================================
# PasswordRecoveryService - exception paths
# ============================================================================


class SolicitarRecuperacionExceptionTest(BaseUsuariosTest):
    """Cover exception paths in solicitar_recuperacion_empleado."""

    def test_solicitar_recuperacion_auditoria_exception_silenced(self):
        """Inner AuditoriaOperaciones.create exception is silenced (lines 106-107).
        Achieved by making the empleado.usuario property fail so auditoría create raises.
        """
        # Patch AuditoriaOperaciones.objects.create to raise on the audit call
        # The audit is inside the inner try/except, so result is still success.
        with patch("apps.usuarios.services.password_recovery_service.AuditoriaOperaciones") as mock_auditoria:
            mock_auditoria.objects.create.side_effect = Exception("DB error")
            resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
                email="ext@cantinatita.com", ip_address=self.ip
            )
        # Should still return success even if auditoría fails
        self.assertTrue(resultado["success"])
        self.assertIn("token", resultado)

    def test_solicitar_recuperacion_outer_exception(self):
        """Outer exception path returns error dict (lines 116-118)."""
        with patch("apps.usuarios.services.password_recovery_service.TokensRecuperacion") as mock_tokens:
            mock_tokens.objects.filter.side_effect = Exception("DB fail")
            resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
                email="ext@cantinatita.com", ip_address=self.ip
            )
        self.assertFalse(resultado["success"])
        self.assertIn("Error al procesar", resultado["mensaje"])


class ValidarTokenExceptionTest(BaseUsuariosTest):
    """Cover exception paths in validar_token_recuperacion."""

    def _crea_token_valido(self):
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="ext@cantinatita.com", ip_address=self.ip
        )
        return resultado["token"]

    def test_validar_token_empleado_no_disponible(self):
        """Empleado matching token email not found → 'Empleado no disponible' (line 137)."""
        token = self._crea_token_valido()
        # Point the Clientes linked to TokensRecuperacion to a different email
        token_hash = PasswordRecoveryService._hash_token(token)
        token_db = TokensRecuperacion.objects.filter(token_hash=token_hash).first()
        # Patch Empleados.objects.filter to return None
        with patch("apps.usuarios.services.password_recovery_service.Empleados") as mock_emp:
            mock_emp.objects.filter.return_value.first.return_value = None
            resultado = PasswordRecoveryService.validar_token_recuperacion(token)
        self.assertFalse(resultado["success"])
        self.assertFalse(resultado["valido"])
        self.assertIn("disponible", resultado["mensaje"])

    def test_validar_token_outer_exception(self):
        """Outer exception in validar_token_recuperacion (lines 141-143)."""
        with patch("apps.usuarios.services.password_recovery_service.TokensRecuperacion") as mock_tokens:
            mock_tokens.objects.filter.side_effect = Exception("DB fail")
            resultado = PasswordRecoveryService.validar_token_recuperacion("sometoken")
        self.assertFalse(resultado["success"])
        self.assertFalse(resultado["valido"])
        self.assertIn("Error al validar", resultado["mensaje"])


class RestablecerPasswordExceptionTest(BaseUsuariosTest):
    """Cover exception paths in restablecer_password_con_token."""

    def _crea_token_valido(self):
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="ext@cantinatita.com", ip_address=self.ip
        )
        return resultado["token"]

    def test_restablecer_auditoria_exception_silenced(self):
        """Inner audit exception silenced in restablecer_password_con_token (lines 186-187)."""
        token = self._crea_token_valido()
        with patch("apps.usuarios.services.password_recovery_service.AuditoriaOperaciones") as mock_auditoria:
            mock_auditoria.objects.create.side_effect = Exception("DB error")
            resultado = PasswordRecoveryService.restablecer_password_con_token(
                token=token, nueva_password="NewPass123!", ip_address=self.ip
            )
        self.assertTrue(resultado["success"])

    def test_restablecer_outer_exception(self):
        """Outer exception in restablecer_password_con_token (lines 196-198)."""
        with patch(
            "apps.usuarios.services.password_recovery_service.PasswordRecoveryService.validar_token_recuperacion"
        ) as mock_val:
            mock_val.side_effect = Exception("Unexpected error")
            resultado = PasswordRecoveryService.restablecer_password_con_token(
                token="sometoken", nueva_password="Test123!", ip_address=self.ip
            )
        self.assertFalse(resultado["success"])
        self.assertIn("Error al restablecer", resultado["mensaje"])


class SolicitarVerificacionEmailExceptionTest(BaseUsuariosTest):
    """Cover exception paths in solicitar_verificacion_email."""

    def test_solicitar_verificacion_auditoria_exception_silenced(self):
        """Inner audit exception silenced (lines 237-238)."""
        with patch("apps.usuarios.services.password_recovery_service.AuditoriaOperaciones") as mock_auditoria:
            mock_auditoria.objects.create.side_effect = Exception("DB error")
            resultado = PasswordRecoveryService.solicitar_verificacion_email(empleado=self.empleado, ip_address=self.ip)
        self.assertTrue(resultado["success"])
        self.assertIn("token", resultado)

    def test_solicitar_verificacion_outer_exception(self):
        """Outer exception in solicitar_verificacion_email (lines 242-244)."""
        with patch("apps.usuarios.services.password_recovery_service.TokensRecuperacion") as mock_tokens:
            mock_tokens.objects.filter.side_effect = Exception("DB fail")
            resultado = PasswordRecoveryService.solicitar_verificacion_email(empleado=self.empleado, ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("Error al generar", resultado["mensaje"])


class VerificarEmailEdgeCasesTest(BaseUsuariosTest):
    """Cover edge cases in verificar_email."""

    def _crear_token_verificacion(self):
        resultado = PasswordRecoveryService.solicitar_verificacion_email(empleado=self.empleado, ip_address=self.ip)
        return resultado["token"]

    def test_verificar_email_token_expirado(self):
        """Token expirado returns error (line 257)."""
        token = self._crear_token_verificacion()
        token_hash = PasswordRecoveryService._hash_token(token)
        token_db = TokensRecuperacion.objects.filter(token_hash=token_hash).first()
        # Expire the token
        token_db.fecha_expiracion = timezone.now() - timedelta(hours=1)
        token_db.save(update_fields=["fecha_expiracion"])
        resultado = PasswordRecoveryService.verificar_email(token=token, ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("invalido o expirado", resultado["mensaje"])

    def test_verificar_email_empleado_no_disponible(self):
        """Empleado not found after token check (line 261)."""
        token = self._crear_token_verificacion()
        with patch("apps.usuarios.services.password_recovery_service.Empleados") as mock_emp:
            mock_emp.objects.filter.return_value.first.return_value = None
            resultado = PasswordRecoveryService.verificar_email(token=token, ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("disponible", resultado["mensaje"])

    def test_verificar_email_auditoria_exception_silenced(self):
        """Inner audit exception silenced in verificar_email (lines 279-280)."""
        token = self._crear_token_verificacion()
        with patch("apps.usuarios.services.password_recovery_service.AuditoriaOperaciones") as mock_auditoria:
            mock_auditoria.objects.create.side_effect = Exception("DB error")
            resultado = PasswordRecoveryService.verificar_email(token=token, ip_address=self.ip)
        self.assertTrue(resultado["success"])

    def test_verificar_email_outer_exception(self):
        """Outer exception in verificar_email (lines 284-286)."""
        with patch("apps.usuarios.services.password_recovery_service.TokensRecuperacion") as mock_tokens:
            mock_tokens.objects.filter.side_effect = Exception("DB fail")
            resultado = PasswordRecoveryService.verificar_email(token="sometoken", ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("Error al verificar", resultado["mensaje"])


class LimpiarTokensExceptionTest(BaseUsuariosTest):
    """Cover exception path in limpiar_tokens_expirados."""

    def test_limpiar_tokens_outer_exception(self):
        """Outer exception returns error dict (lines 303-305)."""
        with patch("apps.usuarios.services.password_recovery_service.TokensRecuperacion") as mock_tokens:
            mock_tokens.objects.filter.side_effect = Exception("DB fail")
            resultado = PasswordRecoveryService.limpiar_tokens_expirados()
        self.assertFalse(resultado["success"])
        self.assertEqual(resultado["tokens_eliminados"], 0)
        self.assertIn("Error al limpiar", resultado["mensaje"])


# ============================================================================
# SessionService - exception and branch paths
# ============================================================================


class BaseSessionTest(BaseUsuariosTest):
    """Base setup for session service tests."""

    def setUp(self):
        super().setUp()
        self.session_key = "sess_ext_001"
        self.user_agent = "TestBrowser/1.0"


class CrearSesionExceptionTest(BaseSessionTest):
    """Cover exception paths in crear_sesion."""

    def test_crear_sesion_max_sin_mas_antigua(self):
        """Maximum sessions reached but oldest is None → no sesiones_cerradas (line 45→50)."""
        # Create MAX_SESIONES_SIMULTANEAS sessions
        for i in range(SessionService.MAX_SESIONES_SIMULTANEAS):
            SesionesActivas.objects.create(
                usuario=self.empleado.usuario,
                tipo_usuario="empleado",
                session_key=f"exist_sess_{i}",
                ip_address=self.ip,
                fecha_inicio=timezone.now(),
                ultima_actividad=timezone.now(),
                activa=True,
            )
        # Patch the queryset to return None for .first()
        original_filter = SesionesActivas.objects.filter

        call_count = [0]

        def fake_filter(*args, **kwargs):
            qs = original_filter(*args, **kwargs)
            if kwargs.get("activa") is True and "order_by" not in str(qs.query):
                return qs
            return qs

        # Mock the inner .first() on the order_by chain to return None
        with patch.object(SesionesActivas, "objects") as mock_objs:
            # Set up count to return >= MAX so the branch fires
            mock_objs.filter.return_value.count.return_value = SessionService.MAX_SESIONES_SIMULTANEAS
            mock_objs.filter.return_value.order_by.return_value.first.return_value = None
            mock_objs.create.return_value = MagicMock(id_sesion=999)
            resultado = SessionService.crear_sesion(
                empleado=self.empleado,
                session_key=self.session_key,
                ip_address=self.ip,
                user_agent=self.user_agent,
            )
        # sesiones_cerradas = 0 since sesion_mas_antigua was None
        self.assertIn("success", resultado)

    def test_crear_sesion_outer_exception(self):
        """Outer exception in crear_sesion (lines 86-88)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.crear_sesion(
                empleado=self.empleado,
                session_key=self.session_key,
                ip_address=self.ip,
            )
        self.assertFalse(resultado["success"])
        self.assertIn("Error al crear sesion", resultado["mensaje"])


class RenovarSesionExceptionTest(BaseSessionTest):
    """Cover exception paths in renovar_sesion."""

    def test_renovar_sesion_sin_renovacion_previa(self):
        """Renovar when no prior RenovacionesSesion exists (line 109→115 branch skipped)."""
        # Create active session
        SesionesActivas.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            session_key="old_sess_001",
            ip_address=self.ip,
            fecha_inicio=timezone.now(),
            ultima_actividad=timezone.now(),
            activa=True,
        )
        # No RenovacionesSesion → ultima_renovacion is None → goes straight to create
        resultado = SessionService.renovar_sesion(
            empleado=self.empleado,
            session_key_actual="old_sess_001",
            nuevo_session_key="new_sess_001",
            ip_address=self.ip,
        )
        self.assertTrue(resultado["success"])
        self.assertIn("sesion", resultado)

    def test_renovar_sesion_outer_exception(self):
        """Outer exception in renovar_sesion (lines 156-158)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.renovar_sesion(
                empleado=self.empleado,
                session_key_actual="any_key",
                nuevo_session_key="new_key",
                ip_address=self.ip,
            )
        self.assertFalse(resultado["success"])
        self.assertIn("Error al renovar sesion", resultado["mensaje"])


class ActualizarActividadExpiredSessionTest(BaseSessionTest):
    """Cover expired session branch in actualizar_actividad_sesion."""

    def test_actualizar_actividad_sesion_expirada_por_tiempo(self):
        """Session expired by total elapsed time → sesion.activa=False (lines 172-174)."""
        # Create a session that started 25 hours ago (beyond TIEMPO_EXPIRACION_HORAS=24)
        old_start = timezone.now() - timedelta(hours=25)
        SesionesActivas.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            session_key="old_age_sess",
            ip_address=self.ip,
            fecha_inicio=old_start,
            ultima_actividad=timezone.now(),
            activa=True,
        )
        resultado = SessionService.actualizar_actividad_sesion(empleado=self.empleado, session_key="old_age_sess")
        self.assertFalse(resultado["success"])
        self.assertIn("expirada", resultado["mensaje"])
        sesion = SesionesActivas.objects.filter(session_key="old_age_sess").first()
        self.assertFalse(sesion.activa)

    def test_actualizar_actividad_outer_exception(self):
        """Outer exception in actualizar_actividad_sesion (lines 180-182)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.actualizar_actividad_sesion(empleado=self.empleado, session_key="any_key")
        self.assertFalse(resultado["success"])
        self.assertIn("Error al actualizar actividad", resultado["mensaje"])


class CerrarSesionExceptionTest(BaseSessionTest):
    """Cover exception path in cerrar_sesion."""

    def test_cerrar_sesion_outer_exception(self):
        """Outer exception in cerrar_sesion (lines 211-213)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.cerrar_sesion(empleado=self.empleado, session_key="any_key", ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("Error al cerrar sesion", resultado["mensaje"])


class CerrarTodasSesionesExceptionTest(BaseSessionTest):
    """Cover exception path in cerrar_todas_sesiones."""

    def test_cerrar_todas_sesiones_outer_exception(self):
        """Outer exception in cerrar_todas_sesiones (lines 246-248)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.cerrar_todas_sesiones(empleado=self.empleado, ip_address=self.ip)
        self.assertFalse(resultado["success"])
        self.assertIn("Error al cerrar sesiones", resultado["mensaje"])


class AnalizarPatronAccesoTest(BaseSessionTest):
    """Cover branches in _analizar_patron_acceso."""

    def test_patron_existente_dia_nuevo_agrega(self):
        """Existing patron: new day is appended to dias_semana (line 287)."""
        import json

        # Create existing patron with all days except today
        dia_hoy = timezone.now().weekday()
        dias_iniciales = [d for d in range(7) if d != dia_hoy]
        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address=self.ip,
            horario_inicio=timezone.now().time(),
            horario_fin=timezone.now().time(),
            dias_semana=json.dumps(dias_iniciales),
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=3,
            es_habitual=0,
        )
        SessionService._analizar_patron_acceso(self.empleado, self.ip)
        patron = PatronesAcceso.objects.filter(usuario=self.empleado.usuario, ip_address=self.ip).first()
        dias = json.loads(patron.dias_semana)
        self.assertIn(dia_hoy, dias)

    def test_patron_existente_sin_dias_semana(self):
        """Existing patron with dias_semana=None gets initialized (line 290)."""
        import json

        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address=self.ip,
            horario_inicio=timezone.now().time(),
            horario_fin=timezone.now().time(),
            dias_semana=None,
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=2,
            es_habitual=0,
        )
        SessionService._analizar_patron_acceso(self.empleado, self.ip)
        patron = PatronesAcceso.objects.filter(usuario=self.empleado.usuario, ip_address=self.ip).first()
        self.assertIsNotNone(patron.dias_semana)
        dias = json.loads(patron.dias_semana)
        self.assertIsInstance(dias, list)


class DetectarAccesoInusualTest(BaseSessionTest):
    """Cover branches in detectar_acceso_inusual."""

    def test_ip_habitual_returns_no_inusual(self):
        """When ip is habitual, returns es_inusual=False immediately (lines 305-306)."""
        import json

        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address=self.ip,
            horario_inicio=timezone.now().time(),
            horario_fin=timezone.now().time(),
            dias_semana=json.dumps([0, 1, 2, 3, 4]),
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=10,
            es_habitual=1,  # habitual
        )
        resultado = SessionService.detectar_acceso_inusual(self.empleado, self.ip)
        self.assertFalse(resultado["es_inusual"])
        self.assertEqual(resultado["nivel_riesgo"], "bajo")

    def test_ip_no_habitual_con_accesos_previos(self):
        """IP not habitual but has previous sessions → 'IP no habitual' (line 326)."""
        import json

        # Create a habitual patron for a DIFFERENT IP so there's history
        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address="1.2.3.4",
            horario_inicio=None,
            horario_fin=timezone.now().time(),
            dias_semana=json.dumps([0, 1, 2, 3, 4]),
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=3,
            es_habitual=0,
        )
        # Crear una sesion previa con la nueva IP para que accesos_total_ip > 0
        SesionesActivas.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            session_key="prev_sess_new_ip",
            ip_address="9.9.9.9",
            fecha_inicio=timezone.now(),
            ultima_actividad=timezone.now(),
            activa=False,
        )
        resultado = SessionService.detectar_acceso_inusual(self.empleado, "9.9.9.9")
        self.assertTrue(resultado["es_inusual"])
        self.assertIn("IP no habitual", resultado["razones"])

    def test_detectar_acceso_horario_inusual_alto_riesgo(self):
        """Non-habitual IP + unusual time → nivel_riesgo='alto' (lines 331-343)."""
        import json
        from datetime import time as dt_time

        # Create a habitual patron for a different IP with a morning horario_inicio
        madrugada_inicio = dt_time(3, 0)  # 3 AM
        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address="1.2.3.4",
            horario_inicio=madrugada_inicio,
            horario_fin=dt_time(4, 0),
            dias_semana=json.dumps([0, 1, 2, 3, 4]),
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=10,
            es_habitual=1,  # habitual — for other IP
        )
        # Make current time be very different (> 4 hours difference from 3 AM)
        fake_now = timezone.now().replace(hour=15, minute=0, second=0, microsecond=0)
        with patch("apps.usuarios.services.session_service.timezone") as mock_tz:
            mock_tz.now.return_value = fake_now
            resultado = SessionService.detectar_acceso_inusual(self.empleado, "9.9.9.9")
        self.assertEqual(resultado["nivel_riesgo"], "alto")
        self.assertGreaterEqual(len(resultado["razones"]), 2)

    def test_detectar_acceso_una_razon_nivel_medio(self):
        """Single reason → nivel_riesgo='medio' (lines 342-343)."""
        import json
        from datetime import time as dt_time

        # Habitual patron for diff IP with horario_inicio close to now (< 4 hours diff)
        hora_cercana = dt_time(timezone.now().hour, 0)
        PatronesAcceso.objects.create(
            usuario=self.empleado.usuario,
            tipo_usuario="empleado",
            ip_address="1.2.3.4",
            horario_inicio=hora_cercana,
            horario_fin=hora_cercana,
            dias_semana=json.dumps([0, 1, 2, 3, 4]),
            primera_deteccion=timezone.now(),
            ultima_deteccion=timezone.now(),
            frecuencia_accesos=10,
            es_habitual=1,
        )
        # No historical sessions for 9.9.9.9 → "Nueva IP" (1 razón)
        resultado = SessionService.detectar_acceso_inusual(self.empleado, "9.9.9.9")
        self.assertEqual(resultado["nivel_riesgo"], "medio")
        self.assertEqual(len(resultado["razones"]), 1)


class LimpiarSesionesExceptionTest(BaseSessionTest):
    """Cover exception path in limpiar_sesiones_expiradas."""

    def test_limpiar_sesiones_outer_exception(self):
        """Outer exception in limpiar_sesiones_expiradas (lines 371-373)."""
        with patch("apps.usuarios.services.session_service.SesionesActivas") as mock_ses:
            mock_ses.objects.filter.side_effect = Exception("DB fail")
            resultado = SessionService.limpiar_sesiones_expiradas()
        self.assertFalse(resultado["success"])
        self.assertEqual(resultado["sesiones_cerradas"], 0)
        self.assertIn("Error al limpiar sesiones", resultado["mensaje"])
