from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    verbose_name = 'Gestión de Usuarios'
    
    def ready(self):
        """
        Código que se ejecuta cuando la app está lista.
        Importa las signals para registrarlas.
        """
        try:
            import apps.usuarios.signals  # noqa
        except ImportError:
            pass
    verbose_name = 'Usuarios y Autenticación'
