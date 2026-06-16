# v1.0 Crítico 2 y 4:
# - Agrega prefijo "public." en v_estado_cajas para que el schema sea explícito
#   y no dependa de search_path del servidor.
# - Trigger fn_sync_factura_venta() hace de contabilidad_factura.venta_id
#   la fuente de verdad y sincroniza ventas_venta.factura_id automáticamente,
#   eliminando el riesgo de inconsistencia de la doble FK circular.

from django.db import migrations

FIX_VIEW_SQL = """
CREATE OR REPLACE VIEW v_estado_cajas AS
SELECT
    cj.id                                           AS caja_id,
    cj.nombre                                       AS caja_nombre,
    cc.id                                           AS cierre_id,
    cc.estado,
    cc.fecha_apertura,
    cc.fecha_cierre,
    cc.monto_inicial,
    cc.monto_contado_fisico,
    cc.diferencia_efectivo,
    COALESCE(u.nombre || ' ' || u.apellido, 'Sin asignar') AS cajero,
    COUNT(DISTINCT mv.id)                           AS total_movimientos,
    COALESCE(SUM(mv.monto)
        FILTER (WHERE mv.tipo = 'INGRESO'), 0)      AS total_ingresos,
    COALESCE(SUM(mv.monto)
        FILTER (WHERE mv.tipo = 'EGRESO'), 0)       AS total_egresos,
    cc.fecha_apertura::date                         AS fecha
FROM contabilidad_caja cj
LEFT JOIN contabilidad_cierrecaja cc ON cc.caja_id = cj.id
LEFT JOIN public.usuarios u ON u.id = cc.empleado_id
LEFT JOIN contabilidad_movimientocaja mv ON mv.cierre_id = cc.id
WHERE cj.activo = true
GROUP BY cj.id, cj.nombre, cc.id, cc.estado, cc.fecha_apertura,
         cc.fecha_cierre, cc.monto_inicial, cc.monto_contado_fisico,
         cc.diferencia_efectivo, u.nombre, u.apellido;
"""

TRIGGER_FACTURA_SQL = """
CREATE OR REPLACE FUNCTION fn_sync_factura_venta()
RETURNS TRIGGER AS $$
BEGIN
    -- Si cambió el venta_id anterior, limpiar el factura_id de esa venta
    IF TG_OP = 'UPDATE'
            AND OLD.venta_id IS NOT NULL
            AND OLD.venta_id IS DISTINCT FROM NEW.venta_id THEN
        UPDATE ventas_venta
        SET    factura_id = NULL
        WHERE  id = OLD.venta_id
          AND  factura_id = NEW.id;
    END IF;

    -- Apuntar la nueva venta a esta factura
    IF NEW.venta_id IS NOT NULL THEN
        UPDATE ventas_venta
        SET    factura_id = NEW.id
        WHERE  id = NEW.venta_id
          AND  factura_id IS DISTINCT FROM NEW.id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_factura_venta ON contabilidad_factura;

CREATE TRIGGER trg_sync_factura_venta
AFTER INSERT OR UPDATE OF venta_id ON contabilidad_factura
FOR EACH ROW EXECUTE FUNCTION fn_sync_factura_venta();
"""

DROP_TRIGGER_FACTURA = """
DROP TRIGGER IF EXISTS trg_sync_factura_venta ON contabilidad_factura;
DROP FUNCTION IF EXISTS fn_sync_factura_venta();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0010_alter_movimientocaja_medio_pago_nullable"),
        ("ventas", "0005_check_constraints_montos"),
    ]

    operations = [
        migrations.RunSQL(FIX_VIEW_SQL, reverse_sql="-- view existente restaurada por migracion previa"),
        migrations.RunSQL(TRIGGER_FACTURA_SQL, reverse_sql=DROP_TRIGGER_FACTURA),
    ]
