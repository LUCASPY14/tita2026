import os
from django.apps import AppConfig


class ContabilidadConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contabilidad"
    verbose_name = "Contabilidad"
