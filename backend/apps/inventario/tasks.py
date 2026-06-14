import logging
from decimal import Decimal
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
    """Crea AlertaStock para productos cuyo stock está en o por debajo del mínimo."""
    from apps.inventario.models import Stock, AlertaStock

    stocks = Stock.objects.select_related("producto").filter(
        producto__activo=True,
        producto__stock_minimo__gt=0,
    )

    creadas = 0
    for stock in stocks:
        if not stock.requiere_reposicion:
            # Si tenía alerta activa, resolverla
            AlertaStock.objects.filter(
                producto=stock.producto, activa=True
            ).update(activa=False, fecha_resuelta=timezone.now())
            continue

        # Determinar tipo de alerta
        if stock.cantidad <= 0:
            tipo = AlertaStock.TipoAlerta.STOCK_CERO
        elif stock.cantidad <= stock.producto.stock_minimo * Decimal("0.5"):
            tipo = AlertaStock.TipoAlerta.STOCK_CRITICO
        else:
            tipo = AlertaStock.TipoAlerta.STOCK_MINIMO

        # No duplicar alertas activas del mismo tipo
        existe = AlertaStock.objects.filter(
            producto=stock.producto,
            tipo=tipo,
            activa=True,
        ).exists()
        if existe:
            continue

        # Resolver alertas anteriores de tipo diferente
        AlertaStock.objects.filter(
            producto=stock.producto, activa=True
        ).update(activa=False, fecha_resuelta=timezone.now())

        AlertaStock.objects.create(
            producto=stock.producto,
            tipo=tipo,
            stock_actual=stock.cantidad,
            stock_minimo=stock.producto.stock_minimo,
        )
        creadas += 1

    logger.info("alertar_stock_minimo: %d alertas creadas", creadas)
    return {"alertas_creadas": creadas}


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
    from apps.inventario.models import Stock, AlertaStock

    total_productos = Stock.objects.count()
    sin_stock = Stock.objects.filter(cantidad__lte=0).count()
    alertas_activas = AlertaStock.objects.filter(activa=True).count()

    resumen = {
        "fecha": timezone.now().date().isoformat(),
        "total_productos_en_stock": total_productos,
        "productos_sin_stock": sin_stock,
        "alertas_activas": alertas_activas,
    }
    logger.info("Resumen diario stock: %s", resumen)
    return resumen
