from django.apps import AppConfig


class ComprasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compras"
    verbose_name = "Compras y Proveedores"

    def ready(self):
        """Importar signals cuando la aplicación esté lista"""
        import apps.compras.signals  # noqa
