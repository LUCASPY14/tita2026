# Paridad con core/migrations/0015_trigger_saldo_tarjeta.py: mismo problema
# (saldo_actual se actualizaba a mano en Python), misma solución. A diferencia
# de MovimientoTarjeta, en MovimientoSaldoAlmuerzo el monto ya viene con
# signo para todos los tipos (positivo = crédito, negativo = débito — ver
# help_text del campo), así que el trigger es una simple suma, sin CASE.

from django.db import migrations

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION fn_sync_saldo_almuerzo()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE almuerzos_saldoalmuerzo
    SET saldo_actual = (
        SELECT COALESCE(SUM(monto), 0)
        FROM almuerzos_movimientosaldoalmuerzo
        WHERE saldo_id = NEW.saldo_id
    )
    WHERE id_saldo_almuerzo = NEW.saldo_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_saldo_almuerzo ON almuerzos_movimientosaldoalmuerzo;

CREATE TRIGGER trg_sync_saldo_almuerzo
AFTER INSERT OR UPDATE OF monto ON almuerzos_movimientosaldoalmuerzo
FOR EACH ROW EXECUTE FUNCTION fn_sync_saldo_almuerzo();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS trg_sync_saldo_almuerzo ON almuerzos_movimientosaldoalmuerzo;
DROP FUNCTION IF EXISTS fn_sync_saldo_almuerzo();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("almuerzos", "0028_saldo_almuerzo_limite_credito"),
    ]

    operations = [
        migrations.RunSQL(TRIGGER_SQL, reverse_sql=DROP_TRIGGER),
    ]
