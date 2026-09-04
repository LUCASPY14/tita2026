# Actualiza verificar_saldo_tarjeta() para usar el nombre de columna nuevo
# (MovimientoTarjeta.id -> id_movimiento_tarjeta) tras el rename de PKs.

from django.db import migrations

SALDO_FN = """
CREATE OR REPLACE FUNCTION verificar_saldo_tarjeta(p_nro varchar)
RETURNS TABLE(
    nro_tarjeta      varchar,
    saldo_almacenado numeric,
    saldo_calculado  numeric,
    diferencia       numeric,
    total_movimientos bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.nro_tarjeta,
        t.saldo_actual,
        COALESCE(SUM(
            CASE m.tipo
                WHEN 'RECARGA' THEN  m.monto
                WHEN 'CONSUMO' THEN -m.monto
                WHEN 'AJUSTE'  THEN  m.monto
                WHEN 'REVERSO' THEN  m.monto
                ELSE 0
            END
        ), 0),
        t.saldo_actual - COALESCE(SUM(
            CASE m.tipo
                WHEN 'RECARGA' THEN  m.monto
                WHEN 'CONSUMO' THEN -m.monto
                WHEN 'AJUSTE'  THEN  m.monto
                WHEN 'REVERSO' THEN  m.monto
                ELSE 0
            END
        ), 0),
        COUNT(m.id_movimiento_tarjeta)
    FROM core_tarjeta t
    LEFT JOIN core_movimientotarjeta m ON m.tarjeta_id = t.nro_tarjeta
    WHERE t.nro_tarjeta = p_nro
    GROUP BY t.nro_tarjeta, t.saldo_actual;
END;
$$ LANGUAGE plpgsql;
"""

DROP_FN = "DROP FUNCTION IF EXISTS verificar_saldo_tarjeta(varchar);"


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_alter_movimientotarjeta_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(SALDO_FN, reverse_sql=DROP_FN),
    ]
