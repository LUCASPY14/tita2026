# v1.0 Mejora 13: trigger que mantiene patrones_acceso automáticamente.
# Al insertar una sesión activa, hace upsert en patrones_acceso para esa
# combinación usuario+IP: amplía la ventana horaria, incrementa la frecuencia
# y marca es_habitual=True cuando el contador supera el umbral (10 accesos).

from django.db import migrations

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION fn_update_patron_acceso()
RETURNS TRIGGER AS $$
DECLARE
    v_hora    time := LOCALTIME;
    v_dia     text := TO_CHAR(NOW(), 'DY');
    v_umbral  int  := 10;
BEGIN
    UPDATE patrones_acceso
    SET
        frecuencia_accesos = frecuencia_accesos + 1,
        ultima_deteccion   = NOW(),
        es_habitual        = (frecuencia_accesos + 1 >= v_umbral),
        horario_inicio     = LEAST(horario_inicio, v_hora),
        horario_fin        = GREATEST(horario_fin, v_hora)
    WHERE usuario_id = NEW.usuario_id
      AND ip_address = NEW.ip_address;

    IF NOT FOUND THEN
        INSERT INTO patrones_acceso
            (usuario_id, ip_address, horario_inicio, horario_fin,
             dias_semana, primera_deteccion, ultima_deteccion,
             frecuencia_accesos, es_habitual)
        VALUES
            (NEW.usuario_id, NEW.ip_address,
             v_hora, v_hora,
             v_dia, NOW(), NOW(),
             1, FALSE);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_patron_acceso ON sesiones_activas;

CREATE TRIGGER trg_update_patron_acceso
AFTER INSERT ON sesiones_activas
FOR EACH ROW EXECUTE FUNCTION fn_update_patron_acceso();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS trg_update_patron_acceso ON sesiones_activas;
DROP FUNCTION IF EXISTS fn_update_patron_acceso();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(TRIGGER_SQL, reverse_sql=DROP_TRIGGER),
    ]
