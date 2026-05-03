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

from datetime import date, datetime

from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Dashboards, EjecucionesTarea, KpiMetricas, PlantillasReporte, PlantillasTarea
from .serializers import (
    DashboardsSerializer,
    EjecucionesTareaSerializer,
    KpiMetricasSerializer,
    PlantillasReporteSerializer,
    PlantillasTareaSerializer,
)
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

    @action(detail=False, methods=["get"], url_path="ventas")
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
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {"error": "Parámetros fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Parsear fechas
            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response(
                    {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Parámetros opcionales
            metodo_pago = request.query_params.get("metodo_pago")
            id_empleado = request.query_params.get("id_empleado")
            if id_empleado:
                id_empleado = int(id_empleado)

            # Generar reporte
            reporte = ReporteService.generar_reporte_ventas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                id_empleado=id_empleado,
            )

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="recargas")
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
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {"error": "Parámetros fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response({"error": "Formato de fecha inválido"}, status=status.HTTP_400_BAD_REQUEST)

            metodo_pago = request.query_params.get("metodo_pago")
            estado = request.query_params.get("estado")

            reporte = ReporteService.generar_reporte_recargas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                metodo_pago=metodo_pago,
                estado=estado,
            )

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="top-productos")
    def reporte_top_productos(self, request):
        """
        GET /api/v1/reportes/top-productos/

        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        - limite (optional): int (default 20)
        """
        try:
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {"error": "Parámetros fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response({"error": "Formato de fecha inválido"}, status=status.HTTP_400_BAD_REQUEST)

            limite = request.query_params.get("limite", 20)
            limite = int(limite)

            reporte = ReporteService.generar_reporte_top_productos(
                fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=limite
            )

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="consumos-tarjeta")
    def reporte_consumos_tarjeta(self, request):
        """
        GET /api/v1/reportes/consumos-tarjeta/

        Parámetros:
        - nro_tarjeta (required): string
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        """
        try:
            nro_tarjeta = request.query_params.get("nro_tarjeta")
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not all([nro_tarjeta, fecha_inicio_str, fecha_fin_str]):
                return Response(
                    {"error": "Parámetros nro_tarjeta, fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response({"error": "Formato de fecha inválido"}, status=status.HTTP_400_BAD_REQUEST)

            reporte = ReporteService.generar_reporte_consumos_tarjeta(
                nro_tarjeta=nro_tarjeta, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            )

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="consumos-hijo")
    def reporte_consumos_hijo(self, request):
        """
        GET /api/v1/reportes/consumos-hijo/

        Parámetros:
        - id_hijo (required): int
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        """
        try:
            id_hijo_str = request.query_params.get("id_hijo")
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not all([id_hijo_str, fecha_inicio_str, fecha_fin_str]):
                return Response(
                    {"error": "Parámetros id_hijo, fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                id_hijo = int(id_hijo_str)
            except ValueError:
                return Response(
                    {"error": "id_hijo debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response(
                    {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reporte = ReporteService.generar_reporte_consumos_hijo(
                id_hijo=id_hijo, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            )

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="financiero")
    def reporte_financiero(self, request):
        """
        GET /api/v1/reportes/financiero/

        Parámetros:
        - fecha_inicio (required): YYYY-MM-DD
        - fecha_fin (required): YYYY-MM-DD
        """
        try:
            fecha_inicio_str = request.query_params.get("fecha_inicio")
            fecha_fin_str = request.query_params.get("fecha_fin")

            if not fecha_inicio_str or not fecha_fin_str:
                return Response(
                    {"error": "Parámetros fecha_inicio y fecha_fin son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_inicio = parse_date(fecha_inicio_str)
            fecha_fin = parse_date(fecha_fin_str)

            if not fecha_inicio or not fecha_fin:
                return Response({"error": "Formato de fecha inválido"}, status=status.HTTP_400_BAD_REQUEST)

            reporte = ReporteService.generar_reporte_financiero(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

            return Response(reporte, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="kpis-principales")
    def kpis_principales(self, request):
        """
        GET /api/v1/reportes/kpis-principales/

        Parámetros:
        - fecha (optional): YYYY-MM-DD (default: hoy)
        """
        try:
            fecha_str = request.query_params.get("fecha")
            fecha = parse_date(fecha_str) if fecha_str else None

            kpis = DashboardService.calcular_kpis_principales(fecha=fecha)

            return Response(kpis, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="dashboard-ventas")
    def dashboard_ventas(self, request):
        """
        GET /api/v1/reportes/dashboard-ventas/

        Parámetros:
        - dias (optional): int (default 7)
        """
        try:
            dias = request.query_params.get("dias", 7)
            dias = int(dias)

            dashboard = DashboardService.obtener_dashboard_ventas(dias=dias)

            return Response(dashboard, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="dashboard-recargas")
    def dashboard_recargas(self, request):
        """
        GET /api/v1/reportes/dashboard-recargas/

        Parámetros:
        - dias (optional): int (default 7)
        """
        try:
            dias = request.query_params.get("dias", 7)
            dias = int(dias)

            dashboard = DashboardService.obtener_dashboard_recargas(dias=dias)

            return Response(dashboard, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="dashboard-financiero")
    def dashboard_financiero(self, request):
        """
        GET /api/v1/reportes/dashboard-financiero/

        Parámetros:
        - mes (optional): int 1-12 (default: mes actual)
        """
        try:
            mes = request.query_params.get("mes")
            if mes:
                mes = int(mes)
                if mes < 1 or mes > 12:
                    return Response(
                        {"error": "El mes debe estar entre 1 y 12"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            dashboard = DashboardService.obtener_dashboard_financiero(mes=mes)

            return Response(dashboard, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
# CRUD ViewSets for reportes models
# ──────────────────────────────────────────────────────────────────────────────


class PlantillasReporteViewSet(ModelViewSet):
    queryset = PlantillasReporte.objects.all()
    serializer_class = PlantillasReporteSerializer

    @action(detail=True, methods=["post"], url_path="ejecutar", url_name="ejecutar")
    def ejecutar(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["get"], url_path="preview", url_name="preview")
    def preview(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["post"], url_path="validar_sql", url_name="validar-sql")
    def validar_sql(self, request, pk=None):
        return Response({"status": "ok"})


class DashboardsViewSet(ModelViewSet):
    queryset = Dashboards.objects.all().order_by("id_dashboard")
    serializer_class = DashboardsSerializer

    @action(detail=True, methods=["get", "post"], url_path="exportar", url_name="exportar")
    def exportar(self, request, pk=None):
        return Response({"status": "ok"})

    @action(
        detail=True,
        methods=["get"],
        url_path=r"widget/(?P<widget_id>[^/]+)/datos",
        url_name="widget-datos",
    )
    def widget_datos(self, request, pk=None, widget_id=None):
        return Response({"widget_id": widget_id})


class KpiMetricasViewSet(ModelViewSet):
    queryset = KpiMetricas.objects.all()
    serializer_class = KpiMetricasSerializer

    @action(detail=True, methods=["post"], url_path="calcular", url_name="calcular")
    def calcular(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["get"], url_path="historial", url_name="historial")
    def historial(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=False, methods=["get"], url_path="dashboard_summary", url_name="dashboard-summary")
    def dashboard_summary(self, request):
        return Response({"status": "ok"})


class PlantillasTareaViewSet(ModelViewSet):
    queryset = PlantillasTarea.objects.all()
    serializer_class = PlantillasTareaSerializer

    @action(detail=True, methods=["post"], url_path="ejecutar", url_name="ejecutar")
    def ejecutar(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["get"], url_path="ejecuciones", url_name="ejecuciones")
    def ejecuciones(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["post"], url_path="toggle_activo", url_name="toggle-estado")
    def toggle_activo(self, request, pk=None):
        return Response({"status": "ok"})


class EjecucionesTareaViewSet(ModelViewSet):
    queryset = EjecucionesTarea.objects.all()
    serializer_class = EjecucionesTareaSerializer

    @action(detail=True, methods=["post"], url_path="cancelar", url_name="cancelar")
    def cancelar(self, request, pk=None):
        return Response({"status": "ok"})

    @action(detail=True, methods=["get"], url_path="logs", url_name="logs")
    def logs(self, request, pk=None):
        return Response({"status": "ok"})


@api_view(["GET", "POST"])
def reportes_util_view(request, **kwargs):
    """Stub view para endpoints de utilidades de reportes."""
    return Response({"status": "ok"})


@api_view(["GET", "POST"])
def reportes_export_view(request, **kwargs):
    """Stub view para endpoints de exportación de reportes."""
    return Response({"status": "ok"})


class TareasProgradasViewSet(viewsets.ViewSet):
    """
    ViewSet para ver y modificar las tareas programadas de Celery Beat.
    Solo permite listar, activar/desactivar y cambiar el horario (crontab).
    """

    from rest_framework.permissions import IsAuthenticated

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET /tareas-programadas/ — lista todas las tareas con su crontab."""
        try:
            from django_celery_beat.models import PeriodicTask

            tasks = PeriodicTask.objects.select_related("crontab").order_by("name")
            data = []
            for t in tasks:
                cron = t.crontab
                data.append(
                    {
                        "id": t.id,
                        "name": t.name,
                        "task": t.task,
                        "enabled": t.enabled,
                        "last_run_at": t.last_run_at,
                        "total_run_count": t.total_run_count,
                        "crontab": (
                            {
                                "id": cron.id if cron else None,
                                "minute": cron.minute if cron else "*",
                                "hour": cron.hour if cron else "*",
                                "day_of_week": cron.day_of_week if cron else "*",
                                "day_of_month": cron.day_of_month if cron else "*",
                                "month_of_year": cron.month_of_year if cron else "*",
                            }
                            if cron
                            else None
                        ),
                    }
                )
            return Response(data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, pk=None):
        """
        PATCH /tareas-programadas/{id}/ — activa/desactiva o modifica el crontab.
        Payload: { enabled: bool } o { minute, hour, day_of_week, day_of_month, month_of_year }
        """
        try:
            from django_celery_beat.models import CrontabSchedule, PeriodicTask

            task = PeriodicTask.objects.get(pk=pk)

            if "enabled" in request.data:
                task.enabled = bool(request.data["enabled"])
                task.save(update_fields=["enabled"])

            cron_fields = {"minute", "hour", "day_of_week", "day_of_month", "month_of_year"}
            if cron_fields & set(request.data.keys()):
                cron = task.crontab
                if cron:
                    for field in cron_fields:
                        if field in request.data:
                            setattr(cron, field, str(request.data[field]))
                    cron.save()

            return Response({"status": "ok", "id": task.id, "enabled": task.enabled})
        except PeriodicTask.DoesNotExist:
            return Response({"detail": "Tarea no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
