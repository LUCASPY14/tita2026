# v1.0 Crítico 3 + Mejora 6:
# - idx_detalleventa_producto_fecha: cubre queries de rentabilidad por producto
#   en un período (hasta ahora idx_det_producto no incluía venta_id ni fecha).
# - idx_venta_pendientes: índice parcial para el dashboard de deudas del POS,
#   la query más frecuente del sistema.

from django.db import migrations

SQL = """
-- Crítico 3: reporte de rentabilidad por producto
CREATE INDEX IF NOT EXISTS idx_detalleventa_producto_venta
    ON ventas_detalleventa(producto_id, venta_id);

-- Mejora 6: ventas activas con pago pendiente (dashboard deudas POS)
CREATE INDEX IF NOT EXISTS idx_venta_pendientes
    ON ventas_venta(cliente_id, fecha)
    WHERE estado = 'ACTIVA' AND estado_pago != 'PAGADO';
"""

DROP_SQL = """
DROP INDEX IF EXISTS idx_detalleventa_producto_venta;
DROP INDEX IF EXISTS idx_venta_pendientes;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0005_check_constraints_montos"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=DROP_SQL),
    ]
