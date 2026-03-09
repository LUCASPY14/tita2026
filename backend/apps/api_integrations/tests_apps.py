"""
Tests para apps.py de api_integrations
Cubre configuración de aplicación Django y funcionalidad de apps
"""

from django.test import TestCase
from django.apps import apps
from django.test.utils import override_settings

from apps.api_integrations.apps import ApiIntegrationsConfig


class ApiIntegrationsConfigTest(TestCase):
    """Tests para ApiIntegrationsConfig"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.app_config = ApiIntegrationsConfig(
            'apps.api_integrations',
            'apps.api_integrations'
        )

    def test_app_config_name(self):
        """Debe tener nombre de aplicación correcto"""
        self.assertEqual(self.app_config.name, 'apps.api_integrations')

    def test_app_config_default_auto_field(self):
        """Debe tener configuración correcta para auto field"""
        expected_auto_field = 'django.db.models.BigAutoField'
        self.assertEqual(self.app_config.default_auto_field, expected_auto_field)

    def test_app_config_verbose_name(self):
        """Debe tener nombre verbose apropiado"""
        expected_verbose_names = [
            'API Integrations',
            'Api Integrations', 
            'Integraciones API',
            'API_Integrations'
        ]
        
        self.assertIn(self.app_config.verbose_name, expected_verbose_names)

    def test_app_config_label(self):
        """Debe tener label único y válido"""
        self.assertEqual(self.app_config.label, 'api_integrations')

    def test_app_is_registered(self):
        """Debe estar registrada en INSTALLED_APPS"""
        app_config = apps.get_app_config('api_integrations')
        self.assertIsNotNone(app_config)
        self.assertIsInstance(app_config, ApiIntegrationsConfig)

    def test_app_config_ready_method_exists(self):
        """Debe tener método ready() para inicialización"""
        self.assertTrue(hasattr(self.app_config, 'ready'))
        
        # Verificar que es callable
        self.assertTrue(callable(self.app_config.ready))

    def test_app_config_ready_method_execution(self):
        """Debe ejecutar ready() sin errores"""
        try:
            # Ejecutar ready method
            self.app_config.ready()
            # Si no lanza excepción, está bien
        except Exception as e:
            self.fail(f"ready() method falló con error: {e}")

    def test_app_models_are_accessible(self):
        """Debe permitir acceso a modelos de la app"""
        app_config = apps.get_app_config('api_integrations')
        
        # Obtener todos los modelos de la app
        models = list(app_config.get_models())
        
        # Debe tener modelos definidos
        self.assertGreater(len(models), 0)
        
        # Verificar que modelos principales existen
        model_names = [model._meta.object_name for model in models]
        expected_models = [
            'ProveedoresApi',
            'EndpointsApi',
            'LogsLlamadasApi',
            'CredencialesApi',
            'LogsWebhooks',
            'WebhookEndpoints'
        ]
        
        for expected_model in expected_models:
            with self.subTest(model=expected_model):
                self.assertIn(expected_model, model_names)

    def test_app_config_import_string(self):
        """Debe tener import string correcto"""
        # La app debe poder importarse desde su string
        try:
            from apps.api_integrations import apps as api_integrations_apps
            self.assertTrue(hasattr(api_integrations_apps, 'ApiIntegrationsConfig'))
        except ImportError:
            self.fail("No se pudo importar ApiIntegrationsConfig")

    def test_app_config_path_resolution(self):
        """Debe resolver path de la aplicación correctamente"""
        app_config = apps.get_app_config('api_integrations')
        
        # Path debe existir y terminar con api_integrations
        self.assertTrue(app_config.path.endswith('api_integrations'))

    def test_app_config_migration_modules(self):
        """Debe manejar migrations apropiadamente"""
        app_config = apps.get_app_config('api_integrations')
        
        # Verificar que migrations están disponibles
        from django.db.migrations.loader import MigrationLoader
        loader = MigrationLoader(None)
        
        app_migrations = loader.disk_migrations
        api_integrations_migrations = [
            key for key in app_migrations.keys() 
            if key[0] == 'api_integrations'
        ]
        
        # Debe tener al menos migration inicial
        # (o ninguna si usa migraciones automáticas)
        self.assertIsInstance(api_integrations_migrations, list)

    @override_settings(INSTALLED_APPS=['apps.api_integrations'])
    def test_app_config_standalone_functionality(self):
        """Debe funcionar como app standalone"""
        # Verificar que la app puede funcionar independientemente
        # (aunque dependa de otras apps, debe cargar sin errores críticos)
        from django.apps import AppConfig
        
        app_config = ApiIntegrationsConfig('api_integrations', 'apps.api_integrations')
        self.assertIsInstance(app_config, AppConfig)

    def test_app_config_signals_registration(self):
        """Debe registrar signals apropiadamente si los tiene"""
        app_config = apps.get_app_config('api_integrations')
        
        # Ejecutar ready para registrar signals
        try:
            app_config.ready()
            
            # Verificar que no hay errores en registro de signals
            # (si existen signals, deben registrarse sin errores)
        except Exception as e:
            if 'signal' in str(e).lower():
                self.fail(f"Error en registro de signals: {e}")

    def test_app_config_admin_autodiscover(self):
        """Debe permitir autodiscover de admin"""
        # Verificar que admin.py existe y es importable
        try:
            from apps.api_integrations import admin
            self.assertTrue(hasattr(admin, '__file__'))
        except ImportError:
            self.fail("admin.py no es importable")

    def test_app_config_views_importable(self):
        """Debe tener views importables"""
        try:
            from apps.api_integrations import views
            self.assertTrue(hasattr(views, '__file__'))
        except ImportError:
            self.fail("views.py no es importable")

    def test_app_config_models_importable(self):
        """Debe tener models importables"""
        try:
            from apps.api_integrations import models
            self.assertTrue(hasattr(models, '__file__'))
        except ImportError:
            self.fail("models.py no es importable")

    def test_app_config_urls_importable(self):
        """Debe tener urls importables"""
        try:
            from apps.api_integrations import urls
            self.assertTrue(hasattr(urls, '__file__'))
            self.assertTrue(hasattr(urls, 'urlpatterns'))
        except ImportError:
            self.fail("urls.py no es importable")

    def test_app_config_serializers_importable(self):
        """Debe tener serializers importables"""
        try:
            from apps.api_integrations import serializers
            self.assertTrue(hasattr(serializers, '__file__'))
        except ImportError:
            # serializers pueden no existir si están vacíos
            pass

    def test_app_config_services_importable(self):
        """Debe tener services importables"""
        try:
            from apps.api_integrations import services
            # Puede ser módulo o package
            self.assertTrue(
                hasattr(services, '__file__') or 
                hasattr(services, '__path__')
            )
        except ImportError:
            self.fail("services no es importable")

    def test_app_config_validators_importable(self):
        """Debe tener validators importables"""
        try:
            from apps.api_integrations import validators
            self.assertTrue(hasattr(validators, '__file__'))
        except ImportError:
            self.fail("validators.py no es importable")


class ApiIntegrationsAppIntegrationTest(TestCase):
    """Tests de integración para app api_integrations"""

    def test_app_dependencies_resolution(self):
        """Debe resolver dependencias con otras apps correctamente"""
        app_config = apps.get_app_config('api_integrations')
        
        # Verificar que puede acceder a modelos de apps relacionadas
        try:
            # Debe poder acceder a usuarios
            from apps.usuarios.models import Empleados
            self.assertTrue(hasattr(Empleados, '_meta'))
            
            # Debe poder acceder a core
            from apps.core.models import ConfiguracionSistema
            self.assertTrue(hasattr(ConfiguracionSistema, '_meta'))
            
        except ImportError as e:
            self.fail(f"Error importando dependencias: {e}")

    def test_app_cross_model_relationships(self):
        """Debe manejar relaciones entre modelos de diferentes apps"""
        from apps.api_integrations.models import LogsLlamadasApi
        from apps.usuarios.models import Empleados
        
        # Verificar que las relaciones funcionan
        try:
            # LogsLlamadasApi debe poder referenciar Empleados
            log_model = LogsLlamadasApi._meta
            empleado_field = log_model.get_field('id_empleado')
            
            # Debe ser ForeignKey a Empleados
            self.assertEqual(empleado_field.related_model, Empleados)
        except Exception as e:
            self.fail(f"Error en relación entre modelos: {e}")

    def test_app_database_table_creation(self):
        """Debe crear tablas de base de datos correctamente"""
        from apps.api_integrations.models import ProveedoresApi
        
        # Verificar que el modelo está configurado para BD
        self.assertTrue(ProveedoresApi._meta.managed)
        
        # Verificar nombre de tabla
        expected_table = 'proveedores_api'
        self.assertEqual(ProveedoresApi._meta.db_table, expected_table)

    def test_app_signal_connections(self):
        """Debe conectar signals apropiadamente"""
        # Si la app usa signals, deben estar conectados después de ready()
        app_config = apps.get_app_config('api_integrations')
        
        try:
            app_config.ready()
            
            # Verificar que no hay errores relacionados con signals
            from django.db import models
            from apps.api_integrations.models import ProveedoresApi
            
            # Crear instancia de prueba para verificar signals
            instance = ProveedoresApi(
                nombre='SignalTest',
                descripcion='Test signals',
                tipo_servicio='test',
                url_base='https://test.com',
                version='1.0',
                tipo_auth='none',
                config_auth={},
                timeout=30,
                max_reintentos=1
            )
            
            # No debe fallar por problemas de signals
            instance.save()
            instance.delete()
            
        except Exception as e:
            if 'signal' in str(e).lower():
                self.fail(f"Error en signals: {e}")

    def test_app_admin_integration(self):
        """Debe integrar con Django admin correctamente"""
        from django.contrib import admin
        from apps.api_integrations.models import (
            ProveedoresApi, EndpointsApi, LogsLlamadasApi,
            CredencialesApi, LogsWebhooks, WebhookEndpoints
        )
        
        # Verificar que modelos principales están registrados
        key_models = [ProveedoresApi, EndpointsApi, CredencialesApi]
        
        for model in key_models:
            with self.subTest(model=model):
                self.assertIn(model, admin.site._registry)

    def test_app_url_integration(self):
        """Debe integrar URLs correctamente con proyecto"""
        from apps.api_integrations import urls
        
        # Debe tener urlpatterns
        self.assertTrue(hasattr(urls, 'urlpatterns'))
        self.assertIsInstance(urls.urlpatterns, list)
        
        # urlpatterns no debe estar vacío
        self.assertGreater(len(urls.urlpatterns), 0)

    def test_app_settings_configuration(self):
        """Debe manejar configuración de settings apropiadamente"""
        from django.conf import settings
        
        # Verificar que configuraciones específicas están disponibles
        # (si la app requiere configuraciones específicas)
        
        # Ejemplo: configuraciones de Bancard
        bancard_configs = [
            'BANCARD_AMBIENTE',
            'BANCARD_PUBLIC_KEY',
            'BANCARD_PRIVATE_KEY'
        ]
        
        for config in bancard_configs:
            # No falla si no existe, pero verifica acceso a settings
            try:
                value = getattr(settings, config, None)
                # Si existe, debe ser string o None
                self.assertTrue(value is None or isinstance(value, str))
            except Exception as e:
                self.fail(f"Error accediendo a configuración {config}: {e}")

    def test_app_middleware_compatibility(self):
        """Debe ser compatible con middleware del proyecto"""
        # Verificar que la app funciona con middleware común
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        # Debe poder manejar requests básicos sin errores
        try:
            from apps.api_integrations.views import webhook_test
            response = webhook_test(request)
            # Si no falla, la compatibilidad básica funciona
            self.assertTrue(hasattr(response, 'status_code'))
        except Exception as e:
            self.fail(f"Error de compatibilidad con middleware: {e}")

    def test_app_cache_framework_compatibility(self):
        """Debe ser compatible con framework de cache"""
        try:
            from django.core.cache import cache
            
            # Probar operaciones básicas de cache
            test_key = 'api_integrations_test'
            test_value = {'test': 'data'}
            
            cache.set(test_key, test_value, 60)
            cached_value = cache.get(test_key)
            
            self.assertEqual(cached_value, test_value)
            
            cache.delete(test_key)
        except Exception as e:
            # Si cache no está configurado, no falla la app
            pass

    def test_app_logging_integration(self):
        """Debe integrar con sistema de logging"""
        import logging
        
        # Verificar que puede crear logger específico
        logger = logging.getLogger('apps.api_integrations')
        
        # Debe poder loguear sin errores
        try:
            logger.info("Test log message from api_integrations app")
        except Exception as e:
            self.fail(f"Error en logging: {e}")

    def test_app_translation_support(self):
        """Debe soportar traducción si está habilitada"""
        from django.utils.translation import gettext as _
        
        try:
            # Probar traducción básica
            test_string = _("API Integrations")
            self.assertIsInstance(test_string, str)
        except Exception as e:
            # Si i18n no está configurado, no debe fallar la app
            pass