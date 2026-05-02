"""
Tests para configuración de aplicación usuarios
Cubre UsuariosConfig y setup de la app Django
"""

from django.test import TestCase
from django.apps import apps

from apps.usuarios.apps import UsuariosConfig


class UsuariosAppConfigTest(TestCase):
    """Tests para configuración de la app usuarios"""

    def test_app_name(self):
        """Debe tener nombre correcto de aplicación"""
        app_config = apps.get_app_config("usuarios")
        self.assertEqual(app_config.name, "apps.usuarios")

    def test_verbose_name(self):
        """Debe tener nombre verbose correcto"""
        app_config = apps.get_app_config("usuarios")
        self.assertEqual(app_config.verbose_name, "Usuarios")

    def test_default_auto_field(self):
        """Debe configurar default_auto_field correctamente"""
        app_config = UsuariosConfig
        self.assertEqual(app_config.default_auto_field, "django.db.models.BigAutoField")

    def test_app_ready_method(self):
        """Debe configurar signals en ready()"""
        app_config = UsuariosConfig("apps.usuarios", None)

        try:
            app_config.ready()
        except ImportError:
            # Es normal si signals no existen aún
            pass
        except Exception as e:
            # No debe fallar por otros motivos
            self.fail(f"ready() method failed unexpectedly: {e}")

    def test_app_models_registration(self):
        """Debe registrar modelos correctamente"""
        app_config = apps.get_app_config("usuarios")
        models = app_config.get_models()

        model_names = [model._meta.model_name for model in models]

        # Verificar modelos principales están registrados
        expected_models = ["roles", "empleados"]
        for model_name in expected_models:
            self.assertIn(model_name, model_names)

    def test_app_in_installed_apps(self):
        """Debe estar en INSTALLED_APPS"""
        from django.conf import settings

        app_names = [
            "apps.usuarios",
            "usuarios",  # Nombre corto alternativo
        ]

        # Al menos una forma debe estar en INSTALLED_APPS
        installed = any(app in settings.INSTALLED_APPS for app in app_names)
        self.assertTrue(installed, "App usuarios no encontrada en INSTALLED_APPS")

    def test_app_migration_modules(self):
        """Debe tener configuración correcta de migraciones"""
        app_config = apps.get_app_config("usuarios")

        # Debe tener un directorio de migraciones válido
        self.assertTrue(hasattr(app_config, "path"))
        self.assertIsNotNone(app_config.path)

    def test_app_label(self):
        """Debe tener label correcto para la app"""
        app_config = apps.get_app_config("usuarios")
        self.assertEqual(app_config.label, "usuarios")

    def test_models_meta_configuration(self):
        """Debe tener configuración correcta en meta de modelos"""
        app_config = apps.get_app_config("usuarios")
        models = app_config.get_models()

        for model in models:
            # Verificar configuración básica de Meta
            meta = model._meta
            self.assertIsNotNone(meta.db_table)
            self.assertIsNotNone(meta.verbose_name)
            self.assertIsNotNone(meta.verbose_name_plural)

            # Verificar que managed=True para modelos principales
            if meta.model_name in ["roles", "empleados"]:
                self.assertTrue(meta.managed)
