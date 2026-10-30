from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_alter_cargasaldo_estado_and_more'),
    ]

    operations = [
        UnaccentExtension(),
    ]
