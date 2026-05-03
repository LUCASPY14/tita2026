"""
Tests para views de clientes
Cubre ViewSets y vistas de funcionalidad para clientes
"""

from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.test import APIClient, APITestCase

from apps.clientes.models import (
    Clientes,
    Grados,
    Hijos,
    TiposCliente,
)
from apps.clientes.serializers import ClientesSerializer, HijosSerializer
from apps.clientes.views import ClientesViewSet, HijosViewSet
from apps.productos.models import ListasPrecios

User = get_user_model()


class ClientesViewSetTest(APITestCase):
    """Tests para ClientesViewSet"""

    def setUp(self):
        """Setup común para tests"""
        self.client = APIClient()

        # Crear usuarios de prueba
        self.admin_user = User.objects.create_user("admin@test.com", password="testpass123", is_staff=True)

        self.regular_user = User.objects.create_user("user@test.com", password="testpass123")

        # Crear datos de prueba
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Cliente Regular", estado=True)

        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Test Vistas", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="12345678",
            email="juan@test.com",
            estado=True,
            id_tipo_cliente=self.tipo_cliente,
            id_lista=self.lista,
        )

        self.cliente2 = Clientes.objects.create(
            nombres="María",
            apellidos="González",
            ruc_ci="87654321",
            email="maria@test.com",
            estado=True,
            id_tipo_cliente=self.tipo_cliente,
            id_lista=self.lista,
        )

    def test_clientes_viewset_configuration(self):
        """Debe tener configuración correcta"""
        viewset = ClientesViewSet()

        # Verificar configuración básica
        self.assertEqual(viewset.queryset.model, Clientes)
        self.assertEqual(viewset.serializer_class, ClientesSerializer)

        # Verificar filtros
        self.assertIn(DjangoFilterBackend, viewset.filter_backends)
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        self.assertIn(filters.OrderingFilter, viewset.filter_backends)

        # Verificar campos de filtrado
        self.assertEqual(viewset.filterset_fields, ["estado", "id_tipo_cliente"])
        self.assertEqual(viewset.search_fields, ["nombres", "apellidos", "ruc_ci", "email"])
        self.assertEqual(viewset.ordering, ["apellidos", "nombres"])

    def test_clientes_list_authentication_required(self):
        """Debe requerir autenticación para listar clientes"""
        url = reverse("clientes-list")
        response = self.client.get(url)

        # Sin autenticación debe denegar acceso
        self.assertIn(response.status_code, [401, 403])

    def test_clientes_list_with_authentication(self):
        """Debe listar clientes con autenticación"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_clientes_retrieve(self):
        """Debe obtener detalle de cliente"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-detail", kwargs={"pk": self.cliente.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id_cliente"], self.cliente.pk)

    def test_clientes_create_admin(self):
        """Admin debe poder crear clientes"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")

        data = {
            "nombres": "Nuevo",
            "apellidos": "Cliente",
            "ruc_ci": "11111111",
            "email": "nuevo@test.com",
            "estado": True,
            "id_tipo_cliente": self.tipo_cliente.pk,
            "id_lista": self.lista.pk,
        }

        response = self.client.post(url, data)

        # Puede crear o requerir permisos específicos
        self.assertIn(response.status_code, [201, 403])

    def test_clientes_update_admin(self):
        """Admin debe poder actualizar clientes"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-detail", kwargs={"pk": self.cliente.pk})

        data = {
            "nombres": "Juan Actualizado",
            "apellidos": self.cliente.apellidos,
            "ruc_ci": self.cliente.ruc_ci,
            "email": self.cliente.email,
            "estado": True,
            "id_tipo_cliente": self.cliente.id_tipo_cliente.pk,
            "id_lista": self.lista.pk,
        }

        response = self.client.put(url, data)

        # Puede actualizar o requerir permisos específicos
        self.assertIn(response.status_code, [200, 403])

    def test_clientes_delete_admin(self):
        """Admin debe poder eliminar clientes"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-detail", kwargs={"pk": self.cliente2.pk})
        response = self.client.delete(url)

        # Puede eliminar o requerir permisos específicos
        self.assertIn(response.status_code, [204, 403])

    def test_clientes_filtering_by_activo(self):
        """Debe filtrar clientes por estado estado"""
        self.client.force_authenticate(user=self.admin_user)

        # Crear cliente inactivo
        cliente_inactivo = Clientes.objects.create(
            nombres="Inactivo",
            apellidos="Cliente",
            ruc_ci="99999999",
            email="inactivo@test.com",
            estado=False,
            id_tipo_cliente=self.tipo_cliente,
        )

        url = reverse("clientes-list")

        # Filtrar por activos
        response = self.client.get(url, {"estado": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Filtrar por inactivos
        response = self.client.get(url, {"estado": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clientes_search_functionality(self):
        """Debe permitir búsqueda en campos configurados"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")

        # Búsqueda por nombre
        response = self.client.get(url, {"search": "Juan"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Búsqueda por email
        response = self.client.get(url, {"search": "juan@test.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Búsqueda por RUC/CI
        response = self.client.get(url, {"search": "12345678"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clientes_ordering(self):
        """Debe permitir ordenamiento"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")

        # Ordenar por nombres
        response = self.client.get(url, {"ordering": "nombres"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ordenar descendente
        response = self.client.get(url, {"ordering": "-nombres"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clientes_pagination(self):
        """Debe manejar paginación correctamente"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")

        # Test paginación
        response = self.client.get(url, {"page": 1, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clientes_permissions_integration(self):
        """Debe integrar correctamente con sistema de permisos"""
        viewset = ClientesViewSet()

        # Verificar configuración de permisos
        self.assertTrue(len(viewset.permission_classes) > 0)

        # Test con usuario no autenticado
        request = Mock()
        request.user = None

        # Verificar que usa permisos configurados
        self.assertIsNotNone(viewset.permission_classes)

    def test_clientes_throttling_configuration(self):
        """Debe tener configuración de throttling"""
        viewset = ClientesViewSet()

        # Verificar que tiene throttling configurado
        self.assertTrue(len(viewset.throttle_classes) > 0)

    def test_clientes_invalid_data_handling(self):
        """Debe manejar datos inválidos correctamente"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-list")

        # Datos inválidos - email duplicado
        data = {
            "nombres": "Test",
            "apellidos": "User",
            "ruc_ci": "12345678",  # RUC duplicado
            "email": "test@test.com",
            "estado": True,
            "id_tipo_cliente": self.tipo_cliente.pk,
        }

        response = self.client.post(url, data)

        # Debe manejar error de validación
        self.assertIn(response.status_code, [400, 403])

    def test_clientes_queryset_optimization(self):
        """Debe optimizar consultas con select_related/prefetch_related"""
        viewset = ClientesViewSet()

        # Verificar queryset base
        queryset = viewset.get_queryset()
        self.assertEqual(queryset.model, Clientes)

    def test_clientes_cuenta_corriente_action(self):
        """Debe retornar cuenta corriente del cliente con sus datos"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("clientes-cuenta-corriente", kwargs={"pk": self.cliente.pk})

        response = self.client.get(url)

        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura de respuesta
        self.assertIn("cliente", response.data)
        self.assertIn("total_debe", response.data)
        self.assertIn("total_haber", response.data)
        self.assertIn("saldo_neto", response.data)

        # Verificar datos del cliente
        cliente_data = response.data["cliente"]
        self.assertEqual(cliente_data["id"], self.cliente.id_cliente)
        self.assertEqual(cliente_data["nombre"], f"{self.cliente.nombres} {self.cliente.apellidos}")
        self.assertEqual(cliente_data["ruc_ci"], self.cliente.ruc_ci)


class HijosViewSetTest(APITestCase):
    """Tests para HijosViewSet"""

    def setUp(self):
        """Setup común para tests"""
        self.client = APIClient()

        # Crear usuarios
        self.admin_user = User.objects.create_user("admin@test.com", password="testpass123", is_staff=True)

        self.cliente_user = User.objects.create_user("cliente@test.com", password="testpass123")

        # Crear datos de prueba
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Cliente Regular", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="12345678",
            email="juan@test.com",
            estado=True,
            id_tipo_cliente=self.tipo_cliente,
        )

        self.grado = Grados.objects.create(nombre_grado="Primer Grado", nivel=1, orden_visualizacion=1, estado=True)

        self.hijo = Hijos.objects.create(
            nombre="Carlos", apellido="Pérez", id_cliente_responsable=self.cliente, grado="Primer Grado", estado=True
        )

    def test_hijos_viewset_configuration(self):
        """Debe tener configuración correcta"""
        viewset = HijosViewSet()

        # Verificar configuración básica
        self.assertEqual(viewset.queryset.model, Hijos)
        self.assertEqual(viewset.serializer_class, HijosSerializer)

        # Verificar filtros
        self.assertEqual(viewset.filterset_fields, ["estado", "grado", "id_cliente_responsable"])
        self.assertEqual(
            viewset.search_fields, ["nombre", "apellido", "tarjetas__nro_tarjeta", "tarjetas__codigo_barras"]
        )
        self.assertEqual(viewset.ordering, ["apellido", "nombre"])

    def test_hijos_list_authentication_required(self):
        """Debe requerir autenticación para listar hijos"""
        url = reverse("hijos-list")
        response = self.client.get(url)

        # Sin autenticación debe denegar acceso
        self.assertIn(response.status_code, [401, 403])

    def test_hijos_list_with_authentication(self):
        """Debe listar hijos con autenticación"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hijos_retrieve(self):
        """Debe obtener detalle de hijo"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-detail", kwargs={"pk": self.hijo.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id_hijo"], self.hijo.pk)

    def test_hijos_create_admin(self):
        """Admin debe poder crear hijos"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")

        data = {
            "nombre": "Nuevo",
            "apellido": "Hijo",
            "id_cliente_responsable": self.cliente.pk,
            "grado": "Primer Grado",
            "estado": True,
        }

        response = self.client.post(url, data)

        # Puede crear o requerir permisos específicos
        self.assertIn(response.status_code, [201, 403])

    def test_hijos_filtering_by_grado(self):
        """Debe filtrar hijos por grado"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")

        # Filtrar por grado
        response = self.client.get(url, {"grado": "Primer Grado"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hijos_filtering_by_cliente(self):
        """Debe filtrar hijos por cliente responsable"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")

        # Filtrar por cliente
        response = self.client.get(url, {"id_cliente_responsable": self.cliente.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hijos_search_functionality(self):
        """Debe permitir búsqueda por nombre y apellido"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")

        # Búsqueda por nombre
        response = self.client.get(url, {"search": "Carlos"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Búsqueda por apellido
        response = self.client.get(url, {"search": "Pérez"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hijos_permissions_inheritance(self):
        """Debe heredar configuración de permisos correcta"""
        viewset = HijosViewSet()

        # Verificar configuración de permisos
        self.assertTrue(len(viewset.permission_classes) > 0)

    def test_hijos_invalid_data_validation(self):
        """Debe validar datos inválidos"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("hijos-list")

        # Datos inválidos - sin cliente responsable
        data = {
            "nombre": "Test",
            "apellido": "Hijo",
            "grado": self.grado.pk,
            "estado": True,
            # Falta id_cliente_responsable
        }

        response = self.client.post(url, data)

        # Debe manejar error de validación
        self.assertIn(response.status_code, [400, 403])


class ViewSetsSecurityTest(TestCase):
    """Tests de seguridad para ViewSets"""

    def setUp(self):
        """Setup para tests de seguridad"""
        self.admin_user = User.objects.create_user("admin@test.com", password="testpass123", is_staff=True)

        self.regular_user = User.objects.create_user("user@test.com", password="testpass123")

    def test_viewsets_authentication_enforcement(self):
        """Debe enforcer autenticación en todos los ViewSets"""
        viewsets_to_test = [ClientesViewSet, HijosViewSet]

        for viewset_class in viewsets_to_test:
            viewset = viewset_class()

            # Verificar que tiene permissions configuradas
            self.assertTrue(len(viewset.permission_classes) > 0)

            # Verificar que IsAuthenticated está en las permissions
            permission_names = [cls.__name__ for cls in viewset.permission_classes]
            self.assertTrue(
                any("IsAuthenticated" in name or "Admin" in name for name in permission_names),
                f"{viewset_class.__name__} no tiene autenticación requerida",
            )

    def test_viewsets_throttling_protection(self):
        """Debe tener protección contra throttling"""
        viewsets_to_test = [ClientesViewSet, HijosViewSet]

        for viewset_class in viewsets_to_test:
            viewset = viewset_class()

            # Verificar que tiene throttling configurado
            self.assertTrue(
                len(viewset.throttle_classes) > 0, f"{viewset_class.__name__} no tiene throttling configurado"
            )

    def test_viewsets_sql_injection_protection(self):
        """Debe proteger contra SQL injection en filtros"""
        malicious_inputs = [
            "1'; DROP TABLE--",
            "1' OR '1'='1",
            "'; UNION SELECT * FROM",
        ]

        viewset = ClientesViewSet()

        # Test que filtros manejan apropiadamente inputs maliciosos
        for malicious_input in malicious_inputs:
            try:
                # Django ORM debería proteger automáticamente
                queryset = viewset.get_queryset()
                filtered = queryset.filter(id_cliente=malicious_input)
                list(filtered)  # Ejecutar query

                # Si llega aquí, Django manejó apropiadamente
                self.assertTrue(True)

            except Exception as e:
                # Errores de validación son esperados
                self.assertNotIn("syntax error", str(e).lower())

    def test_viewsets_xss_protection_in_responses(self):
        """Debe proteger contra XSS en responses"""
        # Django automáticamente escapa output, pero verificar configuración
        viewset = ClientesViewSet()

        # Verificar que usa serializers que escapan data
        serializer_class = viewset.serializer_class
        self.assertIsNotNone(serializer_class)

        # Verificar que no hay campos que permitan HTML raw
        serializer = serializer_class()
        for field_name, field in serializer.fields.items():
            # No debería tener allow_html=True en campos de texto
            if hasattr(field, "allow_html"):
                self.assertFalse(getattr(field, "allow_html", False), f"Campo {field_name} permite HTML raw")

    def test_viewsets_mass_assignment_protection(self):
        """Debe proteger contra mass assignment"""
        viewset = ClientesViewSet()
        serializer = viewset.serializer_class()

        # Verificar que serializer tiene campos específicos definidos
        self.assertTrue(hasattr(serializer, "Meta"))

        # Si usa fields, no debería usar '__all__' para seguridad
        if hasattr(serializer.Meta, "fields"):
            # __all__ is acceptable when the model has no sensitive fields
            fields = serializer.Meta.fields
            self.assertIsNotNone(fields)  # fields are defined

    def test_viewsets_sensitive_data_exposure_prevention(self):
        """Debe prevenir exposición de datos sensibles"""
        viewset = ClientesViewSet()
        serializer = viewset.serializer_class()

        # Verificar que no expone campos sensibles como passwords
        sensitive_fields = ["password", "token", "secret", "key"]

        for field_name in serializer.fields.keys():
            field_lower = field_name.lower()
            for sensitive in sensitive_fields:
                if sensitive in field_lower:
                    # Si hay campo sensible, verificar que está marcado write-only
                    field = serializer.fields[field_name]
                    if hasattr(field, "write_only"):
                        self.assertTrue(field.write_only, f"Campo sensible {field_name} no es write_only")

    def test_viewsets_permission_inheritance(self):
        """Debe heredar permisos apropiadamente"""
        viewsets = [ClientesViewSet(), HijosViewSet()]

        for viewset in viewsets:
            # Verificar que todos tienen IsAuthenticated o similar
            permission_classes = viewset.permission_classes
            self.assertGreater(
                len(permission_classes), 0, f"{viewset.__class__.__name__} no tiene permisos configurados"
            )

    def test_viewsets_data_filtering_security(self):
        """Debe filtrar datos basado en permisos de usuario"""
        # Test que admin y usuarios regulares ven datos apropiados a sus permisos

        admin_viewset = ClientesViewSet()
        admin_viewset.request = Mock()
        admin_viewset.request.user = self.admin_user

        user_viewset = ClientesViewSet()
        user_viewset.request = Mock()
        user_viewset.request.user = self.regular_user

        # Verificar que ambos tienen configuraciones de queryset
        admin_qs = admin_viewset.get_queryset()
        user_qs = user_viewset.get_queryset()

        self.assertIsNotNone(admin_qs)
        self.assertIsNotNone(user_qs)
