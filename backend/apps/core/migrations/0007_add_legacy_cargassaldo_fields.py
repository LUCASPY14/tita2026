from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_configuracionsistema_updated_by_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargassaldo',
            name='metodo_pago',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='comision',
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='total_cobrado',
            field=models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='numero_comprobante_externo',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='referencia_externa',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]
