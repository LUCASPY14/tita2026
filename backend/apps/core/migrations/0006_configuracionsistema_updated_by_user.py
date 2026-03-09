from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0005_cargassaldo_id_factura'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuracionsistema',
            name='updated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='updated_by',
                to='auth.user',
            ),
        ),
    ]
