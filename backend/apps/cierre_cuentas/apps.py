import os

from django.apps import AppConfig


class CierreCuentasConfig(AppConfig):
    path = os.path.dirname(os.path.abspath(__file__))
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cierre_cuentas"
    verbose_name = "Cierre de cuentas de egresados"
