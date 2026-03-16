import os
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.usuarios"
    verbose_name = "Usuarios"

    def ready(self):
        """
        Código que se ejecuta cuando la app está lista.
        Importa las signals para registrarlas.
        """
        try:
            import apps.usuarios.signals  # noqa
        except ImportError:  # pragma: no cover
            pass
