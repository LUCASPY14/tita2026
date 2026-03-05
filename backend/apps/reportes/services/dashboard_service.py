"""
Service Layer para Dashboards y KPIs

Este módulo contiene la lógica para:
- Cálculo de KPIs en tiempo real
- Dashboards personalizados
- Métricas de rendimiento
- Gráficos y visualizaciones

Autor: Cantina Tita Development Team
Fecha: Marzo 2026
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

from apps.core.models import CargasSaldo, ConsumosTarjeta, Tarjetas
from apps.ventas.models import Ventas
from apps.productos.models import Productos
from apps.inventario.models import StockUnico
from apps.reportes.models import KpiMetricas, ValoresKpi, Dashboards


logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service Layer para dashboards y KPIs.
    
    Métodos principales:
    - calcular_kpis_principales()
    - obtener_dashboard_ventas()
    - obtener_dashboard_recargas()
    - obtener_dashboard_financiero()
    - calcular_kpi_individual()
    - guardar_valor_kpi()
    """
    
    @staticmethod
    def calcular_kpis_principales(fecha: Optional[date] = None) -> Dict:
        """
        Calcula los KPIs principales del negocio.
        
        KPIs incluidos:
        - Ventas del día
        - Recargas del día
        - Tarjetas activas
        - Productos bajo stock
        - Ticket promedio
        - Tasa de conversión
        
        Args:
            fecha: Fecha para calcular (default: hoy)
        
        Returns:
            {
                'fecha': date,
                'ventas_del_dia': Decimal,
                'cantidad_ventas': int,
                'recargas_del_dia': Decimal,
                'cantidad_recargas': int,
                'tarjetas_activas': int,
                'productos_bajo_stock': int,
                'ticket_promedio': Decimal,
                'saldo_total_tarjetas': Decimal
            }
        """
        try:
            if not fecha:
                fecha = date.today()
            
            # Ventas del día
            ventas_stats = Ventas.objects.filter(
                fecha_venta__date=fecha
            ).aggregate(
                total_ventas=Sum('total'),
                cantidad_ventas=Count('id_venta'),
                ticket_promedio=Avg('total')
            )
            
            # Recargas del día
            recargas_stats = CargasSaldo.objects.filter(
                fecha_carga__date=fecha,
                estado='completada'
            ).aggregate(
                total_recargas=Sum('monto_cargado'),
                cantidad_recargas=Count('id_recarga')
            )
            
            # Tarjetas activas
            tarjetas_activas = Tarjetas.objects.filter(
                estado='Activa'
            ).count()
            
            # Productos bajo stock
            productos_bajo_stock = StockUnico.objects.filter(
                cantidad__lte=F('id_producto__cantidad_minima')
            ).count()
            
            # Saldo total en tarjetas (dinero circulante)
            saldo_total = Tarjetas.objects.filter(
                estado='Activa'
            ).aggregate(
                saldo_total=Sum('saldo_actual')
            )['saldo_total'] or Decimal('0.00')
            
            return {
                'fecha': fecha,
                'ventas_del_dia': ventas_stats['total_ventas'] or Decimal('0.00'),
                'cantidad_ventas': ventas_stats['cantidad_ventas'] or 0,
                'recargas_del_dia': recargas_stats['total_recargas'] or Decimal('0.00'),
                'cantidad_recargas': recargas_stats['cantidad_recargas'] or 0,
                'tarjetas_activas': tarjetas_activas,
                'productos_bajo_stock': productos_bajo_stock,
                'ticket_promedio': ventas_stats['ticket_promedio'] or Decimal('0.00'),
                'saldo_total_tarjetas': saldo_total
            }
            
        except Exception as e:
            logger.error(f"Error calculando KPIs principales: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
    
    
    @staticmethod
    def obtener_dashboard_ventas(dias: int = 7) -> Dict:
        """
        Obtiene dashboard de ventas de últimos N días.
        
        Args:
            dias: Cantidad de días a analizar
        
        Returns:
            {
                'ventas_por_dia': List[Dict],
                'ventas_por_metodo_pago': List[Dict],
                'productos_mas_vendidos': List[Dict],
                'comparacion_semana_anterior': Dict,
                'tendencia': str  # 'crecimiento' | 'decrecimiento' | 'estable'
            }
        """
        try:
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=dias)
            
            # Ventas por día
            ventas_por_dia = Ventas.objects.filter(
                fecha_venta__gte=fecha_inicio,
                fecha_venta__lte=fecha_fin
            ).extra(
                select={'fecha': 'DATE(fecha_venta)'}
            ).values('fecha').annotate(
                cantidad_ventas=Count('id_venta'),
                total_vendido=Sum('total'),
                ticket_promedio=Avg('total')
            ).order_by('fecha')
            
            # Ventas por método de pago
            ventas_por_metodo = Ventas.objects.filter(
                fecha_venta__gte=fecha_inicio,
                fecha_venta__lte=fecha_fin
            ).values('metodo_pago').annotate(
                cantidad=Count('id_venta'),
                total=Sum('total')
            )
            
            # Productos más vendidos
            from apps.ventas.models import DetallesVenta
            
            productos_mas_vendidos = DetallesVenta.objects.filter(
                id_venta__fecha_venta__gte=fecha_inicio,
                id_venta__fecha_venta__lte=fecha_fin
            ).values(
                'id_producto__nombre',
                'id_producto__codigo'
            ).annotate(
                cantidad_vendida=Sum('cantidad'),
                total_vendido=Sum(F('cantidad') * F('precio_unitario'))
            ).order_by('-cantidad_vendida')[:10]
            
            # Comparación con semana anterior
            fecha_inicio_anterior = fecha_inicio - timedelta(days=dias)
            fecha_fin_anterior = fecha_inicio - timedelta(days=1)
            
            ventas_periodo_actual = Ventas.objects.filter(
                fecha_venta__gte=fecha_inicio,
                fecha_venta__lte=fecha_fin
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            ventas_periodo_anterior = Ventas.objects.filter(
                fecha_venta__gte=fecha_inicio_anterior,
                fecha_venta__lte=fecha_fin_anterior
            ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            
            # Calcular tendencia
            if ventas_periodo_anterior > 0:
                variacion = ((ventas_periodo_actual - ventas_periodo_anterior) / ventas_periodo_anterior) * 100
            else:
                variacion = Decimal('0.00')
            
            if variacion > 5:
                tendencia = 'crecimiento'
            elif variacion < -5:
                tendencia = 'decrecimiento'
            else:
                tendencia = 'estable'
            
            return {
                'periodo': f'Últimos {dias} días',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ventas_por_dia': list(ventas_por_dia),
                'ventas_por_metodo_pago': list(ventas_por_metodo),
                'productos_mas_vendidos': list(productos_mas_vendidos),
                'comparacion_semana_anterior': {
                    'periodo_actual': ventas_periodo_actual,
                    'periodo_anterior': ventas_periodo_anterior,
                    'variacion_porcentual': variacion
                },
                'tendencia': tendencia
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard ventas: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
    
    
    @staticmethod
    def obtener_dashboard_recargas(dias: int = 7) -> Dict:
        """
        Obtiene dashboard de recargas.
        
        Args:
            dias: Cantidad de días a analizar
        
        Returns:
            {
                'recargas_por_dia': List[Dict],
                'recargas_por_metodo': List[Dict],
                'comisiones_generadas': Decimal,
                'tasa_exito': Decimal,
                'tiempo_promedio_procesamiento': Decimal
            }
        """
        try:
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=dias)
            
            # Recargas por día
            recargas_por_dia = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin
            ).extra(
                select={'fecha': 'DATE(fecha_carga)'}
            ).values('fecha').annotate(
                cantidad_recargas=Count('id_recarga'),
                monto_total=Sum('monto_cargado'),
                comision_total=Sum('comision')
            ).order_by('fecha')
            
            # Recargas por método
            recargas_por_metodo = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin
            ).values('metodo_pago').annotate(
                cantidad=Count('id_recarga'),
                monto_total=Sum('monto_cargado'),
                comision_total=Sum('comision')
            )
            
            # Comisiones generadas
            comisiones_total = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin,
                estado='completada'
            ).aggregate(
                total_comisiones=Sum('comision')
            )['total_comisiones'] or Decimal('0.00')
            
            # Tasa de éxito
            total_recargas = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin
            ).count()
            
            recargas_exitosas = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin,
                estado='completada'
            ).count()
            
            tasa_exito = (
                (recargas_exitosas / total_recargas * 100) 
                if total_recargas > 0 
                else Decimal('0.00')
            )
            
            return {
                'periodo': f'Últimos {dias} días',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'recargas_por_dia': list(recargas_por_dia),
                'recargas_por_metodo': list(recargas_por_metodo),
                'comisiones_generadas': comisiones_total,
                'total_recargas': total_recargas,
                'recargas_exitosas': recargas_exitosas,
                'tasa_exito': tasa_exito
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard recargas: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
    
    
    @staticmethod
    def obtener_dashboard_financiero(mes: Optional[int] = None) -> Dict:
        """
        Obtiene dashboard financiero mensual.
        
        Args:
            mes: Mes a analizar (1-12). Default: mes actual
        
        Returns:
            {
                'ingresos_totales': Decimal,
                'ingresos_ventas': Decimal,
                'ingresos_comisiones': Decimal,
                'gastos_estimados': Decimal,
                'margen_neto': Decimal,
                'proyeccion_fin_mes': Decimal
            }
        """
        try:
            hoy = date.today()
            
            if not mes:
                mes = hoy.month
            
            # Primer y último día del mes
            fecha_inicio = date(hoy.year, mes, 1)
            
            if mes == 12:
                fecha_fin = date(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                fecha_fin = date(hoy.year, mes + 1, 1) - timedelta(days=1)
            
            # Ingresos por ventas
            ingresos_ventas = Ventas.objects.filter(
                fecha_venta__gte=fecha_inicio,
                fecha_venta__lte=fecha_fin
            ).aggregate(
                total=Sum('total')
            )['total'] or Decimal('0.00')
            
            # Ingresos por comisiones
            ingresos_comisiones = CargasSaldo.objects.filter(
                fecha_carga__gte=fecha_inicio,
                fecha_carga__lte=fecha_fin,
                estado='completada'
            ).aggregate(
                total=Sum('comision')
            )['total'] or Decimal('0.00')
            
            # Ingresos totales
            ingresos_totales = ingresos_ventas + ingresos_comisiones
            
            # Gastos estimados (aquí puedes implementar lógica real)
            gastos_estimados = Decimal('0.00')
            
            # Margen neto
            margen_neto = ingresos_totales - gastos_estimados
            
            # Proyección fin de mes
            dias_transcurridos = (hoy - fecha_inicio).days + 1
            dias_totales = (fecha_fin - fecha_inicio).days + 1
            
            if dias_transcurridos > 0:
                ingreso_promedio_diario = ingresos_totales / dias_transcurridos
                proyeccion_fin_mes = ingreso_promedio_diario * dias_totales
            else:
                proyeccion_fin_mes = Decimal('0.00')
            
            return {
                'mes': mes,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ingresos_totales': ingresos_totales,
                'ingresos_ventas': ingresos_ventas,
                'ingresos_comisiones': ingresos_comisiones,
                'gastos_estimados': gastos_estimados,
                'margen_neto': margen_neto,
                'proyeccion_fin_mes': proyeccion_fin_mes,
                'dias_transcurridos': dias_transcurridos,
                'dias_totales': dias_totales
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard financiero: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
    
    
    @staticmethod
    def guardar_valor_kpi(
        id_kpi: int,
        fecha: date,
        valor: Decimal,
        notas: Optional[str] = None,
        auto_calc: bool = True
    ) -> Dict:
        """
        Guarda valor de KPI en la base de datos.
        
        Args:
            id_kpi: ID del KPI
            fecha: Fecha del valor
            valor: Valor del KPI
            notas: Notas opcionales
            auto_calc: Si fue calculado automáticamente
        
        Returns:
            {
                'success': bool,
                'id_valor': int
            }
        """
        try:
            # Verificar que el KPI existe
            kpi = KpiMetricas.objects.get(id_kpi=id_kpi)
            
            # Crear o actualizar valor
            valor_kpi, created = ValoresKpi.objects.update_or_create(
                id_kpi=kpi,
                fecha=fecha,
                defaults={
                    'valor': valor,
                    'notas': notas,
                    'auto_calc': 1 if auto_calc else 0,
                    'created_at': timezone.now()
                }
            )
            
            return {
                'success': True,
                'id_valor': valor_kpi.id_valor,
                'created': created
            }
            
        except KpiMetricas.DoesNotExist:
            raise ValidationError(f"KPI {id_kpi} no existe")
        
        except Exception as e:
            logger.error(f"Error guardando valor KPI: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
