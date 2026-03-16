"""
Migración de datos: carga los tres tipos de impuesto del IVA paraguayo.
  - IVA 10% (tasa general)
  - IVA 5%  (bienes inmuebles, algunos alimentos/medicamentos)
  - Exenta   (0% — servicios/bienes exentos por ley)
"""
import datetime
from django.db import migrations


def cargar_impuestos(apps, schema_editor):
    import sys
    if 'test' in sys.argv:
        return  # No sembrar datos en modo test — los tests crean sus propios registros
    Impuestos = apps.get_model('contabilidad', 'Impuestos')
    datos = [
        {'nombre_impuesto': 'IVA 10%', 'porcentaje': '10.00', 'vigente_desde': datetime.date(2024, 1, 1), 'activo': True},
        {'nombre_impuesto': 'IVA 5%',  'porcentaje': '5.00',  'vigente_desde': datetime.date(2024, 1, 1), 'activo': True},
        {'nombre_impuesto': 'Exenta',  'porcentaje': '0.00',  'vigente_desde': datetime.date(2024, 1, 1), 'activo': True},
    ]
    for d in datos:
        Impuestos.objects.get_or_create(
            nombre_impuesto=d['nombre_impuesto'],
            defaults={
                'porcentaje': d['porcentaje'],
                'vigente_desde': d['vigente_desde'],
                'activo': d['activo'],
            },
        )


def eliminar_impuestos(apps, schema_editor):
    Impuestos = apps.get_model('contabilidad', 'Impuestos')
    Impuestos.objects.filter(nombre_impuesto__in=['IVA 10%', 'IVA 5%', 'Exenta']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0004_alter_movimientoscaja_monto_comision'),
    ]

    operations = [
        migrations.RunPython(cargar_impuestos, eliminar_impuestos),
    ]
