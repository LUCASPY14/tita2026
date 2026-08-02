import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0009_add_idx_cuentacorriente_cliente_id'),
        ('core', '0021_alter_mediopago_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagobancard',
            name='card_id_bancard',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Slot de tarjeta guardada en Bancard usado para este pago (si no fue pago ocasional)', null=True),
        ),
        migrations.AddField(
            model_name='pagobancard',
            name='card_masked_number',
            field=models.CharField(blank=True, help_text='Número enmascarado de la tarjeta guardada usada (ej: 5418********0014)', max_length=30, default=''),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SolicitudCatastroBancard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referencia', models.CharField(help_text='ID único generado por nosotros para reconciliar el retorno del iframe', max_length=100, unique=True)),
                ('card_id', models.PositiveSmallIntegerField(help_text='Slot de tarjeta (1-5) reservado para este cliente en Bancard')),
                ('process_id', models.CharField(blank=True, max_length=200)),
                ('resuelto', models.BooleanField(default=False)),
                ('ip_origen', models.GenericIPAddressField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_catastro_bancard', to='clientes.cliente')),
            ],
            options={
                'verbose_name': 'Solicitud de catastro Bancard',
                'verbose_name_plural': 'Solicitudes de catastro Bancard',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.AddIndex(
            model_name='solicitudcatastrobancard',
            index=models.Index(fields=['referencia'], name='idx_catastro_referencia'),
        ),
        migrations.AddIndex(
            model_name='solicitudcatastrobancard',
            index=models.Index(fields=['cliente', 'resuelto'], name='idx_catastro_cliente_resuelto'),
        ),
    ]
