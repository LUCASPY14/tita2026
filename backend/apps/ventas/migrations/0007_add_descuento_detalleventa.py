# v1.0 Mejora 9: campo descuento en DetalleVenta.
# subtotal = precio_unitario × cantidad − descuento (neto con descuento ya aplicado).
# Valor 0 por defecto mantiene compatibilidad con todas las ventas existentes.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0006_sql_indexes_ventas"),
    ]

    operations = [
        migrations.AddField(
            model_name="detalleventa",
            name="descuento",
            field=models.DecimalField(
                max_digits=12,
                decimal_places=0,
                default=0,
                help_text="Descuento en Guaraníes. subtotal = precio_unitario×cantidad − descuento",
            ),
        ),
        migrations.AddConstraint(
            model_name="detalleventa",
            constraint=models.CheckConstraint(
                condition=models.Q(descuento__gte=0),
                name="chk_detalleventa_descuento_no_negativo",
            ),
        ),
    ]
