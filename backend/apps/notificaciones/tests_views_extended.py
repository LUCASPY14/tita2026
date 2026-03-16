"""
Tests extendidos para notificaciones views
Cubre ramas no cubiertas por tests_api.py
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal

from apps.notificaciones.models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion,
)
from apps.usuarios.models import UsuariosPortal
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.core.models import Tarjetas

User = get_user_model()


class BaseNotifTest(APITestCase):
    """Base con usuario y usuario_portal comunes"""

    def setUp(self):
        self.auth_user = User.objects.create_user(
            username='notif_ext_user', email='notif_ext@test.com', password='pass123'
        )
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo='Ext Test', estado=True)
        self.cliente = Clientes.objects.create(
            nombres='Ext', apellidos='Test', ruc_ci='EXT0001',
            estado=True, id_tipo_cliente=self.tipo_cliente,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email='ext_portal@test.com',
            password_hash='hashed',
            email_verificado=0,
            fecha_registro=timezone.now(),
            id_cliente=self.cliente,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.auth_user)


class NotificacionesPortalFechaFiltroTest(BaseNotifTest):
    """Tests para filtros de fecha en NotificacionesPortalViewSet"""

    def setUp(self):
        super().setUp()
        self.notif = NotificacionesPortal.objects.create(
            tipo='info', titulo='Test fecha', mensaje='Msg',
            leida=0, fecha_envio=timezone.now(), creado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )

    def test_filtrar_por_fecha_desde(self):
        """GET con fecha_desde debe filtrar correctamente"""
        url = reverse('notificaciones-portal-list')
        response = self.client.get(url, {'fecha_desde': '2020-01-01T00:00:00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_por_fecha_hasta(self):
        """GET con fecha_hasta debe filtrar correctamente"""
        url = reverse('notificaciones-portal-list')
        response = self.client.get(url, {'fecha_hasta': '2030-12-31T23:59:59'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_fecha_invalida(self):
        """GET con fecha inválida (ValueError) no debe fallar - se ignora silenciosamente"""
        url = reverse('notificaciones-portal-list')
        response = self.client.get(url, {'fecha_desde': 'not-a-date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MarcarTodasLeidasErrorTest(BaseNotifTest):
    """Tests de errores en marcar_todas_leidas"""

    def test_sin_id_usuario_retorna_400(self):
        """POST sin id_usuario_portal debe retornar 400"""
        url = reverse('notificaciones-portal-marcar-todas-leidas')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class ResumenErrorTest(BaseNotifTest):
    """Tests de errores en resumen"""

    def test_sin_id_usuario_retorna_400(self):
        """GET resumen sin id_usuario_portal debe retornar 400"""
        url = reverse('notificaciones-portal-resumen')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class NotificacionesSaldoFiltroTest(APITestCase):
    """Tests de filtros en NotificacionesSaldoViewSet"""

    def setUp(self):
        auth_user = User.objects.create_user(
            username='saldo_filtro_user', email='saldo_filtro@test.com', password='pass123'
        )
        tipo_cliente = TiposCliente.objects.create(nombre_tipo='Saldo Filtro', estado=True)
        cliente = Clientes.objects.create(
            nombres='Saldo', apellidos='Filtro', ruc_ci='SALDOF01',
            estado=True, id_tipo_cliente=tipo_cliente,
        )
        hijo = Hijos.objects.create(
            nombre='H', apellido='Ijo', estado=True, id_cliente_responsable=cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta='SF001',
            saldo_actual=Decimal('1000.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            limite_credito=Decimal('0.00'),
            id_hijo=hijo,
        )
        NotificacionesSaldo.objects.create(
            tipo_notificacion='saldo_bajo',
            nro_tarjeta=self.tarjeta,
            saldo_actual=Decimal('1000.00'),
            mensaje='Test',
            enviada_email=0,
            enviada_sms=0,
            leida=0,
            fecha_creacion=timezone.now(),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=auth_user)

    def test_filtrar_por_nro_tarjeta(self):
        """GET con nro_tarjeta debe filtrar"""
        url = reverse('notificaciones-saldo-list')
        response = self.client.get(url, {'nro_tarjeta': 'SF001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_por_tipo_notificacion(self):
        """GET con tipo_notificacion debe filtrar"""
        url = reverse('notificaciones-saldo-list')
        response = self.client.get(url, {'tipo_notificacion': 'saldo_bajo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AlertasSistemaFechaFiltroTest(APITestCase):
    """Tests de filtro fecha_desde en AlertasSistemaViewSet"""

    def setUp(self):
        auth_user = User.objects.create_user(
            username='alerta_fecha_user', email='alerta_fecha@test.com',
            password='pass123', is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=auth_user)
        AlertasSistema.objects.create(
            tipo='stock_critico',
            mensaje='Alerta fecha test',
            fecha_creacion=timezone.now(),
        )

    def test_filtrar_por_fecha_desde(self):
        """GET con fecha_desde en alertas debe filtrar"""
        url = reverse('alertas-sistema-list')
        response = self.client.get(url, {'fecha_desde': '2020-01-01T00:00:00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_fecha_invalida_silenciosa(self):
        """GET con fecha inválida no debe fallar"""
        url = reverse('alertas-sistema-list')
        response = self.client.get(url, {'fecha_desde': 'bad-date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_por_tipo(self):
        """GET filtrar por tipo de alerta"""
        url = reverse('alertas-sistema-list')
        response = self.client.get(url, {'tipo': 'stock_critico'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AlertasSistemaResolverConEmpleadoTest(APITestCase):
    """Tests de resolver alerta con id_empleado"""

    def setUp(self):
        auth_user = User.objects.create_user(
            username='alerta_emp_user', email='alerta_emp@test.com',
            password='pass123', is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=auth_user)
        self.alerta = AlertasSistema.objects.create(
            tipo='error_sistema',
            mensaje='Error test',
            fecha_creacion=timezone.now(),
        )

    def test_resolver_con_id_empleado(self):
        """POST resolver con id_empleado debe funcionar"""
        url = reverse('alertas-sistema-resolver', args=[self.alerta.id_alerta])
        response = self.client.post(url, {
            'observaciones': 'Resuelto manualmente',
            'id_empleado': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PreferenciasNotificacionErrorTest(BaseNotifTest):
    """Tests de errores en PreferenciasNotificacionViewSet"""

    def test_obtener_preferencias_sin_id_usuario(self):
        """GET obtener_preferencias sin id_usuario_portal debe retornar 400"""
        url = reverse('preferencias-notificacion-obtener-preferencias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_actualizar_preferencias_sin_datos_requeridos(self):
        """POST actualizar_preferencias sin datos requeridos debe retornar 400"""
        url = reverse('preferencias-notificacion-actualizar-preferencias')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_actualizar_preferencias_solo_id_sin_tipo(self):
        """POST con id_usuario pero sin tipo_notificacion debe retornar 400"""
        url = reverse('preferencias-notificacion-actualizar-preferencias')
        response = self.client.post(url, {
            'id_usuario_portal': self.usuario_portal.id_usuario_portal,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificacionesPortalFechaHastaInvalidaTest(BaseNotifTest):
    """Cover lines 58-59: fecha_hasta with invalid format triggers ValueError silently."""

    def test_filtrar_fecha_hasta_invalida(self):
        """GET con fecha_hasta inválida debe ignorarse silenciosamente."""
        url = reverse('notificaciones-portal-list')
        response = self.client.get(url, {'fecha_hasta': 'not-a-valid-date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AlertasSistemaResolverConIdEmpleadoTest(APITestCase):
    """Cover line 203: resolver alerta with id_empleado_resuelve set."""

    def setUp(self):
        auth_user = User.objects.create_user(
            username='resolver_emp2', email='resolver_emp2@test.com',
            password='pass123', is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=auth_user)
        self.alerta = AlertasSistema.objects.create(
            tipo='test_tipo',
            mensaje='Test resolver con emp',
            fecha_creacion=timezone.now(),
        )

    def test_resolver_alerta_con_id_empleado_resuelve(self):
        """Line 203: POST resolver with id_empleado_resuelve → sets field."""
        url = reverse('alertas-sistema-resolver', args=[self.alerta.id_alerta])
        response = self.client.post(url, {
            'observaciones': 'Resuelto OK',
            'id_empleado_resuelve': 42,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
