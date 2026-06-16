# v1.0 Mejora 10: agrega el estado PARCIAL a Compra.EstadoEntrega.
# Flujo: PENDIENTE → PARCIAL → RECIBIDA (o directamente PENDIENTE → RECIBIDA).
# El campo es varchar en PG; AlterField actualiza las choices sin tocar los datos.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("compras", "0004_add_ordencompra"),
    ]

    operations = [
        migrations.AlterField(
            model_name="compra",
            name="estado_entrega",
            field=models.CharField(
                choices=[
                    ("PENDIENTE", "Pendiente"),
                    ("PARCIAL", "Recepción parcial"),
                    ("RECIBIDA", "Recibida"),
                ],
                default="PENDIENTE",
                help_text="Estado de recepcion de la mercaderia",
                max_length=10,
            ),
        ),
    ]
