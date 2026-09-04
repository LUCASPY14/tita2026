from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0008_remove_emailenviado_plantilla_delete_plantillaemail'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pushsubscription',
            old_name='id',
            new_name='id_push',
        ),
        migrations.RenameField(
            model_name='notificacion',
            old_name='id',
            new_name='id_notificacion',
        ),
        migrations.RenameField(
            model_name='preferencianotificacion',
            old_name='id',
            new_name='id_preferencia',
        ),
        migrations.RenameField(
            model_name='emailenviado',
            old_name='id',
            new_name='id_email',
        ),
        migrations.RenameField(
            model_name='solicitudnotificacion',
            old_name='id',
            new_name='id_solicitud_notif',
        ),
    ]
