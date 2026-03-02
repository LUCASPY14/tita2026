"""
Tests para la app inventario - Stock,  Lotes, Vencimientos, Alertas
"""
from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from apps.inventario.models import (
    StockUnico, MovimientosStock, AlertasStock,
    LotesProducto, AlertasVencimiento
)
from apps.inventario.services import StockService
from apps.productos.models import Productos, UnidadesMedida, Categorias
from apps.usuarios.models import Empleados, Roles
from apps.contabilidad.models import Impuestos


class StockServiceTest(TransactionTestCase):
    """
    Tests para StockService.
    
    Usa TransactionTestCase porque necesitamos probar transacciones reales.
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=Decimal('10.00'),
            vigente_desde=timezone.now().date(),
            activo=True
        )
        
        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre='Unidad',
            abreviatura='un'
        )
        
        # Crear categoría
        self.categoria = Categorias.objects.create(
            nombre='Bebidas'
        )
        
        # Crear productos
        self.producto_con_stock = Productos.objects.create(
            descripcion='Coca Cola 500ml',
            codigo_barra='7891234567890',
            stock_minimo=Decimal('10.000'),
            permite_stock_negativo=False,
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
        
        self.producto_sin_stock = Productos.objects.create(
            descripcion='Pepsi 500ml',
            codigo_barra='7891234567891',
            stock_minimo=Decimal('10.000'),
            permite_stock_negativo=False,
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
        
        self.producto_permite_negativo = Productos.objects.create(
            descripcion='Sprite 500ml',
            codigo_barra='7891234567892',
            stock_minimo=Decimal('5.000'),
            permite_stock_negativo=True,  # Permite stock negativo
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
        
        # Crear stock
        self.stock_disponible = StockUnico.objects.create(
            id_producto=self.producto_con_stock,
            cantidad=Decimal('50.000')
        )
        
        self.stock_cero = StockUnico.objects.create(
            id_producto=self.producto_sin_stock,
            cantidad=Decimal('0.000')
        )
        
        self.stock_permite_negativo = StockUnico.objects.create(
            id_producto=self.producto_permite_negativo,
            cantidad=Decimal('5.000')
        )
        
        # Crear rol y empleado
        self.rol = Roles.objects.create(
            nombre_rol='Cajero',
            descripcion='Cajero de ventas'
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Pérez',
            usuario='juan_perez',
            contrasena_hash='hash123',
            fecha_ingreso=timezone.now(),
            email='juan@test.com',
            activo=True,
            id_rol=self.rol
        )
    
    def test_validar_disponibilidad_stock_suficiente(self):
        """Test: Debe validar que haya stock disponible"""
        validacion = StockService.validar_disponibilidad(
            producto_id=self.producto_con_stock.id_producto,
            cantidad_solicitada=Decimal('10.000')
        )
        
        self.assertTrue(validacion['disponible'])
        self.assertEqual(validacion['stock_actual'], Decimal('50.000'))
        self.assertEqual(validacion['faltante'], Decimal('0.000'))
    
    def test_validar_disponibilidad_stock_insuficiente(self):
        """Test: Debe detectar stock insuficiente"""
        validacion = StockService.validar_disponibilidad(
            producto_id=self.producto_sin_stock.id_producto,
            cantidad_solicitada=Decimal('5.000')
        )
        
        self.assertFalse(validacion['disponible'])
        self.assertEqual(validacion['stock_actual'], Decimal('0.000'))
        self.assertEqual(validacion['faltante'], Decimal('5.000'))
    
    def test_validar_disponibilidad_stock_negativo_permitido(self):
        """Test: Stock negativo permitido"""
        validacion = StockService.validar_disponibilidad(
            producto_id=self.producto_permite_negativo.id_producto,
            cantidad_solicitada=Decimal('10.000')  # Más del disponible
        )
        
        # Debe estar disponible porque permite stock negativo
        self.assertTrue(validacion['disponible'])
        self.assertTrue(validacion['permite_negativo'])
        self.assertEqual(validacion['stock_actual'], Decimal('5.000'))
    
    def test_validar_disponibilidad_multiple_productos(self):
        """Test: Validar múltiples productos a la vez"""
        items = [
            {'id_producto': self.producto_con_stock.id_producto, 'cantidad': Decimal('10.000')},
            {'id_producto': self.producto_sin_stock.id_producto, 'cantidad': Decimal('5.000')},
            {'id_producto': self.producto_permite_negativo.id_producto, 'cantidad': Decimal('20.000')}
        ]
        
        validacion = StockService.validar_disponibilidad_multiple(items)
        
        # No todo está disponible (producto_sin_stock falla)
        self.assertFalse(validacion['todo_disponible'])
        
        # Debe haber 1 producto faltante
        self.assertEqual(len(validacion['productos_faltantes']), 1)
        self.assertEqual(
            validacion['productos_faltantes'][0]['producto']['id'],
            self.producto_sin_stock.id_producto
        )
        
        # Debe haber 3 items total
        self.assertEqual(len(validacion['items']), 3)
    
    def test_reservar_stock_exitoso(self):
        """Test: Debe reservar stock correctamente"""
        stock_inicial = self.stock_disponible.cantidad
        cantidad_reservar = Decimal('10.000')
        
        # Reservar stock
        stock = StockService.reservar_stock(
            producto_id=self.producto_con_stock.id_producto,
            cantidad=cantidad_reservar,
            empleado=self.empleado,
            motivo='venta'
        )
        
        # Verificar que se descontó
        self.assertEqual(stock.cantidad, stock_inicial - cantidad_reservar)
        self.assertEqual(stock.cantidad, Decimal('40.000'))
        
        # Verificar que se registró el movimiento
        movimientos = MovimientosStock.objects.filter(
            id_producto=self.producto_con_stock,
            tipo_movimiento='Egreso',
            motivo='venta'
        )
        self.assertEqual(movimientos.count(), 1)
        self.assertEqual(movimientos.first().cantidad, cantidad_reservar)
    
    def test_reservar_stock_sin_disponibilidad(self):
        """Test: Debe fallar al reservar stock insuficiente"""
        # Intentar reservar más stock del disponible
        with self.assertRaises(ValidationError) as context:
            StockService.reservar_stock(
                producto_id=self.producto_sin_stock.id_producto,
                cantidad=Decimal('10.000'),
                empleado=self.empleado,
                motivo='venta'
            )
        
        # Verificar mensaje de error
        self.assertIn('Stock insuficiente', str(context.exception))
    
    def test_reservar_stock_cantidad_cero(self):
        """Test: Debe fallar si cantidad es 0 o negativa"""
        with self.assertRaises(ValidationError):
            StockService.reservar_stock(
                producto_id=self.producto_con_stock.id_producto,
                cantidad=Decimal('0.000'),
                empleado=self.empleado,
                motivo='venta'
            )
        
        with self.assertRaises(ValidationError):
            StockService.reservar_stock(
                producto_id=self.producto_con_stock.id_producto,
                cantidad=Decimal('-5.000'),
                empleado=self.empleado,
                motivo='venta'
            )


class LotesProductoTest(TestCase):
    """Tests para LotesProducto y control de vencimientos"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuesto
        self.impuesto_5 = Impuestos.objects.create(
            nombre_impuesto='IVA 5%',
            porcentaje=Decimal('5.00'),
            vigente_desde=timezone.now().date(),
            activo=True
        )
        
        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre='Unidad',
            abreviatura='un'
        )
        
        # Crear categoría
        self.categoria = Categorias.objects.create(
            nombre='Lácteos'
        )
        
        # Crear producto
        self.producto = Productos.objects.create(
            descripcion='Leche Entera 1L',
            codigo_barra='7891234567890',
            stock_minimo=Decimal('20.000'),
            activo=True,
            id_impuesto=self.impuesto_5,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
    
    def test_crear_lote_producto(self):
        """Test: Crear lote de producto"""
        fecha_venc = timezone.now().date() + timedelta(days=60)
        
        lote = LotesProducto.objects.create(
            numero_lote='LOT-2026-001',
            id_producto=self.producto,
            cantidad_inicial=Decimal('100.000'),
            cantidad_disponible=Decimal('100.000'),
            fecha_vencimiento=fecha_venc
        )
        
        self.assertIsNotNone(lote)
        self.assertEqual(lote.numero_lote, 'LOT-2026-001')
        self.assertEqual(lote.cantidad_disponible, Decimal('100.000'))
        self.assertFalse(lote.bloqueado)
    
    def test_lote_vencido(self):
        """Test: Detectar lote vencido"""
        # Crear lote con fecha pasada
        fecha_venc = timezone.now().date() - timedelta(days=5)
        
        lote = LotesProducto.objects.create(
            numero_lote='LOT-2026-002',
            id_producto=self.producto,
            cantidad_inicial=Decimal('50.000'),
            cantidad_disponible=Decimal('50.000'),
            fecha_vencimiento=fecha_venc
        )
        
        # Debe estar vencido
        self.assertTrue(lote.esta_vencido)
        self.assertEqual(lote.dias_hasta_vencimiento, lote.dias_hasta_vencimiento)
        self.assertTrue(lote.dias_hasta_vencimiento < 0)
    
    def test_lote_proximo_a_vencer(self):
        """Test: Detectar lote próximo a vencer"""
        # Crear lote que vence en 10 días
        fecha_venc = timezone.now().date() + timedelta(days=10)
        
        lote = LotesProducto.objects.create(
            numero_lote='LOT-2026-003',
            id_producto=self.producto,
            cantidad_inicial=Decimal('30.000'),
            cantidad_disponible=Decimal('30.000'),
            fecha_vencimiento=fecha_venc
        )
        
        # Debe estar próximo a vencer (< 15 días)
        self.assertTrue(lote.proximo_a_vencer)
        self.assertFalse(lote.esta_vencido)
        self.assertEqual(lote.dias_hasta_vencimiento, 10)
    
    def test_fifo_ordenamiento(self):
        """Test: FIFO - Lotes ordenados por fecha vencimiento"""
        # Crear varios lotes con diferentes fechas
        lote1 = LotesProducto.objects.create(
            numero_lote='LOT-001',
            id_producto=self.producto,
            cantidad_inicial=Decimal('10.000'),
            cantidad_disponible=Decimal('10.000'),
            fecha_vencimiento=timezone.now().date() + timedelta(days=90)
        )
        
        lote2 = LotesProducto.objects.create(
            numero_lote='LOT-002',
            id_producto=self.producto,
            cantidad_inicial=Decimal('15.000'),
            cantidad_disponible=Decimal('15.000'),
            fecha_vencimiento=timezone.now().date() + timedelta(days=30)
        )
        
        lote3 = LotesProducto.objects.create(
            numero_lote='LOT-003',
            id_producto=self.producto,
            cantidad_inicial=Decimal('20.000'),
            cantidad_disponible=Decimal('20.000'),
            fecha_vencimiento=timezone.now().date() + timedelta(days=60)
        )
        
        # Obtener lotes disponibles (ordenados por FIFO)
        lotes = LotesProducto.objects.filter(
            id_producto=self.producto,
            bloqueado=False
        ).order_by('fecha_vencimiento')
        
        # El primero debe ser LOT-002 (vence en 30 días)
        self.assertEqual(lotes[0].numero_lote, 'LOT-002')
        self.assertEqual(lotes[1].numero_lote, 'LOT-003')
        self.assertEqual(lotes[2].numero_lote, 'LOT-001')


class AlertasStockTest(TestCase):
    """Tests para AlertasStock"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=Decimal('10.00'),
            vigente_desde=timezone.now().date(),
            activo=True
        )
        
        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre='Unidad',
            abreviatura='un'
        )
        
        # Crear categoría
        self.categoria = Categorias.objects.create(
            nombre='Lácteos'
        )
        
        # Crear producto
        self.producto = Productos.objects.create(
            descripcion='Agua Mineral 500ml',
            codigo_barra='7891234567890',
            stock_minimo=Decimal('50.000'),
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
        
        # Crear stock bajo mínimo
        self.stock = StockUnico.objects.create(
            id_producto=self.producto,
            cantidad=Decimal('10.000')  # Menor al stock_minimo (50)
        )
    
    def test_crear_alerta_stock_bajo(self):
        """Test: Crear alerta de stock bajo"""
        alerta = AlertasStock.objects.create(
            id_producto=self.producto,
            tipo_alerta='stock_minimo',
            stock_actual=self.stock.cantidad,
            stock_minimo=self.producto.stock_minimo,
            activa=True
        )
        
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.tipo_alerta, 'stock_minimo')
        self.assertTrue(alerta.activa)
    
    def test_crear_alerta_stock_critico(self):
        """Test: Crear alerta de stock crítico"""
        # Stock a 0
        self.stock.cantidad = Decimal('0.000')
        self.stock.save()
        
        alerta = AlertasStock.objects.create(
            id_producto=self.producto,
            tipo_alerta='stock_cero',
            stock_actual=Decimal('0.000'),
            stock_minimo=self.producto.stock_minimo,
            activa=True
        )
        
        self.assertEqual(alerta.tipo_alerta, 'stock_cero')


class AlertasVencimientoTest(TestCase):
    """Tests para AlertasVencimiento"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=Decimal('10.00'),
            vigente_desde=timezone.now().date(),
            activo=True
        )
        
        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre='Kilogramo',
            abreviatura='kg'
        )
        
        # Crear categoría
        self.categoria = Categorias.objects.create(
            nombre='Carnes'
        )
        
        # Crear producto
        self.producto = Productos.objects.create(
            descripcion='Carne Molida',
            codigo_barra='7891234567890',
            stock_minimo=Decimal('5.000'),
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria
        )
        
        # Crear lote próximo a vencer
        self.lote = LotesProducto.objects.create(
            numero_lote='LOT-CARNE-001',
            id_producto=self.producto,
            cantidad_inicial=Decimal('20.000'),
            cantidad_disponible=Decimal('20.000'),
            fecha_vencimiento=timezone.now().date() + timedelta(days=7)
        )
    
    def test_crear_alerta_vencimiento_7_dias(self):
        """Test: Crear alerta para 7 días"""
        alerta = AlertasVencimiento.objects.create(
            id_lote=self.lote,
            tipo_alerta='7_dias',
            dias_restantes=7,
            fecha_vencimiento=self.lote.fecha_vencimiento,
            cantidad_lote=self.lote.cantidad_disponible,
            accion_tomada='pendiente'
        )
        
        self.assertEqual(alerta.tipo_alerta, '7_dias')
        self.assertEqual(alerta.accion_tomada, 'pendiente')
        self.assertEqual(alerta.id_lote, self.lote)
    
    def test_crear_alerta_vencido(self):
        """Test: Crear alerta para producto vencido"""
        # Crear lote vencido
        lote_vencido = LotesProducto.objects.create(
            numero_lote='LOT-VENCIDO',
            id_producto=self.producto,
            cantidad_inicial=Decimal('10.000'),
            cantidad_disponible=Decimal('5.000'),
            fecha_vencimiento=timezone.now().date() - timedelta(days=2),
            bloqueado=True,
            motivo_bloqueo='vencido'
        )
        
        alerta = AlertasVencimiento.objects.create(
            id_lote=lote_vencido,
            tipo_alerta='vencido',
            dias_restantes=-2,
            fecha_vencimiento=lote_vencido.fecha_vencimiento,
            cantidad_lote=lote_vencido.cantidad_disponible,
            accion_tomada='pendiente'
        )
        
        self.assertEqual(alerta.tipo_alerta, 'vencido')
        self.assertTrue(lote_vencido.bloqueado)
