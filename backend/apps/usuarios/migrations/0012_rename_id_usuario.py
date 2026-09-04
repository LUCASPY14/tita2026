from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0011_remove_tokenrecuperacion_usuario_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usuario',
            old_name='id',
            new_name='id_usuario',
        ),
    ]
