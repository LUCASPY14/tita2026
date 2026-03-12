"""
Tests para la app notificaciones
"""

import pytest  # type: ignore
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.notificaciones.models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion,
    EmailsEnviados,
    SmsEnviados,
)
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.usuarios.models import Empleados, Roles, UsuariosPortal
from apps.productos.models import ListasPrecios
from apps.core.models import Tarjetas


class NotificacionesPortalTest(TestCase):
    """Tests para el modelo NotificacionesPortal"""

    def setUp(self):
        """Configuración inicial para los tests"""
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular Portal", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test", apellidos="Portal", ruc_ci="11111111",
            activo=True, id_tipo_cliente=self.tipo_cliente,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="testportal@cantina.com",
            password_hash="hashed_password",
            email_verificado=0,
            fecha_registro=timezone.now(),
            id_cliente=self.cliente,
        )

    def _make_notif(self, **kwargs):
        defaults = dict(
            tipo="info", titulo="Notif", mensaje="Mensaje",
            leida=0, fecha_envio=timezone.now(), creado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        defaults.update(kwargs)
        return NotificacionesPortal.objects.create(**defaults)

    def test_crear_notificacion_portal(self):
        """Test: Crear notificación del portal"""
        notificacion = self._make_notif(tipo="info", titulo="Test Notificación",
                                        mensaje="Este es un mensaje de prueba")
        self.assertEqual(notificacion.tipo, "info")
        self.assertEqual(notificacion.titulo, "Test Notificación")
        self.assertEqual(notificacion.leida, 0)
        self.assertIsNotNone(notificacion.creado_en)

    def test_marcar_notificacion_leida(self):
        """Test: Marcar notificación como leída"""
        notificacion = self._make_notif(tipo="warning", titulo="Alerta", mensaje="Mensaje de alerta")

        notificacion.leida = 1
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()

        self.assertEqual(notificacion.leida, 1)
        self.assertIsNotNone(notificacion.fecha_lectura)

    def test_filtrar_notificaciones_no_leidas(self):
        """Test: Filtrar notificaciones no leídas"""
        self._make_notif(titulo="No Leída 1", mensaje="Mensaje 1")
        self._make_notif(titulo="No Leída 2", mensaje="Mensaje 2")
        self._make_notif(titulo="Leída", mensaje="Leído", leida=1, fecha_lectura=timezone.now())

        no_leidas = NotificacionesPortal.objects.filter(leida=0)
        self.assertEqual(no_leidas.count(), 2)

    def test_tipos_notificacion_validos(self):
        """Test: Validar tipos de notificación permitidos"""
        tipos_validos = ["info", "warning", "error", "success"]

        for tipo in tipos_validos:
            notif = self._make_notif(tipo=tipo, titulo=f"Test {tipo}", mensaje=f"Mensaje {tipo}")
            self.assertEqual(notif.tipo, tipo)


class NotificacionesSaldoTest(TestCase):
    """Tests para el modelo NotificacionesSaldo"""

    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", activo=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", activo=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="María",
            apellidos="González",
            ruc_ci="87654321",
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Ana",
            apellido="González",
            grado="3ro",
            activo=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="0001",
            saldo_actual=Decimal("5000.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

    def _make_notif_saldo(self, **kwargs):
        defaults = dict(
            tipo_notificacion="saldo_bajo",
            nro_tarjeta=self.tarjeta,
            saldo_actual=Decimal("5000.00"),
            mensaje="Saldo bajo",
            enviada_email=0,
            enviada_sms=0,
            leida=0,
            fecha_creacion=timezone.now(),
        )
        defaults.update(kwargs)
        return NotificacionesSaldo.objects.create(**defaults)

    def test_crear_notificacion_saldo_bajo(self):
        """Test: Crear notificación de saldo bajo"""
        notificacion = self._make_notif_saldo(
            tipo_notificacion="saldo_bajo",
            saldo_actual=Decimal("5000.00"),
            mensaje="Saldo bajo en tarjeta 0001",
            enviada_email=1,
        )

        self.assertEqual(notificacion.tipo_notificacion, "saldo_bajo")
        self.assertEqual(notificacion.saldo_actual, Decimal("5000.00"))
        self.assertEqual(notificacion.enviada_email, 1)

    def test_notificacion_saldo_agotado(self):
        """Test: Notificación de saldo agotado"""
        self.tarjeta.saldo_actual = Decimal("0.00")
        self.tarjeta.save()

        notificacion = self._make_notif_saldo(
            tipo_notificacion="saldo_agotado",
            saldo_actual=Decimal("0.00"),
            mensaje="Saldo agotado en tarjeta 0001",
        )

        self.assertEqual(notificacion.tipo_notificacion, "saldo_agotado")
        self.assertEqual(notificacion.saldo_actual, Decimal("0.00"))


class AlertasSistemaTest(TestCase):
    """Tests para el modelo AlertasSistema"""

    def setUp(self):
        """Configuración inicial"""
        # Crear rol
        self.rol = Roles.objects.create(
            nombre_rol="Administrador", descripcion="Rol de prueba", activo=True
        )

        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Admin",
            usuario="admin",
            contrasena_hash="hashed_password",
            fecha_ingreso=timezone.now(),
            email="admin@cantina.com",
            activo=True,
            id_rol=self.rol,
        )

    def test_crear_alerta_critica(self):
        """Test: Crear alerta crítica del sistema"""
        alerta = AlertasSistema.objects.create(
            tipo="stock_critico",
            mensaje="Producto X con stock por debajo del mínimo",
            fecha_creacion=timezone.now(),
            estado="pendiente",
        )

        self.assertEqual(alerta.tipo, "stock_critico")
        self.assertEqual(alerta.estado, "pendiente")

    def test_resolver_alerta(self):
        """Test: Resolver alerta del sistema"""
        alerta = AlertasSistema.objects.create(
            tipo="anomalia_venta",
            mensaje="Venta inusual detectada",
            fecha_creacion=timezone.now(),
            estado="pendiente",
        )

        alerta.estado = "resuelta"
        alerta.fecha_resolucion = timezone.now()
        alerta.observaciones = "Verificado y corregido"
        alerta.save()

        self.assertEqual(alerta.estado, "resuelta")
        self.assertIsNotNone(alerta.fecha_resolucion)

    def test_filtrar_alertas_pendientes(self):
        """Test: Filtrar alertas pendientes"""
        AlertasSistema.objects.create(
            tipo="stock_critico", mensaje="Alerta 1",
            fecha_creacion=timezone.now(), estado="pendiente",
        )
        AlertasSistema.objects.create(
            tipo="anomalia_venta", mensaje="Alerta 2",
            fecha_creacion=timezone.now(), estado="resuelta",
            fecha_resolucion=timezone.now(),
        )

        pendientes = AlertasSistema.objects.filter(estado="pendiente")
        self.assertEqual(pendientes.count(), 1)


class PreferenciasNotificacionTest(TestCase):
    """Tests para el modelo PreferenciasNotificacion"""

    def setUp(self):
        """Configuración inicial"""
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular Prefs", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Prefs", apellidos="User", ruc_ci="22222222",
            activo=True, id_tipo_cliente=self.tipo_cliente,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="prefs@cantina.com",
            password_hash="hashed_password",
            email_verificado=0,
            fecha_registro=timezone.now(),
            id_cliente=self.cliente,
        )

    def test_crear_preferencias_default(self):
        """Test: Crear preferencias con valores por defecto"""
        prefs = PreferenciasNotificacion.objects.create(
            tipo_notificacion="ventas",
            email_activo=1,
            push_activo=1,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )

        self.assertEqual(prefs.email_activo, 1)
        self.assertEqual(prefs.push_activo, 1)

    def test_actualizar_preferencias(self):
        """Test: Actualizar preferencias de notificaciones"""
        prefs = PreferenciasNotificacion.objects.create(
            tipo_notificacion="stock",
            email_activo=1,
            push_activo=0,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )

        prefs.email_activo = 0
        prefs.push_activo = 1
        prefs.save()

        prefs.refresh_from_db()
        self.assertEqual(prefs.email_activo, 0)
        self.assertEqual(prefs.push_activo, 1)


@pytest.mark.django_db
class TestEmailsEnviados:
    """Tests para el modelo EmailsEnviados usando pytest"""

    def test_crear_email_enviado(self):
        """Test: Registrar email enviado"""
        email = EmailsEnviados.objects.create(
            email_destinatario="test@example.com",
            nombre_destinatario="Test User",
            asunto="Test Email",
            cuerpo="Cuerpo del mensaje",
            estado="enviado",
            fecha_envio=timezone.now(),
            intentos=1,
        )

        assert email.email_destinatario == "test@example.com"
        assert email.estado == "enviado"
        assert email.fecha_envio is not None

    def test_email_con_error(self):
        """Test: Email con error de envío"""
        email = EmailsEnviados.objects.create(
            email_destinatario="error@example.com",
            nombre_destinatario="Error User",
            asunto="Test Error",
            cuerpo="Test",
            estado="error",
            fecha_envio=timezone.now(),
            intentos=3,
            mensaje_error="SMTP connection failed",
        )

        assert email.estado == "error"
        assert email.mensaje_error is not None


@pytest.mark.django_db
class TestSmsEnviados:
    """Tests para el modelo SmsEnviados usando pytest"""

    def test_crear_sms_enviado(self):
        """Test: Registrar SMS enviado"""
        sms = SmsEnviados.objects.create(
            telefono="+595981234567",
            mensaje="Test SMS",
            estado="enviado",
            fecha_envio=timezone.now(),
            costo=Decimal("500.00"),
        )

        assert sms.telefono == "+595981234567"
        assert sms.estado == "enviado"
        assert sms.costo == Decimal("500.00")

    def test_sms_pendiente(self):
        """Test: SMS en estado pendiente"""
        sms = SmsEnviados.objects.create(
            telefono="+595981111111", mensaje="Pending SMS", estado="pendiente",
            fecha_envio=timezone.now(),
        )

        assert sms.estado == "pendiente"
        assert sms.fecha_envio is not None


class NotificacionesModelsStrTest(TestCase):
    """Tests for __str__ methods of all Notificaciones models."""

    def setUp(self):
        from apps.notificaciones.models import (
            PlantillasEmail, PlantillasSms, CampanasComunicacion,
            AlertasAutomaticas, AlertaDestinatarios, AlertasSistema,
            HistorialAlertas, AnomaliasDetectadas, RestriccionesHorarias,
            SolicitudesNotificacion, NotificacionesSaldo, PreferenciasNotificacion,
        )
        from apps.clientes.models import Clientes, TiposCliente, Hijos
        from apps.usuarios.models import UsuariosPortal, Empleados, Roles
        from apps.core.models import Tarjetas
        from apps.productos.models import ListasPrecios

        # Minimal setUp for FK models
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista Str", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Str Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Str", apellidos="Test", ruc_ci="Str001", activo=True,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="StrHijo", apellido="Test", grado="1ro", activo=True,
            id_cliente_responsable=self.cliente,
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="STR001", saldo_actual=Decimal("0.00"), estado="activa",
            fecha_creacion=timezone.now(), limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="str_test@cantina.com", password_hash="x", email_verificado=0,
            fecha_registro=timezone.now(), id_cliente=self.cliente,
        )
        self.rol = Roles.objects.create(nombre_rol="StrRol Emp", descripcion="x", activo=True)
        self.empleado = Empleados.objects.create(
            nombre="StrE", apellido="Emp", usuario="str_emp_notif", contrasena_hash="x",
            fecha_ingreso=timezone.now(), activo=True, id_rol=self.rol,
        )

    def test_notificaciones_portal_str(self):
        from apps.notificaciones.models import NotificacionesPortal
        n = NotificacionesPortal.objects.create(
            tipo="alerta", titulo="T", mensaje="M", leida=0,
            fecha_envio=timezone.now(), creado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        self.assertIn("NotificacionesPortal", str(n))

    def test_notificaciones_saldo_str(self):
        from apps.notificaciones.models import NotificacionesSaldo
        n = NotificacionesSaldo.objects.create(
            tipo_notificacion="saldo", saldo_actual=Decimal("0.00"),
            mensaje="M", enviada_email=0, enviada_sms=0, leida=0,
            fecha_creacion=timezone.now(), nro_tarjeta=self.tarjeta,
        )
        self.assertIn("NotificacionesSaldo", str(n))

    def test_solicitudes_notificacion_str(self):
        from apps.notificaciones.models import SolicitudesNotificacion
        n = SolicitudesNotificacion.objects.create(
            saldo_alerta=Decimal("100.00"), mensaje="M", destino="Email",
            fecha_solicitud=timezone.now(), id_cliente=self.cliente,
            nro_tarjeta=self.tarjeta,
        )
        self.assertIn("SolicitudesNotificacion", str(n))

    def test_preferencias_notificacion_str(self):
        from apps.notificaciones.models import PreferenciasNotificacion
        n = PreferenciasNotificacion.objects.create(
            tipo_notificacion="ventas", email_activo=1, push_activo=0,
            creado_en=timezone.now(), actualizado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        self.assertIn("PreferenciasNotificacion", str(n))

    def test_emails_enviados_str(self):
        from apps.notificaciones.models import EmailsEnviados
        n = EmailsEnviados.objects.create(
            email_destinatario="s@s.com", nombre_destinatario="Test",
            asunto="A", cuerpo="B", estado="Enviado",
            fecha_envio=timezone.now(), intentos=1,
        )
        self.assertIn("EmailsEnviados", str(n))

    def test_sms_enviados_str(self):
        n = SmsEnviados.objects.create(
            telefono="0981000000", mensaje="Test SMS str",
            estado="Enviado", fecha_envio=timezone.now(),
        )
        self.assertIn("SmsEnviados", str(n))

    def test_plantillas_email_str(self):
        from apps.notificaciones.models import PlantillasEmail
        n = PlantillasEmail.objects.create(
            codigo="STR_TPL_01", nombre="Str Tpl", asunto="A",
            cuerpo_html="<p>Hi</p>", variables=[], categoria="Ventas",
            activo=True, created_at=timezone.now(), updated_at=timezone.now(),
        )
        self.assertIn("PlantillasEmail", str(n))

    def test_plantillas_sms_str(self):
        from apps.notificaciones.models import PlantillasSms
        n = PlantillasSms.objects.create(
            codigo="STR_SMS_01", nombre="Str SMS Tpl", mensaje="Test mensaje SMS",
            variables=[], categoria="Ventas", activo=True, created_at=timezone.now(),
        )
        self.assertIn("PlantillasSms", str(n))

    def test_campanas_comunicacion_str(self):
        from apps.notificaciones.models import CampanasComunicacion
        n = CampanasComunicacion.objects.create(
            nombre="Campaña Str", descripcion="Desc", tipo="Email",
            segmentacion="Todos", estado="Borrador",
            total_destinatarios=0, total_enviados=0, total_entregados=0,
            created_at=timezone.now(),
        )
        self.assertIn("CampanasComunicacion", str(n))

    def test_alertas_automaticas_str(self):
        from apps.notificaciones.models import AlertasAutomaticas
        n = AlertasAutomaticas.objects.create(
            nombre="Alerta Str", descripcion="Desc", condicion="cond",
            tipo_alerta="Inventario", criticidad="Baja", frecuencia_min=30, activo=True,
        )
        self.assertIn("AlertasAutomaticas", str(n))

    def test_alerta_destinatarios_str(self):
        from apps.notificaciones.models import AlertasAutomaticas, AlertaDestinatarios
        alerta = AlertasAutomaticas.objects.create(
            nombre="AlertaD Str", descripcion="D", condicion="c",
            tipo_alerta="Ventas", criticidad="Media", frecuencia_min=60, activo=True,
        )
        n = AlertaDestinatarios.objects.create(
            via_email=1, via_sistema=1, activo=True,
            id_alerta=alerta, id_empleado=self.empleado,
        )
        self.assertIn("AlertaDestinatarios", str(n))

    def test_alertas_sistema_str(self):
        from apps.notificaciones.models import AlertasSistema
        n = AlertasSistema.objects.create(
            tipo="warning", mensaje="Str test alerta", fecha_creacion=timezone.now(),
        )
        self.assertIn("AlertasSistema", str(n))

    def test_historial_alertas_str(self):
        from apps.notificaciones.models import AlertasAutomaticas, HistorialAlertas
        alerta = AlertasAutomaticas.objects.create(
            nombre="AlertaH Str", descripcion="D", condicion="c",
            tipo_alerta="Sistema", criticidad="Alta", frecuencia_min=5, activo=True,
        )
        n = HistorialAlertas.objects.create(
            fecha_disparada=timezone.now(), mensaje="M",
            datos_contexto={}, resuelto=0, id_alerta=alerta,
        )
        self.assertIn("HistorialAlertas", str(n))

    def test_anomalias_detectadas_str(self):
        from apps.notificaciones.models import AnomaliasDetectadas
        n = AnomaliasDetectadas.objects.create(
            usuario="admin", tipo_anomalia="acceso_inusual",
            fecha_deteccion=timezone.now(), nivel_riesgo="Bajo", notificado=0,
        )
        self.assertIn("AnomaliasDetectadas", str(n))

    def test_restricciones_horarias_str(self):
        from datetime import time
        from apps.notificaciones.models import RestriccionesHorarias
        n = RestriccionesHorarias.objects.create(
            tipo_usuario="Empleado", dia_semana="Lunes",
            hora_inicio=time(8, 0), hora_fin=time(18, 0),
            activo=True, fecha_creacion=timezone.now(),
        )
        self.assertIn("RestriccionesHorarias", str(n))

