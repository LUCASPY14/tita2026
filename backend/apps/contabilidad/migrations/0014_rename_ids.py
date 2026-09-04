from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0013_delete_conciliacionpago'),
    ]

    operations = [
        migrations.RenameField(
            model_name='caja',
            old_name='id',
            new_name='id_caja',
        ),
        migrations.RenameField(
            model_name='cierrecaja',
            old_name='id',
            new_name='id_cierre',
        ),
        migrations.RenameField(
            model_name='historicalcierrecaja',
            old_name='id',
            new_name='id_cierre',
        ),
        migrations.RenameField(
            model_name='movimientocaja',
            old_name='id',
            new_name='id_movimiento_caja',
        ),
        migrations.RenameField(
            model_name='factura',
            old_name='id',
            new_name='id_factura',
        ),
        migrations.RenameField(
            model_name='historicalfactura',
            old_name='id',
            new_name='id_factura',
        ),
        migrations.RenameField(
            model_name='datosempresa',
            old_name='id',
            new_name='id_datos_empresa',
        ),
    ]
