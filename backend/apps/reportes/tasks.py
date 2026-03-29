"""
Celery tasks para el módulo de Reportes — KPIs diarios

Tareas programadas:
- calcular_y_guardar_kpis_diarios  →  todos los días 23:45
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Definiciones de los KPIs que se calculan y persisten automáticamente.
# El campo 'nombre_kpi' es la clave única en la tabla KpiMetricas.
KPI_DEFINITIONS = [
    {
        'nombre_kpi': 'ventas_diarias',
        'nombre': 'Ventas del Día',
        'descripcion': 'Monto total vendido en el día',
        'formula': 'SUM(ventas.monto_total) WHERE fecha = HOY',
        'unidad': 'guaranies',
        'categoria': 'ventas',
        'frecuencia': 'diaria',
    },
    {
        'nombre_kpi': 'ticket_promedio',
        'nombre': 'Ticket Promedio',
        'descripcion': 'Monto promedio por venta del día',
        'formula': 'AVG(ventas.monto_total) WHERE fecha = HOY',
        'unidad': 'guaranies',
        'categoria': 'ventas',
        'frecuencia': 'diaria',
    },
    {
        'nombre_kpi': 'recargas_diarias',
        'nombre': 'Recargas del Día',
        'descripcion': 'Monto total de recargas completadas en el día',
        'formula': 'SUM(cargas_saldo.monto_cargado) WHERE fecha = HOY AND estado = completada',
        'unidad': 'guaranies',
        'categoria': 'recargas',
        'frecuencia': 'diaria',
    },
    {
        'nombre_kpi': 'tarjetas_activas',
        'nombre': 'Tarjetas Activas',
        'descripcion': 'Cantidad de tarjetas con estado Activa',
        'formula': 'COUNT(tarjetas) WHERE estado = Activa',
        'unidad': 'unidades',
        'categoria': 'clientes',
        'frecuencia': 'diaria',
    },
]


def _get_or_create_kpi_metricas():
    """
    Asegura que los registros KpiMetricas para cada KPI definido existan.
    Retorna un dict {nombre_kpi: id_kpi}.
    """
    from apps.reportes.models import KpiMetricas

    kpi_ids = {}
    for defn in KPI_DEFINITIONS:
        kpi, _ = KpiMetricas.objects.get_or_create(
            nombre_kpi=defn['nombre_kpi'],
            defaults={
                'nombre': defn['nombre'],
                'descripcion': defn['descripcion'],
                'formula': defn['formula'],
                'unidad': defn['unidad'],
                'unidad_medida': defn['unidad'],
                'categoria': defn['categoria'],
                'frecuencia': defn['frecuencia'],
                'frecuencia_actualizacion': defn['frecuencia'],
                'estado': True,
                'created_at': timezone.now(),
            },
        )
        kpi_ids[defn['nombre_kpi']] = kpi.id_kpi
    return kpi_ids


@shared_task(name='apps.reportes.tasks.calcular_y_guardar_kpis_diarios')
def calcular_y_guardar_kpis_diarios():
    """
    Calcula los KPIs principales del día y los persiste en ValoresKpi.
    Se ejecuta todos los días a las 23:45 para capturar el cierre del día.

    Returns:
        {
            'success': bool,
            'fecha': str,
            'kpis_guardados': int
        }
    """
    from apps.reportes.services.dashboard_service import DashboardService

    fecha_hoy = timezone.localdate()
    logger.info(f"[KPIs] Calculando KPIs para {fecha_hoy}")

    try:
        with transaction.atomic():
            kpi_ids = _get_or_create_kpi_metricas()
            kpis = DashboardService.calcular_kpis_principales(fecha=fecha_hoy)

            # Mapeo: nombre_kpi → valor calculado
            values_map = {
                'ventas_diarias': Decimal(str(kpis.get('ventas_del_dia', '0.00'))),
                'ticket_promedio': Decimal(str(kpis.get('ticket_promedio', '0.00'))),
                'recargas_diarias': Decimal(str(kpis.get('recargas_del_dia', '0.00'))),
                'tarjetas_activas': Decimal(str(kpis.get('tarjetas_activas', 0))),
            }

            saved = 0
            for nombre_kpi, valor in values_map.items():
                id_kpi = kpi_ids.get(nombre_kpi)
                if id_kpi is not None:
                    DashboardService.guardar_valor_kpi(
                        id_kpi=id_kpi,
                        fecha=fecha_hoy,
                        valor=valor,
                        notas=f'Auto-calculado {fecha_hoy}',
                        auto_calc=True,
                    )
                    saved += 1

        logger.info(f"[KPIs] {saved} valores guardados para {fecha_hoy}")
        return {'success': True, 'fecha': str(fecha_hoy), 'kpis_guardados': saved}

    except Exception as e:
        logger.error(f"[KPIs] Error al calcular y guardar KPIs: {e}")
        return {'success': False, 'error': str(e)}
