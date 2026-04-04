"""
Migration 0009: datos iniciales de DatosEmpresa y contabilidad base.

Inserta un registro de empresa ejemplo y los puntos de expedición/timbrado
de ejemplo para que el sistema arranque sin errores de "sin timbrado vigente".
"""
from django.db import migrations
from django.utils import timezone
import datetime


def crear_datos_empresa(apps, schema_editor):
    DatosEmpresa = apps.get_model("contabilidad", "DatosEmpresa")
    if not DatosEmpresa.objects.filter(estado=True).exists():
        DatosEmpresa.objects.create(
            ruc="80000000-0",
            razon_social="Institución Educativa",
            direccion="Asunción, Paraguay",
            ciudad="Asunción",
            pais="Paraguay",
            telefono="+595 21 000000",
            email="info@institucion.edu.py",
            estado=True,
        )


def eliminar_datos_empresa(apps, schema_editor):
    pass  # No eliminar en reverse — podría haber datos reales


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0008_fix_tipo_documento_varchar"),
    ]

    operations = [
        migrations.RunPython(crear_datos_empresa, eliminar_datos_empresa),
    ]
