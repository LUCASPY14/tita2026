from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventario'
    verbose_name = 'Gestión de Inventario'
    
    def ready(self):
        """Importar signals cuando la aplicación esté lista"""
        import apps.inventario.signals  # noqa
