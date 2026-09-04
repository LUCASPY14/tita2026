from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_pagobancard_origen_cc'),
    ]

    operations = [
        migrations.RenameField(
            model_name='movimientotarjeta',
            old_name='id',
            new_name='id_movimiento_tarjeta',
        ),
        migrations.RenameField(
            model_name='cargasaldo',
            old_name='id',
            new_name='id_carga',
        ),
        migrations.RenameField(
            model_name='historicalcargasaldo',
            old_name='id',
            new_name='id_carga',
        ),
        migrations.RenameField(
            model_name='mediopago',
            old_name='id',
            new_name='id_medio_pago',
        ),
        migrations.RenameField(
            model_name='pagobancard',
            old_name='id',
            new_name='id_pago_bancard',
        ),
        migrations.RenameField(
            model_name='solicitudcatastrobancard',
            old_name='id',
            new_name='id_solicitud_catastro',
        ),
    ]
