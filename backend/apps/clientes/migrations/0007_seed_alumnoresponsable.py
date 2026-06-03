"""
Migración de datos: crea una fila en AlumnoResponsable (es_titular=True)
por cada Hijo existente, usando su campo cliente_responsable actual.

Esto garantiza que, tras agregar la tabla pivot, cada alumno ya tiene
su responsable titular registrado y el modelo financiero no se rompe.

reverse_populate: elimina todas las filas creadas por esta migración
(identificadas por parentesco='OTRO', ya que no conocemos el parentesco real).
En producción, los usuarios completarán el parentesco desde el frontend.
"""

from django.db import migrations


def populate_responsables(apps, schema_editor):
    Hijo = apps.get_model("clientes", "Hijo")
    AlumnoResponsable = apps.get_model("clientes", "AlumnoResponsable")

    rows = []
    for hijo in Hijo.objects.select_related("cliente_responsable").iterator():
        if hijo.cliente_responsable_id is None:
            continue
        rows.append(
            AlumnoResponsable(
                hijo=hijo,
                cliente_id=hijo.cliente_responsable_id,
                parentesco="OTRO",
                es_titular=True,
                orden_cobro=1,
                recibe_notificaciones=True,
                puede_ver_saldo=True,
                activo=True,
            )
        )

    AlumnoResponsable.objects.bulk_create(rows, ignore_conflicts=True)


def reverse_populate(apps, schema_editor):
    AlumnoResponsable = apps.get_model("clientes", "AlumnoResponsable")
    AlumnoResponsable.objects.filter(es_titular=True, parentesco="OTRO").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0006_alumnoresponsable"),
    ]

    operations = [
        migrations.RunPython(populate_responsables, reverse_code=reverse_populate),
    ]
