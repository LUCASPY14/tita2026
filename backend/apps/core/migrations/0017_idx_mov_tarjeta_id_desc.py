"""
Agrega índice compuesto (tarjeta_id, id DESC) en MovimientoTarjeta.

MovimientoTarjeta.save() ejecuta en cada transacción:
    MovimientoTarjeta.objects.filter(tarjeta=self.tarjeta).order_by("-id").first()

Con el índice existente (tarjeta, fecha), PostgreSQL filtra por tarjeta pero
debe ordenar por -id en memoria. Con (tarjeta_id, id DESC) puede hacer un
index-backward-scan y retornar el primer resultado directamente.

Impacto: toda venta con tarjeta prepago (ModoRecreo) y toda recarga ejecuta
este query. Con 500 tarjetas activas y miles de movimientos acumulados,
el índice elimina el paso de sorting en operaciones de alta frecuencia.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_idx_mov_tarj_solo_fecha"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_mov_tarj_tarjeta_id_desc
                    ON core_movimientotarjeta (tarjeta_id, id DESC);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_mov_tarj_tarjeta_id_desc;",
        ),
    ]
