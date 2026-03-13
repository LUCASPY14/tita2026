"""
Extended tests for apps/reportes/services/__init__.py

Covers missing lines:
- Line 84: metodo_pago filter branch in generar_reporte_ventas
- Lines 157-159: except block in generar_reporte_ventas
- Lines 240-242: except block in generar_reporte_recargas
- Lines 304-306: except block in generar_reporte_top_productos
- Lines 381-383: except block in generar_reporte_consumos_tarjeta
- Lines 475-477: except block in generar_reporte_financiero
"""

from datetime import date
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.reportes.services import ReporteService


class ReporteVentasMetodoPagoTest(TestCase):
    """Cover line 84: metodo_pago optional filter branch."""

    def test_generar_reporte_ventas_con_metodo_pago(self):
        """When metodo_pago is provided, the filter branch is hit (line 84)."""
        today = date.today()
        # Just needs to execute without error — DB may return empty results
        result = ReporteService.generar_reporte_ventas(today, today, metodo_pago="efectivo")
        self.assertIn("total_ventas", result)

    def test_generar_reporte_ventas_con_id_empleado(self):
        """When id_empleado is provided, that filter branch executes too."""
        today = date.today()
        result = ReporteService.generar_reporte_ventas(today, today, id_empleado=9999)
        self.assertIn("total_ventas", result)


class ReporteVentasExcepcionTest(TestCase):
    """Cover lines 157-159: except block in generar_reporte_ventas."""

    @patch("apps.reportes.services.Ventas")
    def test_generar_reporte_ventas_exception_raises_validation_error(self, MockVentas):
        """If the DB query raises, ValidationError is raised (lines 157-159)."""
        MockVentas.objects.filter.side_effect = Exception("DB connection failed")
        today = date.today()
        with self.assertRaises(ValidationError):
            ReporteService.generar_reporte_ventas(today, today)


class ReporteRecargasExcepcionTest(TestCase):
    """Cover lines 240-242: except block in generar_reporte_recargas."""

    @patch("apps.reportes.services.CargasSaldo")
    def test_generar_reporte_recargas_exception_raises_validation_error(self, MockCS):
        """If the DB query raises, ValidationError is raised (lines 240-242)."""
        MockCS.objects.filter.side_effect = Exception("DB error")
        today = date.today()
        with self.assertRaises(ValidationError):
            ReporteService.generar_reporte_recargas(today, today)

    def test_generar_reporte_recargas_con_metodo_pago(self):
        """Cover metodo_pago and estado filter branches in recargas."""
        today = date.today()
        result = ReporteService.generar_reporte_recargas(today, today, metodo_pago="efectivo", estado="completada")
        self.assertIn("total_recargas", result)


class ReporteTopProductosExcepcionTest(TestCase):
    """Cover lines 304-306: except block in generar_reporte_top_productos."""

    @patch("apps.reportes.services.DetallesVenta")
    def test_generar_reporte_top_productos_exception_raises_validation_error(self, MockDV):
        """If the DB query raises, ValidationError is raised (lines 304-306)."""
        MockDV.objects.filter.side_effect = Exception("DB error")
        today = date.today()
        with self.assertRaises(ValidationError):
            ReporteService.generar_reporte_top_productos(today, today)


class ReporteConsumosExcepcionTest(TestCase):
    """Cover lines 381-383: except block in generar_reporte_consumos_tarjeta."""

    @patch("apps.reportes.services.Tarjetas")
    def test_generar_reporte_consumos_exception_raises_validation_error(self, MockTarjetas):
        """If the DB query raises (not DoesNotExist), ValidationError is raised (lines 381-383)."""
        MockTarjetas.objects.select_related.return_value.get.side_effect = Exception("DB error")
        today = date.today()
        with self.assertRaises(ValidationError):
            ReporteService.generar_reporte_consumos_tarjeta("0001", today, today)


class ReporteFinancieroExcepcionTest(TestCase):
    """Cover lines 475-477: except block in generar_reporte_financiero."""

    @patch("apps.reportes.services.Ventas")
    def test_generar_reporte_financiero_exception_raises_validation_error(self, MockVentas):
        """If the DB query raises, ValidationError is raised (lines 475-477)."""
        MockVentas.objects.filter.side_effect = Exception("DB error")
        today = date.today()
        with self.assertRaises(ValidationError):
            ReporteService.generar_reporte_financiero(today, today)
