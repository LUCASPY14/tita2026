"""
Tests para la app notificaciones
"""
import pytest
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
    SMSEnviados
)
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.usuarios.models import Empleados, Usuarios
from apps.productos.models import ListasPrecios
from apps.core.models import Tarjetas


class NotificacionesPortalTest(TestCase):
    """Tests para el modelo NotificacionesPortal"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario
        self.usuario = Usuarios.objects.create(
            username='admin',
            email='admin@cantina.com',
            activo=True
        )
        self.usuario.set_password('admin123')
        self.usuario.save()
        
        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Admin',
            ruc_ci='12345678',
            activo=True,
            id_usuario=self.usuario
        )
    
    def test_crear_notificacion_portal(self):
        """Test: Crear notificación del portal"""
        notificacion = NotificacionesPortal.objects.create(
            tipo='info',
            titulo='Test Notificación',
            mensaje='Este es un mensaje de prueba',
            id_empleado=self.empleado
        )
        
        self.assertEqual(notificacion.tipo, 'info')
        self.assertEqual(notificacion.titulo, 'Test Notificación')
        self.assertFalse(notificacion.leida)
        self.assertIsNotNone(notificacion.fecha_creacion)
    
    def test_marcar_notificacion_leida(self):
        """Test: Marcar notificación como leída"""
        notificacion = NotificacionesPortal.objects.create(
            tipo='warning',
            titulo='Alerta',
            mensaje='Mensaje de alerta',
            id_empleado=self.empleado
        )
        
        # Marcar como leída
        notificacion.leida = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        self.assertTrue(notificacion.leida)
        self.assertIsNotNone(notificacion.fecha_lectura)
    
    def test_filtrar_notificaciones_no_leidas(self):
        """Test: Filtrar notificaciones no leídas"""
        # Crear 3 notificaciones, 2 no leídas y 1 leída
        NotificacionesPortal.objects.create(
            tipo='info',
            titulo='No Leída 1',
            mensaje='Mensaje 1',
            id_empleado=self.empleado
        )
        NotificacionesPortal.objects.create(
            tipo='info',
            titulo='No Leída 2',
            mensaje='Mensaje 2',
            id_empleado=self.empleado
        )
        notif_leida = NotificacionesPortal.objects.create(
            tipo='info',
            titulo='Leída',
            mensaje='Mensaje leído',
            id_empleado=self.empleado,
            leida=True,
            fecha_lectura=timezone.now()
        )
        
        no_leidas = NotificacionesPortal.objects.filter(leida=False)
        self.assertEqual(no_leidas.count(), 2)
    
    def test_tipos_notificacion_validos(self):
        """Test: Validar tipos de notificación permitidos"""
        tipos_validos = ['info', 'warning', 'error', 'success']
        
        for tipo in tipos_validos:
            notif = NotificacionesPortal.objects.create(
                tipo=tipo,
                titulo=f'Test {tipo}',
                mensaje=f'Mensaje {tipo}',
                id_empleado=self.empleado
            )
            self.assertEqual(notif.tipo, tipo)


class NotificacionesSaldoTest(TestCase):
    """Tests para el modelo NotificacionesSaldo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista='Minorista',
            activo=True
        )
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Regular',
            activo=True
        )
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres='María',
            apellidos='González',
            ruc_ci='87654321',
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente
        )
        
        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre='Ana',
            apellido='González',
            grado='3ro',
            activo=True,
            id_cliente_responsable=self.cliente
        )
        
        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            numero_tarjeta='0001',
            saldo_actual=Decimal('5000.00'),
            estado='activa',
            activo=True,
            id_hijo=self.hijo
        )
    
    def test_crear_notificacion_saldo_bajo(self):
        """Test: Crear notificación de saldo bajo"""
        notificacion = NotificacionesSaldo.objects.create(
            tipo='saldo_bajo',
            id_tarjeta=self.tarjeta,
            saldo_actual=Decimal('5000.00'),
            umbral_minimo=Decimal('10000.00'),
            mensaje='Saldo bajo en tarjeta 0001',
            enviada=True
        )
        
        self.assertEqual(notificacion.tipo, 'saldo_bajo')
        self.assertEqual(notificacion.saldo_actual, Decimal('5000.00'))
        self.assertTrue(notificacion.enviada)
    
    def test_notificacion_saldo_agotado(self):
        """Test: Notificación de saldo agotado"""
        self.tarjeta.saldo_actual = Decimal('0.00')
        self.tarjeta.save()
        
        notificacion = NotificacionesSaldo.objects.create(
            tipo='saldo_agotado',
            id_tarjeta=self.tarjeta,
            saldo_actual=Decimal('0.00'),
            mensaje='Saldo agotado en tarjeta 0001',
            enviada=True
        )
        
        self.assertEqual(notificacion.tipo, 'saldo_agotado')
        self.assertEqual(notificacion.saldo_actual, Decimal('0.00'))


class AlertasSistemaTest(TestCase):
    """Tests para el modelo AlertasSistema"""
    
    def setUp(self):
        """Configuración inicial"""
        self.usuario = Usuarios.objects.create(
            username='admin',
            email='admin@cantina.com',
            activo=True
        )
        self.usuario.set_password('admin123')
        self.usuario.save()
        
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Admin',
            ruc_ci='12345678',
            activo=True,
            id_usuario=self.usuario
        )
    
    def test_crear_alerta_critica(self):
        """Test: Crear alerta crítica del sistema"""
        alerta = AlertasSistema.objects.create(
            tipo='stock_critico',
            criticidad='alta',
            titulo='Stock Crítico',
            descripcion='Producto X con stock por debajo del mínimo',
            id_empleado_asignado=self.empleado
        )
        
        self.assertEqual(alerta.tipo, 'stock_critico')
        self.assertEqual(alerta.criticidad, 'alta')
        self.assertEqual(alerta.estado, 'pendiente')
    
    def test_resolver_alerta(self):
        """Test: Resolver alerta del sistema"""
        alerta = AlertasSistema.objects.create(
            tipo='anomalia_venta',
            criticidad='media',
            titulo='Anomalía detectada',
            descripcion='Venta inusual detectada',
            id_empleado_asignado=self.empleado
        )
        
        # Resolver alerta
        alerta.estado = 'resuelta'
        alerta.fecha_resolucion = timezone.now()
        alerta.observaciones_resolucion = 'Verificado y corregido'
        alerta.save()
        
        self.assertEqual(alerta.estado, 'resuelta')
        self.assertIsNotNone(alerta.fecha_resolucion)
    
    def test_filtrar_alertas_pendientes(self):
        """Test: Filtrar alertas pendientes"""
        # Crear alertas
        AlertasSistema.objects.create(
            tipo='stock_critico',
            criticidad='alta',
            titulo='Alerta 1',
            descripcion='Descripción 1',
            id_empleado_asignado=self.empleado
        )
        AlertasSistema.objects.create(
            tipo='anomalia_venta',
            criticidad='media',
            titulo='Alerta 2',
            descripcion='Descripción 2',
            id_empleado_asignado=self.empleado,
            estado='resuelta',
            fecha_resolucion=timezone.now()
        )
        
        pendientes = AlertasSistema.objects.filter(estado='pendiente')
        self.assertEqual(pendientes.count(), 1)


class PreferenciasNotificacionTest(TestCase):
    """Tests para el modelo PreferenciasNotificacion"""
    
    def setUp(self):
        """Configuración inicial"""
        self.usuario = Usuarios.objects.create(
            username='admin',
            email='admin@cantina.com',
            activo=True
        )
        self.usuario.set_password('admin123')
        self.usuario.save()
        
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Admin',
            ruc_ci='12345678',
            activo=True,
            id_usuario=self.usuario
        )
    
    def test_crear_preferencias_default(self):
        """Test: Crear preferencias con valores por defecto"""
        prefs = PreferenciasNotificacion.objects.create(
            id_empleado=self.empleado
        )
        
        # Valores por defecto deben estar en True
        self.assertTrue(prefs.notif_email_ventas)
        self.assertTrue(prefs.notif_email_stock)
        self.assertTrue(prefs.notif_email_alertas)
    
    def test_actualizar_preferencias(self):
        """Test: Actualizar preferencias de notificaciones"""
        prefs = PreferenciasNotificacion.objects.create(
            id_empleado=self.empleado,
            notif_email_ventas=True,
            notif_push_ventas=False
        )
        
        # Actualizar preferencias
        prefs.notif_email_ventas = False
        prefs.notif_push_ventas = True
        prefs.save()
        
        prefs.refresh_from_db()
        self.assertFalse(prefs.notif_email_ventas)
        self.assertTrue(prefs.notif_push_ventas)


@pytest.mark.django_db
class TestEmailsEnviados:
    """Tests para el modelo EmailsEnviados usando pytest"""
    
    def test_crear_email_enviado(self):
        """Test: Registrar email enviado"""
        email = EmailsEnviados.objects.create(
            destinatario='test@example.com',
            asunto='Test Email',
            cuerpo_texto='Cuerpo del mensaje',
            estado='enviado'
        )
        
        assert email.destinatario == 'test@example.com'
        assert email.estado == 'enviado'
        assert email.fecha_envio is not None
    
    def test_email_con_error(self):
        """Test: Email con error de envío"""
        email = EmailsEnviados.objects.create(
            destinatario='error@example.com',
            asunto='Test Error',
            cuerpo_texto='Test',
            estado='error',
            mensaje_error='SMTP connection failed'
        )
        
        assert email.estado == 'error'
        assert email.mensaje_error is not None


@pytest.mark.django_db
class TestSMSEnviados:
    """Tests para el modelo SMSEnviados usando pytest"""
    
    def test_crear_sms_enviado(self):
        """Test: Registrar SMS enviado"""
        sms = SMSEnviados.objects.create(
            numero_destino='+595981234567',
            mensaje='Test SMS',
            estado='enviado',
            costo_envio=Decimal('500.00')
        )
        
        assert sms.numero_destino == '+595981234567'
        assert sms.estado == 'enviado'
        assert sms.costo_envio == Decimal('500.00')
    
    def test_sms_pendiente(self):
        """Test: SMS en estado pendiente"""
        sms = SMSEnviados.objects.create(
            numero_destino='+595981111111',
            mensaje='Pending SMS',
            estado='pendiente'
        )
        
        assert sms.estado == 'pendiente'
        assert sms.fecha_envio is not None
