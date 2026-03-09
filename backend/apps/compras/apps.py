import os
from django.apps import AppConfig


class ComprasConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compras"
    verbose_name = "Compras y Proveedores"

    def ready(self):
        """Importar signals cuando la aplicación esté lista"""
        import apps.compras.signals  # noqa
