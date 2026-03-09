import os
from django.apps import AppConfig


class AlmuerzosConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.almuerzos"
    verbose_name = "Almuerzos Escolares"
