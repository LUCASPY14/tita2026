# Generated migration to expand CargasSaldo model for complete recharge flow
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_limitestransaccion_registroautorizaciones'),
        ('usuarios', '0002_permisos_rolespermisos'),
        ('ventas', '0002_agregar_comision_pagos'),
    ]

    operations = [
        # Expandir campos de CargasSaldo
        migrations.AddField(
            model_name='cargassaldo',
            name='metodo_pago',
            field=models.CharField(
                max_length=30,
                default='efectivo',
                help_text='Método: efectivo, bancard, transferencia, tarjeta_pos'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='total_cobrado',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Monto total cobrado incluyendo comisiones'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='comision_aplicada',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text='Comisión cobrada por la transacción'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='porcentaje_comision',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=0,
                help_text='Porcentaje de comisión aplicado (%)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='numero_comprobante_externo',
            field=models.CharField(
                max_length=100,
                unique=True,
                null=True,
                blank=True,
                help_text='Número de comprobante bancario/transacción externa (idempotencia)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='codigo_referencia_interno',
            field=models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                help_text='Código interno para facilitar conciliación (ej: REF-12345)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='referencia_externa',
            field=models.CharField(
                max_length=100,
                unique=True,
                null=True,
                blank=True,
                help_text='Referencia de pasarela externa (idempotencia Bancard)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='usuario_responsable',
            field=models.ForeignKey(
                'usuarios.Empleados',
                models.SET_NULL,
                db_column='id_empleado_responsable',
                null=True,
                blank=True,
                related_name='recargas_registradas',
                help_text='Cajero que registró la recarga (si aplica)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='supervisor_aprobador',
            field=models.ForeignKey(
                'usuarios.Empleados',
                models.SET_NULL,
                db_column='id_supervisor_aprobador',
                null=True,
                blank=True,
                related_name='recargas_aprobadas',
                help_text='Supervisor que aprobó recarga de monto elevado'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='fecha_aprobacion',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='Fecha de aprobación por supervisor'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='id_factura',
            field=models.ForeignKey(
                'ventas.Ventas',
                models.SET_NULL,
                db_column='id_factura',
                null=True,
                blank=True,
                related_name='recargas_asociadas',
                help_text='Factura generada por esta recarga'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='imagen_comprobante',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                help_text='Ruta a imagen del comprobante de transferencia'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='ip_origen',
            field=models.GenericIPAddressField(
                null=True,
                blank=True,
                help_text='IP desde donde se originó la recarga'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='webhook_payload',
            field=models.TextField(
                null=True,
                blank=True,
                help_text='Payload JSON del webhook (para auditoría)'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='motivo_rechazo',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                help_text='Motivo de rechazo si aplica'
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='requiere_validacion_supervisor',
            field=models.BooleanField(
                default=False,
                help_text='Indica si requiere validación de supervisor por monto elevado'
            ),
        ),
        
        # Actualizar estados permitidos
        migrations.AlterField(
            model_name='cargassaldo',
            name='estado',
            field=models.CharField(
                max_length=30,
                default='pendiente',
                help_text='Estados: pendiente, pendiente_validacion, validacion_pendiente, completada, rechazada, cancelada, reembolsada, expirada'
            ),
        ),
    ]
