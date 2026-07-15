import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.productos.tasks.sincronizar_costos_desde_compras",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def sincronizar_costos_desde_compras():
    """
    Genera registros CostoHistorico para cada Compra con estado_entrega=RECIBIDA
    que aún no tenga sus costos sincronizados.

    Idempotente: usa get_or_create por (compra, producto), por lo que ejecutar
    la tarea dos veces sobre la misma compra no genera duplicados.

    Actualizar CostoHistorico actualiza automáticamente Stock.costo_promedio,
    que es una property calculada a partir de estos registros.

    Corre diario a las 01:30.
    """
    from apps.compras.models import Compra
    from apps.inventario.models import CostoHistorico

    compras_recibidas = (
        Compra.objects
        .filter(estado_entrega=Compra.EstadoEntrega.RECIBIDA)
        .prefetch_related("detalles__producto")
    )

    compras_procesadas = 0
    costos_registrados = 0

    for compra in compras_recibidas:
        detalles = list(compra.detalles.all())
        if not detalles:
            continue

        nuevos = 0
        for detalle in detalles:
            _, created = CostoHistorico.objects.get_or_create(
                compra=compra,
                producto=detalle.producto,
                defaults={
                    "costo_unitario": detalle.costo_unitario,
                    "cantidad_comprada": detalle.cantidad,
                    "fecha_compra": compra.fecha,
                },
            )
            if created:
                nuevos += 1

        if nuevos:
            compras_procesadas += 1
            costos_registrados += nuevos
            logger.info(
                "sincronizar_costos: compra #%d → %d costo(s) nuevos",
                compra.pk, nuevos,
            )

    logger.info(
        "sincronizar_costos_desde_compras: %d compra(s) procesadas, %d registro(s) creados",
        compras_procesadas, costos_registrados,
    )
    return {"compras_procesadas": compras_procesadas, "costos_registrados": costos_registrados}
