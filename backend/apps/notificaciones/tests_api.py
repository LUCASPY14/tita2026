"""
Tests para ViewSets de notificaciones - API Tests
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from decimal import Decimal

from apps.notificaciones.models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion
)
from apps.usuarios.models import Usuarios, Empleados
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios
from apps.core.models import Tarjetas


class NotificacionesPortalViewSetTest(APITestCase):
    """Tests para NotificacionesPortalViewSet"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario y empleado
        self.usuario = Usuarios.objects.create(
            username='testuser',
            email='test@cantina.com',
            activo=True
        )
        self.usuario.set_password('testpass123')
        self.usuario.save()
        
        self.empleado = Empleados.objects.create(
            nombre='Test',
            apellido='User',
            ruc_ci='12345678',
            activo=True,
            id_usuario=self.usuario
        )
        
        # Autenticar cliente
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        
        # Crear notificaciones de prueba
        self.notif1 = NotificacionesPortal.objects.create(
            tipo='info',
            titulo='Notificación 1',
            mensaje='Mensaje 1',
            id_empleado=self.empleado
        )
        
        self.notif2 = NotificacionesPortal.objects.create(
            tipo='warning',
            titulo='Notificación 2',
            mensaje='Mensaje 2',
            id_empleado=self.empleado,
            leida=True,
            fecha_lectura=timezone.now()
        )
    
    def test_listar_notificaciones(self):
        """Test: GET /api/v1/notificaciones/portal/"""
        url = reverse('notificacionesportal-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filtrar_notificaciones_no_leidas(self):
        """Test: Filtrar notificaciones no leídas"""
        url = reverse('notificacionesportal-list')
        response = self.client.get(url, {'leida': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'Notificación 1')
    
    def test_filtrar_por_tipo(self):
        """Test: Filtrar notificaciones por tipo"""
        url = reverse('notificacionesportal-list')
        response = self.client.get(url, {'tipo': 'warning'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tipo'], 'warning')
    
    def test_marcar_notificacion_leida(self):
        """Test: POST /api/v1/notificaciones/portal/{id}/marcar_leida/"""
        url = reverse('notificacionesportal-marcar-leida', args=[self.notif1.id_notificacion])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se marcó como leída
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.leida)
        self.assertIsNotNone(self.notif1.fecha_lectura)
    
    def test_marcar_todas_leidas(self):
        """Test: POST /api/v1/notificaciones/portal/marcar_todas_leidas/"""
        # Crear más notificaciones no leídas
        NotificacionesPortal.objects.create(
            tipo='info',
            titulo='Notificación 3',
            mensaje='Mensaje 3',
            id_empleado=self.empleado
        )
        
        url = reverse('notificacionesportal-marcar-todas-leidas')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todas están leídas
        no_leidas = NotificacionesPortal.objects.filter(
            id_empleado=self.empleado,
            leida=False
        ).count()
        self.assertEqual(no_leidas, 0)
    
    def test_obtener_resumen(self):
        """Test: GET /api/v1/notificaciones/portal/resumen/"""
        url = reverse('notificacionesportal-resumen')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('no_leidas', response.data)
        self.assertIn('por_tipo', response.data)


class AlertasSistemaViewSetTest(APITestCase):
    """Tests para AlertasSistemaViewSet"""
    
    def setUp(self):
        """Configuración inicial"""
        self.usuario = Usuarios.objects.create(
            username='admin',
            email='admin@cantina.com',
            activo=True,
            is_staff=True
        )
        self.usuario.set_password('admin123')
        self.usuario.save()
        
        self.empleado = Empleados.objects.create(
            nombre='Admin',
            apellido='User',
            ruc_ci='87654321',
            activo=True,
            id_usuario=self.usuario
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        
        # Crear alertas de prueba
        self.alerta1 = AlertasSistema.objects.create(
            tipo='stock_critico',
            criticidad='alta',
            titulo='Stock Bajo',
            descripcion='Producto X crítico',
            id_empleado_asignado=self.empleado
        )
        
        self.alerta2 = AlertasSistema.objects.create(
            tipo='anomalia_venta',
            criticidad='media',
            titulo='Anomalía',
            descripcion='Venta inusual',
            id_empleado_asignado=self.empleado,
            estado='resuelta',
            fecha_resolucion=timezone.now()
        )
    
    def test_listar_alertas(self):
        """Test: GET /api/v1/notificaciones/alertas/"""
        url = reverse('alertassistema-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filtrar_alertas_pendientes(self):
        """Test: Filtrar alertas pendientes"""
        url = reverse('alertassistema-list')
        response = self.client.get(url, {'estado': 'pendiente'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_resolver_alerta(self):
        """Test: POST /api/v1/notificaciones/alertas/{id}/resolver/"""
        url = reverse('alertassistema-resolver', args=[self.alerta1.id_alerta])
        data = {
            'observaciones': 'Stock reabastecido correctamente'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se resolvió
        self.alerta1.refresh_from_db()
        self.assertEqual(self.alerta1.estado, 'resuelta')
        self.assertIsNotNone(self.alerta1.fecha_resolucion)
        self.assertEqual(self.alerta1.observaciones_resolucion, 'Stock reabastecido correctamente')


class PreferenciasNotificacionViewSetTest(APITestCase):
    """Tests para PreferenciasNotificacionViewSet"""
    
    def setUp(self):
        """Configuración inicial"""
        self.usuario = Usuarios.objects.create(
            username='user1',
            email='user1@cantina.com',
            activo=True
        )
        self.usuario.set_password('pass123')
        self.usuario.save()
        
        self.empleado = Empleados.objects.create(
            nombre='User',
            apellido='One',
            ruc_ci='11111111',
            activo=True,
            id_usuario=self.usuario
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
    
    def test_obtener_preferencias(self):
        """Test: GET /api/v1/notificaciones/preferencias/obtener_preferencias/"""
        url = reverse('preferenciasnotificacion-obtener-preferencias')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('notif_email_ventas', response.data)
    
    def test_actualizar_preferencias(self):
        """Test: POST /api/v1/notificaciones/preferencias/actualizar_preferencias/"""
        url = reverse('preferenciasnotificacion-actualizar-preferencias')
        data = {
            'notif_email_ventas': False,
            'notif_push_ventas': True,
            'notif_email_stock': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar actualización
        prefs = PreferenciasNotificacion.objects.get(id_empleado=self.empleado)
        self.assertFalse(prefs.notif_email_ventas)
        self.assertTrue(prefs.notif_push_ventas)


@pytest.mark.api
@pytest.mark.django_db
class TestNotificacionesSaldoViewSet:
    """Tests para NotificacionesSaldoViewSet usando pytest"""
    
    def setup_method(self):
        """Configuración para cada test"""
        # Crear datos de prueba
        lista = ListasPrecios.objects.create(
            nombre_lista='Test',
            activo=True
        )
        tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Regular',
            activo=True
        )
        cliente = Clientes.objects.create(
            nombres='Test',
            apellidos='Cliente',
            ruc_ci='99999999',
            activo=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente
        )
        hijo = Hijos.objects.create(
            nombre='Test',
            apellido='Hijo',
            grado='1ro',
            activo=True,
            id_cliente_responsable=cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            numero_tarjeta='9999',
            saldo_actual=Decimal('5000.00'),
            estado='activa',
            activo=True,
            id_hijo=hijo
        )
        
        # Crear usuario
        usuario = Usuarios.objects.create(
            username='testapi',
            email='api@test.com',
            activo=True
        )
        usuario.set_password('test123')
        usuario.save()
        
        self.client = APIClient()
        self.client.force_authenticate(user=usuario)
    
    def test_listar_notificaciones_saldo(self):
        """Test: Listar notificaciones de saldo"""
        # Crear notificación
        NotificacionesSaldo.objects.create(
            tipo='saldo_bajo',
            id_tarjeta=self.tarjeta,
            saldo_actual=Decimal('5000.00'),
            umbral_minimo=Decimal('10000.00'),
            mensaje='Saldo bajo',
            enviada=True
        )
        
        url = reverse('notificacionessaldo-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_filtrar_por_tarjeta(self):
        """Test: Filtrar notificaciones por tarjeta"""
        NotificacionesSaldo.objects.create(
            tipo='saldo_bajo',
            id_tarjeta=self.tarjeta,
            saldo_actual=Decimal('5000.00'),
            mensaje='Test',
            enviada=True
        )
        
        url = reverse('notificacionessaldo-list')
        response = self.client.get(url, {'id_tarjeta': self.tarjeta.id_tarjeta})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
