"""
Desactiva "Tarjeta RFID" como Medio de Pago: es solo una etiqueta (no
descuenta saldo de ninguna tarjeta, a diferencia del modo "Prepago" real)
y generaba confusión con el flujo genuino de pago con tarjeta. 0 ventas
la usaron nunca.
"""

from django.db import migrations


def desactivar(apps, schema_editor):
    MedioPago = apps.get_model("core", "MedioPago")
    MedioPago.objects.filter(descripcion="Tarjeta RFID").update(activo=False)


def reactivar(apps, schema_editor):
    MedioPago = apps.get_model("core", "MedioPago")
    MedioPago.objects.filter(descripcion="Tarjeta RFID").update(activo=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_desactivar_medios_pago_duplicados"),
    ]

    operations = [
        migrations.RunPython(desactivar, reactivar),
    ]
