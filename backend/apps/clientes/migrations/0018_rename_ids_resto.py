from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0017_alter_cliente_id_cliente_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cuentacorrientecliente',
            old_name='id',
            new_name='id_movimiento_cc',
        ),
        migrations.RenameField(
            model_name='tipocliente',
            old_name='id',
            new_name='id_tipo_cliente',
        ),
        migrations.RenameField(
            model_name='hijo',
            old_name='id',
            new_name='id_hijo',
        ),
        migrations.RenameField(
            model_name='grado',
            old_name='id',
            new_name='id_grado',
        ),
        migrations.RenameField(
            model_name='historialgrado',
            old_name='id',
            new_name='id_historial_grado',
        ),
        migrations.RenameField(
            model_name='restriccionhijo',
            old_name='id',
            new_name='id_restriccion',
        ),
        migrations.RenameField(
            model_name='autorizacionsaldonegativo',
            old_name='id',
            new_name='id_autorizacion',
        ),
        migrations.RenameField(
            model_name='pais',
            old_name='id',
            new_name='id_pais',
        ),
        migrations.RenameField(
            model_name='ciudad',
            old_name='id',
            new_name='id_ciudad',
        ),
        migrations.RenameField(
            model_name='alumnoresponsable',
            old_name='id',
            new_name='id_responsable',
        ),
    ]
