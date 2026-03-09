import os
from django.apps import AppConfig


class ProductosConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.productos"
    verbose_name = "Productos"
