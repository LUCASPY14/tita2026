import os

from django.apps import AppConfig


class ApiIntegrationsConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_integrations"
    verbose_name = "Integraciones API"
