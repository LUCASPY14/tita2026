from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0006_add_pais_ciudad'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientes',
            name='id_ciudad',
            field=models.ForeignKey(
                blank=True,
                db_column='id_ciudad',
                help_text='Ciudad del catálogo (opcional)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='clientes.ciudad',
            ),
        ),
    ]
