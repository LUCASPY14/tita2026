import os

from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notificaciones"
    verbose_name = "Sistema de Notificaciones"
