from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_movimientotarjeta_creado_por_nullable"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="tarjeta",
            index=models.Index(fields=["estado"], name="idx_tarjeta_estado"),
        ),
        migrations.AddIndex(
            model_name="tarjeta",
            index=models.Index(
                fields=["estado", "fecha_vencimiento"],
                name="idx_tarjeta_estado_vto",
            ),
        ),
        migrations.AddIndex(
            model_name="consumotarjeta",
            index=models.Index(
                fields=["tarjeta", "fecha_consumo"],
                name="idx_consumo_tarj_fecha",
            ),
        ),
    ]
