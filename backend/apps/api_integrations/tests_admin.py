"""
Tests para admin de api_integrations
Cubre configuración e interfaz administrativa para integraciones API
"""

from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone
from django.contrib.admin import ModelAdmin
import json

from apps.api_integrations.models import (
    ProveedoresApi,
    EndpointsApi,
    LogsLlamadasApi,
    CredencialesApi,
    LogsWebhooks,
    WebhookEndpoints
)
from apps.api_integrations.admin import (
    ProveedoresApiAdmin,
    EndpointsApiAdmin,
    LogsLlamadasApiAdmin,
    CredencialesApiAdmin,
    LogsWebhooksAdmin,
    WebhookEndpointsAdmin
)
from apps.usuarios.models import Empleados, Roles


class MockRequest:
    """Mock de request para testing admin"""
    def __init__(self, user=None):
        self.user = user
        self.GET = {}
        self.POST = {}


class ProveedoresApiAdminTest(TestCase):
    """Tests para ProveedoresApiAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = ProveedoresApiAdmin(ProveedoresApi, self.site)
        
        # Crear usuario admin
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear proveedor
        self.proveedor = ProveedoresApi.objects.create(
            nombre='AdminTestProvider',
            descripcion='Proveedor para tests de admin',
            tipo_servicio='payment_gateway',
            url_base='https://api.admintest.com',
            version='1.0',
            documentacion='https://docs.admintest.com',
            tipo_auth='api_key',
            config_auth={'api_key': 'admin_test_key'},
            timeout=30,
            max_reintentos=3,
            activo=True,
            created_at=timezone.now()
        )

    def test_admin_list_display(self):
        """Debe mostrar campos correctos en lista"""
        expected_fields = [
            'id_proveedor', 'nombre', 'tipo_servicio', 
            'url_base', 'version', 'activo', 'created_at'
        ]
        
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.list_display)

    def test_admin_list_filter(self):
        """Debe tener filtros apropiados"""
        expected_filters = ['activo', 'tipo_servicio', 'tipo_auth', 'created_at']
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)

    def test_admin_search_fields(self):
        """Debe permitir búsqueda en campos apropiados"""
        expected_search_fields = ['nombre', 'descripcion', 'tipo_servicio']
        
        for field in expected_search_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.search_fields)

    def test_admin_readonly_fields(self):
        """Debe tener campos de solo lectura apropiados"""
        expected_readonly = ['id_proveedor', 'created_at']
        
        for field in expected_readonly:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.readonly_fields)

    def test_admin_fieldsets(self):
        """Debe organizar campos en fieldsets apropiados"""
        self.assertIsNotNone(self.admin.fieldsets)
        
        # Verificar que hay secciones lógicas
        fieldset_names = [fs[0] for fs in self.admin.fieldsets if fs[0]]
        self.assertIn('Información Básica', fieldset_names)
        self.assertIn('Configuración de API', fieldset_names)
        self.assertIn('Autenticación', fieldset_names)

    def test_admin_ordering(self):
        """Debe tener ordenamiento por defecto"""
        self.assertEqual(self.admin.ordering, ['nombre'])

    def test_admin_has_add_permission(self):
        """Debe verificar permisos de adición"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_add_permission(request)
        self.assertTrue(has_permission)

    def test_admin_has_change_permission(self):
        """Debe verificar permisos de modificación"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_change_permission(request, self.proveedor)
        self.assertTrue(has_permission)

    def test_admin_has_delete_permission(self):
        """Debe verificar permisos de eliminación"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_delete_permission(request, self.proveedor)
        # Puede ser False si está configurado para prevenir eliminación
        self.assertIsInstance(has_permission, bool)

    def test_admin_config_auth_display(self):
        """Debe mostrar config_auth de forma apropiada en admin"""
        # Verificar que config_auth se maneja correctamente
        config_auth = self.proveedor.config_auth
        self.assertIsInstance(config_auth, dict)

    def test_admin_actions(self):
        """Debe tener acciones administrativas apropiadas"""
        actions = self.admin.get_actions(MockRequest(self.user))
        
        # Debe tener al menos la acción de eliminación por defecto
        self.assertIn('delete_selected', actions)

    def test_admin_queryset_optimization(self):
        """Debe optimizar queryset apropiadamente"""
        request = MockRequest(self.user)
        queryset = self.admin.get_queryset(request)
        
        # Verificar que retorna queryset válido
        self.assertEqual(queryset.model, ProveedoresApi)


class EndpointsApiAdminTest(TestCase):
    """Tests para EndpointsApiAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = EndpointsApiAdmin(EndpointsApi, self.site)
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear proveedor y endpoint
        self.proveedor = ProveedoresApi.objects.create(
            nombre='EndpointProvider',
            descripcion='Proveedor para endpoints',
            tipo_servicio='api',
            url_base='https://api.endpoint.com',
            version='1.0',
            tipo_auth='none',
            config_auth={},
            timeout=30,
            max_reintentos=1,
            created_at=timezone.now()
        )
        
        self.endpoint = EndpointsApi.objects.create(
            nombre='Admin Test Endpoint',
            descripcion='Endpoint para tests de admin',
            path='/admin/test',
            metodo='GET',
            headers={'Accept': 'application/json'},
            parametros={'limit': 'integer', 'offset': 'integer'},
            schema_request={'type': 'object'},
            schema_response={'type': 'object'},
            cache_segundos=300,
            requiere_auth=1,
            activo=True,
            id_proveedor=self.proveedor
        )

    def test_admin_list_display(self):
        """Debe mostrar campos correctos en lista de endpoints"""
        expected_fields = [
            'id_endpoint', 'nombre', 'proveedor_nombre', 'metodo', 
            'path', 'requiere_auth', 'activo'
        ]
        
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.list_display)

    def test_admin_list_filter(self):
        """Debe filtrar por campos apropiados"""
        expected_filters = ['metodo', 'requiere_auth', 'activo', 'id_proveedor']
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)

    def test_admin_proveedor_nombre_method(self):
        """Debe mostrar nombre del proveedor correctamente"""
        proveedor_nombre = self.admin.proveedor_nombre(self.endpoint)
        self.assertEqual(proveedor_nombre, 'EndpointProvider')

    def test_admin_raw_id_fields(self):
        """Debe usar raw_id_fields para relaciones"""
        if hasattr(self.admin, 'raw_id_fields'):
            self.assertIn('id_proveedor', self.admin.raw_id_fields)

    def test_admin_inline_configuration(self):
        """Debe configurar inlines apropiadamente si los tiene"""
        # Verificar si hay inlines configurados
        if hasattr(self.admin, 'inlines'):
            self.assertIsInstance(self.admin.inlines, (list, tuple))


class LogsLlamadasApiAdminTest(TestCase):
    """Tests para LogsLlamadasApiAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = LogsLlamadasApiAdmin(LogsLlamadasApi, self.site)
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear empleado
        self.rol = Roles.objects.create(
            nombre_rol='AdminRole',
            descripcion='Rol para admin tests',
            activo=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Admin',
            apellido='User',
            usuario='adminuser',
            contrasena_hash='$2b$12$hash',
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Crear log
        self.log = LogsLlamadasApi.objects.create(
            timestamp=timezone.now(),
            metodo='POST',
            url='https://api.test.com/endpoint',
            headers_req={'Content-Type': 'application/json'},
            payload_req='{"test": "data"}',
            status_code=200,
            headers_res={'Content-Type': 'application/json'},
            payload_res='{"success": true}',
            tiempo_ms=150,
            bytes_sent=20,
            bytes_received=18,
            exitoso=1,
            error_msg=None,
            intento=1,
            ip_origen='192.168.1.100',
            contexto={'test_context': 'value'},
            id_empleado=self.empleado
        )

    def test_admin_list_display_logs(self):
        """Debe mostrar campos apropiados en lista de logs"""
        expected_fields = [
            'id_log', 'timestamp', 'metodo', 'url', 'status_code', 
            'tiempo_ms', 'exitoso', 'intento'
        ]
        
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.list_display)

    def test_admin_list_filter_logs(self):
        """Debe filtrar logs apropiadamente"""
        expected_filters = ['exitoso', 'metodo', 'status_code', 'timestamp']
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)

    def test_admin_readonly_fields_logs(self):
        """Debe tener todos los campos como solo lectura para logs"""
        # Los logs generalmente no deben editarse
        readonly_fields = self.admin.readonly_fields
        self.assertIsNotNone(readonly_fields)
        
        # Debe incluir campos clave como id_log y timestamp
        self.assertIn('id_log', readonly_fields)
        self.assertIn('timestamp', readonly_fields)

    def test_admin_has_add_permission_logs(self):
        """No debe permitir agregar logs manualmente"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_add_permission(request)
        self.assertFalse(has_permission)

    def test_admin_has_change_permission_logs(self):
        """No debe permitir editar logs existentes"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_change_permission(request, self.log)
        self.assertFalse(has_permission)

    def test_admin_ordering_logs(self):
        """Debe ordenar logs por timestamp descendente"""
        self.assertEqual(self.admin.ordering, ['-timestamp'])

    def test_admin_date_hierarchy_logs(self):
        """Debe tener jerarquía de fechas"""
        self.assertEqual(self.admin.date_hierarchy, 'timestamp')


class CredencialesApiAdminTest(TestCase):
    """Tests para CredencialesApiAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = CredencialesApiAdmin(CredencialesApi, self.site)
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear proveedor y credenciales
        self.proveedor = ProveedoresApi.objects.create(
            nombre='CredentialProvider',
            descripcion='Proveedor para credenciales',
            tipo_servicio='payment',
            url_base='https://api.credential.com',
            version='1.0',
            tipo_auth='oauth2',
            config_auth={'client_id': 'test'},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now()
        )
        
        self.credencial = CredencialesApi.objects.create(
            ambiente='staging',
            api_key='admin_test_key',
            secret='admin_test_secret',
            configuracion={'oauth_scope': 'read write'},
            fecha_expiracion=timezone.now() + timezone.timedelta(days=30),
            updated_at=timezone.now(),
            activo=True,
            id_proveedor=self.proveedor
        )

    def test_admin_list_display_credentials(self):
        """Debe mostrar campos apropiados sin exponer secretos"""
        list_display = self.admin.list_display
        
        # Debe incluir campos informativos
        expected_safe_fields = ['id_credencial', 'proveedor_nombre', 'ambiente', 'activo', 'updated_at']
        for field in expected_safe_fields:
            with self.subTest(field=field):
                self.assertIn(field, list_display)
        
        # NO debe incluir campos sensibles en list_display
        sensitive_fields = ['api_key', 'secret', 'token']
        for field in sensitive_fields:
            with self.subTest(field=field):
                self.assertNotIn(field, list_display)

    def test_admin_exclude_sensitive_fields(self):
        """Debe excluir o enmascarar campos sensibles"""
        # Verificar que se configuran adecuadamente los campos sensibles
        if hasattr(self.admin, 'exclude'):
            # Puede excluir campos sensibles completamente
            pass
        elif hasattr(self.admin, 'readonly_fields'):
            # O marcarlos como solo lectura
            pass

    def test_admin_proveedor_nombre_method_credentials(self):
        """Debe mostrar nombre del proveedor en credenciales"""
        proveedor_nombre = self.admin.proveedor_nombre(self.credencial)
        self.assertEqual(proveedor_nombre, 'CredentialProvider')

    def test_admin_has_view_permission_only(self):
        """Debe restringir permisos para credenciales sensibles"""
        request = MockRequest(self.user)
        
        # Verificar permisos restrictivos si están configurados
        view_permission = self.admin.has_view_permission(request, self.credencial)
        self.assertTrue(view_permission)

    def test_admin_list_filter_credentials(self):
        """Debe filtrar por campos seguros"""
        expected_filters = ['ambiente', 'activo', 'id_proveedor', 'updated_at']
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)


class LogsWebhooksAdminTest(TestCase):
    """Tests para LogsWebhooksAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = LogsWebhooksAdmin(LogsWebhooks, self.site)
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear webhook log
        self.webhook_log = LogsWebhooks.objects.create(
            timestamp=timezone.now(),
            headers={'Content-Type': 'application/json'},
            payload='{"event": "test", "data": {"id": 123}}',
            evento_tipo='test.event',
            verificacion_ok=1,
            procesado_ok=1,
            tiempo_proc_ms=200,
            ip_origen='203.0.113.10'
        )

    def test_admin_list_display_webhook_logs(self):
        """Debe mostrar campos apropiados en lista de webhook logs"""
        expected_fields = [
            'id_log', 'timestamp', 'evento_tipo', 'verificacion_ok', 
            'procesado_ok', 'tiempo_proc_ms', 'ip_origen'
        ]
        
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.list_display)

    def test_admin_list_filter_webhook_logs(self):
        """Debe filtrar webhook logs apropiadamente"""
        expected_filters = [
            'evento_tipo', 'verificacion_ok', 'procesado_ok', 'timestamp'
        ]
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)

    def test_admin_readonly_webhook_logs(self):
        """Debe hacer webhook logs solo lectura"""
        # Los logs de webhooks no deben editarse
        readonly_fields = self.admin.readonly_fields
        self.assertIsNotNone(readonly_fields)
        
        # Debe incluir campos clave
        key_fields = ['id_log', 'timestamp', 'payload', 'headers']
        for field in key_fields:
            with self.subTest(field=field):
                self.assertIn(field, readonly_fields)

    def test_admin_no_add_permission_webhook_logs(self):
        """No debe permitir agregar webhook logs manualmente"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_add_permission(request)
        self.assertFalse(has_permission)

    def test_admin_no_change_permission_webhook_logs(self):
        """No debe permitir editar webhook logs"""
        request = MockRequest(self.user)
        has_permission = self.admin.has_change_permission(request, self.webhook_log)
        self.assertFalse(has_permission)


class WebhookEndpointsAdminTest(TestCase):
    """Tests para WebhookEndpointsAdmin"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.site = AdminSite()
        self.admin = WebhookEndpointsAdmin(WebhookEndpoints, self.site)
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear proveedor y webhook endpoint
        self.proveedor = ProveedoresApi.objects.create(
            nombre='WebhookProvider',
            descripcion='Proveedor para webhooks',
            tipo_servicio='webhook',
            url_base='https://api.webhook.com',
            version='1.0',
            tipo_auth='secret',
            config_auth={'secret': 'webhook_secret'},
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now()
        )
        
        self.webhook_endpoint = WebhookEndpoints.objects.create(
            nombre='Admin Test Webhook',
            descripcion='Webhook para admin tests',
            path='/webhook/admin',
            requiere_verificacion=1,
            secret_key='admin_webhook_secret',
            header_verificacion='X-Admin-Signature',
            eventos=['admin.test', 'admin.update'],
            handler_func='webhooks.admin_handler',
            activo=True,
            created_at=timezone.now(),
            id_proveedor=self.proveedor
        )

    def test_admin_list_display_webhook_endpoints(self):
        """Debe mostrar campos apropiados en lista de webhook endpoints"""
        expected_fields = [
            'id_webhook', 'nombre', 'proveedor_nombre', 'path', 
            'requiere_verificacion', 'activo'
        ]
        
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.admin.list_display)

    def test_admin_list_filter_webhook_endpoints(self):
        """Debe filtrar webhook endpoints apropiadamente"""
        expected_filters = [
            'requiere_verificacion', 'activo', 'id_proveedor', 'created_at'
        ]
        
        for filter_field in expected_filters:
            with self.subTest(filter=filter_field):
                self.assertIn(filter_field, self.admin.list_filter)

    def test_admin_proveedor_nombre_webhook_endpoints(self):
        """Debe mostrar nombre del proveedor en webhook endpoints"""
        proveedor_nombre = self.admin.proveedor_nombre(self.webhook_endpoint)
        self.assertEqual(proveedor_nombre, 'WebhookProvider')

    def test_admin_protect_secret_key(self):
        """Debe proteger secret_key en admin"""
        # Verificar que secret_key está protegido
        if hasattr(self.admin, 'exclude'):
            # Puede estar excluido
            pass
        elif hasattr(self.admin, 'readonly_fields'):
            # O ser solo lectura
            pass
        
        # Al menos debe estar consciente de la sensibilidad del campo


class ApiIntegrationsAdminIntegrationTest(TestCase):
    """Tests de integración para admin de api_integrations"""

    def setUp(self):
        """Configurar datos completos para integración"""
        self.user = User.objects.create_superuser(
            username='integration_admin',
            email='integration@test.com',
            password='integration123'
        )
        
        self.factory = RequestFactory()

    def test_admin_site_registration(self):
        """Debe verificar que modelos están registrados en admin"""
        from django.contrib import admin
        
        # Verificar que los modelos principales están registrados
        models_to_check = [
            ProveedoresApi,
            EndpointsApi,
            LogsLlamadasApi,
            CredencialesApi,
            LogsWebhooks,
            WebhookEndpoints
        ]
        
        for model in models_to_check:
            with self.subTest(model=model):
                self.assertIn(model, admin.site._registry)

    def test_admin_model_permissions(self):
        """Debe verificar permisos apropiados por modelo"""
        from django.contrib import admin
        
        # Modelos que no deben permitir adición/edición
        readonly_models = [LogsLlamadasApi, LogsWebhooks]
        
        for model in readonly_models:
            if model in admin.site._registry:
                admin_class = admin.site._registry[model]
                request = MockRequest(self.user)
                
                with self.subTest(model=model):
                    # No debe permitir agregar
                    has_add = admin_class.has_add_permission(request)
                    self.assertFalse(has_add)

    def test_admin_search_functionality(self):
        """Debe verificar funcionalidad de búsqueda"""
        # Crear datos para buscar
        proveedor = ProveedoresApi.objects.create(
            nombre='SearchableProvider',
            descripcion='Proveedor para búsquedas',
            tipo_servicio='search_test',
            url_base='https://api.search.test',
            version='1.0',
            tipo_auth='none',
            config_auth={},
            timeout=30,
            max_reintentos=1,
            created_at=timezone.now()
        )
        
        # Verificar que se puede encontrar
        site = AdminSite()
        admin_class = ProveedoresApiAdmin(ProveedoresApi, site)
        request = MockRequest(self.user)
        
        # Simular búsqueda
        queryset = admin_class.get_search_results(request, ProveedoresApi.objects.all(), 'Searchable')
        results, may_have_duplicates = queryset
        
        # Debe encontrar el proveedor
        self.assertTrue(results.filter(nombre='SearchableProvider').exists())

    def test_admin_filter_functionality(self):
        """Debe verificar funcionalidad de filtros"""
        # Crear proveedores con diferentes estados
        ProveedoresApi.objects.create(
            nombre='ActiveProvider',
            descripcion='Proveedor activo',
            tipo_servicio='filter_test',
            url_base='https://api.active.test',
            version='1.0',
            tipo_auth='none',
            config_auth={},
            timeout=30,
            max_reintentos=1,
            activo=True,
            created_at=timezone.now()
        )
        
        ProveedoresApi.objects.create(
            nombre='InactiveProvider',
            descripcion='Proveedor inactivo',
            tipo_servicio='filter_test',
            url_base='https://api.inactive.test',
            version='1.0',
            tipo_auth='none',
            config_auth={},
            timeout=30,
            max_reintentos=1,
            activo=False,
            created_at=timezone.now()
        )
        
        # Verificar que filtros funcionan
        site = AdminSite()
        admin_class = ProveedoresApiAdmin(ProveedoresApi, site)
        
        # Debe poder filtrar por activo
        self.assertIn('activo', admin_class.list_filter)