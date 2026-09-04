"""
Convierte Proveedor.ciudad de texto libre a FK real hacia clientes.Ciudad —
misma jerarquía País→Departamento→Ciudad que ya usan Cliente y Empleado.

Hecha a mano en vez de dejar que makemigrations genere un AlterField directo:
ese AlterField haría un `ALTER COLUMN ciudad TYPE bigint` sin USING, que
Postgres rechaza porque hoy la columna es texto real ("Asunción", "Luque",
...) para los proveedores ya cargados en producción — no está vacía como
pasaba con Cliente/Empleado en el momento del rename. Se resuelve el texto
existente contra el catálogo Ciudad por nombre (case-insensitive) antes de
tirar la columna vieja; lo que no matchee queda en null (no se inventa
una ciudad).
"""

from django.db import migrations, models
import django.db.models.deletion


def resolver_ciudad_desde_texto(apps, schema_editor):
    Proveedor = apps.get_model("compras", "Proveedor")
    Ciudad = apps.get_model("clientes", "Ciudad")

    for proveedor in Proveedor.objects.exclude(ciudad_texto__isnull=True).exclude(ciudad_texto=""):
        ciudad = Ciudad.objects.filter(nombre__iexact=proveedor.ciudad_texto.strip()).first()
        if ciudad:
            proveedor.ciudad_nueva_id = ciudad.pk
            proveedor.save(update_fields=["ciudad_nueva"])


def revertir(apps, schema_editor):
    # No hace falta reconstruir el texto original — el rollback de esta
    # migración solo se usaría en desarrollo, nunca contra datos reales.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0020_remove_ciudad_pais_remove_cliente_ciudad_catalogo_and_more"),
        ("compras", "0013_alter_aplicacionpagocompra_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="proveedor",
            old_name="ciudad",
            new_name="ciudad_texto",
        ),
        migrations.AddField(
            model_name="proveedor",
            name="ciudad_nueva",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="proveedores", to="clientes.ciudad",
            ),
        ),
        migrations.RunPython(resolver_ciudad_desde_texto, revertir),
        migrations.RemoveField(
            model_name="proveedor",
            name="ciudad_texto",
        ),
        migrations.RenameField(
            model_name="proveedor",
            old_name="ciudad_nueva",
            new_name="ciudad",
        ),
    ]
