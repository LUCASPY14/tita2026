"""
Tests para apps.reportes.tasks — calcular_y_guardar_kpis_diarios
"""

from decimal import Decimal
from unittest.mock import MagicMock, call, patch

from django.test import TestCase


class CalcularKpisDiariosTest(TestCase):
    """Tests para la tarea Celery calcular_y_guardar_kpis_diarios."""

    @patch("apps.reportes.tasks._get_or_create_kpi_metricas")
    @patch("apps.reportes.services.dashboard_service.DashboardService.guardar_valor_kpi")
    @patch("apps.reportes.services.dashboard_service.DashboardService.calcular_kpis_principales")
    def test_retorna_success_true(self, mock_calcular, mock_guardar, mock_get_kpis):
        """La tarea retorna success=True cuando todo funciona correctamente."""
        from apps.reportes.tasks import calcular_y_guardar_kpis_diarios

        mock_get_kpis.return_value = {
            "ventas_diarias": 1,
            "ticket_promedio": 2,
            "recargas_diarias": 3,
            "tarjetas_activas": 4,
        }
        mock_calcular.return_value = {
            "ventas_del_dia": Decimal("150000.00"),
            "ticket_promedio": Decimal("7500.00"),
            "recargas_del_dia": Decimal("80000.00"),
            "tarjetas_activas": 42,
        }
        mock_guardar.return_value = {"success": True, "id_valor": 1, "created": True}

        result = calcular_y_guardar_kpis_diarios()

        self.assertTrue(result["success"])
        self.assertIn("fecha", result)
        self.assertEqual(result["kpis_guardados"], 4)

    @patch("apps.reportes.tasks._get_or_create_kpi_metricas")
    def test_retorna_success_false_ante_error(self, mock_get_kpis):
        """La tarea retorna success=False si ocurre una excepción."""
        from apps.reportes.tasks import calcular_y_guardar_kpis_diarios

        mock_get_kpis.side_effect = Exception("DB error")

        result = calcular_y_guardar_kpis_diarios()

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("apps.reportes.models.KpiMetricas")
    def test_get_or_create_kpi_metricas_crea_definiciones(self, mock_kpi_class):
        """_get_or_create_kpi_metricas llama get_or_create por cada definición."""
        from apps.reportes.tasks import KPI_DEFINITIONS, _get_or_create_kpi_metricas

        mock_kpi = MagicMock()
        mock_kpi.id_kpi = 99
        mock_kpi_class.objects.get_or_create.return_value = (mock_kpi, True)

        result = _get_or_create_kpi_metricas()

        self.assertEqual(mock_kpi_class.objects.get_or_create.call_count, len(KPI_DEFINITIONS))
        self.assertEqual(len(result), len(KPI_DEFINITIONS))
        # Each value should be the id_kpi from the mock
        for val in result.values():
            self.assertEqual(val, 99)

    def test_kpi_definitions_tienen_campos_requeridos(self):
        """Cada entrada en KPI_DEFINITIONS tiene los campos mínimos requeridos."""
        from apps.reportes.tasks import KPI_DEFINITIONS

        required_fields = {"nombre_kpi", "nombre", "descripcion", "categoria", "frecuencia"}
        for defn in KPI_DEFINITIONS:
            for field in required_fields:
                self.assertIn(field, defn, f"Falta '{field}' en {defn.get('nombre_kpi')}")

    def test_kpi_definitions_nombres_kpi_son_unicos(self):
        """Los nombre_kpi en KPI_DEFINITIONS son únicos."""
        from apps.reportes.tasks import KPI_DEFINITIONS

        nombres = [d["nombre_kpi"] for d in KPI_DEFINITIONS]
        self.assertEqual(len(nombres), len(set(nombres)), "Nombres KPI duplicados")
