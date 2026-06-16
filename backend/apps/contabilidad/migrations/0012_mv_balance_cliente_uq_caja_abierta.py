# v1.0 Mejoras 8 y 11:
# - mv_balance_cliente: vista materializada con índice único para permitir
#   REFRESH CONCURRENTLY sin bloquear lecturas. Reemplaza la consulta live
#   en el dashboard principal (refrescar cada 5 minutos o tras cada pago).
# - uq_caja_abierta: garantiza que nunca haya dos cierres en estado ABIERTO
#   para la misma caja al mismo tiempo.

from django.db import migrations

MV_SQL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_balance_cliente AS
SELECT
    c.id                                    AS cliente_id,
    c.nombres || ' ' || c.apellidos        AS cliente_nombre,
    c.ruc_ci,
    c.telefono,
    c.email,
    COALESCE(ult.saldo_resultante, 0)       AS saldo_deuda,
    ult.fecha                               AS fecha_ultimo_mov,
    CASE
        WHEN COALESCE(ult.saldo_resultante, 0) > 0 THEN 'CON_DEUDA'
        WHEN COALESCE(ult.saldo_resultante, 0) < 0 THEN 'A_FAVOR'
        ELSE 'SIN_MOVIMIENTOS'
    END                                     AS estado_cuenta
FROM clientes_cliente c
LEFT JOIN LATERAL (
    SELECT saldo_resultante, fecha
    FROM clientes_cuentacorrientecliente
    WHERE cliente_id = c.id
    ORDER BY id DESC
    LIMIT 1
) ult ON true
WHERE c.activo = true
WITH DATA;

-- Índice único requerido para REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS mv_balance_cliente_pk
    ON mv_balance_cliente(cliente_id);
"""

DROP_MV = """
DROP MATERIALIZED VIEW IF EXISTS mv_balance_cliente;
"""

UQ_CAJA_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_caja_abierta
    ON contabilidad_cierrecaja(caja_id)
    WHERE estado = 'ABIERTO';
"""

DROP_UQ_CAJA = "DROP INDEX IF EXISTS uq_caja_abierta;"


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0011_fix_view_schema_trigger_factura"),
        ("clientes", "0008_add_pin_autorizacion"),
    ]

    operations = [
        migrations.RunSQL(MV_SQL, reverse_sql=DROP_MV),
        migrations.RunSQL(UQ_CAJA_SQL, reverse_sql=DROP_UQ_CAJA),
    ]
