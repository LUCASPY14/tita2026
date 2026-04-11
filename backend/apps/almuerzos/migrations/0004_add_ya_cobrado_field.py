# Generated migration for adding ya_cobrado field and implementing double-lunch logic
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almuerzos', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrosconsumoalmuerzo',
            name='ya_cobrado',
            field=models.BooleanField(
                default=True,
                help_text='Indica si este registro generó cobro de saldo. El primer registro del día cobra (True), el segundo no cobra (False)'
            ),
        ),
        # Establecer ya_cobrado=True para registros existentes (backward compatibility)
        migrations.RunSQL(
            sql="UPDATE registros_consumo_almuerzo SET ya_cobrado = 1 WHERE ya_cobrado IS NULL;",
            reverse_sql="UPDATE registros_consumo_almuerzo SET ya_cobrado = NULL;"
        ),
    ]
