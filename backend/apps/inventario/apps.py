import os

from django.apps import AppConfig


class InventarioConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventario"
    verbose_name = "Gestión de Inventario"

    def ready(self):
        """Importar signals cuando la aplicación esté lista"""
        import apps.inventario.signals  # noqa
