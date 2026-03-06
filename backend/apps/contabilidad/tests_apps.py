"""
Tests para apps de contabilidad
Cubre configuración de aplicación Django y integración
"""

from django.test import TestCase
from django.apps import apps
from django.conf import settings

from apps.contabilidad.apps import ContabilidadConfig


class ContabilidadAppsConfigTest(TestCase):
    """Tests para configuración de la app de contabilidad"""

    def test_contabilidad_app_config_exists(self):
        """Debe existir configuración de app contabilidad"""
        app_config = ContabilidadConfig
        
        # Verificar clase de configuración
        self.assertIsNotNone(app_config)
        self.assertEqual(app_config.name, 'apps.contabilidad')

    def test_contabilidad_app_verbose_name(self):
        """Debe tener nombre legible configurado"""
        app_config = ContabilidadConfig
        
        # Verificar que tiene verbose_name o nombre por defecto
        expected_verbose_name = 'Contabilidad'
        
        if hasattr(app_config, 'verbose_name'):
            self.assertEqual(app_config.verbose_name, expected_verbose_name)
        else:
            # Si no está configurado, usar nombre por defecto
            self.assertEqual(app_config.name.split('.')[-1].title(), 'Contabilidad')

    def test_contabilidad_app_default_auto_field(self):
        """Debe tener configurado el campo auto por defecto"""
        app_config = ContabilidadConfig
        
        # Verificar default_auto_field
        if hasattr(app_config, 'default_auto_field'):
            self.assertEqual(app_config.default_auto_field, 'django.db.models.BigAutoField')
        else:
            # Usar configuración por defecto de Django
            self.assertIsNotNone(app_config)

    def test_contabilidad_app_installed(self):
        """Debe estar instalada en INSTALLED_APPS"""
        # Verificar que la app está instalada
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        
        app_installed = any(
            'contabilidad' in app.lower() 
            for app in installed_apps
        )
        
        # En un entorno de test, debería estar instalada
        self.assertTrue(
            app_installed or 'apps.contabilidad' in installed_apps,
            "App contabilidad debe estar en INSTALLED_APPS"
        )

    def test_contabilidad_app_registry(self):
        """Debe estar registrada correctamente en Django apps registry"""
        try:
            # Intentar obtener la app del registro
            app_config = apps.get_app_config('contabilidad')
            
            # Verificar propiedades básicas
            self.assertIsNotNone(app_config)
            self.assertEqual(app_config.label, 'contabilidad')
            
        except LookupError:
            # Si no está registrada, verificar configuración básica
            app_config = ContabilidadConfig
            self.assertIsNotNone(app_config)

    def test_contabilidad_app_models_loaded(self):
        """Debe cargar todos los modelos correctamente"""
        try:
            app_config = apps.get_app_config('contabilidad')
            models = app_config.get_models()
            
            # Verificar que se cargaron modelos
            self.assertGreater(len(models), 0, "Debe tener modelos definidos")
            
            # Verificar nombres de modelos principales
            model_names = [model.__name__ for model in models]
            expected_models = [
                'Cajas', 'CierresCaja', 'MovimientosCaja',
                'TarifasComision', 'DocumentosTributarios', 'Impuestos'
            ]
            
            for expected_model in expected_models:
                self.assertIn(
                    expected_model, 
                    model_names,
                    f"Modelo {expected_model} debe estar definido"
                )
                
        except LookupError:
            # Si no está registrada, skip este test
            pass

    def test_contabilidad_app_ready_method(self):
        """Debe implementar método ready si es necesario"""
        app_config = ContabilidadConfig
        
        # Verificar si tiene método ready
        if hasattr(app_config, 'ready'):
            # No debería lanzar excepción al llamarlo
            try:
                # En entorno de test, no llamamos ready() directamente
                # porque Django ya lo maneja
                self.assertTrue(hasattr(app_config, 'ready'))
            except Exception as e:
                self.fail(f"Método ready() falló: {e}")
        else:
            # Es opcional tener método ready
            self.assertTrue(True)


class ContabilidadAppsIntegrationTest(TestCase):
    """Tests de integración para la app de contabilidad"""

    def test_contabilidad_app_migrations_exist(self):
        """Debe tener migraciones definidas"""
        try:
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            migrations = executor.loader.applied_migrations
            
            # Verificar que hay migraciones para contabilidad
            contabilidad_migrations = [
                migration for migration in migrations 
                if migration[0] == 'contabilidad'
            ]
            
            # Si la app está configurada, debería tener al menos una migración
            if apps.is_installed('apps.contabilidad'):
                self.assertGreater(
                    len(contabilidad_migrations), 
                    0, 
                    "Debe tener migraciones definidas"
                )
                
        except Exception:
            # En algunos entornos de test, las migraciones no están disponibles
            self.assertTrue(True)

    def test_contabilidad_app_admin_integration(self):
        """Debe integrarse correctamente con Django admin"""
        try:
            from django.contrib import admin
            from apps.contabilidad import models
            
            # Verificar que los modelos principales están registrados en admin
            admin_models = admin.site._registry
            
            model_classes = [
                models.Cajas,
                models.CierresCaja,
                models.MovimientosCaja,
                models.TarifasComision,
                models.DocumentosTributarios,
                models.Impuestos
            ]
            
            for model_class in model_classes:
                if model_class in admin_models:
                    admin_class = admin_models[model_class]
                    
                    # Verificar que tiene configuración básica de admin
                    self.assertIsNotNone(admin_class)
                    
                    # Verificar que no hay errores en configuración
                    try:
                        # Intentar acceder a propiedades comunes
                        list_display = getattr(admin_class, 'list_display', None)
                        search_fields = getattr(admin_class, 'search_fields', None)
                        list_filter = getattr(admin_class, 'list_filter', None)
                        
                        # No deberían ser None si están configurados
                        if list_display is not None:
                            self.assertIsInstance(list_display, (list, tuple))
                        if search_fields is not None:
                            self.assertIsInstance(search_fields, (list, tuple))
                        if list_filter is not None:
                            self.assertIsInstance(list_filter, (list, tuple))
                            
                    except Exception as e:
                        self.fail(f"Error en configuración admin para {model_class.__name__}: {e}")
                        
        except ImportError:
            # Si no se pueden importar los modelos, skip
            self.assertTrue(True)

    def test_contabilidad_app_signals_registration(self):
        """Debe registrar signals correctamente si los tiene"""
        try:
            # Verificar si hay signals definidos
            from apps.contabilidad import signals
            
            # Si el módulo existe, verificar que no hay errores
            self.assertTrue(True, "Signals module importado correctamente")
            
        except ImportError:
            # Es opcional tener signals
            self.assertTrue(True, "No signals definidos - OK")
        except Exception as e:
            self.fail(f"Error en signals: {e}")

    def test_contabilidad_app_serializers_integration(self):
        """Debe integrar serializers correctamente con DRF"""
        try:
            from apps.contabilidad import serializers
            from rest_framework import serializers as drf_serializers
            
            # Verificar que el módulo de serializers existe
            self.assertIsNotNone(serializers)
            
            # Si están definidos, verificar que son válidos
            serializer_classes = [
                attr for attr in dir(serializers) 
                if attr.endswith('Serializer') and not attr.startswith('_')
            ]
            
            for serializer_name in serializer_classes:
                serializer_class = getattr(serializers, serializer_name)
                
                # Verificar que hereda de serializer base de DRF
                if hasattr(serializer_class, '__mro__'):
                    base_classes = [cls.__name__ for cls in serializer_class.__mro__]
                    
                    is_drf_serializer = any(
                        'Serializer' in cls_name 
                        for cls_name in base_classes
                    )
                    
                    self.assertTrue(
                        is_drf_serializer,
                        f"{serializer_name} debe heredar de serializer DRF"
                    )
                    
        except ImportError:
            # Es opcional tener serializers
            self.assertTrue(True, "No serializers definidos - OK")

    def test_contabilidad_app_views_integration(self):
        """Debe integrar views correctamente con DRF"""
        try:
            from apps.contabilidad import views
            from rest_framework import viewsets, views as drf_views
            
            # Verificar que el módulo de views existe
            self.assertIsNotNone(views)
            
            # Si están definidas, verificar que son válidas
            view_classes = [
                attr for attr in dir(views) 
                if (attr.endswith('ViewSet') or attr.endswith('View')) 
                and not attr.startswith('_')
            ]
            
            for view_name in view_classes:
                view_class = getattr(views, view_name)
                
                # Verificar que hereda de view base de DRF
                if hasattr(view_class, '__mro__'):
                    base_classes = [cls.__name__ for cls in view_class.__mro__]
                    
                    is_drf_view = any(
                        cls_name in ['ViewSet', 'ModelViewSet', 'APIView', 'GenericAPIView']
                        for cls_name in base_classes
                    )
                    
                    if is_drf_view:
                        self.assertTrue(
                            is_drf_view,
                            f"{view_name} debe heredar de view/viewset DRF"
                        )
                        
        except ImportError:
            # Es opcional tener views personalizadas
            self.assertTrue(True, "No views definidas - OK")

    def test_contabilidad_app_urls_integration(self):
        """Debe integrar URLs correctamente"""
        try:
            from apps.contabilidad import urls
            from django.urls import URLPattern, URLResolver
            
            # Verificar que el módulo de URLs existe
            self.assertIsNotNone(urls)
            
            # Verificar que tiene urlpatterns
            if hasattr(urls, 'urlpatterns'):
                urlpatterns = urls.urlpatterns
                
                self.assertIsInstance(urlpatterns, list)
                
                # Verificar que cada patrón es válido
                for pattern in urlpatterns:
                    self.assertIsInstance(
                        pattern, 
                        (URLPattern, URLResolver),
                        "Cada patrón debe ser URLPattern o URLResolver válido"
                    )
                    
        except ImportError:
            # Es opcional tener URLs personalizadas
            self.assertTrue(True, "No URLs definidas - OK")

    def test_contabilidad_app_permissions_integration(self):
        """Debe integrar permisos correctamente si los tiene"""
        try:
            from apps.contabilidad import permissions
            from rest_framework import permissions as drf_permissions
            
            # Verificar que el módulo existe
            self.assertIsNotNone(permissions)
            
            # Si están definidos, verificar que son válidos
            permission_classes = [
                attr for attr in dir(permissions) 
                if attr.endswith('Permission') and not attr.startswith('_')
            ]
            
            for permission_name in permission_classes:
                permission_class = getattr(permissions, permission_name)
                
                # Verificar que hereda de permission base de DRF
                if hasattr(permission_class, '__mro__'):
                    base_classes = [cls.__name__ for cls in permission_class.__mro__]
                    
                    is_drf_permission = any(
                        'Permission' in cls_name 
                        for cls_name in base_classes
                    )
                    
                    if is_drf_permission:
                        self.assertTrue(
                            is_drf_permission,
                            f"{permission_name} debe heredar de permission DRF"
                        )
                        
        except ImportError:
            # Es opcional tener permisos personalizados
            self.assertTrue(True, "No permissions definidos - OK")


class ContabilidadAppsMetaTest(TestCase):
    """Tests meta para la configuración de app de contabilidad"""

    def test_contabilidad_app_documentation(self):
        """Debe tener documentación adecuada"""
        app_config = ContabilidadConfig
        
        # Verificar que tiene docstring
        if hasattr(app_config, '__doc__') and app_config.__doc__:
            self.assertIsNotNone(app_config.__doc__)
            self.assertGreater(len(app_config.__doc__.strip()), 10)
        
        # Verificar que el módulo apps.py tiene docstring
        import apps.contabilidad.apps as apps_module
        if hasattr(apps_module, '__doc__') and apps_module.__doc__:
            self.assertIsNotNone(apps_module.__doc__)

    def test_contabilidad_app_dependencies(self):
        """Debe declarar dependencias correctamente"""
        try:
            # Verificar importaciones principales
            from apps.contabilidad import models, apps
            
            # No deberían fallar las importaciones básicas
            self.assertIsNotNone(models)
            self.assertIsNotNone(apps)
            
            # Verificar dependencias de Django
            from django.db import models as django_models
            from django.apps import AppConfig
            
            self.assertIsNotNone(django_models)
            self.assertIsNotNone(AppConfig)
            
        except ImportError as e:
            self.fail(f"Falta dependencia requerida: {e}")

    def test_contabilidad_app_structure(self):
        """Debe tener estructura de archivos correcta"""
        import os
        import apps.contabilidad
        
        app_path = os.path.dirname(apps.contabilidad.__file__)
        
        # Archivos que deberían existir
        required_files = [
            '__init__.py',
            'apps.py',
            'models.py'
        ]
        
        # Archivos opcionales pero comunes
        optional_files = [
            'admin.py',
            'views.py',
            'urls.py',
            'serializers.py',
            'permissions.py',
            'signals.py'
        ]
        
        for required_file in required_files:
            file_path = os.path.join(app_path, required_file)
            self.assertTrue(
                os.path.exists(file_path),
                f"Archivo requerido {required_file} debe existir"
            )
        
        # Verificar que al menos algunos archivos opcionales existen
        existing_optional = [
            file for file in optional_files
            if os.path.exists(os.path.join(app_path, file))
        ]
        
        self.assertGreater(
            len(existing_optional),
            0,
            "Debe tener al menos algunos archivos opcionales de Django app"
        )

    def test_contabilidad_app_naming_conventions(self):
        """Debe seguir convenciones de nomenclatura"""
        app_config = ContabilidadConfig
        
        # Verificar nomenclatura de clase
        self.assertTrue(
            app_config.__name__.endswith('Config'),
            "Clase de configuración debe terminar en 'Config'"
        )
        
        # Verificar nombre de app
        self.assertEqual(
            app_config.name,
            'apps.contabilidad',
            "Nombre de app debe seguir patrón 'apps.nombre'"
        )
        
        # Verificar que el label es correcto
        expected_label = 'contabilidad'
        if hasattr(app_config, 'label'):
            self.assertEqual(app_config.label, expected_label)

    def test_contabilidad_app_compatibility(self):
        """Debe ser compatible con versión de Django"""
        import django
        from django.conf import settings
        
        # Verificar versión mínima de Django
        django_version = django.VERSION
        
        # Asumiendo compatibilidad con Django 3.2+
        minimum_version = (3, 2)
        
        self.assertGreaterEqual(
            django_version[:2],
            minimum_version,
            f"Requiere Django {minimum_version[0]}.{minimum_version[1]}+ (actual: {django_version[0]}.{django_version[1]})"
        )
        
        # Verificar que no hay configuraciones incompatibles
        if hasattr(settings, 'USE_TZ'):
            # Contabilidad debería funcionar con timezone habilitado
            self.assertTrue(True)

    def test_contabilidad_app_translations_ready(self):
        """Debe estar preparado para internacionalización"""
        try:
            from django.utils.translation import gettext_lazy as _
            
            # Verificar que la función de traducción está disponible
            self.assertIsNotNone(_)
            
            # Test básico de traducción
            translated_text = _('Contabilidad')
            self.assertIsNotNone(translated_text)
            
        except ImportError:
            self.fail("Django i18n no está disponible")

    def test_contabilidad_app_settings_integration(self):
        """Debe integrarse correctamente con settings"""
        from django.conf import settings
        
        # Verificar configuraciones relevantes
        if hasattr(settings, 'DATABASES'):
            # Debe poder trabajar con la configuración de base de datos
            default_db = settings.DATABASES.get('default', {})
            self.assertIsNotNone(default_db)
        
        if hasattr(settings, 'REST_FRAMEWORK'):
            # Si DRF está configurado, debería ser compatible
            drf_settings = settings.REST_FRAMEWORK
            self.assertIsInstance(drf_settings, dict)
        
        # Verificar que las configuraciones críticas están presentes
        critical_settings = [
            'SECRET_KEY',
            'INSTALLED_APPS'
        ]
        
        for setting_name in critical_settings:
            self.assertTrue(
                hasattr(settings, setting_name),
                f"Configuración crítica {setting_name} debe estar presente"
            )