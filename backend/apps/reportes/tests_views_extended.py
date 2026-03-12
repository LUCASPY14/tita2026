"""
Extended tests for apps/reportes/views.py to cover missing exception and
success paths.

Missing lines targeted:
- 109: reporte_ventas success with id_empleado conversion
- 118: reporte_ventas except 500
- 134-135: reporte_recargas invalid date 400
- 152: reporte_recargas success 200
- 161: reporte_recargas except 500
- 174-175: reporte_top_productos invalid date 400
- 202: reporte_top_productos success 200 / except 500
- 212-213: reporte_top_productos except 500
- 229: reporte_consumos_tarjeta success 200
- 238: reporte_consumos_tarjeta except 500
- 248-249: reporte_financiero success / except 500
- 267-268: kpis_principales success / except 500
- 286-287: dashboard_ventas success / except 500
- 305-306: dashboard_recargas success / except 500
- 330-331: dashboard_financiero invalid mes 400 / except 500
- 344: dashboard_financiero success 200
- 348: dashboard_financiero except 500
- 352: PlantillasReporteViewSet.ejecutar
- 361: PlantillasReporteViewSet.preview
- 370: PlantillasReporteViewSet.validar_sql
- 379: DashboardsViewSet.exportar
- 383: DashboardsViewSet.widget_datos
- 387: KpiMetricasViewSet.calcular
- 396: KpiMetricasViewSet.historial
- 400: KpiMetricasViewSet.dashboard_summary
- 404: PlantillasTareaViewSet.ejecutar
- 413: PlantillasTareaViewSet.ejecuciones
- 417: PlantillasTareaViewSet.toggle_activo
- 423: EjecucionesTareaViewSet.cancelar
- 429: EjecucionesTareaViewSet.logs
"""

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

from apps.reportes.models import (
    PlantillasReporte,
    Dashboards,
    KpiMetricas,
    PlantillasTarea,
    EjecucionesTarea,
)


class BaseReportesExtTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reports_ext", password="testpass"
        )
        self.client.force_authenticate(user=self.user)


# ─────────────────────────────────────────────────────────────
# reporte_ventas
# ─────────────────────────────────────────────────────────────

class ReportesVentasBranchTest(BaseReportesExtTest):
    """Cover the branch where fecha_inicio is valid but fecha_fin is invalid (line 109 branch)."""

    def test_reporte_ventas_fecha_fin_invalida_400(self):
        """fecha_inicio valid but fecha_fin invalid → 400 (line 109 branch)."""
        url = reverse("reportes-reporte-ventas")
        response = self.client.get(
            url, {"fecha_inicio": "2026-01-01", "fecha_fin": "not-a-date"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReportesRecargasBranchTest(BaseReportesExtTest):
    """Cover missing params and branch checks in recargas endpoint."""

    def test_recargas_missing_params_400(self):
        """Missing fecha params → 400 (line 109 in recargas endpoint)."""
        url = reverse("reportes-reporte-recargas")
        # missing fecha_fin
        response = self.client.get(url, {"fecha_inicio": "2026-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recargas_fecha_fin_invalida_400(self):
        """fecha_inicio valid but fecha_fin invalid → 400."""
        url = reverse("reportes-reporte-recargas")
        response = self.client.get(
            url, {"fecha_inicio": "2026-01-01", "fecha_fin": "not-a-date"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReportesTopProductosBranchTest(BaseReportesExtTest):
    """Cover missing params check in top_productos endpoint (line 152)."""

    def test_top_productos_missing_params_400(self):
        """Missing fecha params → 400 (line 152 in top_productos endpoint)."""
        url = reverse("reportes-reporte-top-productos")
        # missing fecha_fin
        response = self.client.get(url, {"fecha_inicio": "2026-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReportesFinancieroBranchTest(BaseReportesExtTest):
    """Cover missing params check in consumos_tarjeta and financiero endpoints (line 229)."""

    def test_consumos_missing_params_400(self):
        """Missing fecha params in consumos → 400 (line 229 area)."""
        url = reverse("reportes-reporte-consumos-tarjeta")
        response = self.client.get(url, {"nro_tarjeta": "1234", "fecha_inicio": "2026-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_financiero_missing_fecha_fin_400(self):
        """Missing fecha_fin in financiero → 400 (line 229)."""
        url = reverse("reportes-reporte-financiero")
        response = self.client.get(url, {"fecha_inicio": "2026-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_financiero_fecha_fin_invalida_400(self):
        """fecha_inicio valid but fecha_fin invalid → 400 (line 229 branch)."""
        url = reverse("reportes-reporte-financiero")
        response = self.client.get(
            url, {"fecha_inicio": "2026-01-01", "fecha_fin": "not-a-date"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReportesVentasTest(BaseReportesExtTest):

    def test_reporte_ventas_success_with_id_empleado(self):
        """id_empleado int conversion + success 200 (line 109)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_ventas",
            return_value={"resultado": "ok"},
        ):
            url = reverse("reportes-reporte-ventas")
            response = self.client.get(
                url,
                {
                    "fecha_inicio": "2026-01-01",
                    "fecha_fin": "2026-01-31",
                    "id_empleado": "42",
                },
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reporte_ventas_exception_500(self):
        """except Exception returns 500 (line 118)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_ventas",
            side_effect=Exception("internal error"),
        ):
            url = reverse("reportes-reporte-ventas")
            response = self.client.get(
                url,
                {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"},
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# reporte_recargas
# ─────────────────────────────────────────────────────────────

class ReportesRecargasTest(BaseReportesExtTest):

    def test_recargas_fecha_invalida_400(self):
        """Invalid date → 400 (lines 134-135)."""
        url = reverse("reportes-reporte-recargas")
        response = self.client.get(
            url, {"fecha_inicio": "not-a-date", "fecha_fin": "2026-01-31"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recargas_success_200(self):
        """Success path 200 (line 152)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_recargas",
            return_value={"total": 0},
        ):
            url = reverse("reportes-reporte-recargas")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recargas_exception_500(self):
        """except Exception 500 (line 161)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_recargas",
            side_effect=Exception("recargas error"),
        ):
            url = reverse("reportes-reporte-recargas")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# reporte_top_productos
# ─────────────────────────────────────────────────────────────

class ReportesTopProductosTest(BaseReportesExtTest):

    def test_top_productos_fecha_invalida_400(self):
        """Invalid fecha → 400 (lines 174-175)."""
        url = reverse("reportes-reporte-top-productos")
        response = self.client.get(
            url, {"fecha_inicio": "bad", "fecha_fin": "2026-01-31"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_productos_success_200(self):
        """Success 200 (line 202)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_top_productos",
            return_value={"productos": []},
        ):
            url = reverse("reportes-reporte-top-productos")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_top_productos_exception_500(self):
        """except Exception 500 (lines 212-213)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_top_productos",
            side_effect=Exception("top productos error"),
        ):
            url = reverse("reportes-reporte-top-productos")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# reporte_consumos_tarjeta
# ─────────────────────────────────────────────────────────────

class ReportesConsumosTarjetaTest(BaseReportesExtTest):

    def test_consumos_fecha_invalida_400(self):
        """Invalid fecha → 400."""
        url = reverse("reportes-reporte-consumos-tarjeta")
        response = self.client.get(
            url,
            {
                "nro_tarjeta": "1234",
                "fecha_inicio": "bad",
                "fecha_fin": "2026-01-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consumos_success_200(self):
        """Success 200 (line 229)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_consumos_tarjeta",
            return_value={"consumos": []},
        ):
            url = reverse("reportes-reporte-consumos-tarjeta")
            response = self.client.get(
                url,
                {
                    "nro_tarjeta": "1234",
                    "fecha_inicio": "2026-01-01",
                    "fecha_fin": "2026-01-31",
                },
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consumos_exception_500(self):
        """except Exception 500 (lines 212-213)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_consumos_tarjeta",
            side_effect=Exception("consumos error"),
        ):
            url = reverse("reportes-reporte-consumos-tarjeta")
            response = self.client.get(
                url,
                {
                    "nro_tarjeta": "1234",
                    "fecha_inicio": "2026-01-01",
                    "fecha_fin": "2026-01-31",
                },
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# reporte_financiero
# ─────────────────────────────────────────────────────────────

class ReportesFinancieroTest(BaseReportesExtTest):

    def test_financiero_fecha_invalida_400(self):
        """Invalid fecha → 400."""
        url = reverse("reportes-reporte-financiero")
        response = self.client.get(
            url, {"fecha_inicio": "bad", "fecha_fin": "2026-01-31"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_financiero_success_200(self):
        """Success 200 (line 248-249)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_financiero",
            return_value={"ingresos": 0},
        ):
            url = reverse("reportes-reporte-financiero")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_financiero_exception_500(self):
        """except Exception 500 (line 229)."""
        with patch(
            "apps.reportes.services.ReporteService.generar_reporte_financiero",
            side_effect=Exception("financiero error"),
        ):
            url = reverse("reportes-reporte-financiero")
            response = self.client.get(
                url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31"}
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# kpis_principales
# ─────────────────────────────────────────────────────────────

class KpisPrincipalesTest(BaseReportesExtTest):

    def test_kpis_success_200(self):
        """Success 200 with fecha param (lines 267-268)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.calcular_kpis_principales",
            return_value={"kpis": []},
        ):
            url = reverse("reportes-kpis-principales")
            response = self.client.get(url, {"fecha": "2026-01-01"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_kpis_exception_500(self):
        """except Exception 500 (line 238)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.calcular_kpis_principales",
            side_effect=Exception("kpis error"),
        ):
            url = reverse("reportes-kpis-principales")
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# dashboard_ventas
# ─────────────────────────────────────────────────────────────

class DashboardVentasTest(BaseReportesExtTest):

    def test_dashboard_ventas_success_200(self):
        """Success 200 (lines 286-287)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_ventas",
            return_value={"tendencia": "estable"},
        ):
            url = reverse("reportes-dashboard-ventas")
            response = self.client.get(url, {"dias": "7"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_ventas_exception_500(self):
        """except Exception 500 (lines 305-306)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_ventas",
            side_effect=Exception("dashboard ventas error"),
        ):
            url = reverse("reportes-dashboard-ventas")
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# dashboard_recargas
# ─────────────────────────────────────────────────────────────

class DashboardRecargasTest(BaseReportesExtTest):

    def test_dashboard_recargas_success_200(self):
        """Success 200 (lines 330-331)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_recargas",
            return_value={"tasa_exito": 0},
        ):
            url = reverse("reportes-dashboard-recargas")
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_recargas_exception_500(self):
        """except Exception 500."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_recargas",
            side_effect=Exception("dashboard recargas error"),
        ):
            url = reverse("reportes-dashboard-recargas")
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# dashboard_financiero
# ─────────────────────────────────────────────────────────────

class DashboardFinancieroTest(BaseReportesExtTest):

    def test_dashboard_financiero_mes_invalido_400(self):
        """mes > 12 → 400 (line 344)."""
        url = reverse("reportes-dashboard-financiero")
        response = self.client.get(url, {"mes": "13"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_financiero_mes_cero_400(self):
        """mes < 1 → 400 (line 344)."""
        url = reverse("reportes-dashboard-financiero")
        response = self.client.get(url, {"mes": "0"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_financiero_success_200(self):
        """Success 200 (line 348)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_financiero",
            return_value={"financiero": {}},
        ):
            url = reverse("reportes-dashboard-financiero")
            response = self.client.get(url, {"mes": "6"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_financiero_exception_500(self):
        """except Exception 500 (line 352)."""
        with patch(
            "apps.reportes.services.dashboard_service.DashboardService.obtener_dashboard_financiero",
            side_effect=Exception("dashboard financiero error"),
        ):
            url = reverse("reportes-dashboard-financiero")
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# CRUD ViewSet action methods
# ─────────────────────────────────────────────────────────────

class PlantillasReporteActionsTest(BaseReportesExtTest):

    def setUp(self):
        super().setUp()
        from django.utils import timezone
        self.plantilla = PlantillasReporte.objects.create(
            nombre="Test Plantilla",
            tipo_reporte="ventas",
            frecuencia="diaria",
            query_sql="SELECT 1",
            parametros={},
            created_at=timezone.now(),
            activo=True,
        )

    def test_ejecutar(self):
        """POST ejecutar action (line ~387)."""
        url = reverse(
            "plantillas-reporte-ejecutar", kwargs={"pk": self.plantilla.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_preview(self):
        """GET preview action (line ~396)."""
        url = reverse(
            "plantillas-reporte-preview", kwargs={"pk": self.plantilla.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validar_sql(self):
        """POST validar_sql action (line ~400)."""
        url = reverse(
            "plantillas-reporte-validar-sql", kwargs={"pk": self.plantilla.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardsActionsTest(BaseReportesExtTest):

    def setUp(self):
        super().setUp()
        from apps.usuarios.models import Roles, Empleados
        rol, _ = Roles.objects.get_or_create(nombre_rol="TestDashboardRol")
        empleado, _ = Empleados.objects.get_or_create(
            usuario="dashboard_test_emp",
            defaults={
                "nombre": "Dashboard",
                "apellido": "Tester",
                "contrasena_hash": "x" * 60,
                "fecha_ingreso": timezone.now(),
                "id_rol": rol,
            },
        )
        self.dashboard = Dashboards.objects.create(
            nombre="Test Dashboard",
            descripcion="Test",
            configuracion={},
            es_publico=0,
            predeterminado=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=empleado,
            activo=True,
        )

    def test_exportar_get(self):
        """GET exportar action (line ~404)."""
        url = reverse("dashboards-exportar", kwargs={"pk": self.dashboard.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_exportar_post(self):
        """POST exportar action."""
        url = reverse("dashboards-exportar", kwargs={"pk": self.dashboard.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_widget_datos(self):
        """GET widget_datos action (line ~413)."""
        url = reverse(
            "dashboards-widget-datos",
            kwargs={"pk": self.dashboard.pk, "widget_id": "widget_test"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class KpiMetricasActionsTest(BaseReportesExtTest):

    def setUp(self):
        super().setUp()
        self.kpi = KpiMetricas.objects.create(
            nombre="Test KPI",
            nombre_kpi="test_kpi",
            descripcion="Test",
            categoria="ventas",
            activo=True,
        )

    def test_calcular(self):
        """POST calcular action (line ~417)."""
        url = reverse("kpi-metricas-calcular", kwargs={"pk": self.kpi.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_historial(self):
        """GET historial action (line ~423)."""
        url = reverse("kpi-metricas-historial", kwargs={"pk": self.kpi.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_summary(self):
        """GET dashboard_summary action (line ~429)."""
        url = reverse("kpi-metricas-dashboard-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PlantillasTareaActionsTest(BaseReportesExtTest):

    def setUp(self):
        super().setUp()
        self.tarea = PlantillasTarea.objects.create(
            nombre="Test Tarea",
            created_at=timezone.now(),
        )

    def test_ejecutar(self):
        """POST ejecutar action (line ~361)."""
        url = reverse(
            "plantillas-tarea-ejecutar", kwargs={"pk": self.tarea.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ejecuciones(self):
        """GET ejecuciones action (line ~370)."""
        url = reverse(
            "plantillas-tarea-ejecuciones", kwargs={"pk": self.tarea.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_toggle_activo(self):
        """POST toggle_activo action (line ~379)."""
        url = reverse(
            "plantillas-tarea-toggle-activo", kwargs={"pk": self.tarea.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EjecucionesTareaActionsTest(BaseReportesExtTest):

    def setUp(self):
        super().setUp()
        self.tarea = PlantillasTarea.objects.create(
            nombre="Test Tarea",
            created_at=timezone.now(),
        )
        self.ejecucion = EjecucionesTarea.objects.create(
            id_plantilla=self.tarea,
            estado="pendiente",
            fecha_inicio=timezone.now(),
        )

    def test_cancelar(self):
        """POST cancelar action (line ~352 area)."""
        url = reverse(
            "ejecuciones-tarea-cancelar", kwargs={"pk": self.ejecucion.pk}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logs(self):
        """GET logs action."""
        url = reverse(
            "ejecuciones-tarea-logs", kwargs={"pk": self.ejecucion.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReportesUtilViewsTest(BaseReportesExtTest):

    def test_reportes_util_view_get(self):
        """GET reportes_util_view (line ~423 area)."""
        url = reverse("reportes-validar-cron")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reportes_util_view_post(self):
        """POST reportes_util_view."""
        url = reverse("reportes-validar-cron")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reportes_export_view_get(self):
        """GET reportes_export_view (line ~429 area)."""
        url = reverse("reportes-exportar-reporte", kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
