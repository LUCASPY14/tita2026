from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notificaciones", "0004_notificacion_email_intentos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificacion",
            name="destino",
            field=models.CharField(
                choices=[
                    ("EMAIL", "Email"),
                    ("SISTEMA", "En sistema"),
                    ("WHATSAPP", "WhatsApp"),
                ],
                default="SISTEMA",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="preferencianotificacion",
            name="whatsapp_activo",
            field=models.BooleanField(
                default=False,
                help_text="Recibir alertas por WhatsApp",
            ),
        ),
    ]
