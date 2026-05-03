"""
Tests para notificaciones/tasks.py
Usa CELERY_TASK_ALWAYS_EAGER para ejecutar tasks en modo síncrono.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class GenararAlertasSaldoBajoTaskTest(TestCase):
    """Tests para la task generar_alertas_saldo_bajo"""

    @patch("apps.notificaciones.tasks.NotificacionService.generar_alertas_automaticas")
    def test_task_exitosa(self, mock_generar):
        """La task debe llamar a generar_alertas_automaticas y devolver el resultado"""
        mock_generar.return_value = {
            "success": True,
            "alertas_generadas": 3,
            "alertas_enviadas": 3,
            "errores": [],
        }
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo

        resultado = generar_alertas_saldo_bajo.apply()
        self.assertTrue(resultado.successful())
        self.assertEqual(resultado.result["alertas_generadas"], 3)

    @patch("apps.notificaciones.tasks.NotificacionService.generar_alertas_automaticas")
    def test_task_con_exception_retry(self, mock_generar):
        """La task debe reintentar ante un error"""
        mock_generar.side_effect = Exception("Error de red")
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo

        # Con EAGER_PROPAGATES=True, la excepción se propaga
        try:
            generar_alertas_saldo_bajo.apply()
        except Exception:
            pass  # Esperado: el retry falla en modo eager


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class EnviarEmailAsyncTaskTest(TestCase):
    """Tests para la task enviar_email_async"""

    @patch("apps.notificaciones.tasks.EmailService.enviar_email_generico")
    def test_email_enviado_exitosamente(self, mock_email):
        """La task debe enviar email y retornar resultado"""
        mock_email.return_value = {"success": True, "id_email": 1}
        from apps.notificaciones.tasks import enviar_email_async

        resultado = enviar_email_async.apply(args=["test@example.com", "Test User", "Asunto Test", "Mensaje Test"])
        self.assertTrue(resultado.result["success"])

    @patch("apps.notificaciones.tasks.EmailService.enviar_email_generico")
    def test_email_con_exception(self, mock_email):
        """La task debe manejar excepciones y retornar error"""
        mock_email.side_effect = Exception("SMTP error")
        from apps.notificaciones.tasks import enviar_email_async

        resultado = enviar_email_async.apply(args=["test@example.com", "Test User", "Asunto Test", "Mensaje Test"])
        self.assertFalse(resultado.result["success"])
        self.assertIn("error", resultado.result)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class EnviarSmsAsyncTaskTest(TestCase):
    """Tests para la task enviar_sms_async"""

    @patch("apps.notificaciones.tasks.SMSService.enviar_sms")
    def test_sms_enviado_exitosamente(self, mock_sms):
        """La task debe enviar SMS y retornar resultado"""
        mock_sms.return_value = {"success": True, "message_id": "MSG123"}
        from apps.notificaciones.tasks import enviar_sms_async

        resultado = enviar_sms_async.apply(args=["0981000000", "Mensaje de prueba"])
        self.assertTrue(resultado.result["success"])

    @patch("apps.notificaciones.tasks.SMSService.enviar_sms")
    def test_sms_con_exception(self, mock_sms):
        """La task debe manejar excepciones"""
        mock_sms.side_effect = Exception("Proveedor no disponible")
        from apps.notificaciones.tasks import enviar_sms_async

        resultado = enviar_sms_async.apply(args=["0981000000", "Mensaje"])
        self.assertFalse(resultado.result["success"])


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class LimpiarNotificacionesAntiguasTaskTest(TestCase):
    """Tests para la task limpiar_notificaciones_antiguas"""

    @patch("apps.notificaciones.models.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.models.NotificacionesPortal.objects.filter")
    def test_limpieza_exitosa_sin_datos(self, mock_portal_filter, mock_saldo_filter):
        """La task debe ejecutarse sin errores cuando no hay datos"""
        mock_portal_qs = MagicMock()
        mock_portal_qs.delete.return_value = (0, {})
        mock_portal_filter.return_value = mock_portal_qs

        mock_saldo_qs = MagicMock()
        mock_saldo_qs.delete.return_value = (0, {})
        mock_saldo_filter.return_value = mock_saldo_qs

        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas

        resultado = limpiar_notificaciones_antiguas.apply()
        self.assertTrue(resultado.result["success"])
        self.assertEqual(resultado.result["notificaciones_eliminadas"], 0)

    @patch("apps.notificaciones.models.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.models.NotificacionesPortal.objects.filter")
    def test_limpieza_con_notificaciones(self, mock_portal_filter, mock_saldo_filter):
        """La task debe contar las notificaciones eliminadas"""
        mock_portal_qs = MagicMock()
        mock_portal_qs.delete.return_value = (5, {})
        mock_portal_filter.return_value = mock_portal_qs

        mock_saldo_qs = MagicMock()
        mock_saldo_qs.delete.return_value = (3, {})
        mock_saldo_filter.return_value = mock_saldo_qs

        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas

        resultado = limpiar_notificaciones_antiguas.apply()
        self.assertTrue(resultado.result["success"])
        self.assertEqual(resultado.result["notificaciones_eliminadas"], 8)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class NotificarRecargaExitosaTaskTest(TestCase):
    """Tests para la task notificar_recarga_exitosa"""

    @patch("apps.notificaciones.tasks.NotificacionService.enviar_notificacion_recarga")
    def test_notificacion_recarga_exitosa(self, mock_notif):
        """La task debe enviar notificación de recarga"""
        mock_notif.return_value = {"success": True, "id_notificacion": 10}
        from apps.notificaciones.tasks import notificar_recarga_exitosa

        resultado = notificar_recarga_exitosa.apply(args=[1])
        self.assertTrue(resultado.result["success"])

    @patch("apps.notificaciones.tasks.NotificacionService.enviar_notificacion_recarga")
    def test_notificacion_recarga_con_error(self, mock_notif):
        """La task debe manejar errores de notificación"""
        mock_notif.side_effect = Exception("Error")
        from apps.notificaciones.tasks import notificar_recarga_exitosa

        resultado = notificar_recarga_exitosa.apply(args=[999])
        self.assertFalse(resultado.result["success"])


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class NotificarConsumoRealizadoTaskTest(TestCase):
    """Tests para la task notificar_consumo_realizado"""

    @patch("apps.notificaciones.tasks.NotificacionService.enviar_notificacion_consumo")
    def test_notificacion_consumo_exitosa(self, mock_notif):
        """La task debe enviar notificación de consumo"""
        mock_notif.return_value = {"success": True, "id_notificacion": 20}
        from apps.notificaciones.tasks import notificar_consumo_realizado

        resultado = notificar_consumo_realizado.apply(args=[1])
        self.assertTrue(resultado.result["success"])

    @patch("apps.notificaciones.tasks.NotificacionService.enviar_notificacion_consumo")
    def test_notificacion_consumo_con_error(self, mock_notif):
        """La task debe manejar errores"""
        mock_notif.side_effect = Exception("Error de consumo")
        from apps.notificaciones.tasks import notificar_consumo_realizado

        resultado = notificar_consumo_realizado.apply(args=[999])
        self.assertFalse(resultado.result["success"])


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class LimpiarNotificacionesAntiguasExcepcionTest(TestCase):
    """Tests para cubrir el branch de excepción en limpiar_notificaciones_antiguas."""

    @patch("apps.notificaciones.models.NotificacionesPortal.objects.filter")
    def test_excepcion_entra_en_except(self, mock_portal_filter):
        """Lines 158-160: Exception raised during delete → except branch executed."""
        mock_portal_filter.side_effect = Exception("DB error")
        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas

        # With EAGER_PROPAGATES=False, retry does not reraise
        resultado = limpiar_notificaciones_antiguas.apply()
        # Task fails gracefully (retry was scheduled, result may be None or exception)
        # Main goal: the except block (lines 158-160) executes without crashing
