from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_cargassaldo_codigo_referencia_interno_and_more'),
        ('ventas', '0001_initial'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargassaldo',
            name='id_factura',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='id_factura',
                related_name='recargas',
                to='ventas.ventas',
            ),
        ),
        migrations.AlterField(
            model_name='cargassaldo',
            name='nro_tarjeta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='nro_tarjeta',
                to='core.tarjetas',
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='usuario_responsable',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='usuario_responsable',
                related_name='recargas_procesadas',
                to='usuarios.empleados',
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='supervisor_aprobador',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='supervisor_aprobador',
                related_name='recargas_aprobadas',
                to='usuarios.empleados',
            ),
        ),
        migrations.AddField(
            model_name='cargassaldo',
            name='fecha_aprobacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
