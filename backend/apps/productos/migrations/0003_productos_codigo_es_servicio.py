from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0002_categorias_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='productos',
            name='codigo',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                help_text='Código interno del producto (legacy compat)',
            ),
        ),
        migrations.AddField(
            model_name='productos',
            name='es_servicio',
            field=models.BooleanField(
                default=False,
                help_text='True si es un servicio (no requiere stock físico)',
            ),
        ),
        migrations.AddField(
            model_name='productos',
            name='requiere_stock',
            field=models.BooleanField(
                default=True,
                help_text='False si no gestiona stock',
            ),
        ),
    ]
