"""
Marca "Almuerzo Completo" y "Plan Estándar Mensual" como predeterminados,
ya que son los únicos activos hoy y son los que ModalConsumo/ModalSuscripcion
deben preseleccionar por defecto.
"""

from django.db import migrations


def marcar_predeterminados(apps, schema_editor):
    TipoAlmuerzo = apps.get_model("almuerzos", "TipoAlmuerzo")
    PlanAlmuerzo = apps.get_model("almuerzos", "PlanAlmuerzo")
    TipoAlmuerzo.objects.filter(nombre="Almuerzo Completo").update(es_predeterminado=True)
    PlanAlmuerzo.objects.filter(nombre="Plan Estándar Mensual").update(es_predeterminado=True)


def desmarcar_predeterminados(apps, schema_editor):
    TipoAlmuerzo = apps.get_model("almuerzos", "TipoAlmuerzo")
    PlanAlmuerzo = apps.get_model("almuerzos", "PlanAlmuerzo")
    TipoAlmuerzo.objects.filter(nombre="Almuerzo Completo").update(es_predeterminado=False)
    PlanAlmuerzo.objects.filter(nombre="Plan Estándar Mensual").update(es_predeterminado=False)


class Migration(migrations.Migration):

    dependencies = [
        ("almuerzos", "0018_agregar_es_predeterminado"),
    ]

    operations = [
        migrations.RunPython(marcar_predeterminados, desmarcar_predeterminados),
    ]
