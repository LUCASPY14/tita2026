from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0006_add_id_caja_to_ventas'),
    ]

    operations = [
        migrations.CreateModel(
            name='CondicionVenta',
            fields=[
                ('id_condicion_venta', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Condición de Venta',
                'verbose_name_plural': 'Condiciones de Venta',
                'db_table': 'condicion_venta',
                'ordering': ['nombre'],
                'managed': True,
            },
        ),
    ]
