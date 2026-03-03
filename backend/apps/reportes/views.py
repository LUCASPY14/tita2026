"""
ViewSets para app de Reportes

Endpoints disponibles:
- /api/v1/reportes/ventas/
- /api/v1/reportes/recargas/
- /api/v1/reportes/top-productos/
- /api/v1/reportes/consumos-tarjeta/
- /api/v1/reportes/financiero/
- /api/v1/reportes/kpis-principales/
- /api/v1/reportes/dashboard-ventas/
- /api/v1/reportes/dashboard-recargas/
- /api/v1/reportes/dashboard-financiero/
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date, datetime
from django.utils.dateparse import parse_date

from .services import ReporteService
from .services.dashboard_service import DashboardService


class ReportesViewSet(viewsets.ViewSet):
    """
    ViewSet para manejo de reportes y estadísticas.
    
    Proporciona endpoints para:
    - Reportes de ventas, recargas, productos, consumos, financiero
    - Dashboards y KPIs en tiempo real
    - Exportación de reportes (futuro)
    """
    
    @action(detail=False, methods=['get'], url_path='ventas')
    def reporte_ventas(self, request):
        """
        GET /api/v1/reportes/ventas/
        
        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        - metodo_pago (optional): efectivo|tarjeta|online
        - id_empleado (optional): int
        """
        try:
            # Validar parámetros requeridos
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            
            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {'error': 'Parámetros fecha_inicio y fecha_fin son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parsear fechas
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parámetros opcionales
            metodo_pago = request.query_params.get('metodo_pago')
            id_empleado = request.query_params.get('id_empleado')
            if id_empleado:
                id_empleado = int(id_empleado)
            
            # Generar reporte
            reporte = ReporteService.generar_reporte_ventas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                id_empleado=id_empleado
            )
            
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='recargas')
    def reporte_recargas(self, request):
        """
        GET /api/v1/reportes/recargas/
        
        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        - metodo_pago (optional): string
        - estado (optional): string
        """
        try:
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            
            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {'error': 'Parámetros fecha_inicio y fecha_fin son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                return Response(
                    {'error': 'Formato de fecha inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            metodo_pago = request.query_params.get('metodo_pago')
            estado = request.query_params.get('estado')
            
            reporte = ReporteService.generar_reporte_recargas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                estado=estado
            )
            
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='top-productos')
    def reporte_top_productos(self, request):
        """
        GET /api/v1/reportes/top-productos/
        
        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        - limite (optional): int (default 20)
        """
        try:
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            
            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {'error': 'Parámetros fecha_inicio y fecha_fin son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                return Response(
                    {'error': 'Formato de fecha inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            limite = request.query_params.get('limite', 20)
            limite = int(limite)
            
            reporte = ReporteService.generar_reporte_top_productos(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limite=limite
            )
            
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='consumos-tarjeta')
    def reporte_consumos_tarjeta(self, request):
        """
        GET /api/v1/reportes/consumos-tarjeta/
        
        Parámetros:
        - nro_tarjeta (required): string
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        """
        try:
            nro_tarjeta = request.query_params.get('nro_tarjeta')
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            
            if not all([nro_tarjeta, fecha_inicio_str, fecha_fin_str]):
                return Response(
                    {'error': 'Parámetros nro_tarjeta, fecha_inicio y fecha_fin son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                return Response(
                    {'error': 'Formato de fecha inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reporte = ReporteService.generar_reporte_consumos_tarjeta(
                nro_tarjeta=nro_tarjeta,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='financiero')
    def reporte_financiero(self, request):
        """
        GET /api/v1/reportes/financiero/
        
        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        """
        try:
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')
            
            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {'error': 'Parámetros fecha_inicio y fecha_fin son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                return Response(
                    {'error': 'Formato de fecha inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reporte = ReporteService.generar_reporte_financiero(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='kpis-principales')
    def kpis_principales(self, request):
        """
        GET /api/v1/reportes/kpis-principales/
        
        Parámetros:
        - fecha (optional): YYYY-MM-DD (default: hoy)
        """
        try:
            fecha_str = request.query_params.get('fecha')
            fecha = parse_date(fecha_str) if fecha_str else None
            
            kpis = DashboardService.calcular_kpis_principales(fecha=fecha)
            
            return Response(kpis, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='dashboard-ventas')
    def dashboard_ventas(self, request):
        """
        GET /api/v1/reportes/dashboard-ventas/
        
        Parámetros:
        - dias (optional): int (default 7)
        """
        try:
            dias = request.query_params.get('dias', 7)
            dias = int(dias)
            
            dashboard = DashboardService.obtener_dashboard_ventas(dias=dias)
            
            return Response(dashboard, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='dashboard-recargas')
    def dashboard_recargas(self, request):
        """
        GET /api/v1/reportes/dashboard-recargas/
        
        Parámetros:
        - dias (optional): int (default 7)
        """
        try:
            dias = request.query_params.get('dias', 7)
            dias = int(dias)
            
            dashboard = DashboardService.obtener_dashboard_recargas(dias=dias)
            
            return Response(dashboard, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='dashboard-financiero')
    def dashboard_financiero(self, request):
        """
        GET /api/v1/reportes/dashboard-financiero/
        
        Parámetros:
        - mes (optional): int 1-12 (default: mes actual)
        """
        try:
            mes = request.query_params.get('mes')
            if mes:
                mes = int(mes)
                if mes < 1 or mes > 12:
                    return Response(
                        {'error': 'El mes debe estar entre 1 y 12'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            dashboard = DashboardService.obtener_dashboard_financiero(mes=mes)
            
            return Response(dashboard, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

