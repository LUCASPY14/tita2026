"""
Limpia duplicados de MedioPago cargados manualmente desde Configuración
que nunca se usaron en ninguna venta:

- "Transferencia Bancaria" duplica a "Transferencia" (0 ventas, se desactiva
  la Bancaria y queda "Transferencia" como la única activa).
- "POS (débito/crédito)" se desactiva a favor de separar el cobro por POS en
  "POS Bancario crédito" y "POS Bancario debito" (conciliación bancaria por
  separado). Las 110 ventas históricas que ya usaron la opción combinada
  mantienen su referencia intacta — no se reclasifican retroactivamente
  porque no hay forma de saber si cada una fue débito o crédito.
"""

from django.db import migrations


def desactivar_duplicados(apps, schema_editor):
    MedioPago = apps.get_model("core", "MedioPago")
    MedioPago.objects.filter(descripcion="Transferencia Bancaria").update(activo=False)
    MedioPago.objects.filter(descripcion="POS (débito/crédito)").update(activo=False)


def reactivar_duplicados(apps, schema_editor):
    MedioPago = apps.get_model("core", "MedioPago")
    MedioPago.objects.filter(descripcion="Transferencia Bancaria").update(activo=True)
    MedioPago.objects.filter(descripcion="POS (débito/crédito)").update(activo=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_tarjetas_guardadas_bancard"),
    ]

    operations = [
        migrations.RunPython(desactivar_duplicados, reactivar_duplicados),
    ]
