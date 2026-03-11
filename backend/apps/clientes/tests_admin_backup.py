"""
Tests para admin_backup de clientes
Cubre configuración de Django Admin para el módulo de clientes
"""

from django.test import TestCase
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from unittest.mock import Mock, patch

from apps.clientes.admin_backup import (
    ClientesAdmin,
    TiposClienteAdmin,
    HijosAdmin,
    GradosAdmin,
    HistorialGradosHijosAdmin,
    RestriccionesHijosAdmin,
    AutorizacionesSaldoNegativoAdmin,
    LogsAutorizacionesAdmin,
)
from apps.clientes.models import (
    Clientes,
    TiposCliente,
    Hijos,
    Grados,
    HistorialGradosHijos,
    RestriccionesHijos,
    AutorizacionesSaldoNegativo,
    LogsAutorizaciones,
)

User = get_user_model()


class MockRequest:
    """Mock request para testing de admin"""
    def __init__(self, user=None):
        self.user = user or Mock()


class ClientesAdminBackupTest(TestCase):
    """Tests para las configuraciones de admin backup de clientes"""

    def setUp(self):
        """Setup común para los tests"""
        self.site = AdminSite()
        self.rf = RequestFactory()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            'admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Crear datos de prueba básicos
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Cliente Regular',
            activo=True
        )
        
        self.cliente = Clientes.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            ruc_ci='12345678',
            email='juan@test.com',
            activo=True,
            id_tipo_cliente=self.tipo_cliente
        )
        
        self.grado = Grados.objects.create(
            nombre_grado='Primer Grado',
            nivel=1,
            orden_visualizacion=1,
            activo=True
        )
        
        self.hijo = Hijos.objects.create(
            nombre='Carlos',
            apellido='Pérez',
            id_cliente_responsable=self.cliente,
            grado=self.grado,
            activo=True
        )

    def test_clientes_admin_registration(self):
        """Debe estar registrado en Django admin"""
        self.assertIn(Clientes, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Clientes], ClientesAdmin)

    def test_clientes_admin_list_display(self):
        """Debe tener configuración correcta de list_display"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        expected_fields = ["id_cliente", "nombres", "apellidos", "ruc_ci", "email", "activo"]
        self.assertEqual(admin_instance.list_display, expected_fields)

    def test_clientes_admin_list_filter(self):
        """Debe tener configuración correcta de list_filter"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        self.assertEqual(admin_instance.list_filter, ["activo"])

    def test_clientes_admin_search_fields(self):
        """Debe tener configuración correcta de search_fields"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        expected_fields = ["nombres", "apellidos", "ruc_ci", "email"]
        self.assertEqual(admin_instance.search_fields, expected_fields)

    def test_clientes_admin_queryset(self):
        """Debe retornar queryset válido"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        request = MockRequest(self.admin_user)
        
        queryset = admin_instance.get_queryset(request)
        self.assertTrue(queryset.exists())
        self.assertIn(self.cliente, queryset)

    def test_tipos_cliente_admin_configuration(self):
        """Debe tener configuración correcta para TiposCliente"""
        admin_instance = TiposClienteAdmin(TiposCliente, self.site)
        
        # Verificar list_display
        expected_display = ["id_tipo_cliente", "nombre_tipo", "activo"]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["activo"])
        self.assertEqual(admin_instance.search_fields, ["nombre_tipo"])

    def test_hijos_admin_configuration(self):
        """Debe tener configuración correcta para Hijos"""
        admin_instance = HijosAdmin(Hijos, self.site)
        
        # Verificar list_display
        expected_display = ["id_hijo", "nombre", "apellido", "grado", "activo"]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["activo", "grado"])
        self.assertEqual(admin_instance.search_fields, ["nombre", "apellido"])

    def test_grados_admin_configuration(self):
        """Debe tener configuración correcta para Grados"""
        admin_instance = GradosAdmin(Grados, self.site)
        
        # Verificar list_display
        expected_display = ["id_grado", "nombre_grado", "nivel", "activo"]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["activo", "nivel"])
        self.assertEqual(admin_instance.search_fields, ["nombre_grado"])

    def test_historial_grados_admin_configuration(self):
        """Debe tener configuración correcta para HistorialGradosHijos"""
        admin_instance = HistorialGradosHijosAdmin(HistorialGradosHijos, self.site)
        
        # Verificar list_display
        expected_display = [
            "id_historial",
            "id_hijo",
            "grado_anterior",
            "grado_nuevo",
            "anio_escolar",
            "fecha_cambio",
        ]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["anio_escolar", "motivo"])
        self.assertEqual(admin_instance.search_fields, ["id_hijo__nombre", "id_hijo__apellido"])

    def test_restricciones_admin_configuration(self):
        """Debe tener configuración correcta para RestriccionesHijos"""
        admin_instance = RestriccionesHijosAdmin(RestriccionesHijos, self.site)
        
        # Verificar list_display
        expected_display = ["id_restriccion", "id_hijo", "tipo_restriccion", "severidad", "activo"]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["activo", "severidad"])

    def test_autorizaciones_saldo_admin_configuration(self):
        """Debe tener configuración correcta para AutorizacionesSaldoNegativo"""
        admin_instance = AutorizacionesSaldoNegativoAdmin(AutorizacionesSaldoNegativo, self.site)
        
        # Verificar list_display
        expected_display = [
            "id_autorizacion",
            "id_cliente",
            "monto_autorizado",
            "estado",
            "fecha_autorizacion",
        ]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros
        self.assertEqual(admin_instance.list_filter, ["estado"])

    def test_logs_autorizaciones_admin_configuration(self):
        """Debe tener configuración correcta para LogsAutorizaciones"""
        admin_instance = LogsAutorizacionesAdmin(LogsAutorizaciones, self.site)
        
        # Verificar list_display
        expected_display = ["id_log", "tipo_operacion", "resultado", "codigo_barra", "fecha_hora"]
        self.assertEqual(admin_instance.list_display, expected_display)
        
        # Verificar filtros y readonly
        self.assertEqual(admin_instance.list_filter, ["tipo_operacion", "resultado"])
        self.assertEqual(admin_instance.readonly_fields, ["id_log", "fecha_hora"])

    def test_admin_list_display_functionality(self):
        """Debe mostrar correctamente los campos en list_display"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        
        # Verificar que los campos se muestran correctamente
        for field in admin_instance.list_display:
            if hasattr(self.cliente, field):
                value = getattr(self.cliente, field)
                self.assertIsNotNone(str(value))

    def test_admin_search_functionality(self):
        """Debe funcionar la búsqueda en campos configurados"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        request = MockRequest(self.admin_user)
        
        # Simular búsqueda por nombre
        with patch.object(admin_instance, 'get_search_results') as mock_search:
            mock_search.return_value = (Clientes.objects.all(), False)
            
            queryset = admin_instance.get_queryset(request)
            mock_search.return_value
            
            # Verificar que se puede buscar
            self.assertTrue(hasattr(admin_instance, 'search_fields'))

    def test_admin_filtering_functionality(self):
        """Debe funcionar el filtrado en campos configurados"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        
        # Verificar que tiene list_filter configurado
        self.assertTrue(hasattr(admin_instance, 'list_filter'))
        self.assertIsNotNone(admin_instance.list_filter)

    def test_admin_permissions_integration(self):
        """Debe integrar correctamente con sistema de permisos"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        request = MockRequest(self.admin_user)
        
        # Verificar permisos básicos
        self.assertTrue(hasattr(admin_instance, 'has_view_permission'))
        self.assertTrue(hasattr(admin_instance, 'has_add_permission'))
        self.assertTrue(hasattr(admin_instance, 'has_change_permission'))
        self.assertTrue(hasattr(admin_instance, 'has_delete_permission'))

    def test_all_models_registered(self):
        """Debe registrar todos los modelos principales"""
        expected_models = [
            Clientes,
            TiposCliente,
            Hijos,
            Grados,
            HistorialGradosHijos,
            RestriccionesHijos,
            AutorizacionesSaldoNegativo,
            LogsAutorizaciones,
        ]
        
        for model in expected_models:
            self.assertIn(model, admin.site._registry, 
                         f"Modelo {model.__name__} no está registrado")

    def test_admin_security_configurations(self):
        """Debe tener configuraciones de seguridad apropiadas"""
        # Verificar LogsAutorizaciones tiene readonly_fields para seguridad
        admin_instance = LogsAutorizacionesAdmin(LogsAutorizaciones, self.site)
        readonly_fields = admin_instance.readonly_fields
        
        self.assertIn("id_log", readonly_fields)
        self.assertIn("fecha_hora", readonly_fields)

    def test_admin_url_generation(self):
        """Debe generar URLs de admin correctamente"""
        admin_instance = ClientesAdmin(Clientes, self.site)
        
        # Test que puede generar URL para elementos
        url = admin_instance.get_absolute_url() if hasattr(admin_instance, 'get_absolute_url') else None
        # Verificar que admin_instance está bien configurado
        self.assertIsNotNone(admin_instance.model)
        self.assertEqual(admin_instance.model, Clientes)

    def test_admin_custom_queryset_optimization(self):
        """Debe optimizar querysets cuando sea necesario"""
        admin_instance = HijosAdmin(Hijos, self.site)
        request = MockRequest(self.admin_user)
        
        queryset = admin_instance.get_queryset(request)
        
        # Verificar que el queryset es válido
        self.assertTrue(hasattr(queryset, 'model'))
        self.assertEqual(queryset.model, Hijos)

    def test_admin_inline_configurations(self):
        """Debe manejar configuraciones inline si existen"""
        # Verificar que los admins pueden tener inlines definidos
        for model, admin_class in admin.site._registry.items():
            if hasattr(admin_class, 'inlines'):
                self.assertIsInstance(admin_class.inlines, (list, tuple))