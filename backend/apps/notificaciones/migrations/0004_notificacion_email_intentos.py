from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notificaciones", "0003_add_push_subscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificacion",
            name="email_intentos",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Intentos de envío por email realizados (máx. 3 antes de descartar).",
            ),
        ),
    ]
