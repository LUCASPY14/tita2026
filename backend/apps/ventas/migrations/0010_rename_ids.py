from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0009_alter_aplicacionpago_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='venta',
            old_name='id',
            new_name='id_venta',
        ),
        migrations.RenameField(
            model_name='historicalventa',
            old_name='id',
            new_name='id_venta',
        ),
        migrations.RenameField(
            model_name='detalleventa',
            old_name='id',
            new_name='id_detalle_venta',
        ),
        migrations.RenameField(
            model_name='pagoventa',
            old_name='id',
            new_name='id_pago_venta',
        ),
        migrations.RenameField(
            model_name='aplicacionpago',
            old_name='id',
            new_name='id_aplicacion_pago',
        ),
        migrations.RenameField(
            model_name='notacredito',
            old_name='id',
            new_name='id_nota_credito',
        ),
        migrations.RenameField(
            model_name='detallenotacredito',
            old_name='id',
            new_name='id_detalle_nc',
        ),
        migrations.RenameField(
            model_name='condicionventa',
            old_name='id',
            new_name='id_condicion_venta',
        ),
    ]
