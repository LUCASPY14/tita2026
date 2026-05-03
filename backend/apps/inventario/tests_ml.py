"""
Tests para funcionalidades de Machine Learning en inventario.

Prueba:
- Predicción de demanda
- Cálculo de punto de reorden
- Detección de anomalías
- Análisis de estacionalidad
- Recomendaciones de compra
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, TiposCliente
from apps.contabilidad.models import Impuestos
from apps.inventario.ml_forecasting import StockForecastingService
from apps.inventario.models import MovimientosStock, StockUnico
from apps.productos.models import Categorias, ListasPrecios, Productos, UnidadesMedida
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import DetallesVenta, Ventas


class StockForecastingServiceTest(TestCase):
    """Tests para el servicio de forecasting de stock"""

    def setUp(self):
        """Configuración inicial para tests"""
        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde="2024-01-01",
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas")

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")

        # Crear lista de precios
        self.lista_precios = ListasPrecios.objects.create(
            nombre_lista="Lista General", fecha_vigencia="2024-01-01", moneda="PYG", estado=True
        )

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7791234567890",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("10.00"),
        )

        # Crear stock
        self.stock = StockUnico.objects.create(id_producto=self.producto, cantidad=Decimal("9999.00"))

        # Crear rol para empleado
        self.rol = Roles.objects.create(nombre_rol="Vendedor", descripcion="Rol de vendedor", estado=True)

        # Crear empleado para ventas
        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Pérez",
            usuario="jperez",
            contrasena_hash="hash_dummy",
            email="juan@test.com",
            telefono="1234567890",
            direccion="Calle 123",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
            estado=True,
        )

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Estudiante", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Cliente",
            apellidos="Test",
            ruc_ci="12345678-9",
            email="cliente@test.com",
            telefono="1234567890",
            id_lista=self.lista_precios,
            id_tipo_cliente=self.tipo_cliente,
        )

    def _crear_ventas_historicas(self, dias=30, cantidad_diaria=10):
        """Crear ventas históricas para testing"""
        for dia in range(dias):
            fecha = timezone.now() - timedelta(days=dias - dia)

            # Crear venta
            venta = Ventas.objects.create(
                id_cliente=self.cliente,
                id_empleado_cajero=self.empleado,
                monto_total=Decimal(str(cantidad_diaria * 80)),
                estado="Activa",
            )

            # Signal auto-creates MovimientosStock when DetallesVenta is saved
            DetallesVenta.objects.create(
                id_venta=venta,
                id_producto=self.producto,
                cantidad=Decimal(str(cantidad_diaria)),
                precio_unitario=Decimal("80.00"),
                subtotal=Decimal(str(cantidad_diaria * 80)),
            )

            # Backdate the signal-created movement for ML historical queries
            MovimientosStock.objects.filter(id_venta=venta, tipo_movimiento="Egreso", motivo="venta").update(
                fecha_hora=fecha
            )

    def test_obtener_datos_historicos(self):
        """Test: obtener datos históricos de ventas"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        datos = StockForecastingService.obtener_datos_historicos(self.producto.id_producto, dias=30)

        self.assertGreater(datos["total_registros"], 0)
        self.assertEqual(len(datos["fechas"]), len(datos["cantidades"]))
        self.assertIsNotNone(datos["periodo"]["inicio"])
        self.assertIsNotNone(datos["periodo"]["fin"])

    def test_calcular_estadisticas_basicas(self):
        """Test: cálculo de estadísticas básicas"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        stats = StockForecastingService.calcular_estadisticas_basicas(self.producto.id_producto, dias=30)

        self.assertIn("demanda_promedio_diaria", stats)
        self.assertIn("demanda_maxima", stats)
        self.assertIn("demanda_minima", stats)
        self.assertIn("desviacion_estandar", stats)
        self.assertIn("tendencia", stats)
        self.assertIn("estacionalidad", stats)

        # Con demanda constante, promedio debe ser cercano a 10
        self.assertAlmostEqual(float(stats["demanda_promedio_diaria"]), 10.0, places=1)

    def test_predecir_demanda_simple(self):
        """Test: predicción de demanda usando promedio móvil"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        predicciones = StockForecastingService.predecir_demanda_simple(self.producto.id_producto, dias_adelante=7)

        self.assertEqual(len(predicciones), 7)

        for pred in predicciones:
            self.assertIn("fecha", pred)
            self.assertIn("demanda_predicha", pred)
            self.assertIn("intervalo_confianza", pred)
            self.assertIn("dia_semana", pred)
            self.assertIn("confianza", pred)

            # Predicción debe ser positiva
            self.assertGreater(pred["demanda_predicha"], Decimal("0"))

            # Confianza debe estar entre 0 y 1
            self.assertGreaterEqual(pred["confianza"], 0)
            self.assertLessEqual(pred["confianza"], 1)

    def test_calcular_punto_reorden(self):
        """Test: cálculo de punto de reorden"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        resultado = StockForecastingService.calcular_punto_reorden(self.producto.id_producto, lead_time_dias=7)

        self.assertIn("punto_reorden", resultado)
        self.assertIn("stock_seguridad", resultado)
        self.assertIn("demanda_durante_lead_time", resultado)

        # Punto de reorden debe ser positivo
        self.assertGreater(resultado["punto_reorden"], Decimal("0"))

        # Debe incluir demanda del lead time
        demanda_lead_time = resultado["demanda_durante_lead_time"]
        self.assertAlmostEqual(float(demanda_lead_time), 70.0, places=1)  # 10/día × 7 días

    def test_detectar_anomalias(self):
        """Test: detección de anomalías en ventas"""
        # Crear ventas normales
        self._crear_ventas_historicas(dias=25, cantidad_diaria=10)

        # Crear anomalías (picos y caídas)
        fecha_pico = timezone.now() - timedelta(days=5)
        venta_pico = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            monto_total=Decimal("4000.00"),
            estado="Activa",
        )
        DetallesVenta.objects.create(
            id_venta=venta_pico,
            id_producto=self.producto,
            cantidad=Decimal("50"),  # Pico: 5x lo normal
            precio_unitario=Decimal("80.00"),
            subtotal=Decimal("4000.00"),
        )
        MovimientosStock.objects.filter(id_venta=venta_pico, tipo_movimiento="Egreso", motivo="venta").update(
            fecha_hora=fecha_pico
        )

        anomalias = StockForecastingService.detectar_anomalias(self.producto.id_producto, dias=30)

        # Debe detectar al menos la anomalía del pico
        self.assertGreater(len(anomalias), 0)

        # Verificar estructura de anomalías
        for anomalia in anomalias:
            self.assertIn("fecha", anomalia)
            self.assertIn("cantidad", anomalia)
            self.assertIn("tipo", anomalia)
            self.assertIn("desviacion", anomalia)
            self.assertIn("explicacion", anomalia)
            self.assertIn(anomalia["tipo"], ["pico", "caida"])

    def test_analizar_estacionalidad(self):
        """Test: análisis de patrones estacionales"""
        # Crear patrón semanal (más ventas lunes y viernes)
        for dia in range(60):
            fecha = timezone.now() - timedelta(days=60 - dia)
            dia_semana = fecha.weekday()

            # Lunes (0) y Viernes (4): 15 unidades
            # Otros días: 8 unidades
            if dia_semana in [0, 4]:
                cantidad = 15
            else:
                cantidad = 8

            venta = Ventas.objects.create(
                id_cliente=self.cliente,
                id_empleado_cajero=self.empleado,
                monto_total=Decimal(str(cantidad * 80)),
                estado="Activa",
            )
            DetallesVenta.objects.create(
                id_venta=venta,
                id_producto=self.producto,
                cantidad=Decimal(str(cantidad)),
                precio_unitario=Decimal("80.00"),
                subtotal=Decimal(str(cantidad * 80)),
            )
            MovimientosStock.objects.filter(id_venta=venta, tipo_movimiento="Egreso", motivo="venta").update(
                fecha_hora=fecha
            )

        patron = StockForecastingService.analizar_estacionalidad(self.producto.id_producto, dias=60)

        self.assertIn("tiene_estacionalidad", patron)
        self.assertIn("patron_semanal", patron)
        self.assertIn("dias_pico", patron)
        self.assertIn("dias_valle", patron)

        # Debe detectar estacionalidad
        self.assertTrue(patron["tiene_estacionalidad"])

        # Lunes y Viernes deben ser días pico
        self.assertIn("Lunes", patron["dias_pico"])
        self.assertIn("Viernes", patron["dias_pico"])

    def test_obtener_recomendacion_compra_stock_critico(self):
        """Test: recomendación de compra con stock crítico"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        # Stock crítico: solo 15 unidades (1.5 días de cobertura)
        self.stock.cantidad = Decimal("15.00")
        self.stock.save()

        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            self.producto.id_producto, stock_actual=Decimal("15.00"), dias_cobertura_deseada=14
        )

        self.assertIn("cantidad_comprar", recomendacion)
        self.assertIn("urgencia", recomendacion)
        self.assertIn("dias_cobertura_actual", recomendacion)
        self.assertIn("prediccion_agotamiento", recomendacion)

        # Con stock bajo, urgencia debe ser crítica o alta
        self.assertIn(recomendacion["urgencia"], ["critica", "alta"])

        # Debe recomendar comprar
        self.assertGreater(recomendacion["cantidad_comprar"], Decimal("0"))

    def test_obtener_recomendacion_compra_stock_suficiente(self):
        """Test: recomendación de compra con stock suficiente"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)

        # Stock alto: 300 unidades (30 días de cobertura)
        self.stock.cantidad = Decimal("300.00")
        self.stock.save()

        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            self.producto.id_producto, stock_actual=Decimal("300.00"), dias_cobertura_deseada=14
        )

        # Con stock alto, urgencia debe ser baja o no necesaria
        self.assertIn(recomendacion["urgencia"], ["baja", "no_necesaria"])

        # Días de cobertura debe ser alto
        self.assertGreater(recomendacion["dias_cobertura_actual"], 14)

    def test_sin_datos_historicos(self):
        """Test: manejo de productos sin datos históricos"""
        # No crear ventas históricas

        stats = StockForecastingService.calcular_estadisticas_basicas(self.producto.id_producto, dias=30)

        # Debe retornar error o valores en cero
        self.assertIn("error", stats)

        predicciones = StockForecastingService.predecir_demanda_simple(self.producto.id_producto, dias_adelante=7)

        # Sin datos, no debe haber predicciones
        self.assertEqual(len(predicciones), 0)

    def test_tendencia_creciente(self):
        """Test: detección de tendencia creciente"""
        # Primera mitad: 8 unidades/día
        for dia in range(15):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=8)

        # Segunda mitad: 12 unidades/día (50% más)
        for dia in range(15, 30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=12)

        stats = StockForecastingService.calcular_estadisticas_basicas(self.producto.id_producto, dias=30)

        self.assertEqual(stats["tendencia"], "creciente")

    def test_tendencia_decreciente(self):
        """Test: detección de tendencia decreciente"""
        # Primera mitad: 15 unidades/día
        for dia in range(15):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=15)

        # Segunda mitad: 8 unidades/día (47% menos)
        for dia in range(15, 30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=8)

        stats = StockForecastingService.calcular_estadisticas_basicas(self.producto.id_producto, dias=30)

        self.assertEqual(stats["tendencia"], "decreciente")

    def _crear_venta_unitaria(self, fecha, cantidad):
        """Helper: crear una venta individual"""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            monto_total=Decimal(str(cantidad * 80)),
            estado="Activa",
        )
        DetallesVenta.objects.create(
            id_venta=venta,
            id_producto=self.producto,
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal("80.00"),
            subtotal=Decimal(str(cantidad * 80)),
        )
        MovimientosStock.objects.filter(id_venta=venta, tipo_movimiento="Egreso", motivo="venta").update(
            fecha_hora=fecha
        )

    # ── New extended tests for branch coverage ──────────────────────────────

    def test_calcular_estadisticas_un_solo_dato(self):
        """Line 154: else branch when mitad==0 (only 1 data point)."""
        # Create just 1 sale so len(cantidades)=1 → mitad=0 → else: tendencia='estable'
        fecha = timezone.now() - timedelta(days=1)
        self._crear_venta_unitaria(fecha, cantidad=10)
        stats = StockForecastingService.calcular_estadisticas_basicas(self.producto.id_producto, dias=30)
        self.assertEqual(stats["tendencia"], "estable")

    def test_predecir_demanda_tendencia_creciente(self):
        """Line 224: factor_tendencia=1.05 when tendencia='creciente'."""
        # Build creciente stats: second half > first half * 1.1
        for dia in range(15):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=5)
        for dia in range(15, 30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=8)  # 60% more → creciente
        predicciones = StockForecastingService.predecir_demanda_simple(self.producto.id_producto, dias_adelante=3)
        self.assertEqual(len(predicciones), 3)

    def test_predecir_demanda_tendencia_decreciente(self):
        """Line 226: factor_tendencia=0.95 when tendencia='decreciente'."""
        for dia in range(15):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=15)
        for dia in range(15, 30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=8)  # decreciente
        predicciones = StockForecastingService.predecir_demanda_simple(self.producto.id_producto, dias_adelante=3)
        self.assertEqual(len(predicciones), 3)

    def test_predecir_demanda_dias_sin_venta(self):
        """Line 220: promedios_dia_semana[dia] = float(promedio) for days with no sales."""
        # Create sales only on Mondays for 30 days — other days have no ventas
        for semana in range(5):
            fecha = timezone.now() - timedelta(days=28 - semana * 7)
            # force Monday (weekday=0)
            while fecha.weekday() != 0:
                fecha -= timedelta(days=1)
            self._crear_venta_unitaria(fecha, cantidad=10)
        predicciones = StockForecastingService.predecir_demanda_simple(self.producto.id_producto, dias_adelante=7)
        # Should return predictions using fallback for days with no sales
        self.assertGreater(len(predicciones), 0)

    def test_calcular_punto_reorden_sin_datos(self):
        """Line 305: early return when no historical data."""
        resultado = StockForecastingService.calcular_punto_reorden(self.producto.id_producto, lead_time_dias=7)
        self.assertIn("error", resultado)
        self.assertEqual(resultado["punto_reorden"], Decimal("0"))

    def test_calcular_punto_reorden_menor_que_minimo(self):
        """Lines 335-336: punto_reorden < stock_minimo_actual → uses stock_minimo."""
        # Create sales with low demand so punto_reorden ends up below default stock_minimo=10
        for dia in range(30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=1)  # 1 unit/day → reorden ≈ 7+small
        # stock_minimo is 10, so if calculated punto_reorden < 10, it should use 10
        resultado = StockForecastingService.calcular_punto_reorden(self.producto.id_producto, lead_time_dias=7)
        # Regardless of which branch, resultado should have punto_reorden and recomendacion
        self.assertIn("punto_reorden", resultado)
        self.assertIn("recomendacion", resultado)

    def test_calcular_punto_reorden_producto_inexistente(self):
        """Lines 341-342: bare except when Productos.get raises DoesNotExist."""
        from unittest.mock import patch

        # Need real historical data so we don't exit early at line 305
        for dia in range(30):
            fecha = timezone.now() - timedelta(days=30 - dia)
            self._crear_venta_unitaria(fecha, cantidad=10)
        # Patch Productos.objects.get (imported inside the method) to raise so except branch fires
        with patch("apps.productos.models.Productos.objects.get", side_effect=Exception("not found")):
            resultado = StockForecastingService.calcular_punto_reorden(self.producto.id_producto, lead_time_dias=7)
        self.assertIn("recomendacion", resultado)
        self.assertIn("Configurar como nuevo stock m", resultado["recomendacion"])

    def test_detectar_anomalias_menos_de_7_registros(self):
        """Line 383: returns [] when total_registros < 7."""
        # Create only 3 sales
        for dia in range(3):
            fecha = timezone.now() - timedelta(days=3 - dia)
            self._crear_venta_unitaria(fecha, cantidad=10)
        resultado = StockForecastingService.detectar_anomalias(self.producto.id_producto, dias=30)
        self.assertEqual(resultado, [])

    def test_detectar_anomalias_caida(self):
        """Lines 412-413: caida anomaly detected when quantity far below mean."""
        # Create 20 days of normal sales (10 units) then 1 very low sale
        for dia in range(20):
            fecha = timezone.now() - timedelta(days=25 - dia)
            self._crear_venta_unitaria(fecha, cantidad=10)
        # Very low sale = 0.1 units → caida below (media - 2*std)
        fecha_caida = timezone.now() - timedelta(days=3)
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            monto_total=Decimal("8.00"),
            estado="Activa",
        )
        from apps.ventas.models import DetallesVenta

        DetallesVenta.objects.create(
            id_venta=venta,
            id_producto=self.producto,
            cantidad=Decimal("0.1"),  # Extremely low → caida
            precio_unitario=Decimal("80.00"),
            subtotal=Decimal("8.00"),
        )
        MovimientosStock.objects.filter(id_venta=venta, tipo_movimiento="Egreso", motivo="venta").update(
            fecha_hora=fecha_caida
        )
        anomalias = StockForecastingService.detectar_anomalias(self.producto.id_producto, dias=30)
        tipos = [a["tipo"] for a in anomalias]
        self.assertIn("caida", tipos)

    def test_analizar_estacionalidad_menos_de_14(self):
        """Line 447: early return when total_registros < 14."""
        # Create only 10 sales
        for dia in range(10):
            fecha = timezone.now() - timedelta(days=10 - dia)
            self._crear_venta_unitaria(fecha, cantidad=5)
        resultado = StockForecastingService.analizar_estacionalidad(self.producto.id_producto, dias=30)
        self.assertFalse(resultado["tiene_estacionalidad"])
        self.assertIn("error", resultado)

    def test_analizar_estacionalidad_dias_sin_venta(self):
        """Line 467: patron_semanal[dia]=0 for days with no sales."""
        # Create 14+ sales but all on same day of week → other days get 0
        for semana in range(3):
            monday_offset = 21 - semana * 7
            for day_offset in range(5):  # 5 consecutive days each week
                fecha = timezone.now() - timedelta(days=monday_offset - day_offset)
                self._crear_venta_unitaria(fecha, cantidad=8)
        resultado = StockForecastingService.analizar_estacionalidad(self.producto.id_producto, dias=90)
        # Should complete without error; at least one day with 0 ventas should be covered
        self.assertIn("patron_semanal", resultado)

    def test_recomendacion_compra_sin_datos(self):
        """Line 530: early return when no historical data."""
        resultado = StockForecastingService.obtener_recomendacion_compra(
            self.producto.id_producto, stock_actual=Decimal("100.00")
        )
        self.assertIn("error", resultado)
        self.assertEqual(resultado["cantidad_comprar"], Decimal("0"))

    def test_recomendacion_compra_demanda_cero(self):
        """Lines 542, 581: demanda_diaria=0 paths (dias_cobertura=999, agotamiento=None)."""
        # Create a product with exactly zero demand (movement saved but with qty 0 via mock)
        from unittest.mock import patch

        # Patch calcular_estadisticas_basicas to return demanda=0 but no error key
        stats_mock = {
            "demanda_promedio_diaria": Decimal("0"),
            "demanda_maxima": Decimal("0"),
            "demanda_minima": Decimal("0"),
            "desviacion_estandar": 0.0,
            "tendencia": "estable",
            "estacionalidad": False,
            "total_dias_con_venta": 5,
        }
        punto_reorden_mock = {"punto_reorden": Decimal("10"), "error": "x"}
        with (
            patch.object(StockForecastingService, "calcular_estadisticas_basicas", return_value=stats_mock),
            patch.object(StockForecastingService, "calcular_punto_reorden", return_value=punto_reorden_mock),
        ):
            resultado = StockForecastingService.obtener_recomendacion_compra(
                self.producto.id_producto, stock_actual=Decimal("50.00")
            )
        self.assertEqual(resultado["dias_cobertura_actual"], 999)
        self.assertIsNone(resultado["prediccion_agotamiento"])

    def test_recomendacion_compra_urgencia_alta(self):
        """Lines 564-565: urgencia='alta' when dias_cobertura in (2,5]."""
        from unittest.mock import patch

        stats_mock = {
            "demanda_promedio_diaria": Decimal("10"),
            "demanda_maxima": Decimal("15"),
            "demanda_minima": Decimal("5"),
            "desviacion_estandar": 2.0,
            "tendencia": "estable",
            "estacionalidad": False,
            "total_dias_con_venta": 30,
        }
        punto_reorden_mock = {"punto_reorden": Decimal("200")}
        with (
            patch.object(StockForecastingService, "calcular_estadisticas_basicas", return_value=stats_mock),
            patch.object(StockForecastingService, "calcular_punto_reorden", return_value=punto_reorden_mock),
        ):
            # stock=40 → dias_cobertura = 40//10 = 4 → 'alta'
            resultado = StockForecastingService.obtener_recomendacion_compra(
                self.producto.id_producto, stock_actual=Decimal("40")
            )
        self.assertEqual(resultado["urgencia"], "alta")

    def test_recomendacion_compra_urgencia_media(self):
        """Lines 567-568: urgencia='media' when dias_cobertura in (5,10]."""
        from unittest.mock import patch

        stats_mock = {
            "demanda_promedio_diaria": Decimal("10"),
            "demanda_maxima": Decimal("15"),
            "demanda_minima": Decimal("5"),
            "desviacion_estandar": 2.0,
            "tendencia": "estable",
            "estacionalidad": False,
            "total_dias_con_venta": 30,
        }
        punto_reorden_mock = {"punto_reorden": Decimal("200")}
        with (
            patch.object(StockForecastingService, "calcular_estadisticas_basicas", return_value=stats_mock),
            patch.object(StockForecastingService, "calcular_punto_reorden", return_value=punto_reorden_mock),
        ):
            # stock=80 → dias_cobertura = 80//10 = 8 → 'media'
            resultado = StockForecastingService.obtener_recomendacion_compra(
                self.producto.id_producto, stock_actual=Decimal("80")
            )
        self.assertEqual(resultado["urgencia"], "media")

    def test_recomendacion_compra_urgencia_baja(self):
        """Lines 570-571: urgencia='baja' when dias_cobertura>10 but stock<punto_reorden."""
        from unittest.mock import patch

        stats_mock = {
            "demanda_promedio_diaria": Decimal("10"),
            "demanda_maxima": Decimal("15"),
            "demanda_minima": Decimal("5"),
            "desviacion_estandar": 2.0,
            "tendencia": "estable",
            "estacionalidad": False,
            "total_dias_con_venta": 30,
        }
        # punto_reorden=200, stock=120 → dias_cobertura=12>10, stock<punto_reorden → baja
        punto_reorden_mock = {"punto_reorden": Decimal("200")}
        with (
            patch.object(StockForecastingService, "calcular_estadisticas_basicas", return_value=stats_mock),
            patch.object(StockForecastingService, "calcular_punto_reorden", return_value=punto_reorden_mock),
        ):
            resultado = StockForecastingService.obtener_recomendacion_compra(
                self.producto.id_producto, stock_actual=Decimal("120")
            )
        self.assertEqual(resultado["urgencia"], "baja")
