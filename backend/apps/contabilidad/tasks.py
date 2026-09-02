from datetime import timedelta
import logging

from celery import shared_task
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)

_DIAS_FACTURACION_MENSUAL_PENDIENTE = 30


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


@shared_task(
    name="apps.contabilidad.tasks.recordar_facturacion_mensual_pendiente",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def recordar_facturacion_mensual_pendiente():
    """
    Avisa a ADMIN si hay ítems de clientes con modalidad_facturacion=MENSUAL
    pendientes de facturar con más de _DIAS_FACTURACION_MENSUAL_PENDIENTE días
    de antigüedad. No emite nada — la numeración preimpresa de facturas
    requiere revisión humana; esto es solo un recordatorio para que no se
    olvide. Corre el día 5 de cada mes.
    """
    from apps.contabilidad.services import FacturacionService
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    fecha_corte = timezone.now() - timedelta(days=_DIAS_FACTURACION_MENSUAL_PENDIENTE)
    pendientes = FacturacionService.get_pendientes()

    def _cliente_de(item, tipo):
        if tipo == "CARGA_SALDO":
            return item.cliente_origen or (
                item.tarjeta.hijo.cliente_responsable if item.tarjeta and item.tarjeta.hijo else None
            )
        if tipo == "PAGO_ALMUERZO":
            return item.cuenta.hijo.cliente_responsable
        if tipo == "RECARGA_ALMUERZO":
            return item.hijo.cliente_responsable
        return item.cliente

    fuentes = [
        ("CARGA_SALDO", pendientes["cargas"], "fecha_carga"),
        ("PAGO_ALMUERZO", pendientes["pagos"], "fecha_pago"),
        ("RECARGA_ALMUERZO", pendientes["recargas_almuerzo"], "fecha_carga"),
        ("VENTA", pendientes["ventas"], "fecha"),
        ("PAGO_CREDITO", pendientes["pagos_credito"], "fecha"),
    ]

    por_cliente: dict = {}
    for tipo, queryset, campo_fecha in fuentes:
        for item in queryset:
            fecha_item = getattr(item, campo_fecha)
            if fecha_item > fecha_corte:
                continue
            cliente = _cliente_de(item, tipo)
            if not cliente or cliente.modalidad_facturacion != "MENSUAL":
                continue
            por_cliente.setdefault(cliente, {"cantidad": 0, "fecha_mas_antigua": fecha_item})
            por_cliente[cliente]["cantidad"] += 1
            if fecha_item < por_cliente[cliente]["fecha_mas_antigua"]:
                por_cliente[cliente]["fecha_mas_antigua"] = fecha_item

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    alertados = 0
    for cliente, info in por_cliente.items():
        dias = (timezone.now() - info["fecha_mas_antigua"]).days
        msg = (
            f"{cliente.nombre_completo} (facturación mensual) tiene "
            f"{info['cantidad']} ítem(s) sin facturar, el más antiguo con {dias} días."
        )
        for admin in admins:
            Notificacion.objects.create(
                usuario=admin,
                tipo=Notificacion.Tipo.SISTEMA,
                titulo=f"Facturación mensual pendiente: {cliente.nombre_completo}",
                mensaje=msg,
                destino=Notificacion.Destino.SISTEMA,
            )
        alertados += 1

    logger.info(
        "recordar_facturacion_mensual_pendiente: %d clientes con facturación mensual atrasada",
        alertados,
    )
    return {"clientes_alertados": alertados}
