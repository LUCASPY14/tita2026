# Actualiza fn_sync_factura_venta() para usar los nombres de columna nuevos
# (Venta.id -> id_venta, Factura.id -> id_factura) tras el rename de PKs.

from django.db import migrations

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
        WHERE  id_venta = OLD.venta_id
          AND  factura_id = NEW.id_factura;
    END IF;

    -- Apuntar la nueva venta a esta factura
    IF NEW.venta_id IS NOT NULL THEN
        UPDATE ventas_venta
        SET    factura_id = NEW.id_factura
        WHERE  id_venta = NEW.venta_id
          AND  factura_id IS DISTINCT FROM NEW.id_factura;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

DROP_TRIGGER_FACTURA = """
DROP TRIGGER IF EXISTS trg_sync_factura_venta ON contabilidad_factura;
DROP FUNCTION IF EXISTS fn_sync_factura_venta();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0015_alter_caja_id_caja_alter_cierrecaja_id_cierre_and_more'),
        ('ventas', '0011_alter_aplicacionpago_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(TRIGGER_FACTURA_SQL, reverse_sql=DROP_TRIGGER_FACTURA),
    ]
