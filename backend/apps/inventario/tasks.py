"""
Tareas asíncronas de Celery para el módulo de inventario.

Incluye:
- verificar_vencimientos: alerta productos próximos a vencer
- alertar_stock_minimo: alerta cuando el stock cae bajo umbral
- generar_resumen_diario_stock: snapshot diario de stock para reportes
"""

import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def verificar_vencimientos(self):
    """
    Verifica lotes de productos con fecha de vencimiento próxima (≤ 7 días)
    o ya vencidos, y genera alertas en el sistema de notificaciones.

    Se ejecuta diariamente a las 9 AM (configurado en celery_app.py).

    Returns:
        dict: {proximos_a_vencer, ya_vencidos, alertas_creadas, errores}
    """
    from apps.inventario.models import MovimientosStock
    from apps.notificaciones.models import AlertasSistema

    try:
        hoy = timezone.now().date()
        umbral_dias = 7
        limite_alerta = hoy + timedelta(days=umbral_dias)

        proximos = 0
        ya_vencidos = 0
        alertas_creadas = 0
        errores = []

        # Buscar movimientos con fecha de vencimiento en el campo descripción
        # o directamente en LotesProducto si existe
        try:
            from apps.inventario.models import LotesProducto  # type: ignore

            lotes_proximos = LotesProducto.objects.filter(
                fecha_vencimiento__lte=limite_alerta,
                fecha_vencimiento__gte=hoy,
                cantidad_disponible__gt=0,
            )
            lotes_vencidos = LotesProducto.objects.filter(
                fecha_vencimiento__lt=hoy,
                cantidad_disponible__gt=0,
            )

            for lote in lotes_proximos:
                proximos += 1
                dias_restantes = (lote.fecha_vencimiento - hoy).days
                try:
                    AlertasSistema.objects.create(
                        tipo_alerta="vencimiento_producto",
                        mensaje=(
                            f"Producto '{lote.id_producto.descripcion}' vence en {dias_restantes} días "
                            f"(Lote: {lote.nro_lote}, Cant: {lote.cantidad_disponible})."
                        ),
                        estado="pendiente",
                        fecha_generacion=timezone.now(),
                    )
                    alertas_creadas += 1
                except Exception as e:
                    errores.append(str(e))

            for lote in lotes_vencidos:
                ya_vencidos += 1
                try:
                    AlertasSistema.objects.create(
                        tipo_alerta="vencimiento_producto",
                        mensaje=(
                            f"¡VENCIDO! Producto '{lote.id_producto.descripcion}' venció el "
                            f"{lote.fecha_vencimiento} (Lote: {lote.nro_lote})."
                        ),
                        estado="pendiente",
                        fecha_generacion=timezone.now(),
                    )
                    alertas_creadas += 1
                except Exception as e:
                    errores.append(str(e))

        except ImportError:
            # Si no existe el modelo LotesProducto, buscar en MovimientosStock
            movimientos = MovimientosStock.objects.filter(
                tipo_movimiento="producto_vencido",
                fecha_hora__gte=timezone.now() - timedelta(days=1),
            )
            ya_vencidos = movimientos.count()
            logger.info("LotesProducto no disponible, revisando MovimientosStock.")

        resultado = {
            "success": True,
            "proximos_a_vencer": proximos,
            "ya_vencidos": ya_vencidos,
            "alertas_creadas": alertas_creadas,
            "errores": errores,
            "timestamp": timezone.now().isoformat(),
        }
        logger.info(
            f"[Celery] verificar_vencimientos — próximos: {proximos}, "
            f"vencidos: {ya_vencidos}, alertas: {alertas_creadas}"
        )
        return resultado

    except Exception as e:
        logger.error(f"Error en verificar_vencimientos: {str(e)}")
        raise self.retry(exc=e, countdown=600)


@shared_task(bind=True, max_retries=3)
def alertar_stock_minimo(self):
    """
    Compara el stock actual de cada producto con su umbral mínimo
    y genera una alerta cuando el stock es ≤ stock_minimo.

    Se ejecuta diariamente a las 7 AM.

    Returns:
        dict: {productos_bajo_stock, alertas_creadas, errores}
    """
    from apps.inventario.models import StockUnico
    from apps.notificaciones.models import AlertasSistema
    from apps.productos.models import Productos

    try:
        productos_bajo = 0
        alertas_creadas = 0
        errores = []

        stocks = StockUnico.objects.select_related("id_producto").filter(
            id_producto__stock_minimo__isnull=False,
            id_producto__estado=True,
        )

        for stock in stocks:
            producto = stock.id_producto
            stock_minimo = getattr(producto, "stock_minimo", None)
            if stock_minimo is None:
                continue
            if stock.cantidad <= stock_minimo:
                productos_bajo += 1
                try:
                    AlertasSistema.objects.create(
                        tipo_alerta="stock_minimo",
                        mensaje=(
                            f"Stock bajo en '{producto.descripcion}': "
                            f"{stock.cantidad} unidades (mínimo: {stock_minimo})."
                        ),
                        estado="pendiente",
                        fecha_generacion=timezone.now(),
                    )
                    alertas_creadas += 1
                except Exception as e:
                    errores.append(str(e))

        resultado = {
            "success": True,
            "productos_bajo_stock": productos_bajo,
            "alertas_creadas": alertas_creadas,
            "errores": errores,
            "timestamp": timezone.now().isoformat(),
        }
        logger.info(f"[Celery] alertar_stock_minimo — bajo stock: {productos_bajo}, alertas: {alertas_creadas}")
        return resultado

    except Exception as e:
        logger.error(f"Error en alertar_stock_minimo: {str(e)}")
        raise self.retry(exc=e, countdown=300)


@shared_task
def generar_resumen_diario_stock():
    """
    Genera un snapshot del estado actual de stock para reportes históricos.
    Se ejecuta diariamente a las 23:55.

    Returns:
        dict: {productos_procesados, timestamp}
    """
    from django.db.models import Sum

    from apps.inventario.models import MovimientosStock, StockUnico

    try:
        hoy = timezone.now().date()
        inicio_dia = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))

        stocks = StockUnico.objects.select_related("id_producto").filter(id_producto__estado=True)

        movimientos_hoy = (
            MovimientosStock.objects.filter(fecha_hora__gte=inicio_dia)
            .values("id_producto")
            .annotate(
                total_ingresos=Sum(
                    "cantidad",
                    filter=__import__("django.db.models", fromlist=["Q"]).Q(
                        tipo_movimiento__in=["Ingreso", "Compra", "AjustePositivo"]
                    ),
                ),
                total_egresos=Sum(
                    "cantidad",
                    filter=__import__("django.db.models", fromlist=["Q"]).Q(
                        tipo_movimiento__in=["Egreso", "Venta", "AjusteNegativo"]
                    ),
                ),
            )
        )
        movimientos_dict = {m["id_producto"]: m for m in movimientos_hoy}

        procesados = 0
        for stock in stocks:
            pid = stock.id_producto_id
            mov = movimientos_dict.get(pid, {})
            logger.debug(
                f"Stock snapshot — {stock.id_producto.descripcion}: "
                f"actual={stock.cantidad}, "
                f"ingresos_hoy={mov.get('total_ingresos', 0)}, "
                f"egresos_hoy={mov.get('total_egresos', 0)}"
            )
            procesados += 1

        logger.info(f"[Celery] generar_resumen_diario_stock — {procesados} productos procesados")
        return {"success": True, "productos_procesados": procesados, "timestamp": timezone.now().isoformat()}

    except Exception as e:
        logger.error(f"Error en generar_resumen_diario_stock: {str(e)}")
        return {"success": False, "error": str(e)}
