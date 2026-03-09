import os
from django.apps import AppConfig


class ReportesConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reportes"
    verbose_name = "Sistema de Reportes"
