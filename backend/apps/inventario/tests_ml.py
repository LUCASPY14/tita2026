"""
Tests para funcionalidades de Machine Learning en inventario.

Prueba:
- Predicción de demanda
- Cálculo de punto de reorden
- Detección de anomalías
- Análisis de estacionalidad
- Recomendaciones de compra
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.productos.models import Productos, Categorias, UnidadesMedida, ListasPrecios
from apps.inventario.models import StockUnico, MovimientosStock
from apps.ventas.models import Ventas, DetallesVenta
from apps.clientes.models import Clientes, TiposCliente
from apps.usuarios.models import Empleados, PerfilesUsuario, Roles
from apps.contabilidad.models import Impuestos
from apps.inventario.ml_forecasting import StockForecastingService


class StockForecastingServiceTest(TestCase):
    """Tests para el servicio de forecasting de stock"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal('10.00'),
            vigente_desde='2024-01-01',
            activo=True
        )
        
        # Crear categoría
        self.categoria = Categorias.objects.create(
            nombre="Bebidas"
        )
        
        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre="Unidad",
            abreviatura="un"
        )
        
        # Crear lista de precios
        self.lista_precios = ListasPrecios.objects.create(
            nombre_lista="Lista General",
            fecha_vigencia='2024-01-01',
            moneda='PYG',
            activo=True
        )
        
        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7791234567890",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal('10.00')
        )
        
        # Crear stock
        self.stock = StockUnico.objects.create(
            id_producto=self.producto,
            cantidad=Decimal('100.00')
        )
        
        # Crear rol para empleado
        self.rol = Roles.objects.create(
            nombre_rol="Vendedor",
            descripcion="Rol de vendedor",
            activo=True
        )
        
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
            activo=True
        )
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo="Estudiante",
            activo=True
        )
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Cliente",
            apellidos="Test",
            ruc_ci="12345678-9",
            email="cliente@test.com",
            telefono="1234567890",
            id_lista=self.lista_precios,
            id_tipo_cliente=self.tipo_cliente
        )
    
    def _crear_ventas_historicas(self, dias=30, cantidad_diaria=10):
        """Crear ventas históricas para testing"""
        for dia in range(dias):
            fecha = timezone.now() - timedelta(days=dias - dia)
            
            # Crear venta
            venta = Ventas.objects.create(
                id_cliente=self.cliente,
                id_empleado=self.empleado,
                fecha_hora=fecha,
                total=Decimal('800.00'),
                estado='confirmada',
                metodo_pago='efectivo'
            )
            
            # Crear detalle
            DetallesVenta.objects.create(
                id_venta=venta,
                id_producto=self.producto,
                cantidad=Decimal(str(cantidad_diaria)),
                precio_unitario=Decimal('80.00'),
                subtotal=Decimal(str(cantidad_diaria * 80))
            )
            
            # Registrar movimiento de stock
            MovimientosStock.objects.create(
                id_producto=self.producto,
                tipo_movimiento='Egreso',
                cantidad=Decimal(str(cantidad_diaria)),
                motivo='venta',
                id_venta=venta,
                fecha_hora=fecha
            )
    
    def test_obtener_datos_historicos(self):
        """Test: obtener datos históricos de ventas"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        datos = StockForecastingService.obtener_datos_historicos(
            self.producto.id_producto, dias=30
        )
        
        self.assertGreater(datos['total_registros'], 0)
        self.assertEqual(len(datos['fechas']), len(datos['cantidades']))
        self.assertIsNotNone(datos['periodo']['inicio'])
        self.assertIsNotNone(datos['periodo']['fin'])
    
    def test_calcular_estadisticas_basicas(self):
        """Test: cálculo de estadísticas básicas"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        stats = StockForecastingService.calcular_estadisticas_basicas(
            self.producto.id_producto, dias=30
        )
        
        self.assertIn('demanda_promedio_diaria', stats)
        self.assertIn('demanda_maxima', stats)
        self.assertIn('demanda_minima', stats)
        self.assertIn('desviacion_estandar', stats)
        self.assertIn('tendencia', stats)
        self.assertIn('estacionalidad', stats)
        
        # Con demanda constante, promedio debe ser cercano a 10
        self.assertAlmostEqual(
            float(stats['demanda_promedio_diaria']), 10.0, places=1
        )
    
    def test_predecir_demanda_simple(self):
        """Test: predicción de demanda usando promedio móvil"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        predicciones = StockForecastingService.predecir_demanda_simple(
            self.producto.id_producto, dias_adelante=7
        )
        
        self.assertEqual(len(predicciones), 7)
        
        for pred in predicciones:
            self.assertIn('fecha', pred)
            self.assertIn('demanda_predicha', pred)
            self.assertIn('intervalo_confianza', pred)
            self.assertIn('dia_semana', pred)
            self.assertIn('confianza', pred)
            
            # Predicción debe ser positiva
            self.assertGreater(pred['demanda_predicha'], Decimal('0'))
            
            # Confianza debe estar entre 0 y 1
            self.assertGreaterEqual(pred['confianza'], 0)
            self.assertLessEqual(pred['confianza'], 1)
    
    def test_calcular_punto_reorden(self):
        """Test: cálculo de punto de reorden"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        resultado = StockForecastingService.calcular_punto_reorden(
            self.producto.id_producto, lead_time_dias=7
        )
        
        self.assertIn('punto_reorden', resultado)
        self.assertIn('stock_seguridad', resultado)
        self.assertIn('demanda_durante_lead_time', resultado)
        
        # Punto de reorden debe ser positivo
        self.assertGreater(resultado['punto_reorden'], Decimal('0'))
        
        # Debe incluir demanda del lead time
        demanda_lead_time = resultado['demanda_durante_lead_time']
        self.assertAlmostEqual(
            float(demanda_lead_time), 70.0, places=1  # 10/día × 7 días
        )
    
    def test_detectar_anomalias(self):
        """Test: detección de anomalías en ventas"""
        # Crear ventas normales
        self._crear_ventas_historicas(dias=25, cantidad_diaria=10)
        
        # Crear anomalías (picos y caídas)
        fecha_pico = timezone.now() - timedelta(days=5)
        venta_pico = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado=self.empleado,
            fecha_hora=fecha_pico,
            total=Decimal('4000.00'),
            estado='confirmada',
            metodo_pago='efectivo'
        )
        DetallesVenta.objects.create(
            id_venta=venta_pico,
            id_producto=self.producto,
            cantidad=Decimal('50'),  # Pico: 5x lo normal
            precio_unitario=Decimal('80.00'),
            subtotal=Decimal('4000.00')
        )
        MovimientosStock.objects.create(
            id_producto=self.producto,
            tipo_movimiento='Egreso',
            cantidad=Decimal('50'),
            motivo='venta',
            id_venta=venta_pico,
            fecha_hora=fecha_pico
        )
        
        anomalias = StockForecastingService.detectar_anomalias(
            self.producto.id_producto, dias=30
        )
        
        # Debe detectar al menos la anomalía del pico
        self.assertGreater(len(anomalias), 0)
        
        # Verificar estructura de anomalías
        for anomalia in anomalias:
            self.assertIn('fecha', anomalia)
            self.assertIn('cantidad', anomalia)
            self.assertIn('tipo', anomalia)
            self.assertIn('desviacion', anomalia)
            self.assertIn('explicacion', anomalia)
            self.assertIn(anomalia['tipo'], ['pico', 'caida'])
    
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
                id_empleado=self.empleado,
                fecha_hora=fecha,
                total=Decimal(str(cantidad * 80)),
                estado='confirmada',
                metodo_pago='efectivo'
            )
            DetallesVenta.objects.create(
                id_venta=venta,
                id_producto=self.producto,
                cantidad=Decimal(str(cantidad)),
                precio_unitario=Decimal('80.00'),
                subtotal=Decimal(str(cantidad * 80))
            )
            MovimientosStock.objects.create(
                id_producto=self.producto,
                tipo_movimiento='Egreso',
                cantidad=Decimal(str(cantidad)),
                motivo='venta',
                id_venta=venta,
                fecha_hora=fecha
            )
        
        patron = StockForecastingService.analizar_estacionalidad(
            self.producto.id_producto, dias=60
        )
        
        self.assertIn('tiene_estacionalidad', patron)
        self.assertIn('patron_semanal', patron)
        self.assertIn('dias_pico', patron)
        self.assertIn('dias_valle', patron)
        
        # Debe detectar estacionalidad
        self.assertTrue(patron['tiene_estacionalidad'])
        
        # Lunes y Viernes deben ser días pico
        self.assertIn('Lunes', patron['dias_pico'])
        self.assertIn('Viernes', patron['dias_pico'])
    
    def test_obtener_recomendacion_compra_stock_critico(self):
        """Test: recomendación de compra con stock crítico"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        # Stock crítico: solo 15 unidades (1.5 días de cobertura)
        self.stock.cantidad = Decimal('15.00')
        self.stock.save()
        
        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            self.producto.id_producto,
            stock_actual=Decimal('15.00'),
            dias_cobertura_deseada=14
        )
        
        self.assertIn('cantidad_comprar', recomendacion)
        self.assertIn('urgencia', recomendacion)
        self.assertIn('dias_cobertura_actual', recomendacion)
        self.assertIn('prediccion_agotamiento', recomendacion)
        
        # Con stock bajo, urgencia debe ser crítica o alta
        self.assertIn(recomendacion['urgencia'], ['critica', 'alta'])
        
        # Debe recomendar comprar
        self.assertGreater(recomendacion['cantidad_comprar'], Decimal('0'))
    
    def test_obtener_recomendacion_compra_stock_suficiente(self):
        """Test: recomendación de compra con stock suficiente"""
        self._crear_ventas_historicas(dias=30, cantidad_diaria=10)
        
        # Stock alto: 300 unidades (30 días de cobertura)
        self.stock.cantidad = Decimal('300.00')
        self.stock.save()
        
        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            self.producto.id_producto,
            stock_actual=Decimal('300.00'),
            dias_cobertura_deseada=14
        )
        
        # Con stock alto, urgencia debe ser baja o no necesaria
        self.assertIn(recomendacion['urgencia'], ['baja', 'no_necesaria'])
        
        # Días de cobertura debe ser alto
        self.assertGreater(recomendacion['dias_cobertura_actual'], 14)
    
    def test_sin_datos_historicos(self):
        """Test: manejo de productos sin datos históricos"""
        # No crear ventas históricas
        
        stats = StockForecastingService.calcular_estadisticas_basicas(
            self.producto.id_producto, dias=30
        )
        
        # Debe retornar error o valores en cero
        self.assertIn('error', stats)
        
        predicciones = StockForecastingService.predecir_demanda_simple(
            self.producto.id_producto, dias_adelante=7
        )
        
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
        
        stats = StockForecastingService.calcular_estadisticas_basicas(
            self.producto.id_producto, dias=30
        )
        
        self.assertEqual(stats['tendencia'], 'creciente')
    
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
        
        stats = StockForecastingService.calcular_estadisticas_basicas(
            self.producto.id_producto, dias=30
        )
        
        self.assertEqual(stats['tendencia'], 'decreciente')
    
    def _crear_venta_unitaria(self, fecha, cantidad):
        """Helper: crear una venta individual"""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado=self.empleado,
            fecha_hora=fecha,
            total=Decimal(str(cantidad * 80)),
            estado='confirmada',
            metodo_pago='efectivo'
        )
        DetallesVenta.objects.create(
            id_venta=venta,
            id_producto=self.producto,
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal('80.00'),
            subtotal=Decimal(str(cantidad * 80))
        )
        MovimientosStock.objects.create(
            id_producto=self.producto,
            tipo_movimiento='Egreso',
            cantidad=Decimal(str(cantidad)),
            motivo='venta',
            id_venta=venta,
            fecha_hora=fecha
        )
