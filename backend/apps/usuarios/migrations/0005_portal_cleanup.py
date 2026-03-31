# Portal cleanup:
#   - Drop UsuariosWebClientes (legacy duplicate of UsuariosPortal)
#   - Fix UsuariosPortal.email_verificado: IntegerField → BooleanField
#   - Fix UsuariosPortal.fecha_registro: plain DateTimeField → auto_now_add

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_rename_activo_to_estado'),
    ]

    operations = [
        # Drop legacy table
        migrations.DeleteModel(
            name='UsuariosWebClientes',
        ),
        # Fix email_verificado type
        migrations.AlterField(
            model_name='usuariosportal',
            name='email_verificado',
            field=models.BooleanField(default=False),
        ),
        # Fix fecha_registro to auto_now_add
        migrations.AlterField(
            model_name='usuariosportal',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
