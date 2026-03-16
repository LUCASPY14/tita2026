"""
Tests para ViewSets de notificaciones - API Tests
"""

import pytest  # type: ignore
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
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


class NotificacionesPortalViewSetTest(APITestCase):
    """Tests para NotificacionesPortalViewSet"""

    def setUp(self):
        """Configuración inicial"""
        # Crear usuario Django para autenticación
        self.auth_user = User.objects.create_user(
            username="testuser_napi", email="test_napi@cantina.com", password="testpass123"
        )

        # Crear cadena: TiposCliente -> Clientes -> UsuariosPortal
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular NApi", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Test", apellidos="NApi", ruc_ci="12340001",
            estado=True, id_tipo_cliente=self.tipo_cliente,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="portal_napi@cantina.com",
            password_hash="hashed",
            email_verificado=0,
            fecha_registro=timezone.now(),
            id_cliente=self.cliente,
        )

        # Autenticar cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.auth_user)

        # Crear notificaciones de prueba
        self.notif1 = NotificacionesPortal.objects.create(
            tipo="info", titulo="Notificación 1", mensaje="Mensaje 1",
            leida=0, fecha_envio=timezone.now(), creado_en=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )
        self.notif2 = NotificacionesPortal.objects.create(
            tipo="warning", titulo="Notificación 2", mensaje="Mensaje 2",
            leida=1, fecha_envio=timezone.now(), creado_en=timezone.now(),
            fecha_lectura=timezone.now(),
            id_usuario_portal=self.usuario_portal,
        )

    def test_listar_notificaciones(self):
        """Test: GET /api/v1/notificaciones-portal/"""
        url = reverse("notificaciones-portal-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_notificaciones_no_leidas(self):
        """Test: Filtrar notificaciones no leídas"""
        url = reverse("notificaciones-portal-list")
        response = self.client.get(url, {"leida": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_por_tipo(self):
        """Test: Filtrar notificaciones por tipo"""
        url = reverse("notificaciones-portal-list")
        response = self.client.get(url, {"tipo": "warning"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_marcar_notificacion_leida(self):
        """Test: POST marcar_leida"""
        url = reverse("notificaciones-portal-marcar-leida", args=[self.notif1.id_notificacion])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notif1.refresh_from_db()
        self.assertEqual(self.notif1.leida, 1)
        self.assertIsNotNone(self.notif1.fecha_lectura)

    def test_marcar_todas_leidas(self):
        """Test: POST marcar_todas_leidas (requires id_usuario_portal)"""
        url = reverse("notificaciones-portal-marcar-todas-leidas")
        response = self.client.post(url, {"id_usuario_portal": self.usuario_portal.id_usuario_portal})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        no_leidas = NotificacionesPortal.objects.filter(
            id_usuario_portal=self.usuario_portal, leida=0
        ).count()
        self.assertEqual(no_leidas, 0)

    def test_obtener_resumen(self):
        """Test: GET resumen (requires id_usuario_portal query param)"""
        url = reverse("notificaciones-portal-resumen")
        response = self.client.get(url, {"id_usuario_portal": self.usuario_portal.id_usuario_portal})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_notificaciones", response.data)
        self.assertIn("no_leidas", response.data)


class AlertasSistemaViewSetTest(APITestCase):
    """Tests para AlertasSistemaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.auth_user = User.objects.create_user(
            username="admin_alert", email="admin_alert@cantina.com",
            password="admin123", is_staff=True
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.auth_user)

        # Crear alertas con campos reales del modelo
        self.alerta1 = AlertasSistema.objects.create(
            tipo="stock_critico",
            mensaje="Stock bajo en Producto X",
            fecha_creacion=timezone.now(),
        )
        self.alerta2 = AlertasSistema.objects.create(
            tipo="anomalia_venta",
            mensaje="Venta inusual detectada",
            fecha_creacion=timezone.now(),
            estado="Resuelta",
            fecha_resolucion=timezone.now(),
        )

    def test_listar_alertas(self):
        """Test: GET /api/v1/alertas-sistema/"""
        url = reverse("alertas-sistema-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filtrar_alertas_por_estado(self):
        """Test: Filtrar alertas por estado"""
        url = reverse("alertas-sistema-list")
        response = self.client.get(url, {"estado": "Resuelta"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resolver_alerta(self):
        """Test: POST resolver"""
        url = reverse("alertas-sistema-resolver", args=[self.alerta1.id_alerta])
        data = {"observaciones": "Stock reabastecido correctamente"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.alerta1.refresh_from_db()
        self.assertEqual(self.alerta1.estado, "Resuelta")
        self.assertIsNotNone(self.alerta1.fecha_resolucion)
        self.assertEqual(self.alerta1.observaciones, "Stock reabastecido correctamente")


class PreferenciasNotificacionViewSetTest(APITestCase):
    """Tests para PreferenciasNotificacionViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.auth_user = User.objects.create_user(
            username="user_pref", email="user_pref@cantina.com", password="pass123"
        )

        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular Pref", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="User", apellidos="Pref", ruc_ci="11110002",
            estado=True, id_tipo_cliente=self.tipo_cliente,
        )
        self.usuario_portal = UsuariosPortal.objects.create(
            email="portal_pref@cantina.com",
            password_hash="hashed",
            email_verificado=0,
            fecha_registro=timezone.now(),
            id_cliente=self.cliente,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.auth_user)

    def test_obtener_preferencias(self):
        """Test: GET obtener_preferencias (requires id_usuario_portal)"""
        url = reverse("preferencias-notificacion-obtener-preferencias")
        response = self.client.get(url, {"id_usuario_portal": self.usuario_portal.id_usuario_portal})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_actualizar_preferencias(self):
        """Test: POST actualizar_preferencias"""
        url = reverse("preferencias-notificacion-actualizar-preferencias")
        data = {
            "id_usuario_portal": self.usuario_portal.id_usuario_portal,
            "tipo_notificacion": "ventas",
            "email_activo": 0,
            "push_activo": 1,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prefs = PreferenciasNotificacion.objects.get(
            id_usuario_portal=self.usuario_portal, tipo_notificacion="ventas"
        )
        self.assertEqual(prefs.email_activo, 0)
        self.assertEqual(prefs.push_activo, 1)


@pytest.mark.api
@pytest.mark.django_db
class TestNotificacionesSaldoViewSet:
    """Tests para NotificacionesSaldoViewSet usando pytest"""

    def setup_method(self):
        """Configuración para cada test"""
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular Saldo", estado=True)
        cliente = Clientes.objects.create(
            nombres="Test", apellidos="Saldo", ruc_ci="99990001",
            estado=True, id_tipo_cliente=tipo_cliente,
        )
        hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", estado=True, id_cliente_responsable=cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="9999001",
            saldo_actual=Decimal("5000.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0.00"),
            id_hijo=hijo,
        )

        usuario = User.objects.create_user(
            username="testapi_saldo", email="api_saldo@test.com", password="test123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=usuario)

    def test_listar_notificaciones_saldo(self):
        """Test: Listar notificaciones de saldo"""
        NotificacionesSaldo.objects.create(
            tipo_notificacion="saldo_bajo",
            nro_tarjeta=self.tarjeta,
            saldo_actual=Decimal("5000.00"),
            mensaje="Saldo bajo",
            enviada_email=1,
            enviada_sms=0,
            leida=0,
            fecha_creacion=timezone.now(),
        )

        url = reverse("notificaciones-saldo-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filtrar_por_tarjeta(self):
        """Test: Filtrar notificaciones por nro_tarjeta"""
        NotificacionesSaldo.objects.create(
            tipo_notificacion="saldo_bajo",
            nro_tarjeta=self.tarjeta,
            saldo_actual=Decimal("5000.00"),
            mensaje="Test",
            enviada_email=0,
            enviada_sms=0,
            leida=0,
            fecha_creacion=timezone.now(),
        )

        url = reverse("notificaciones-saldo-list")
        response = self.client.get(url, {"nro_tarjeta": self.tarjeta.nro_tarjeta})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
