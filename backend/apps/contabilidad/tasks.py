from celery import shared_task
from django.db import connection
import logging

logger = logging.getLogger(__name__)


@shared_task(name="apps.contabilidad.tasks.refrescar_mv_balance_cliente", bind=True, max_retries=2)
def refrescar_mv_balance_cliente(self):
    """
    Refresca la vista materializada mv_balance_cliente sin bloquear lecturas.
    El índice único mv_balance_cliente_pk (cliente_id) permite usar CONCURRENTLY.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_balance_cliente;")
        logger.info("mv_balance_cliente refrescada correctamente.")
    except Exception as exc:
        logger.error("Error al refrescar mv_balance_cliente: %s", exc)
        raise self.retry(exc=exc, countdown=60)
