from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('almuerzos', '0021_remove_suscripcionalmuerzo_tipo_cobro_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='precioalmuerzo',
            old_name='id',
            new_name='id_precio_almuerzo',
        ),
        migrations.RenameField(
            model_name='tipoalmuerzo',
            old_name='id',
            new_name='id_tipo_almuerzo',
        ),
        migrations.RenameField(
            model_name='planalmuerzo',
            old_name='id',
            new_name='id_plan_almuerzo',
        ),
        migrations.RenameField(
            model_name='suscripcionalmuerzo',
            old_name='id',
            new_name='id_suscripcion',
        ),
        migrations.RenameField(
            model_name='registroconsumoalmuerzo',
            old_name='id',
            new_name='id_registro_consumo',
        ),
        migrations.RenameField(
            model_name='cuentaalmuerzomensual',
            old_name='id',
            new_name='id_cuenta_mensual',
        ),
        migrations.RenameField(
            model_name='pagocuentaalmuerzo',
            old_name='id',
            new_name='id_pago_cuenta',
        ),
        migrations.RenameField(
            model_name='alergeno',
            old_name='id',
            new_name='id_alergeno',
        ),
        migrations.RenameField(
            model_name='productoalergeno',
            old_name='id',
            new_name='id_producto_alergeno',
        ),
        migrations.RenameField(
            model_name='menudiario',
            old_name='id',
            new_name='id_menu',
        ),
        migrations.RenameField(
            model_name='detallemenudiario',
            old_name='id',
            new_name='id_detalle_menu',
        ),
        migrations.RenameField(
            model_name='saldoalmuerzo',
            old_name='id',
            new_name='id_saldo_almuerzo',
        ),
        migrations.RenameField(
            model_name='recargasaldoalmuerzo',
            old_name='id',
            new_name='id_recarga_almuerzo',
        ),
        migrations.RenameField(
            model_name='movimientosaldoalmuerzo',
            old_name='id',
            new_name='id_movimiento_almuerzo',
        ),
    ]
