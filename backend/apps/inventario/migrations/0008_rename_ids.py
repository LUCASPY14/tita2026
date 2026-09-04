from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0007_remove_loteproducto_compra_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stock',
            old_name='id',
            new_name='id_stock',
        ),
        migrations.RenameField(
            model_name='movimientostock',
            old_name='id',
            new_name='id_movimiento_stock',
        ),
        migrations.RenameField(
            model_name='ajusteinventario',
            old_name='id',
            new_name='id_ajuste',
        ),
        migrations.RenameField(
            model_name='detalleajuste',
            old_name='id',
            new_name='id_detalle_ajuste',
        ),
        migrations.RenameField(
            model_name='costohistorico',
            old_name='id',
            new_name='id_costo_historico',
        ),
    ]
