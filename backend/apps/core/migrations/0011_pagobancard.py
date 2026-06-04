from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
        ('core', '0010_check_constraints_and_saldo_fn'),
    ]

    operations = [
        migrations.CreateModel(
            name='PagoBancard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop_process_id', models.CharField(help_text='ID único generado por nosotros (UUID)', max_length=100, unique=True)),
                ('process_id', models.CharField(blank=True, help_text='process_id devuelto por Bancard', max_length=200, null=True)),
                ('monto', models.DecimalField(decimal_places=0, help_text='Monto en Guaraníes a cargar en la tarjeta', max_digits=12)),
                ('descripcion', models.CharField(default='Recarga de saldo — Cantina Tita', max_length=255)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('APROBADO', 'Aprobado'), ('RECHAZADO', 'Rechazado'), ('CANCELADO', 'Cancelado'), ('ERROR', 'Error')], default='PENDIENTE', max_length=15)),
                ('bancard_response', models.JSONField(default=dict)),
                ('ip_origen', models.GenericIPAddressField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_confirmacion', models.DateTimeField(blank=True, null=True)),
                ('tarjeta', models.ForeignKey(help_text='Tarjeta prepago que se recargará', on_delete=django.db.models.deletion.PROTECT, related_name='pagos_bancard', to='core.tarjeta')),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pagos_bancard', to='clientes.cliente')),
                ('carga_saldo', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pago_bancard', to='core.cargasaldo')),
            ],
            options={
                'verbose_name': 'Pago Bancard',
                'verbose_name_plural': 'Pagos Bancard',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.AddIndex(
            model_name='pagobancard',
            index=models.Index(fields=['shop_process_id'], name='idx_bancard_shop_pid'),
        ),
        migrations.AddIndex(
            model_name='pagobancard',
            index=models.Index(fields=['tarjeta', '-fecha_creacion'], name='idx_bancard_tarjeta'),
        ),
        migrations.AddIndex(
            model_name='pagobancard',
            index=models.Index(fields=['estado', '-fecha_creacion'], name='idx_bancard_estado'),
        ),
    ]
