from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0005_alter_productoimpuesto_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='categoria',
            old_name='id',
            new_name='id_categoria',
        ),
        migrations.RenameField(
            model_name='unidadmedida',
            old_name='id',
            new_name='id_unidad_medida',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='id',
            new_name='id_producto',
        ),
        migrations.RenameField(
            model_name='listaprecio',
            old_name='id',
            new_name='id_lista_precio',
        ),
        migrations.RenameField(
            model_name='precioporlista',
            old_name='id',
            new_name='id_precio_lista',
        ),
        migrations.RenameField(
            model_name='historicoprecio',
            old_name='id',
            new_name='id_historico_precio',
        ),
        migrations.RenameField(
            model_name='impuesto',
            old_name='id',
            new_name='id_impuesto',
        ),
        migrations.RenameField(
            model_name='productoimpuesto',
            old_name='id',
            new_name='id_producto_impuesto',
        ),
    ]
