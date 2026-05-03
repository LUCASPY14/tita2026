"""
Tests para notificaciones/services/__init__.py (NotificacionService)
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone


class NotificacionServiceImportTest(TestCase):
    """Test que el módulo se importa correctamente"""

    def test_importar_servicio(self):
        from apps.notificaciones.services import NotificacionService

        self.assertIsNotNone(NotificacionService)

    def test_metodos_existen(self):
        from apps.notificaciones.services import NotificacionService

        self.assertTrue(hasattr(NotificacionService, "enviar_notificacion_saldo_bajo"))
        self.assertTrue(hasattr(NotificacionService, "enviar_notificacion_recarga"))
        self.assertTrue(hasattr(NotificacionService, "enviar_notificacion_consumo"))
        self.assertTrue(hasattr(NotificacionService, "generar_alertas_automaticas"))


class NotificacionServiceSaldoBajoTest(TestCase):
    """Tests para enviar_notificacion_saldo_bajo"""

    def _crear_mocks_tarjeta(self, mock_tarjetas_get, telefono="0981000000", email="test@test.com"):
        hijo_mock = MagicMock()
        hijo_mock.nombre = "Pedro"
        hijo_mock.apellido = "García"

        cliente_mock = MagicMock()
        cliente_mock.nombre = "Juan"
        cliente_mock.apellido = "García"
        cliente_mock.email = email
        cliente_mock.telefono = telefono

        hijo_mock.id_cliente = cliente_mock

        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.id_hijo = hijo_mock

        mock_tarjetas_get.return_value = tarjeta_mock
        return tarjeta_mock, hijo_mock, cliente_mock

    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.core.models.Tarjetas.objects.select_related")
    def test_tarjeta_no_existe(self, mock_select, mock_create):
        from apps.core.models import Tarjetas
        from apps.notificaciones.services import NotificacionService

        mock_chain = MagicMock()
        mock_chain.get.side_effect = Tarjetas.DoesNotExist()
        mock_select.return_value = mock_chain

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_saldo_bajo(
                nro_tarjeta="NOEEXISTE",
                saldo_actual=Decimal("5000"),
                saldo_alerta=Decimal("10000"),
            )

    @patch(
        "apps.notificaciones.services.email_service.EmailService.enviar_alerta_saldo_bajo",
        return_value={"success": True},
    )
    @patch("apps.notificaciones.services.sms_service.SMSService.enviar_sms", return_value={"success": True})
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_notificacion_exitosa_con_email_y_sms(self, mock_select, mock_create, mock_sms, mock_email):
        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Pedro"
        hijo_mock.apellido = "García"
        cliente_mock = MagicMock()
        cliente_mock.nombre = "Juan"
        cliente_mock.apellido = "García"
        cliente_mock.email = "test@test.com"
        cliente_mock.telefono = "0981000000"
        hijo_mock.id_cliente = cliente_mock
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.id_hijo = hijo_mock

        mock_chain = MagicMock()
        mock_chain.get.return_value = tarjeta_mock
        mock_select.return_value = mock_chain

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 1
        mock_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_saldo_bajo(
            nro_tarjeta="TAR001",
            saldo_actual=Decimal("5000"),
            saldo_alerta=Decimal("10000"),
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["id_notificacion"], 1)


class NotificacionServiceRecargaTest(TestCase):
    """Tests para enviar_notificacion_recarga"""

    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_recarga_no_completada(self, mock_select):
        from apps.notificaciones.services import NotificacionService

        recarga_mock = MagicMock()
        recarga_mock.estado = "pendiente"

        mock_chain = MagicMock()
        mock_chain.get.return_value = recarga_mock
        mock_select.return_value = mock_chain

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_recarga(id_recarga=1)

    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_recarga_no_existe(self, mock_select):
        from apps.core.models import CargasSaldo
        from apps.notificaciones.services import NotificacionService

        mock_chain = MagicMock()
        mock_chain.get.side_effect = CargasSaldo.DoesNotExist()
        mock_select.return_value = mock_chain

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_recarga(id_recarga=9999)

    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_recarga_sin_usuario_portal(self, mock_select, mock_usuario_get):
        from apps.notificaciones.services import NotificacionService
        from apps.usuarios.models import UsuariosPortal

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Ana"
        hijo_mock.apellido = "Pérez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR002"
        tarjeta_mock.saldo_actual = Decimal("30000")
        tarjeta_mock.id_hijo = hijo_mock

        recarga_mock = MagicMock()
        recarga_mock.estado = "completada"
        recarga_mock.nro_tarjeta = tarjeta_mock
        recarga_mock.monto_cargado = Decimal("20000")
        recarga_mock.metodo_pago = "Efectivo"
        recarga_mock.fecha_carga = timezone.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = recarga_mock
        mock_select.return_value = mock_chain

        # Usuario portal no existe
        mock_usuario_get.side_effect = UsuariosPortal.DoesNotExist()

        result = NotificacionService.enviar_notificacion_recarga(id_recarga=1)
        # Sin usuario portal, debe retornar False con error
        self.assertFalse(result["success"])


class NotificacionServiceConsumoTest(TestCase):
    """Tests para enviar_notificacion_consumo"""

    @patch("apps.core.models.ConsumosTarjeta.objects.select_related")
    def test_consumo_no_existe(self, mock_select):
        from apps.core.models import ConsumosTarjeta
        from apps.notificaciones.services import NotificacionService

        mock_chain = MagicMock()
        mock_chain.get.side_effect = ConsumosTarjeta.DoesNotExist()
        mock_select.return_value = mock_chain

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_consumo(id_consumo=9999)


class NotificacionServiceGenararAlertasTest(TestCase):
    """Tests para generar_alertas_automaticas"""

    @patch("apps.core.models.Tarjetas.objects.filter")
    def test_sin_tarjetas_con_saldo_bajo(self, mock_filter):
        from apps.notificaciones.services import NotificacionService

        mock_filter.return_value.select_related.return_value = []

        result = NotificacionService.generar_alertas_automaticas()
        self.assertTrue(result["success"])
        self.assertEqual(result["alertas_generadas"], 0)
        self.assertEqual(result["alertas_enviadas"], 0)


class NotificacionServiceSaldoBajoEmailErrorTest(TestCase):
    """Cover email/SMS exception paths in enviar_notificacion_saldo_bajo (lines 136-138, 158-160)."""

    @patch(
        "apps.notificaciones.services.email_service.EmailService.enviar_alerta_saldo_bajo",
        side_effect=Exception("Email error"),
    )
    @patch("apps.notificaciones.services.sms_service.SMSService.enviar_sms", side_effect=Exception("SMS error"))
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_email_y_sms_exception_pasan_silenciosamente(self, mock_select, mock_create, mock_sms, mock_email):
        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Pedro"
        hijo_mock.apellido = "García"
        cliente_mock = MagicMock()
        cliente_mock.nombre = "Juan"
        cliente_mock.apellido = "García"
        cliente_mock.email = "test@test.com"
        cliente_mock.telefono = "0981000000"
        hijo_mock.id_cliente = cliente_mock
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.id_hijo = hijo_mock

        mock_chain = MagicMock()
        mock_chain.get.return_value = tarjeta_mock
        mock_select.return_value = mock_chain

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 1
        mock_create.return_value = notif_mock

        # Should NOT raise - email/sms errors are caught silently
        result = NotificacionService.enviar_notificacion_saldo_bajo(
            nro_tarjeta="TAR001",
            saldo_actual=Decimal("5000"),
            saldo_alerta=Decimal("10000"),
        )
        self.assertTrue(result["success"])
        self.assertFalse(result["enviada_email"])
        self.assertFalse(result["enviada_sms"])

    @patch(
        "apps.notificaciones.services.email_service.EmailService.enviar_alerta_saldo_bajo",
        return_value={"success": True},
    )
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_sin_telefono_no_envia_sms(self, mock_select, mock_create, mock_email):
        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Pedro"
        hijo_mock.apellido = "García"
        cliente_mock = MagicMock()
        cliente_mock.nombre = "Juan"
        cliente_mock.apellido = "García"
        cliente_mock.email = "test@test.com"
        cliente_mock.telefono = None  # No phone
        hijo_mock.id_cliente = cliente_mock
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.id_hijo = hijo_mock

        mock_chain = MagicMock()
        mock_chain.get.return_value = tarjeta_mock
        mock_select.return_value = mock_chain

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 2
        mock_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_saldo_bajo(
            nro_tarjeta="TAR001",
            saldo_actual=Decimal("5000"),
            saldo_alerta=Decimal("10000"),
            enviar_sms=True,
        )
        self.assertTrue(result["success"])
        self.assertFalse(result["enviada_sms"])


class NotificacionServiceRecargaCompletadaTest(TestCase):
    """Cover recarga completada success path (lines 234, 243-258)."""

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.create")
    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_recarga_completada_crea_notificacion_portal(self, mock_select, mock_usuario_get, mock_portal_create):
        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Ana"
        hijo_mock.apellido = "López"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR003"
        tarjeta_mock.saldo_actual = Decimal("50000")
        tarjeta_mock.id_hijo = hijo_mock

        recarga_mock = MagicMock()
        recarga_mock.estado = "completada"
        recarga_mock.nro_tarjeta = tarjeta_mock
        recarga_mock.monto_cargado = Decimal("20000")
        recarga_mock.metodo_pago = "Efectivo"
        import django.utils.timezone as tz_module

        recarga_mock.fecha_carga = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = recarga_mock
        mock_select.return_value = mock_chain

        usuario_portal_mock = MagicMock()
        mock_usuario_get.return_value = usuario_portal_mock

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 42
        mock_portal_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_recarga(id_recarga=1, id_usuario_portal=5)
        self.assertTrue(result["success"])
        self.assertEqual(result["id_notificacion"], 42)

    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_recarga_sin_id_usuario_portal_no_existe(self, mock_select, mock_usuario_get):
        from apps.notificaciones.services import NotificacionService
        from apps.usuarios.models import UsuariosPortal

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Ana"
        hijo_mock.apellido = "López"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR003"
        tarjeta_mock.saldo_actual = Decimal("50000")
        tarjeta_mock.id_hijo = hijo_mock

        recarga_mock = MagicMock()
        recarga_mock.estado = "completada"
        recarga_mock.nro_tarjeta = tarjeta_mock
        recarga_mock.monto_cargado = Decimal("20000")
        recarga_mock.metodo_pago = "Efectivo"
        import django.utils.timezone as tz_module

        recarga_mock.fecha_carga = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = recarga_mock
        mock_select.return_value = mock_chain

        mock_usuario_get.side_effect = UsuariosPortal.DoesNotExist()

        result = NotificacionService.enviar_notificacion_recarga(id_recarga=1)
        self.assertFalse(result["success"])


class NotificacionServiceConsumoExitosoTest(TestCase):
    """Cover consumo exitoso path."""

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.create")
    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.ConsumosTarjeta.objects.select_related")
    def test_consumo_exitoso_con_usuario_portal(self, mock_select, mock_usuario_get, mock_portal_create):
        import django.utils.timezone as tz_module

        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Carlos"
        hijo_mock.apellido = "Mendez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.id_hijo = hijo_mock

        consumo_mock = MagicMock()
        consumo_mock.nro_tarjeta = tarjeta_mock
        consumo_mock.monto_consumido = Decimal("5000")
        consumo_mock.saldo_anterior = Decimal("30000")
        consumo_mock.saldo_nuevo = Decimal("25000")
        consumo_mock.fecha_consumo = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = consumo_mock
        mock_select.return_value = mock_chain

        usuario_mock = MagicMock()
        mock_usuario_get.return_value = usuario_mock

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 10
        mock_portal_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_consumo(id_consumo=1, id_usuario_portal=5)
        self.assertTrue(result["success"])
        self.assertEqual(result["id_notificacion"], 10)

    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.ConsumosTarjeta.objects.select_related")
    def test_consumo_sin_usuario_portal(self, mock_select, mock_usuario_get):
        import django.utils.timezone as tz_module

        from apps.notificaciones.services import NotificacionService
        from apps.usuarios.models import UsuariosPortal

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Carlos"
        hijo_mock.apellido = "Mendez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.id_hijo = hijo_mock

        consumo_mock = MagicMock()
        consumo_mock.nro_tarjeta = tarjeta_mock
        consumo_mock.monto_consumido = Decimal("5000")
        consumo_mock.saldo_anterior = Decimal("30000")
        consumo_mock.saldo_nuevo = Decimal("25000")
        consumo_mock.fecha_consumo = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = consumo_mock
        mock_select.return_value = mock_chain

        mock_usuario_get.side_effect = UsuariosPortal.DoesNotExist()

        result = NotificacionService.enviar_notificacion_consumo(id_consumo=1)
        self.assertFalse(result["success"])


class NotificacionServiceAlertasConTarjetasTest(TestCase):
    """Cover generar_alertas_automaticas main body with tarjetas (lines 296-340)."""

    @patch("apps.notificaciones.services.NotificacionService.enviar_notificacion_saldo_bajo")
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.services.Tarjetas.objects.filter")
    def test_con_tarjeta_sin_alerta_reciente_genera_alerta(self, mock_tarjetas_filter, mock_notif_filter, mock_enviar):
        from apps.notificaciones.services import NotificacionService

        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.saldo_actual = Decimal("5000")
        tarjeta_mock.saldo_alerta = Decimal("10000")

        mock_tarjetas_filter.return_value.select_related.return_value = [tarjeta_mock]

        # No recent alert
        notif_filter_chain = MagicMock()
        notif_filter_chain.exists.return_value = False
        mock_notif_filter.return_value = notif_filter_chain

        mock_enviar.return_value = {
            "success": True,
            "enviada_email": True,
            "enviada_sms": False,
        }

        result = NotificacionService.generar_alertas_automaticas()
        self.assertTrue(result["success"])
        self.assertEqual(result["alertas_generadas"], 1)
        self.assertEqual(result["alertas_enviadas"], 1)

    @patch("apps.notificaciones.services.NotificacionService.enviar_notificacion_saldo_bajo")
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.services.Tarjetas.objects.filter")
    def test_con_alerta_reciente_salta(self, mock_tarjetas_filter, mock_notif_filter, mock_enviar):
        from apps.notificaciones.services import NotificacionService

        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.saldo_actual = Decimal("5000")
        tarjeta_mock.saldo_alerta = Decimal("10000")

        mock_tarjetas_filter.return_value.select_related.return_value = [tarjeta_mock]

        # Recent alert found
        notif_filter_chain = MagicMock()
        notif_filter_chain.exists.return_value = True
        mock_notif_filter.return_value = notif_filter_chain

        result = NotificacionService.generar_alertas_automaticas()
        self.assertTrue(result["success"])
        # Alert not sent because recent exists
        self.assertEqual(result["alertas_generadas"], 0)
        mock_enviar.assert_not_called()

    @patch(
        "apps.notificaciones.services.NotificacionService.enviar_notificacion_saldo_bajo",
        side_effect=Exception("Error al enviar"),
    )
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.services.Tarjetas.objects.filter")
    def test_error_al_enviar_registra_en_errores(self, mock_tarjetas_filter, mock_notif_filter, mock_enviar):
        from apps.notificaciones.services import NotificacionService

        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.saldo_actual = Decimal("5000")
        tarjeta_mock.saldo_alerta = Decimal("10000")

        mock_tarjetas_filter.return_value.select_related.return_value = [tarjeta_mock]

        notif_filter_chain = MagicMock()
        notif_filter_chain.exists.return_value = False
        mock_notif_filter.return_value = notif_filter_chain

        result = NotificacionService.generar_alertas_automaticas()
        self.assertTrue(result["success"])
        self.assertEqual(len(result["errores"]), 1)


class NotificacionServiceObtenerPreferenciasTest(TestCase):
    """Cover obtener_preferencias_usuario (lines 375-397)."""

    @patch("apps.notificaciones.services.PreferenciasNotificacion.objects.filter")
    def test_obtener_preferencias_lista(self, mock_filter):
        from apps.notificaciones.services import NotificacionService

        pref_mock = MagicMock()
        pref_mock.tipo_notificacion = "saldo_bajo"
        pref_mock.email_activo = 1
        pref_mock.push_activo = 0
        mock_filter.return_value = [pref_mock]

        result = NotificacionService.obtener_preferencias_usuario(id_usuario_portal=1)
        self.assertIn("preferencias", result)
        self.assertEqual(len(result["preferencias"]), 1)
        self.assertEqual(result["preferencias"][0]["tipo_notificacion"], "saldo_bajo")
        self.assertTrue(result["preferencias"][0]["email_activo"])

    @patch("apps.notificaciones.services.PreferenciasNotificacion.objects.filter")
    def test_obtener_preferencias_vacia(self, mock_filter):
        from apps.notificaciones.services import NotificacionService

        mock_filter.return_value = []
        result = NotificacionService.obtener_preferencias_usuario(id_usuario_portal=1)
        self.assertEqual(result["preferencias"], [])

    @patch("apps.notificaciones.services.PreferenciasNotificacion.objects.filter", side_effect=Exception("DB error"))
    def test_obtener_preferencias_excepcion_retorna_vacia(self, mock_filter):
        from apps.notificaciones.services import NotificacionService

        result = NotificacionService.obtener_preferencias_usuario(id_usuario_portal=1)
        self.assertEqual(result["preferencias"], [])


class NotificacionServiceMarcarLeidaTest(TestCase):
    """Cover marcar_notificacion_leida (lines 407-481)."""

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.get")
    def test_marcar_portal_leida(self, mock_get):
        from apps.notificaciones.services import NotificacionService

        notif_mock = MagicMock()
        import django.utils.timezone as tz_module

        notif_mock.fecha_lectura = tz_module.now()
        mock_get.return_value = notif_mock

        result = NotificacionService.marcar_notificacion_leida(id_notificacion=1, tipo="portal")
        self.assertTrue(result["success"])
        notif_mock.save.assert_called_once()

    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.get")
    def test_marcar_saldo_leida(self, mock_get):
        from apps.notificaciones.services import NotificacionService

        notif_mock = MagicMock()
        import django.utils.timezone as tz_mod

        notif_mock.fecha_lectura = tz_mod.now()
        mock_get.return_value = notif_mock

        result = NotificacionService.marcar_notificacion_leida(id_notificacion=2, tipo="saldo")
        self.assertTrue(result["success"])
        notif_mock.save.assert_called_once()

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.get")
    def test_marcar_portal_no_existe_raises(self, mock_get):
        from apps.notificaciones.models import NotificacionesPortal
        from apps.notificaciones.services import NotificacionService

        mock_get.side_effect = NotificacionesPortal.DoesNotExist()

        with self.assertRaises(ValidationError):
            NotificacionService.marcar_notificacion_leida(id_notificacion=999, tipo="portal")

    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.get")
    def test_marcar_saldo_no_existe_raises(self, mock_get):
        from apps.notificaciones.models import NotificacionesSaldo
        from apps.notificaciones.services import NotificacionService

        mock_get.side_effect = NotificacionesSaldo.DoesNotExist()

        with self.assertRaises(ValidationError):
            NotificacionService.marcar_notificacion_leida(id_notificacion=999, tipo="saldo")


class NotificacionServiceSaldoBajoRamasFaltantesTest(TestCase):
    """Cover branch 91->95 (email_destinatario provided), 121->141 (no email), 179-181 (outer except)."""

    def _base_tarjeta_mock(self, mock_select, email="test@test.com", telefono="0981000000"):
        hijo_mock = MagicMock()
        hijo_mock.nombre = "Pedro"
        hijo_mock.apellido = "Garcia"
        cliente_mock = MagicMock()
        cliente_mock.nombre = "Juan"
        cliente_mock.apellido = "Garcia"
        cliente_mock.email = email
        cliente_mock.telefono = telefono
        hijo_mock.id_cliente = cliente_mock
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.id_hijo = hijo_mock
        mock_chain = MagicMock()
        mock_chain.get.return_value = tarjeta_mock
        mock_select.return_value = mock_chain
        return tarjeta_mock

    @patch(
        "apps.notificaciones.services.email_service.EmailService.enviar_alerta_saldo_bajo",
        return_value={"success": True},
    )
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_email_destinatario_provisto_salta_asignacion_cliente(self, mock_select, mock_create, mock_email):
        """Branch 91->95: email_destinatario IS provided, so if-body is skipped."""
        from apps.notificaciones.services import NotificacionService

        self._base_tarjeta_mock(mock_select)

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 1
        mock_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_saldo_bajo(
            nro_tarjeta="TAR001",
            saldo_actual=Decimal("5000"),
            saldo_alerta=Decimal("10000"),
            email_destinatario="custom@test.com",  # provided → skips line 92
            enviar_sms=False,
        )
        self.assertTrue(result["success"])

    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create")
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_sin_email_no_enviar_email(self, mock_select, mock_create):
        """Branch 121->141: email_destinatario is falsy after assignment → skip email block."""
        from apps.notificaciones.services import NotificacionService

        self._base_tarjeta_mock(mock_select, email="", telefono=None)

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 2
        mock_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_saldo_bajo(
            nro_tarjeta="TAR001",
            saldo_actual=Decimal("5000"),
            saldo_alerta=Decimal("10000"),
            email_destinatario=None,  # will try cliente.email which is ''
            enviar_sms=False,
        )
        self.assertTrue(result["success"])
        self.assertFalse(result["enviada_email"])

    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.create", side_effect=Exception("DB create error"))
    @patch("apps.notificaciones.services.Tarjetas.objects.select_related")
    def test_excepcion_inesperada_eleva_validation_error(self, mock_select, mock_create):
        """Lines 179-181: outer except Exception."""
        from apps.notificaciones.services import NotificacionService

        self._base_tarjeta_mock(mock_select)

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_saldo_bajo(
                nro_tarjeta="TAR001",
                saldo_actual=Decimal("5000"),
                saldo_alerta=Decimal("10000"),
            )


class NotificacionServiceRecargaSinIdEncontradoTest(TestCase):
    """Cover line 234: recarga without id_usuario_portal but portal found in DB."""

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.create")
    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.CargasSaldo.objects.select_related")
    def test_sin_id_portal_pero_encontrado_en_db(self, mock_select, mock_usuario_get, mock_portal_create):
        """Line 234: id_usuario_portal not provided, but UsuariosPortal.get succeeds."""
        import django.utils.timezone as tz_module

        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Ana"
        hijo_mock.apellido = "Lopez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR003"
        tarjeta_mock.saldo_actual = Decimal("50000")
        tarjeta_mock.id_hijo = hijo_mock

        recarga_mock = MagicMock()
        recarga_mock.estado = "completada"
        recarga_mock.nro_tarjeta = tarjeta_mock
        recarga_mock.monto_cargado = Decimal("20000")
        recarga_mock.metodo_pago = "Efectivo"
        recarga_mock.fecha_carga = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = recarga_mock
        mock_select.return_value = mock_chain

        # Portal found without explicit id
        usuario_portal_mock = MagicMock()
        mock_usuario_get.return_value = usuario_portal_mock

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 99
        mock_portal_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_recarga(
            id_recarga=1, id_usuario_portal=None  # Not provided → go through try block
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["id_notificacion"], 99)


class NotificacionServiceConsumoPortalEncontradoTest(TestCase):
    """Cover line 314: consumo without id_usuario_portal but portal found in DB."""

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.create")
    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.ConsumosTarjeta.objects.select_related")
    def test_sin_id_portal_pero_encontrado_en_db(self, mock_select, mock_usuario_get, mock_portal_create):
        """Line 314: id_usuario_portal not provided, but UsuariosPortal.get succeeds."""
        import django.utils.timezone as tz_module

        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Carlos"
        hijo_mock.apellido = "Mendez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.id_hijo = hijo_mock

        consumo_mock = MagicMock()
        consumo_mock.nro_tarjeta = tarjeta_mock
        consumo_mock.monto_consumido = Decimal("5000")
        consumo_mock.saldo_anterior = Decimal("30000")
        consumo_mock.saldo_nuevo = Decimal("25000")
        consumo_mock.fecha_consumo = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = consumo_mock
        mock_select.return_value = mock_chain

        usuario_mock = MagicMock()
        mock_usuario_get.return_value = usuario_mock

        notif_mock = MagicMock()
        notif_mock.id_notificacion = 77
        mock_portal_create.return_value = notif_mock

        result = NotificacionService.enviar_notificacion_consumo(
            id_consumo=1, id_usuario_portal=None  # Not provided → go through try block
        )
        self.assertTrue(result["success"])

    @patch("apps.notificaciones.services.NotificacionesPortal.objects.create", side_effect=Exception("DB error"))
    @patch("apps.notificaciones.services.UsuariosPortal.objects.get")
    @patch("apps.core.models.ConsumosTarjeta.objects.select_related")
    def test_consumo_excepcion_inesperada_raises(self, mock_select, mock_usuario_get, mock_portal_create):
        """Lines 338-340: outer except Exception in enviar_notificacion_consumo."""
        import django.utils.timezone as tz_module

        from apps.notificaciones.services import NotificacionService

        hijo_mock = MagicMock()
        hijo_mock.nombre = "Carlos"
        hijo_mock.apellido = "Mendez"
        hijo_mock.id_cliente = MagicMock()
        tarjeta_mock = MagicMock()
        tarjeta_mock.id_hijo = hijo_mock

        consumo_mock = MagicMock()
        consumo_mock.nro_tarjeta = tarjeta_mock
        consumo_mock.monto_consumido = Decimal("5000")
        consumo_mock.saldo_anterior = Decimal("30000")
        consumo_mock.saldo_nuevo = Decimal("25000")
        consumo_mock.fecha_consumo = tz_module.now()

        mock_chain = MagicMock()
        mock_chain.get.return_value = consumo_mock
        mock_select.return_value = mock_chain

        usuario_mock = MagicMock()
        mock_usuario_get.return_value = usuario_mock

        with self.assertRaises(ValidationError):
            NotificacionService.enviar_notificacion_consumo(id_consumo=1)


class NotificacionServiceAlertasRamasFaltantesTest(TestCase):
    """Cover branch 393->373 (neither email nor SMS sent) and 407-409 (outer except)."""

    @patch("apps.notificaciones.services.NotificacionService.enviar_notificacion_saldo_bajo")
    @patch("apps.notificaciones.services.NotificacionesSaldo.objects.filter")
    @patch("apps.notificaciones.services.Tarjetas.objects.filter")
    def test_alerta_generada_sin_envio_email_ni_sms(self, mock_tarjetas_filter, mock_notif_filter, mock_enviar):
        """Branch 393->373: resultado has no email/sms sent → alertas_enviadas stays 0."""
        from apps.notificaciones.services import NotificacionService

        tarjeta_mock = MagicMock()
        tarjeta_mock.numero_tarjeta = "TAR001"
        tarjeta_mock.saldo_actual = Decimal("5000")
        tarjeta_mock.saldo_alerta = Decimal("10000")

        mock_tarjetas_filter.return_value.select_related.return_value = [tarjeta_mock]

        notif_filter_chain = MagicMock()
        notif_filter_chain.exists.return_value = False
        mock_notif_filter.return_value = notif_filter_chain

        # Neither email nor sms sent
        mock_enviar.return_value = {
            "success": True,
            "enviada_email": False,
            "enviada_sms": False,
        }

        result = NotificacionService.generar_alertas_automaticas()
        self.assertTrue(result["success"])
        self.assertEqual(result["alertas_generadas"], 1)
        self.assertEqual(result["alertas_enviadas"], 0)  # Not incremented

    @patch("apps.notificaciones.services.Tarjetas.objects.filter", side_effect=Exception("DB error"))
    def test_excepcion_en_filtro_tarjetas(self, mock_filter):
        """Lines 407-409: outer except Exception in generar_alertas_automaticas."""
        from apps.notificaciones.services import NotificacionService

        result = NotificacionService.generar_alertas_automaticas()
        self.assertFalse(result["success"])
        self.assertIn("error", result)


class NotificacionServiceMarcarLeidaExcepcionTest(TestCase):
    """Cover lines 479-481: outer except Exception in marcar_notificacion_leida."""

    @patch(
        "apps.notificaciones.services.NotificacionesPortal.objects.get", side_effect=Exception("Unexpected DB error")
    )
    def test_excepcion_inesperada_raises_validation_error(self, mock_get):
        from apps.notificaciones.services import NotificacionService

        with self.assertRaises(ValidationError):
            NotificacionService.marcar_notificacion_leida(id_notificacion=1, tipo="portal")
