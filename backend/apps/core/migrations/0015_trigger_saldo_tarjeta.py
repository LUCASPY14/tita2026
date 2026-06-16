# v1.0 Crítico 1: Trigger que garantiza la consistencia de core_tarjeta.saldo_actual
# a nivel de BD. Sin esto, si la app falla a mitad de una transacción el saldo
# queda desfasado y verificar_saldo_tarjeta() detecta la discrepancia.

from django.db import migrations

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION fn_sync_saldo_tarjeta()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE core_tarjeta
    SET saldo_actual = (
        SELECT COALESCE(SUM(
            CASE tipo
                WHEN 'RECARGA' THEN  monto
                WHEN 'CONSUMO' THEN -monto
                WHEN 'AJUSTE'  THEN  monto
                WHEN 'REVERSO' THEN  monto
                ELSE 0
            END
        ), 0)
        FROM core_movimientotarjeta
        WHERE tarjeta_id = NEW.tarjeta_id
    )
    WHERE nro_tarjeta = NEW.tarjeta_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_saldo_tarjeta ON core_movimientotarjeta;

CREATE TRIGGER trg_sync_saldo_tarjeta
AFTER INSERT OR UPDATE OF monto, tipo ON core_movimientotarjeta
FOR EACH ROW EXECUTE FUNCTION fn_sync_saldo_tarjeta();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS trg_sync_saldo_tarjeta ON core_movimientotarjeta;
DROP FUNCTION IF EXISTS fn_sync_saldo_tarjeta();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_add_indexes_tarjeta_consumo"),
    ]

    operations = [
        migrations.RunSQL(TRIGGER_SQL, reverse_sql=DROP_TRIGGER),
    ]
