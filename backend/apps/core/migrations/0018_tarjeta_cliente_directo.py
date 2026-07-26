"""
Migración: tarjeta de docente/funcionario
- hace Tarjeta.hijo nullable (antes era NOT NULL)
- agrega Tarjeta.cliente_directo (OneToOne a clientes.Cliente, nullable)
- agrega CheckConstraint: al menos uno de los dos debe estar presente
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0009_add_idx_cuentacorriente_cliente_id"),
        ("core", "0017_idx_mov_tarjeta_id_desc"),
    ]

    operations = [
        # 1. Agregar cliente_directo (nullable)
        migrations.AddField(
            model_name="tarjeta",
            name="cliente_directo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tarjeta_directa",
                to="clientes.cliente",
                help_text="Docente/funcionario dueño de la tarjeta (cuando no es alumno)",
            ),
        ),
        # 2. Hacer hijo nullable (todos los registros existentes ya tienen hijo NOT NULL → OK)
        migrations.AlterField(
            model_name="tarjeta",
            name="hijo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tarjeta",
                to="clientes.hijo",
                help_text="Estudiante dueño de la tarjeta",
            ),
        ),
        # 3. CheckConstraint: debe tener hijo O cliente_directo
        migrations.AddConstraint(
            model_name="tarjeta",
            constraint=models.CheckConstraint(
                condition=models.Q(hijo__isnull=False) | models.Q(cliente_directo__isnull=False),
                name="tarjeta_tiene_titular",
            ),
        ),
        # 4. Lo mismo para el modelo histórico (simple_history)
        migrations.AddField(
            model_name="historicaltarjeta",
            name="cliente_directo",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="clientes.cliente",
            ),
        ),
        migrations.AlterField(
            model_name="historicaltarjeta",
            name="hijo",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="clientes.hijo",
            ),
        ),
    ]
