import os

from django.apps import AppConfig


class VentasConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ventas"
    verbose_name = "Ventas y Facturacion"
