"""
Migration 0007 – Facturación física (timbrada) sin SIFEN.

Cambios:
- Elimina campos SIFEN de documentos_tributarios: cdc, url_kude,
  estado_sifen, fecha_envio, fecha_respuesta
- Elimina campo es_electronico de timbrados
- Agrega id_cliente (FK nullable) a documentos_tributarios
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0006_rename_activo_to_estado"),
        ("clientes", "0005_alter_hijos_foto_perfil"),
    ]

    operations = [
        # ── Limpiar campos SIFEN ──────────────────────────────────────────────
        migrations.RemoveField(
            model_name="documentostributarios",
            name="cdc",
        ),
        migrations.RemoveField(
            model_name="documentostributarios",
            name="url_kude",
        ),
        migrations.RemoveField(
            model_name="documentostributarios",
            name="estado_sifen",
        ),
        migrations.RemoveField(
            model_name="documentostributarios",
            name="fecha_envio",
        ),
        migrations.RemoveField(
            model_name="documentostributarios",
            name="fecha_respuesta",
        ),
        # ── Eliminar es_electronico de Timbrados ─────────────────────────────
        migrations.RemoveField(
            model_name="timbrados",
            name="es_electronico",
        ),
        # ── Agregar FK al cliente ─────────────────────────────────────────────
        migrations.AddField(
            model_name="documentostributarios",
            name="id_cliente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column="id_cliente",
                related_name="documentos",
                to="clientes.clientes",
                help_text="Cliente al que se emite la factura",
            ),
        ),
    ]
