from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core - Funcionalidades Base'

    def ready(self):
        """Importar signals cuando la aplicación esté lista"""
        import apps.core.signals  # noqa
