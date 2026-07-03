from django.db import migrations

TRIGGER_SQL = """
DROP TRIGGER IF EXISTS trg_sync_cuenta_almuerzo ON almuerzos_registroconsumoalmuerzo;

CREATE OR REPLACE FUNCTION fn_sync_cuenta_almuerzo_mensual()
RETURNS TRIGGER AS $$
DECLARE
    v_hijo_id   bigint;
    v_anio      int;
    v_mes       int;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_hijo_id := OLD.hijo_id;
        v_anio    := EXTRACT(YEAR  FROM OLD.fecha_consumo)::int;
        v_mes     := EXTRACT(MONTH FROM OLD.fecha_consumo)::int;
    ELSE
        v_hijo_id := NEW.hijo_id;
        v_anio    := EXTRACT(YEAR  FROM NEW.fecha_consumo)::int;
        v_mes     := EXTRACT(MONTH FROM NEW.fecha_consumo)::int;
    END IF;

    UPDATE almuerzos_cuentaalmuerzomensual
    SET
        cantidad_almuerzos  = sub.cant,
        monto_total         = sub.total,
        fecha_actualizacion = now()
    FROM (
        SELECT
            COUNT(*)                         AS cant,
            COALESCE(SUM(costo_almuerzo), 0) AS total
        FROM almuerzos_registroconsumoalmuerzo
        WHERE hijo_id = v_hijo_id
          AND EXTRACT(YEAR  FROM fecha_consumo) = v_anio
          AND EXTRACT(MONTH FROM fecha_consumo) = v_mes
          AND ya_cobrado = true
          AND estado = 'REGISTRADO'
    ) sub
    WHERE hijo_id = v_hijo_id
      AND anio    = v_anio
      AND mes     = v_mes;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_cuenta_almuerzo
AFTER INSERT OR UPDATE OR DELETE
ON almuerzos_registroconsumoalmuerzo
FOR EACH ROW EXECUTE FUNCTION fn_sync_cuenta_almuerzo_mensual();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS trg_sync_cuenta_almuerzo ON almuerzos_registroconsumoalmuerzo;
DROP FUNCTION IF EXISTS fn_sync_cuenta_almuerzo_mensual();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("almuerzos", "0013_add_tipo_cobro_suscripcion"),
    ]

    operations = [
        migrations.RunSQL(TRIGGER_SQL, reverse_sql=DROP_TRIGGER),
    ]
