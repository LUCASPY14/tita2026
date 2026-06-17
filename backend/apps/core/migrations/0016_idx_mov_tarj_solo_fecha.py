from django.db import migrations


class Migration(migrations.Migration):
    """
    Índice standalone sobre core_movimientotarjeta.fecha para consultas de auditoría
    global ("todos los movimientos del día X") que no filtran por tarjeta_id.
    El índice compuesto (tarjeta_id, fecha) ya existe; este cubre el otro eje de acceso.
    """

    dependencies = [
        ("core", "0015_trigger_saldo_tarjeta"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_mov_tarj_solo_fecha ON core_movimientotarjeta (fecha);",
            reverse_sql="DROP INDEX IF EXISTS idx_mov_tarj_solo_fecha;",
        ),
    ]
