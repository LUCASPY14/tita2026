import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.compras.tasks.alertar_ordenes_compra_pendientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_ordenes_compra_pendientes():
    """
    Detecta OrdenesDeCompra en estado PENDIENTE con más de 48h sin aprobación
    y crea notificaciones internas para los usuarios ADMIN.
    """
    from apps.compras.models import OrdenCompra
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    corte = timezone.now() - timedelta(hours=48)
    ordenes = OrdenCompra.objects.filter(
        estado=OrdenCompra.Estado.PENDIENTE,
        fecha_creacion__lt=corte,
    ).select_related("proveedor")

    if not ordenes.exists():
        logger.info("alertar_ordenes_compra_pendientes: sin órdenes pendientes > 48h")
        return {"alertas_creadas": 0}

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    if not admins:
        logger.warning("alertar_ordenes_compra_pendientes: no hay usuarios ADMIN activos")
        return {"alertas_creadas": 0}

    alertas = 0
    for admin in admins:
        for orden in ordenes:
            Notificacion.objects.create(
                usuario=admin,
                tipo=Notificacion.Tipo.SISTEMA,
                titulo="Orden de compra pendiente de aprobación",
                mensaje=(
                    f"La OC #{orden.pk} del proveedor {orden.proveedor.razon_social} "
                    f"lleva más de 48h esperando aprobación "
                    f"(creada el {orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')})."
                ),
                destino=Notificacion.Destino.SISTEMA,
            )
            alertas += 1

    logger.info(
        "alertar_ordenes_compra_pendientes: %d alertas creadas para %d órdenes",
        alertas, ordenes.count(),
    )
    return {"alertas_creadas": alertas}


@shared_task(
    name="apps.compras.tasks.alertar_compras_pendientes_pago",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_compras_pendientes_pago():
    """
    Detecta Compras a crédito con estado_pago=PENDIENTE con más de 7 días sin pago
    y crea notificaciones internas para los usuarios ADMIN.
    """
    from apps.compras.models import Compra
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    corte = timezone.now() - timedelta(days=7)
    compras = Compra.objects.filter(
        tipo_pago=Compra.TipoPago.CREDITO,
        estado_pago=Compra.EstadoPago.PENDIENTE,
        fecha_creacion__lt=corte,
    ).select_related("proveedor")

    if not compras.exists():
        logger.info("alertar_compras_pendientes_pago: sin compras con deuda pendiente > 7 días")
        return {"alertas_creadas": 0}

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    if not admins:
        logger.warning("alertar_compras_pendientes_pago: no hay usuarios ADMIN activos")
        return {"alertas_creadas": 0}

    alertas = 0
    for admin in admins:
        for compra in compras:
            Notificacion.objects.create(
                usuario=admin,
                tipo=Notificacion.Tipo.SISTEMA,
                titulo="Compra con pago pendiente",
                mensaje=(
                    f"La compra #{compra.pk} al proveedor {compra.proveedor.razon_social} "
                    f"por ₲{int(compra.monto_total):,} tiene pago pendiente hace más de 7 días "
                    f"(fecha: {compra.fecha.strftime('%d/%m/%Y')})."
                ),
                destino=Notificacion.Destino.SISTEMA,
            )
            alertas += 1

    logger.info(
        "alertar_compras_pendientes_pago: %d alertas creadas para %d compras",
        alertas, compras.count(),
    )
    return {"alertas_creadas": alertas}
