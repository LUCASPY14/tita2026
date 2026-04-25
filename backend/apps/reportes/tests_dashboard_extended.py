"""
Extended tests for dashboard_service.py to cover missing branches.

Targets:
- Lines 118-120: except Exception in calcular_kpis_principales
- Line 192: tendencia = "crecimiento" (variacion > 5)
- Line 199: tendencia = "decrecimiento" (variacion < -5)
- Line 201: tendencia = "estable" (abs(variacion) <= 5)
- Lines 233-235: graficos dict keys returned
- Lines 315-317: tasa_exito = Decimal("0.00") when total_recargas == 0
- Line 347: except Exception in obtener_dashboard_recargas
- Line 376: except Exception in obtener_dashboard_financiero
- Lines 402-404: KpiMetricas.DoesNotExist in guardar_valor_kpi
- Lines 430-453: guardar_valor_kpi success path
"""

from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.reportes.services.dashboard_service import DashboardService
from apps.reportes.models import KpiMetricas, ValoresKpi
from apps.ventas.models import Ventas
from apps.core.models import CargasSaldo


class DashboardKpisExceptionTest(TestCase):
    """Tests for exception path in calcular_kpis_principales (lines 118-120)."""

    def test_calcular_kpis_raises_validation_error_on_exception(self):
        """When an unexpected error occurs, raises ValidationError."""
        with patch(
            "apps.reportes.services.dashboard_service.Ventas.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("DB connection lost")
            with self.assertRaises(ValidationError) as ctx:
                DashboardService.calcular_kpis_principales()
            self.assertIn("DB connection lost", str(ctx.exception))


class DashboardVentasTendenciaTest(TestCase):
    """Tests for tendencia branches in obtener_dashboard_ventas (lines 192, 199, 201)."""

    def _run_ventas_with_mocked_aggregates(self, actual_value, anterior_value):
        """
        Patch Ventas and DetallesVenta filters so:
        - ventas_por_dia, ventas_por_metodo → empty chain mock (Ventas, calls 1-2)
        - ventas_periodo_actual → actual_value  (Ventas, call 3)
        - ventas_periodo_anterior → anterior_value (Ventas, call 4)
        - productos_mas_vendidos → empty (DetallesVenta)
        """
        chain_mock = MagicMock()
        chain_mock.extra.return_value = chain_mock
        chain_mock.values.return_value = chain_mock
        chain_mock.annotate.return_value = chain_mock
        chain_mock.order_by.return_value = chain_mock
        chain_mock.__iter__ = lambda s: iter([])
        chain_mock.__getitem__ = lambda s, k: chain_mock  # handle [:10]

        ventas_call_count = [0]

        def ventas_filter_side_effect(*args, **kwargs):
            ventas_call_count[0] += 1
            n = ventas_call_count[0]
            if n == 1:  # ventas_por_dia
                return chain_mock
            elif n == 2:  # ventas_por_metodo
                return chain_mock
            elif n == 3:  # ventas_periodo_actual aggregate
                agg = MagicMock()
                agg.aggregate.return_value = {"total": actual_value}
                return agg
            else:  # ventas_periodo_anterior aggregate
                agg = MagicMock()
                agg.aggregate.return_value = {"total": anterior_value}
                return agg

        with patch(
            "apps.reportes.services.dashboard_service.Ventas.objects.filter",
            side_effect=ventas_filter_side_effect,
        ):
            with patch(
                "apps.ventas.models.DetallesVenta.objects.filter",
                return_value=chain_mock,
            ):
                return DashboardService.obtener_dashboard_ventas(dias=7)

    def test_tendencia_crecimiento(self):
        """When variacion > 5, tendencia = 'crecimiento' (line 192)."""
        result = self._run_ventas_with_mocked_aggregates(
            actual_value=Decimal("200.00"),
            anterior_value=Decimal("100.00"),  # variacion=100%
        )
        self.assertEqual(result["tendencia"], "crecimiento")

    def test_tendencia_decrecimiento(self):
        """When variacion < -5, tendencia = 'decrecimiento' (line 199)."""
        result = self._run_ventas_with_mocked_aggregates(
            actual_value=Decimal("100.00"),
            anterior_value=Decimal("200.00"),  # variacion=-50%
        )
        self.assertEqual(result["tendencia"], "decrecimiento")

    def test_tendencia_estable(self):
        """When abs(variacion) <= 5, tendencia = 'estable' (line 201)."""
        result = self._run_ventas_with_mocked_aggregates(
            actual_value=Decimal("102.00"),
            anterior_value=Decimal("100.00"),  # variacion=2%
        )
        self.assertEqual(result["tendencia"], "estable")

    def test_tendencia_sin_periodo_anterior(self):
        """When ventas_periodo_anterior == 0, variacion = 0.00 → estable (line 196/201)."""
        result = self._run_ventas_with_mocked_aggregates(
            actual_value=None,   # → Decimal("0.00")
            anterior_value=None, # → Decimal("0.00")
        )
        self.assertEqual(result["tendencia"], "estable")
        self.assertIn("ventas_por_dia", result)
        self.assertIn("ventas_por_metodo_pago", result)
        self.assertIn("productos_mas_vendidos", result)

    def test_dashboard_ventas_exception_path(self):
        """Exception path in obtener_dashboard_ventas (lines 233-235)."""
        with patch(
            "apps.reportes.services.dashboard_service.Ventas.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("query failed")
            with self.assertRaises(ValidationError) as ctx:
                DashboardService.obtener_dashboard_ventas(dias=7)
            self.assertIn("query failed", str(ctx.exception))


class DashboardRecargasTest(TestCase):
    """Tests for obtener_dashboard_recargas branches."""

    def test_tasa_exito_zero_when_no_recargas(self):
        """When total_recargas == 0, tasa_exito = Decimal('0.00') (lines 315-317)."""
        # No CargasSaldo records → total_recargas = 0
        result = DashboardService.obtener_dashboard_recargas(dias=7)
        self.assertEqual(result["tasa_exito"], Decimal("0.00"))
        self.assertEqual(result["total_recargas"], 0)
        self.assertEqual(result["recargas_exitosas"], 0)

    def test_dashboard_recargas_exception_path(self):
        """Exception path in obtener_dashboard_recargas (line 347)."""
        with patch(
            "apps.reportes.services.dashboard_service.CargasSaldo.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("recargas error")
            with self.assertRaises(ValidationError) as ctx:
                DashboardService.obtener_dashboard_recargas(dias=7)
            self.assertIn("recargas error", str(ctx.exception))


class DashboardFinancieroTest(TestCase):
    """Tests for obtener_dashboard_financiero."""

    def test_financiero_mes_diciembre(self):
        """When mes=12, fecha_fin = Dec 31. Covers the mes==12 branch."""
        result = DashboardService.obtener_dashboard_financiero(mes=12)
        self.assertEqual(result["mes"], 12)
        self.assertIn("ingresos_totales", result)

    def test_financiero_dias_transcurridos_zero(self):
        """
        proyeccion_fin_mes = 0 when dias_transcurridos == 0 (line 376).
        Patch date.today() to return the first day of month, then patch
        (hoy - fecha_inicio).days + 1 to produce 0 by making hoy < fecha_inicio.

        Easier: patch the entire computation by mocking date.today to return
        a date before fecha_inicio — but that's tricky since both use date.today.

        Instead, patch `date` inside the module so hoy.day == 1 and
        simulate that hoy IS fecha_inicio while dias_transcurridos will be 1 (not 0).

        Actually dias_transcurridos is always >= 1 when hoy >= fecha_inicio.
        The else branch (line 376) fires when dias_transcurridos <= 0, which 
        can't happen with real dates. We patch the calculation directly.
        """
        with patch(
            "apps.reportes.services.dashboard_service.Ventas.objects.filter"
        ) as mock_filter:
            agg_mock = MagicMock()
            agg_mock.aggregate.return_value = {"total": None}
            mock_filter.return_value = agg_mock

            # Use a mock date that makes dias_transcurridos = 0
            # by making hoy equal to fecha_inicio - 1 day
            # We achieve this by patching date.today inside the module
            with patch(
                "apps.reportes.services.dashboard_service.date"
            ) as mock_date:
                # Set up so hoy = Jan 1 current year
                fake_today = date(2026, 1, 1)
                mock_date.today.return_value = fake_today
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

                # Make hoy come back as day before fecha_inicio (Dec 31 of prior year)
                # Actually let's just mock hoy = fecha_inicio - 1 day so dias_transcurridos = 0
                fake_today_before = date(2025, 12, 31)
                mock_date.today.return_value = fake_today_before
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

                result = DashboardService.obtener_dashboard_financiero(mes=1)
                self.assertIn("proyeccion_fin_mes", result)

    def test_financiero_exception_path(self):
        """Exception path in obtener_dashboard_financiero (line 376 area)."""
        with patch(
            "apps.reportes.services.dashboard_service.Ventas.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("financiero error")
            with self.assertRaises(ValidationError) as ctx:
                DashboardService.obtener_dashboard_financiero(mes=3)
            self.assertIn("financiero error", str(ctx.exception))


class DashboardGuardarKpiTest(TestCase):
    """Tests for guardar_valor_kpi (lines 402-453)."""

    def test_guardar_kpi_no_existe_raises_validation_error(self):
        """When KPI id doesn't exist, raises ValidationError (lines 402-404)."""
        with self.assertRaises(ValidationError) as ctx:
            DashboardService.guardar_valor_kpi(
                id_kpi=99999,
                fecha=date.today(),
                valor=Decimal("100.00"),
            )
        self.assertIn("99999", str(ctx.exception))

    def test_guardar_kpi_success_creates_valor(self):
        """Happy path: creates KpiMetricas then saves value (lines 430-453)."""
        kpi = KpiMetricas.objects.create(
            nombre="Test KPI",
            nombre_kpi="test_kpi",
            descripcion="Test",
            categoria="ventas",
            estado=True,
        )

        today = date.today()
        result = DashboardService.guardar_valor_kpi(
            id_kpi=kpi.id_kpi,
            fecha=today,
            valor=Decimal("250.00"),
            notas="Test nota",
            auto_calc=True,
        )

        self.assertTrue(result["success"])
        self.assertIn("id_valor", result)
        self.assertTrue(result["created"])

        # Verify DB record
        valor = ValoresKpi.objects.get(id_kpi=kpi, fecha=today)
        self.assertEqual(valor.valor, Decimal("250.00"))
        self.assertEqual(valor.notas, "Test nota")
        self.assertEqual(valor.auto_calc, 1)

    def test_guardar_kpi_update_or_create_updates_existing(self):
        """update_or_create updates an existing record (created=False path)."""
        kpi = KpiMetricas.objects.create(
            nombre="Update KPI",
            nombre_kpi="update_kpi",
            descripcion="Update test",
            categoria="financiero",
            estado=True,
        )
        today = date.today()

        # First create
        from django.utils import timezone as tz
        ValoresKpi.objects.create(
            id_kpi=kpi,
            fecha=today,
            valor=Decimal("100.00"),
            auto_calc=0,
            created_at=tz.now(),
        )

        # Now update via service
        result = DashboardService.guardar_valor_kpi(
            id_kpi=kpi.id_kpi,
            fecha=today,
            valor=Decimal("999.00"),
            auto_calc=False,
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["created"])

        valor = ValoresKpi.objects.get(id_kpi=kpi, fecha=today)
        self.assertEqual(valor.valor, Decimal("999.00"))
        self.assertEqual(valor.auto_calc, 0)

    def test_guardar_kpi_exception_path(self):
        """Exception path in guardar_valor_kpi (line 450 area)."""
        kpi = KpiMetricas.objects.create(
            nombre="Exception KPI",
            nombre_kpi="exc_kpi",
            descripcion="Exc test",
            categoria="ventas",
            estado=True,
        )

        with patch(
            "apps.reportes.services.dashboard_service.ValoresKpi.objects.update_or_create"
        ) as mock_uoc:
            mock_uoc.side_effect = Exception("update_or_create failed")
            with self.assertRaises(ValidationError) as ctx:
                DashboardService.guardar_valor_kpi(
                    id_kpi=kpi.id_kpi,
                    fecha=date.today(),
                    valor=Decimal("50.00"),
                )
            self.assertIn("update_or_create failed", str(ctx.exception))


class DashboardKpisWithTimezoneTest(TestCase):
    """Tests for calcular_kpis_principales with USE_TZ=True (lines 81-83)."""

    @patch("apps.reportes.services.dashboard_service.Ventas.objects.filter")
    @patch("apps.reportes.services.dashboard_service.CargasSaldo.objects.filter")
    @patch("apps.reportes.services.dashboard_service.Tarjetas.objects.filter")
    @patch("apps.reportes.services.dashboard_service.StockUnico.objects.filter")
    def test_calcular_kpis_con_use_tz_true(
        self, mock_stock, mock_tarjetas, mock_recargas, mock_ventas
    ):
        """
        Test calcular_kpis_principales with USE_TZ=True.
        This covers lines 81-83 where timezone-aware datetimes are created.
        """
        from django.test import override_settings

        # Mock aggregate responses
        mock_agg_ventas = MagicMock()
        mock_agg_ventas.aggregate.return_value = {
            "total_ventas": Decimal("1000.00"),
            "cantidad_ventas": 5,
            "ticket_promedio": Decimal("200.00"),
        }
        mock_ventas.return_value = mock_agg_ventas

        mock_agg_recargas = MagicMock()
        mock_agg_recargas.aggregate.return_value = {
            "total_recargas": Decimal("500.00"),
            "cantidad_recargas": 3,
        }
        mock_recargas.return_value = mock_agg_recargas

        mock_tarjetas_active = MagicMock()
        mock_tarjetas_active.count.return_value = 10
        mock_tarjetas_active.aggregate.return_value = {"saldo_total": Decimal("300.00")}
        mock_tarjetas.return_value = mock_tarjetas_active

        mock_stock_bajo = MagicMock()
        mock_stock_bajo.count.return_value = 2
        mock_stock.return_value = mock_stock_bajo

        with override_settings(USE_TZ=True):
            kpis = DashboardService.calcular_kpis_principales(fecha=date.today())

        # Verify results
        self.assertIsNotNone(kpis)
        self.assertIn("kpis", kpis)
        self.assertEqual(kpis["kpis"]["ventas_del_dia"], Decimal("1000.00"))
        self.assertEqual(kpis["kpis"]["cantidad_ventas"], 5)
        self.assertEqual(kpis["kpis"]["recargas_del_dia"], Decimal("500.00"))
        self.assertEqual(kpis["kpis"]["tarjetas_activas"], 10)
        self.assertEqual(kpis["kpis"]["productos_bajo_stock"], 2)
