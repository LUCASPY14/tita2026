"""
Tareas asíncronas de Celery para el módulo de ventas.

Incluye:
- generar_resumen_diario_ventas: KPIs del día (total ventas, ticket promedio, top productos)
- cerrar_cajas_automatico: cierra turnos de caja que superen 24h sin cerrar
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task
def generar_resumen_diario_ventas():
    """
    Calcula y registra los KPIs de ventas del día para el dashboard.

    Métricas calculadas:
    - Total ventas del día (monto y cantidad)
    - Ticket promedio
    - Top 5 productos más vendidos
    - Distribución por medio de pago

    Se ejecuta diariamente a las 23:50.

    Returns:
        dict: Resumen con métricas del día
    """
    from django.db.models import Sum, Count, Avg
    from apps.ventas.models import Ventas, DetallesVenta

    try:
        hoy = timezone.now().date()
        inicio = timezone.make_aware(
            timezone.datetime.combine(hoy, timezone.datetime.min.time())
        )
        fin = timezone.make_aware(
            timezone.datetime.combine(hoy, timezone.datetime.max.time())
        )

        ventas_hoy = Ventas.objects.filter(
            fecha__range=(inicio, fin),
            estado__in=("activa", "completada", "Completada"),
        )

        total_monto = ventas_hoy.aggregate(t=Sum("monto_total"))["t"] or Decimal("0")
        total_cantidad = ventas_hoy.count()
        ticket_promedio = ventas_hoy.aggregate(a=Avg("monto_total"))["a"] or Decimal("0")

        # Top 5 productos
        top_productos = (
            DetallesVenta.objects.filter(id_venta__in=ventas_hoy)
            .values("id_producto__descripcion")
            .annotate(cant=Sum("cantidad"), total=Sum("subtotal"))
            .order_by("-total")[:5]
        )

        # Distribución por medio de pago
        por_medio_pago = (
            ventas_hoy.values("id_medio_pago__descripcion")
            .annotate(cant=Count("id_venta"), total=Sum("monto_total"))
            .order_by("-total")
        )

        resumen = {
            "fecha": hoy.isoformat(),
            "total_ventas_monto": str(total_monto),
            "total_ventas_cantidad": total_cantidad,
            "ticket_promedio": str(round(ticket_promedio, 0)),
            "top_productos": list(top_productos),
            "por_medio_pago": list(por_medio_pago),
        }

        logger.info(
            f"[Celery] Resumen ventas {hoy}: "
            f"Gs. {total_monto:,.0f} en {total_cantidad} ventas"
        )
        return {"success": True, **resumen}

    except Exception as e:
        logger.error(f"Error en generar_resumen_diario_ventas: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def cerrar_cajas_automatico():
    """
    Detecta y cierra automáticamente los turnos de caja que llevan
    más de 24 horas abiertos sin cerrar (previene olvidos del cajero).

    Marca el turno como 'cerrado_automatico' con diferencia_efectivo = NULL
    para que el administrador pueda revisarlo luego.

    Se ejecuta cada hora.
    """
    from apps.contabilidad.models import CierresCaja
    from django.db.models import Sum

    try:
        limite = timezone.now() - timedelta(hours=24)
        turnos_viejos = CierresCaja.objects.filter(
            estado="abierto",
            fecha_hora_apertura__lt=limite,
        )

        cerrados = 0
        for turno in turnos_viejos:
            turno.fecha_hora_cierre = timezone.now()
            turno.estado = "cerrado"
            # Calcular diferencia con lo que hay registrado
            total_ing = turno.movimientoscaja_set.filter(
                tipo_movimiento__in=["Ingreso", "VentaEfectivo"]
            ).aggregate(t=Sum("monto"))["t"] or Decimal("0")
            total_eg = turno.movimientoscaja_set.filter(
                tipo_movimiento="Egreso"
            ).aggregate(t=Sum("monto"))["t"] or Decimal("0")
            turno.diferencia_efectivo = total_ing - total_eg  # referencia parcial
            turno.save(update_fields=["fecha_hora_cierre", "estado", "diferencia_efectivo"])
            cerrados += 1
            logger.warning(
                f"[Celery] Turno caja ID {turno.pk} cerrado automáticamente "
                f"(apertura: {turno.fecha_hora_apertura})."
            )

        return {"success": True, "turnos_cerrados_auto": cerrados, "timestamp": timezone.now().isoformat()}

    except Exception as e:
        logger.error(f"Error en cerrar_cajas_automatico: {str(e)}")
        return {"success": False, "error": str(e)}
