"""
Tests for apps/inventario/views.py - AjustesInventarioViewSet custom actions
Covers the 188 missing lines in inventario/views.py (22.31% coverage)
"""

from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from apps.inventario.views import AjustesInventarioViewSet

PERM_PATCH_AUTH = "rest_framework.permissions.IsAuthenticated.has_permission"
PERM_PATCH_INV = "apps.common.permissions.CanManageInventario.has_permission"


def perm_patches():
    """Return context manager list for patching all permissions."""
    return [
        patch(PERM_PATCH_AUTH, return_value=True),
        patch(PERM_PATCH_INV, return_value=True),
    ]


class ReporteMermasMensualTest(TestCase):
    """Tests for AjustesInventarioViewSet.reporte_mermas_mensual"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "reporte_mermas_mensual"})

    def test_sin_mes_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/reporte_mermas_mensual/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_con_mes_sin_datos_retorna_200(self):
        request = self.factory.get(
            "/api/v1/ajustes-inventario/reporte_mermas_mensual/", {"mes": "2025-01"}  # Far past month, no data
        )
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("periodo", response.data)
        self.assertEqual(response.data["periodo"], "2025-01")

    def test_tendencia_sin_datos_anteriores(self):
        """When both current and previous month have 0 ajustes → sin_datos."""
        request = self.factory.get("/api/v1/ajustes-inventario/reporte_mermas_mensual/", {"mes": "2025-06"})
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.data["tendencia"], "sin_datos")

    def test_con_mes_enero_year_rollback(self):
        """Month 1 (enero) triggers year rollback to December of previous year."""
        request = self.factory.get(
            "/api/v1/ajustes-inventario/reporte_mermas_mensual/",
            {"mes": "2025-01"},  # January: mes_anterior=12, year_anterior=2024
        )
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        comparacion = response.data["resumen"]["comparacion_mes_anterior"]
        self.assertEqual(comparacion["mes_anterior"], "2024-12")

    def test_con_datos_reales_analiza_motivos(self):
        """With actual AjustesInventario, the motivo loop is executed."""
        from apps.inventario.models import AjustesInventario

        # Create merma ajustes with different motivos
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="producto vencido", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="daño físico", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="Sin especificar", estado="Aprobado")
        # Use current month to hit the fecha filter
        from django.utils import timezone

        now = timezone.now()
        mes_str = f"{now.year}-{now.month:02d}"

        request = self.factory.get("/api/v1/ajustes-inventario/reporte_mermas_mensual/", {"mes": mes_str})
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("por_motivo", response.data)
        # 3 ajustes were created, should have motivos
        self.assertGreaterEqual(len(response.data["por_motivo"]), 1)


class ProductosMayorDesperdicioTest(TestCase):
    """Tests for AjustesInventarioViewSet.productos_mayor_desperdicio"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "productos_mayor_desperdicio"})

    def test_retorna_200_ranking_vacio(self):
        request = self.factory.get("/api/v1/ajustes-inventario/productos_mayor_desperdicio/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ranking", response.data)
        self.assertEqual(response.data["ranking"], [])

    def test_retorna_con_parametros_personalizados(self):
        request = self.factory.get(
            "/api/v1/ajustes-inventario/productos_mayor_desperdicio/", {"limite": "5", "periodo_dias": "30"}
        )
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["periodo_dias"], 30)


class AnalisisCausasMermaTest(TestCase):
    """Tests for AjustesInventarioViewSet.analisis_causas_merma"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "analisis_causas_merma"})

    def test_retorna_200_sin_datos(self):
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("causas_principales", response.data)
        self.assertEqual(response.data["total_mermas"], 0)

    def test_con_periodo_personalizado(self):
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/", {"periodo_dias": "30"})
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_con_datos_clasifica_todos_los_motivos(self):
        """Covers all 5 categoria branches in the motivo classifier."""
        from apps.inventario.models import AjustesInventario

        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="producto vencido en bodega", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="daño en transporte", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="robo confirmado", estado="Aprobado")
        AjustesInventario.objects.create(
            tipo_ajuste="Merma", motivo="conteo diferente al inventario real", estado="Aprobado"
        )
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="causa desconocida", estado="Aprobado")
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_mermas"], 5)
        # All 5 categories should be in causas_principales
        motivos = [c["motivo"] for c in response.data["causas_principales"]]
        self.assertIn("Producto vencido", motivos)
        self.assertIn("Daño físico", motivos)
        self.assertIn("Robo/Hurto", motivos)
        self.assertIn("Diferencia de inventario", motivos)
        self.assertIn("Otros", motivos)

    def test_ajuste_sin_motivo_usa_sin_especificar(self):
        """Motivo=None uses 'Sin especificar' fallback."""
        from apps.inventario.models import AjustesInventario

        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="", estado="Aprobado")
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)


class PrediccionDemandaTest(TestCase):
    """Tests for AjustesInventarioViewSet.prediccion_demanda"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "prediccion_demanda"})

    def test_sin_id_producto_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/prediccion-demanda/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_producto_no_encontrado_retorna_404(self):
        from apps.productos.models import Productos

        request = self.factory.get("/api/v1/ajustes-inventario/prediccion-demanda/", {"id_producto": "99999"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", side_effect=Productos.DoesNotExist),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 404)

    def test_prediccion_exitosa(self):
        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Producto Test"

        request = self.factory.get("/api/v1/ajustes-inventario/prediccion-demanda/", {"id_producto": "1", "dias": "7"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.views.StockForecastingService.calcular_estadisticas_basicas", return_value={}),
            patch("apps.inventario.views.StockForecastingService.predecir_demanda_simple", return_value=[]),
            patch("apps.inventario.views.StockForecastingService.analizar_estacionalidad", return_value={}),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("producto", response.data)
        self.assertIn("predicciones", response.data)


class PuntoReordenTest(TestCase):
    """Tests for AjustesInventarioViewSet.punto_reorden"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "punto_reorden"})

    def test_sin_id_producto_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_producto_no_encontrado_retorna_404(self):
        from apps.productos.models import Productos

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "99999"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", side_effect=Productos.DoesNotExist),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 404)

    def test_punto_reorden_estado_critico(self):
        """stock_actual <= punto_reorden * 0.5 → estado=critico"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("5")  # 5 <= 20*0.5=10 → critico

        mock_resultado = {
            "punto_reorden": Decimal("20"),
            "stock_seguridad": Decimal("5"),
            "demanda_durante_lead_time": Decimal("15"),
            "recomendacion": "Comprar urgente",
            "confianza": 0.9,
        }

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1", "lead_time": "7"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "critico")
        self.assertEqual(response.data["nivel_urgencia"], "alto")

    def test_punto_reorden_estado_bajo(self):
        """stock_actual <= punto_reorden → estado=bajo"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("15")  # 15 <= 20 but > 10 → bajo

        mock_resultado = {
            "punto_reorden": Decimal("20"),
            "stock_seguridad": Decimal("5"),
            "demanda_durante_lead_time": Decimal("15"),
            "recomendacion": "Comprar pronto",
            "confianza": 0.8,
        }

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "bajo")

    def test_punto_reorden_estado_saludable(self):
        """stock_actual <= punto_reorden * 1.5 → estado=saludable"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("25")  # 25 <= 20*1.5=30 but > 20 → saludable

        mock_resultado = {
            "punto_reorden": Decimal("20"),
            "stock_seguridad": Decimal("5"),
            "demanda_durante_lead_time": Decimal("15"),
            "recomendacion": "Stock OK",
            "confianza": 0.7,
        }

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "saludable")

    def test_punto_reorden_estado_exceso(self):
        """stock_actual > punto_reorden * 1.5 → estado=exceso"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("50")  # 50 > 20*1.5=30 → exceso

        mock_resultado = {
            "punto_reorden": Decimal("20"),
            "stock_seguridad": Decimal("5"),
            "demanda_durante_lead_time": Decimal("15"),
            "recomendacion": "Stock en exceso",
            "confianza": 0.6,
        }

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "exceso")

    def test_punto_reorden_con_error_en_resultado(self):
        """When resultado has 'error' key → estado=sin_datos"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("20")

        mock_resultado = {"error": "insufficient data"}

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "sin_datos")
        self.assertEqual(response.data["nivel_urgencia"], "revisar")

    def test_punto_reorden_sin_stock(self):
        """StockUnico.DoesNotExist → stock_actual=0"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_resultado = {"error": "no stock data"}

        request = self.factory.get("/api/v1/ajustes-inventario/punto-reorden/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", side_effect=StockUnico.DoesNotExist),
            patch("apps.inventario.views.StockForecastingService.calcular_punto_reorden", return_value=mock_resultado),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "sin_datos")


class DetectarAnomaliasTest(TestCase):
    """Tests for AjustesInventarioViewSet.detectar_anomalias"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "detectar_anomalias"})

    def test_sin_id_producto_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/detectar-anomalias/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_producto_no_encontrado_retorna_404(self):
        from apps.productos.models import Productos

        request = self.factory.get("/api/v1/ajustes-inventario/detectar-anomalias/", {"id_producto": "99999"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", side_effect=Productos.DoesNotExist),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 404)

    def test_detectar_sin_anomalias(self):
        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"

        request = self.factory.get("/api/v1/ajustes-inventario/detectar-anomalias/", {"id_producto": "1", "dias": "30"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.views.StockForecastingService.detectar_anomalias", return_value=[]),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_anomalias"], 0)
        # periodo_analizado.desde and hasta are None when no anomalias
        self.assertIsNone(response.data["periodo_analizado"]["desde"])

    def test_detectar_con_picos_y_caidas(self):
        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"

        mock_anomalias = [
            {"fecha": "2026-01-10", "tipo": "pico", "cantidad": 100},
            {"fecha": "2026-01-05", "tipo": "caida", "cantidad": 2},
            {"fecha": "2026-01-15", "tipo": "pico", "cantidad": 90},
        ]

        request = self.factory.get("/api/v1/ajustes-inventario/detectar-anomalias/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.views.StockForecastingService.detectar_anomalias", return_value=mock_anomalias),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_anomalias"], 3)
        self.assertEqual(response.data["clasificacion"]["picos"], 2)
        self.assertEqual(response.data["clasificacion"]["caidas"], 1)
        self.assertEqual(response.data["periodo_analizado"]["desde"], "2026-01-05")
        self.assertEqual(response.data["periodo_analizado"]["hasta"], "2026-01-15")


class RecomendacionCompraTest(TestCase):
    """Tests for AjustesInventarioViewSet.recomendacion_compra"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "recomendacion_compra"})

    def test_sin_id_producto_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/recomendacion-compra/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_producto_no_encontrado_retorna_404(self):
        from apps.productos.models import Productos

        request = self.factory.get("/api/v1/ajustes-inventario/recomendacion-compra/", {"id_producto": "99999"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", side_effect=Productos.DoesNotExist),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 404)

    def test_recomendacion_exitosa_con_urgencia_alta(self):
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("10")

        mock_recomendacion = {
            "cantidad_comprar": Decimal("150"),
            "urgencia": "alta",
            "dias_cobertura_actual": 3,
            "prediccion_agotamiento": "2026-03-15",
            "demanda_diaria_estimada": Decimal("5"),
            "punto_reorden": Decimal("30"),
            "justificacion": "Stock muy bajo",
        }

        request = self.factory.get(
            "/api/v1/ajustes-inventario/recomendacion-compra/", {"id_producto": "1", "dias_cobertura": "14"}
        )
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch(
                "apps.inventario.views.StockForecastingService.obtener_recomendacion_compra",
                return_value=mock_recomendacion,
            ),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["urgencia"], "alta")
        self.assertEqual(response.data["color_urgencia"], "#fd7e14")  # naranja

    def test_recomendacion_sin_stock(self):
        """StockUnico.DoesNotExist → stock_actual=0"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"

        mock_recomendacion = {
            "urgencia": "critica",
            "cantidad_comprar": Decimal("200"),
            "dias_cobertura_actual": 0,
            "prediccion_agotamiento": None,
            "demanda_diaria_estimada": Decimal("0"),
            "punto_reorden": Decimal("0"),
            "justificacion": "Sin stock",
        }

        request = self.factory.get("/api/v1/ajustes-inventario/recomendacion-compra/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", side_effect=StockUnico.DoesNotExist),
            patch(
                "apps.inventario.views.StockForecastingService.obtener_recomendacion_compra",
                return_value=mock_recomendacion,
            ),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stock_actual"], Decimal("0"))

    def test_color_urgencia_no_necesaria(self):
        """urgencia 'no_necesaria' maps to green color"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("500")

        mock_recomendacion = {
            "urgencia": "no_necesaria",
            "cantidad_comprar": Decimal("0"),
            "dias_cobertura_actual": 90,
            "prediccion_agotamiento": None,
            "demanda_diaria_estimada": Decimal("5"),
            "punto_reorden": Decimal("30"),
            "justificacion": "Stock suficiente",
        }

        request = self.factory.get("/api/v1/ajustes-inventario/recomendacion-compra/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch(
                "apps.inventario.views.StockForecastingService.obtener_recomendacion_compra",
                return_value=mock_recomendacion,
            ),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["color_urgencia"], "#28a745")  # verde


class AnalisisCompletoTest(TestCase):
    """Tests for AjustesInventarioViewSet.analisis_completo"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "analisis_completo"})

    def test_sin_id_producto_retorna_400(self):
        request = self.factory.get("/api/v1/ajustes-inventario/analisis-completo/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_producto_no_encontrado_retorna_404(self):
        from apps.productos.models import Productos

        request = self.factory.get("/api/v1/ajustes-inventario/analisis-completo/", {"id_producto": "99999"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", side_effect=Productos.DoesNotExist),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 404)

    def test_analisis_completo_sin_stock(self):
        """StockUnico.DoesNotExist → stock_actual=0"""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        request = self.factory.get("/api/v1/ajustes-inventario/analisis-completo/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", side_effect=StockUnico.DoesNotExist),
            patch(
                "apps.inventario.views.StockForecastingService.calcular_estadisticas_basicas",
                return_value={"tendencia": "sin_datos", "demanda_promedio_diaria": Decimal("0")},
            ),
            patch("apps.inventario.views.StockForecastingService.predecir_demanda_simple", return_value=[]),
            patch(
                "apps.inventario.views.StockForecastingService.calcular_punto_reorden",
                return_value={"punto_reorden": Decimal("0")},
            ),
            patch("apps.inventario.views.StockForecastingService.detectar_anomalias", return_value=[]),
            patch(
                "apps.inventario.views.StockForecastingService.obtener_recomendacion_compra",
                return_value={"urgencia": "revisar"},
            ),
            patch(
                "apps.inventario.views.StockForecastingService.analizar_estacionalidad",
                return_value={"tiene_estacionalidad": False},
            ),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["producto"]["stock_actual"], Decimal("0"))

    def test_analisis_completo_exitoso_con_predicciones(self):
        """Full analysis with predictions list for demanda_total_7dias sum."""
        from apps.inventario.models import StockUnico

        mock_producto = Mock()
        mock_producto.id_producto = 1
        mock_producto.codigo_producto = "P001"
        mock_producto.descripcion = "Test"
        mock_producto.stock_minimo = Decimal("10")

        mock_stock = Mock()
        mock_stock.cantidad = Decimal("50")

        mock_predicciones = [{"demanda_predicha": Decimal("5")} for _ in range(7)]

        request = self.factory.get("/api/v1/ajustes-inventario/analisis-completo/", {"id_producto": "1"})
        with (
            patch(PERM_PATCH_AUTH, return_value=True),
            patch(PERM_PATCH_INV, return_value=True),
            patch("apps.productos.models.Productos.objects.get", return_value=mock_producto),
            patch("apps.inventario.models.StockUnico.objects.get", return_value=mock_stock),
            patch(
                "apps.inventario.views.StockForecastingService.calcular_estadisticas_basicas",
                return_value={"tendencia": "estable", "demanda_promedio_diaria": Decimal("5")},
            ),
            patch(
                "apps.inventario.views.StockForecastingService.predecir_demanda_simple", return_value=mock_predicciones
            ),
            patch(
                "apps.inventario.views.StockForecastingService.calcular_punto_reorden",
                return_value={"punto_reorden": Decimal("20")},
            ),
            patch("apps.inventario.views.StockForecastingService.detectar_anomalias", return_value=[]),
            patch(
                "apps.inventario.views.StockForecastingService.obtener_recomendacion_compra",
                return_value={"urgencia": "baja"},
            ),
            patch(
                "apps.inventario.views.StockForecastingService.analizar_estacionalidad",
                return_value={"tiene_estacionalidad": True},
            ),
        ):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("resumen", response.data)
        self.assertEqual(response.data["resumen"]["demanda_predicha_7dias"], Decimal("35"))


# =============================================================================
# Tests for missing lines: 140-152, 167-173, 192-197, 269-280, 347-350
# These require actual Productos + DetallesAjuste records
# =============================================================================


def _make_producto_for_views(suffix="vw"):
    from apps.contabilidad.models import Impuestos
    from apps.productos.models import Categorias, Productos, UnidadesMedida

    impuesto, _ = Impuestos.objects.get_or_create(
        nombre_impuesto=f"IVA views {suffix}",
        defaults={"porcentaje": 10.0, "vigente_desde": "2024-01-01", "estado": True},
    )
    categoria, _ = Categorias.objects.get_or_create(nombre=f"Cat views {suffix}", defaults={"estado": True})
    unidad, _ = UnidadesMedida.objects.get_or_create(
        nombre=f"Um views {suffix}", defaults={"abreviatura": f"u{suffix[:3]}", "estado": True}
    )
    producto = Productos.objects.create(
        codigo_barra=f"VIEWS{suffix[:7]:0<7}",
        descripcion=f"Producto Views {suffix}",
        stock_minimo=5,
        permite_stock_negativo=False,
        id_impuesto=impuesto,
        id_categoria=categoria,
        id_unidad_medida=unidad,
        estado=True,
    )
    return producto


class ReporteMermasMensualConDatosTest(TestCase):
    """Tests that create actual DetallesAjuste to cover lines 140-152, 167-173, 192-197."""

    def setUp(self):
        self.factory = APIRequestFactory()
        from django.utils import timezone

        self.now = timezone.now()
        self.mes_actual = f"{self.now.year}-{self.now.month:02d}"

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "reporte_mermas_mensual"})

    def _make_request(self, mes=None):
        if mes is None:
            mes = self.mes_actual
        request = self.factory.get("/api/v1/ajustes-inventario/reporte_mermas_mensual/", {"mes": mes})
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            return self._get_view()(request)

    def test_con_detalles_ajuste_cubre_producto_loop(self):
        """Lines 140-152: loop over productos_merma with DetallesAjuste records."""
        from apps.inventario.models import AjustesInventario, DetallesAjuste

        producto = _make_producto_for_views("rm1")
        ajuste = AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="vencido test rm1", estado="Aprobado")
        DetallesAjuste.objects.create(
            id_ajuste=ajuste,
            id_producto=producto,
            cantidad_ajustada=Decimal("5.000"),
        )
        response = self._make_request()
        self.assertEqual(response.status_code, 200)
        self.assertIn("por_producto", response.data)

    def test_motivo_repetido_cubre_elif_por_motivo(self):
        """Lines 167-173: multiple ajustes with same motivo populate ejemplos list."""
        from apps.inventario.models import AjustesInventario

        # Create 4 ajustes with same motivo (coverage: motivo in por_motivo branch = line 170)
        for i in range(4):
            AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="motivo repetido rm2", estado="Aprobado")
        response = self._make_request()
        self.assertEqual(response.status_code, 200)
        self.assertIn("por_motivo", response.data)

    def test_tendencia_aumentando(self):
        """Line 192-193: total_ajustes > ajustes_mes_anterior → 'aumentando'."""
        import datetime

        from django.utils import timezone

        from apps.inventario.models import AjustesInventario

        now = timezone.now()
        # Compute previous month
        if now.month == 1:
            prev_year, prev_month = now.year - 1, 12
        else:
            prev_year, prev_month = now.year, now.month - 1

        # 1 ajuste in previous month, 2 in current → aumentando
        prev_date = datetime.datetime(prev_year, prev_month, 15)
        aj_prev = AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="test ant", estado="Aprobado")
        AjustesInventario.objects.filter(pk=aj_prev.pk).update(fecha_hora=prev_date)

        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="test act1", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="test act2", estado="Aprobado")

        response = self._make_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tendencia"], "aumentando")

    def test_tendencia_disminuyendo(self):
        """Line 194-195: total_ajustes < ajustes_mes_anterior → 'disminuyendo'."""
        import datetime

        from django.utils import timezone

        from apps.inventario.models import AjustesInventario

        now = timezone.now()
        if now.month == 1:
            prev_year, prev_month = now.year - 1, 12
        else:
            prev_year, prev_month = now.year, now.month - 1

        prev_date = datetime.datetime(prev_year, prev_month, 15)
        for _ in range(3):
            aj = AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="disminuye", estado="Aprobado")
            AjustesInventario.objects.filter(pk=aj.pk).update(fecha_hora=prev_date)

        # Only 1 in current month
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="disminuye actual", estado="Aprobado")

        response = self._make_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tendencia"], "disminuyendo")

    def test_tendencia_estable(self):
        """Line 196-197: total_ajustes == ajustes_mes_anterior → 'estable'."""
        import datetime

        from django.utils import timezone

        from apps.inventario.models import AjustesInventario

        now = timezone.now()
        if now.month == 1:
            prev_year, prev_month = now.year - 1, 12
        else:
            prev_year, prev_month = now.year, now.month - 1

        prev_date = datetime.datetime(prev_year, prev_month, 15)
        aj = AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="estable mes ant", estado="Aprobado")
        AjustesInventario.objects.filter(pk=aj.pk).update(fecha_hora=prev_date)

        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="estable actual", estado="Aprobado")

        response = self._make_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tendencia"], "estable")


class ProductosMayorDesperdicioConDatosTest(TestCase):
    """Tests with real DetallesAjuste to cover lines 269-280."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "productos_mayor_desperdicio"})

    def test_con_detalles_cubre_ranking_loop(self):
        """Lines 269-280: loop over detalles with producto lookup to build ranking."""
        from apps.inventario.models import AjustesInventario, DetallesAjuste

        producto = _make_producto_for_views("pd1")
        ajuste = AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="test desperdicio", estado="Aprobado")
        DetallesAjuste.objects.create(
            id_ajuste=ajuste,
            id_producto=producto,
            cantidad_ajustada=Decimal("10.000"),
        )
        request = self.factory.get("/api/v1/ajustes-inventario/productos_mayor_desperdicio/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data["ranking"]), 0)
        self.assertEqual(response.data["ranking"][0]["posicion"], 1)


class AnalisisCausasMermaMotivosTest(TestCase):
    """Tests to cover lines 347-350 (motivos_clasificados first-time insertion)."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_view(self):
        return AjustesInventarioViewSet.as_view({"get": "analisis_causas_merma"})

    def test_primera_vez_categoria_crea_entrada(self):
        """Lines 347-348: if categoria not in motivos_clasificados → creates new entry."""
        from apps.inventario.models import AjustesInventario

        # Use unique motivos to force first-time categoria creation
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="causa nueva 347", estado="Aprobado")
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["total_mermas"], 0)
        self.assertGreater(len(response.data["causas_principales"]), 0)

    def test_categoria_repetida_cubre_false_branch(self):
        """Line 347→350: categoria already in motivos_clasificados → skip creation."""
        from apps.inventario.models import AjustesInventario

        # Two ajustes with same category (vencido → 'Producto vencido')
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="producto vencido primera vez", estado="Aprobado")
        AjustesInventario.objects.create(tipo_ajuste="Merma", motivo="producto vencido segunda vez", estado="Aprobado")
        request = self.factory.get("/api/v1/ajustes-inventario/analisis_causas_merma/")
        with patch(PERM_PATCH_AUTH, return_value=True), patch(PERM_PATCH_INV, return_value=True):
            response = self._get_view()(request)
        self.assertEqual(response.status_code, 200)
        causas = response.data["causas_principales"]
        vencido = next(c for c in causas if c["motivo"] == "Producto vencido")
        self.assertEqual(vencido["frecuencia"], 2)
