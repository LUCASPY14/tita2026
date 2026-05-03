"""
Tests para modelos de la app notificaciones
Cubre el método __str__ de todos los modelos.
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, TiposCliente
from apps.core.models import Tarjetas
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles, UsuariosPortal

from .models import (
    AlertaDestinatarios,
    AlertasAutomaticas,
    AlertasSistema,
    AnomaliasDetectadas,
    CampanasComunicacion,
    EmailsEnviados,
    HistorialAlertas,
    NotificacionesPortal,
    NotificacionesSaldo,
    PlantillasEmail,
    PlantillasSms,
    PreferenciasNotificacion,
    RestriccionesHorarias,
    SmsEnviados,
    SolicitudesNotificacion,
)


class NotificacionesModelsBaseTest(TestCase):
    """Base con fixtures compartidos para tests de notificaciones models."""

    def setUp(self):
        self.lista = ListasPrecios.objects.create(
            nombre_lista="Lista Notif",
            moneda="PYG",
            estado=True,
        )
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Tipo Notif", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Cli",
            apellidos="Notif",
            ruc_ci="7000001",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        from apps.clientes.models import Hijos

        self.hijo = Hijos.objects.create(
            nombre="Hijo",
            apellido="Notif",
            fecha_nacimiento=timezone.now().date(),
            estado=True,
            id_cliente_responsable=self.cliente,
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="NOTIF00001",
            saldo_actual=Decimal("100000"),
            estado="Activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0"),
            id_hijo=self.hijo,
        )
        self.rol = Roles.objects.create(nombre_rol="Rol Notif", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Emp",
            apellido="Notif",
            usuario="emp_notif",
            contrasena_hash="hash",
            email="emp_notif@test.com",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="portal_notif@test.com",
            password_hash="hash",
            email_verificado=0,
            fecha_registro=timezone.now(),
            estado=True,
            id_cliente=self.cliente,
        )


class NotificacionesPortalStrTest(NotificacionesModelsBaseTest):
    def test_str(self):
        obj = NotificacionesPortal.objects.create(
            tipo="alerta",
            titulo="Test Titulo",
            mensaje="Mensaje de prueba",
            leida=0,
            fecha_envio=timezone.now(),
            creado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        self.assertIn("#", str(obj))


class NotificacionesSaldoStrTest(NotificacionesModelsBaseTest):
    def test_str(self):
        obj = NotificacionesSaldo.objects.create(
            tipo_notificacion="saldo_bajo",
            saldo_actual=Decimal("5000"),
            mensaje="Saldo bajo en tarjeta",
            enviada_email=0,
            enviada_sms=0,
            leida=0,
            fecha_creacion=timezone.now(),
            nro_tarjeta=self.tarjeta,
        )
        self.assertIn("#", str(obj))


class SolicitudesNotificacionStrTest(NotificacionesModelsBaseTest):
    def test_str(self):
        obj = SolicitudesNotificacion.objects.create(
            saldo_alerta=Decimal("10000"),
            mensaje="Mensaje solicitud",
            destino="Email",
            estado="Pendiente",
            fecha_solicitud=timezone.now(),
            id_cliente=self.cliente,
            nro_tarjeta=self.tarjeta,
        )
        self.assertIn("#", str(obj))


class PreferenciasNotificacionStrTest(NotificacionesModelsBaseTest):
    def test_str(self):
        obj = PreferenciasNotificacion.objects.create(
            tipo_notificacion="ventas",
            email_activo=1,
            push_activo=0,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        self.assertIn("#", str(obj))


class EmailsEnviadosStrTest(TestCase):
    def test_str(self):
        obj = EmailsEnviados.objects.create(
            email_destinatario="dest@test.com",
            nombre_destinatario="Destinatario",
            asunto="Asunto test",
            cuerpo="Cuerpo del email",
            estado="Enviado",
            fecha_envio=timezone.now(),
            intentos=1,
        )
        self.assertIn("#", str(obj))


class SmsEnviadosStrTest(TestCase):
    def test_str(self):
        obj = SmsEnviados.objects.create(
            telefono="0981000001",
            mensaje="SMS de prueba test",
            estado="Enviado",
            fecha_envio=timezone.now(),
        )
        self.assertIn("#", str(obj))


class PlantillasEmailStrTest(TestCase):
    def test_str(self):
        obj = PlantillasEmail.objects.create(
            codigo="TEST_TPL_EMAIL",
            nombre="Plantilla Email Test",
            asunto="Asunto de plantilla",
            cuerpo_html="<p>Hola {nombre}</p>",
            variables={"nombre": "string"},
            categoria="transaccional",
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.assertIn("#", str(obj))


class PlantillasSmsStrTest(TestCase):
    def test_str(self):
        obj = PlantillasSms.objects.create(
            codigo="TEST_TPL_SMS",
            nombre="Plantilla SMS Test",
            mensaje="Hola {nombre}, tu saldo es {saldo}",
            variables={"nombre": "string", "saldo": "number"},
            categoria="transaccional",
            estado=True,
            created_at=timezone.now(),
        )
        self.assertIn("#", str(obj))


class CampanasComunicacionStrTest(TestCase):
    def test_str(self):
        obj = CampanasComunicacion.objects.create(
            nombre="Campana Test Str",
            descripcion="Descripcion campana",
            tipo="email",
            segmentacion="{}",
            estado="Borrador",
            total_destinatarios=0,
            total_enviados=0,
            total_entregados=0,
            created_at=timezone.now(),
        )
        self.assertIn("#", str(obj))


class AlertasAutomaticasStrTest(TestCase):
    def test_str(self):
        obj = AlertasAutomaticas.objects.create(
            nombre="Alerta Test Str",
            descripcion="Descripcion alerta test",
            condicion="stock < 5",
            tipo_alerta="sistema",
            criticidad="Alto",
            frecuencia_min=60,
            estado=True,
        )
        self.assertIn("#", str(obj))


class AlertaDestinatariosStrTest(TestCase):
    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol="Rol AD", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="AD",
            apellido="Test",
            usuario="ad_str",
            contrasena_hash="hash",
            email="ad_str@test.com",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )
        self.alerta = AlertasAutomaticas.objects.create(
            nombre="Alerta AD Str",
            descripcion="Descripcion",
            condicion="x > 0",
            tipo_alerta="sistema",
            criticidad="Bajo",
            frecuencia_min=30,
            estado=True,
        )

    def test_str(self):
        obj = AlertaDestinatarios.objects.create(
            via_email=1,
            via_sistema=0,
            estado=True,
            id_alerta=self.alerta,
            id_empleado=self.empleado,
        )
        self.assertIn("#", str(obj))


class AlertasSistemaStrTest(TestCase):
    def test_str(self):
        obj = AlertasSistema.objects.create(
            tipo="stock_bajo",
            mensaje="Stock bajo para produc",
            fecha_creacion=timezone.now(),
            estado="Pendiente",
        )
        self.assertIn("#", str(obj))


class HistorialAlertasStrTest(TestCase):
    def setUp(self):
        self.alerta = AlertasAutomaticas.objects.create(
            nombre="Alerta Hist Str",
            descripcion="Descripcion",
            condicion="y > 0",
            tipo_alerta="sistema",
            criticidad="Medio",
            frecuencia_min=15,
            estado=True,
        )

    def test_str(self):
        obj = HistorialAlertas.objects.create(
            fecha_disparada=timezone.now(),
            mensaje="Alerta disparada en test",
            datos_contexto={"key": "value"},
            resuelto=0,
            id_alerta=self.alerta,
        )
        self.assertIn("#", str(obj))


class AnomaliasDetectadasStrTest(TestCase):
    def test_str(self):
        obj = AnomaliasDetectadas.objects.create(
            usuario="usuario_test",
            tipo_anomalia="acceso_inusual",
            fecha_deteccion=timezone.now(),
            nivel_riesgo="Medio",
            notificado=0,
        )
        self.assertIn("#", str(obj))


class RestriccionesHorariasStrTest(TestCase):
    def test_str(self):
        obj = RestriccionesHorarias.objects.create(
            tipo_usuario="empleado",
            dia_semana="Lunes",
            hora_inicio="08:00",
            hora_fin="18:00",
            estado=True,
            fecha_creacion=timezone.now(),
        )
        self.assertIn("#", str(obj))
