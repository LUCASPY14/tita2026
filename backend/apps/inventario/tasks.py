import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.inventario.tasks.alertar_stock_minimo",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_stock_minimo():
    """
    Detecta productos con stock en o por debajo del mínimo (mismo cálculo
    en vivo que usa la pantalla de Inventario) y crea notificaciones
    internas para los usuarios ADMIN.
    """
    from apps.inventario.services import StockService
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    productos_bajo = StockService.calcular_alertas_stock()
    if not productos_bajo:
        logger.info("alertar_stock_minimo: sin productos bajo el mínimo")
        return {"alertas_creadas": 0}

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    if not admins:
        logger.warning("alertar_stock_minimo: no hay usuarios ADMIN activos")
        return {"alertas_creadas": 0}

    detalle = "\n".join(
        f"- {a['producto_nombre']}: {a['stock_actual']} (mínimo {a['stock_minimo']})"
        for a in productos_bajo
    )
    alertas = 0
    for admin in admins:
        Notificacion.objects.create(
            usuario=admin,
            tipo=Notificacion.Tipo.SISTEMA,
            titulo=f"{len(productos_bajo)} producto(s) bajo el stock mínimo",
            mensaje=f"Los siguientes productos requieren reposición:\n{detalle}",
            destino=Notificacion.Destino.SISTEMA,
        )
        alertas += 1

    logger.info(
        "alertar_stock_minimo: %d alertas creadas para %d productos bajo mínimo",
        alertas, len(productos_bajo),
    )
    return {"alertas_creadas": alertas}


@shared_task(
    name="apps.inventario.tasks.verificar_vencimientos",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def verificar_vencimientos():
    """Crea AlertaVencimiento para lotes próximos a vencer o ya vencidos."""
    from apps.inventario.models import LoteProducto, AlertaVencimiento

    hoy = timezone.now().date()
    umbrales = [
        (30, AlertaVencimiento.TipoAlerta.DIAS_30),
        (15, AlertaVencimiento.TipoAlerta.DIAS_15),
        (7,  AlertaVencimiento.TipoAlerta.DIAS_7),
        (3,  AlertaVencimiento.TipoAlerta.DIAS_3),
    ]

    lotes = LoteProducto.objects.filter(
        bloqueado=False,
        cantidad_disponible__gt=0,
        fecha_vencimiento__lte=hoy + timedelta(days=30),
    ).select_related("producto")

    creadas = 0
    for lote in lotes:
        dias = (lote.fecha_vencimiento - hoy).days

        if dias < 0:
            tipo = AlertaVencimiento.TipoAlerta.VENCIDO
        else:
            tipo = next((t for d, t in umbrales if dias <= d), None)
            if not tipo:
                continue

        existe = AlertaVencimiento.objects.filter(
            lote=lote,
            tipo=tipo,
        ).exists()
        if existe:
            continue

        AlertaVencimiento.objects.create(
            lote=lote,
            tipo=tipo,
            dias_restantes=dias,
            fecha_vencimiento=lote.fecha_vencimiento,
            cantidad_lote=lote.cantidad_disponible,
        )
        creadas += 1

    logger.info("verificar_vencimientos: %d alertas de vencimiento creadas", creadas)
    return {"alertas_creadas": creadas}


@shared_task(
    name="apps.inventario.tasks.generar_resumen_diario_stock",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def generar_resumen_diario_stock():
    """Registra en log un resumen del estado del stock al cierre del día."""
    from apps.inventario.models import Stock
    from apps.inventario.services import StockService

    total_productos = Stock.objects.count()
    sin_stock = Stock.objects.filter(cantidad__lte=0).count()
    alertas_activas = len(StockService.calcular_alertas_stock())

    resumen = {
        "fecha": timezone.now().date().isoformat(),
        "total_productos_en_stock": total_productos,
        "productos_sin_stock": sin_stock,
        "alertas_activas": alertas_activas,
    }
    logger.info("Resumen diario stock: %s", resumen)
    return resumen
