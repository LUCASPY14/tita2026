from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0007_seed_alumnoresponsable'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='pin_autorizacion',
            field=models.CharField(
                blank=True,
                default='',
                help_text='PIN hasheado para autorizar ventas con saldo insuficiente',
                max_length=128,
            ),
        ),
        migrations.AddField(
            model_name='historicalcliente',
            name='pin_autorizacion',
            field=models.CharField(
                blank=True,
                default='',
                help_text='PIN hasheado para autorizar ventas con saldo insuficiente',
                max_length=128,
            ),
        ),
    ]
