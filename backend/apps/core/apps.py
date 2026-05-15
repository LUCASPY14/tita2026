import os

from django.apps import AppConfig


class CoreConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core - Funcionalidades Base"
