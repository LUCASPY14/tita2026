import os

from django.apps import AppConfig


class ClientesConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.clientes"
    verbose_name = "Clientes"
