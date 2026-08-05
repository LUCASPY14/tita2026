"""
Simplifica el flujo de almuerzos a un único tipo ("Almuerzo Completo") y un
único plan ("Plan Estándar Mensual"). Desactiva las alternativas que no se
usan en la operación real (0 registros de consumo referencian un tipo, y 0
suscripciones activas usan el plan por cantidad).
"""

from django.db import migrations


def desactivar_alternativas(apps, schema_editor):
    TipoAlmuerzo = apps.get_model("almuerzos", "TipoAlmuerzo")
    PlanAlmuerzo = apps.get_model("almuerzos", "PlanAlmuerzo")
    TipoAlmuerzo.objects.filter(nombre="Almuerzo Simple").update(activo=False)
    PlanAlmuerzo.objects.filter(nombre="Plan Básico 20 días").update(activo=False)


def reactivar_alternativas(apps, schema_editor):
    TipoAlmuerzo = apps.get_model("almuerzos", "TipoAlmuerzo")
    PlanAlmuerzo = apps.get_model("almuerzos", "PlanAlmuerzo")
    TipoAlmuerzo.objects.filter(nombre="Almuerzo Simple").update(activo=True)
    PlanAlmuerzo.objects.filter(nombre="Plan Básico 20 días").update(activo=True)


class Migration(migrations.Migration):

    dependencies = [
        ("almuerzos", "0016_alter_productoalergeno_options"),
    ]

    operations = [
        migrations.RunPython(desactivar_alternativas, reactivar_alternativas),
    ]
