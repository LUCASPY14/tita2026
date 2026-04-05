"""
Agrega condicion_venta (CONTADO/CREDITO) y plazo_dias (nullable) a
documentos_tributarios, como exige la normativa SET Paraguay.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0010_alter_documentostributarios_nro_preimpreso_interno_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentostributarios',
            name='condicion_venta',
            field=models.CharField(
                max_length=7,
                choices=[('CONTADO', 'Contado'), ('CREDITO', 'Crédito')],
                default='CONTADO',
                help_text='Condición de venta exigida por la SET',
            ),
        ),
        migrations.AddField(
            model_name='documentostributarios',
            name='plazo_dias',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text='Plazo en días para condición Crédito (obligatorio si CREDITO)',
            ),
        ),
    ]
