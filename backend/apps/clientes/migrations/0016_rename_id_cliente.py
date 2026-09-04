from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0015_cuentacorrientecliente_origen_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cliente',
            old_name='id',
            new_name='id_cliente',
        ),
        migrations.RenameField(
            model_name='historicalcliente',
            old_name='id',
            new_name='id_cliente',
        ),
    ]
