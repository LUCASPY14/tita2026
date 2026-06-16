# v1.0 Mejora 7: índice parcial para el cierre mensual de almuerzos.
# El trigger fn_sync_cuenta_almuerzo_mensual() y el proceso de cierre
# filtran siempre ya_cobrado = false; este índice cubre exactamente ese subconjunto.

from django.db import migrations

SQL = """
CREATE INDEX IF NOT EXISTS idx_consumo_sin_cobrar
    ON almuerzos_registroconsumoalmuerzo(hijo_id, fecha_consumo)
    WHERE ya_cobrado = false;
"""

DROP_SQL = "DROP INDEX IF EXISTS idx_consumo_sin_cobrar;"


class Migration(migrations.Migration):

    dependencies = [
        ("almuerzos", "0011_trigger_cuenta_mensual"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=DROP_SQL),
    ]
