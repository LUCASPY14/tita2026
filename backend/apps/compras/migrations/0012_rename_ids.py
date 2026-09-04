from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0011_alter_compra_estado_entrega_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='proveedor',
            old_name='id',
            new_name='id_proveedor',
        ),
        migrations.RenameField(
            model_name='cuentacorrienteproveedor',
            old_name='id',
            new_name='id_movimiento_ccp',
        ),
        migrations.RenameField(
            model_name='compra',
            old_name='id',
            new_name='id_compra',
        ),
        migrations.RenameField(
            model_name='detallecompra',
            old_name='id',
            new_name='id_detalle_compra',
        ),
        migrations.RenameField(
            model_name='pagoproveedor',
            old_name='id',
            new_name='id_pago_proveedor',
        ),
        migrations.RenameField(
            model_name='aplicacionpagocompra',
            old_name='id',
            new_name='id_aplicacion_pago_compra',
        ),
        migrations.RenameField(
            model_name='notacreditoproveedor',
            old_name='id',
            new_name='id_nc_proveedor',
        ),
        migrations.RenameField(
            model_name='ordencompra',
            old_name='id',
            new_name='id_orden_compra',
        ),
        migrations.RenameField(
            model_name='detalleordencompra',
            old_name='id',
            new_name='id_detalle_oc',
        ),
        migrations.RenameField(
            model_name='detallenotacreditoproveedor',
            old_name='id',
            new_name='id_detalle_ncp',
        ),
        migrations.RenameField(
            model_name='productoproveedor',
            old_name='id',
            new_name='id_producto_proveedor',
        ),
    ]
