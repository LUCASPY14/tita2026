"""
Agrega índice compuesto (cliente_id, id DESC) en CuentaCorrienteCliente.

La vista materializada mv_balance_cliente ejecuta por cada cliente:
    SELECT saldo_resultante, fecha
    FROM clientes_cuentacorrientecliente
    WHERE cliente_id = X
    ORDER BY id DESC
    LIMIT 1

El índice existente (cliente, fecha) no cubre ORDER BY id DESC.
Este índice compuesto permite a PostgreSQL hacer un index-backward-scan
y retornar el primer resultado sin un paso de sorting extra, acelerando
el REFRESH MATERIALIZED VIEW CONCURRENTLY de mv_balance_cliente.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0008_add_pin_autorizacion"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_cc_cliente_id_desc
                    ON clientes_cuentacorrientecliente (cliente_id, id DESC);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_cc_cliente_id_desc;",
        ),
    ]
