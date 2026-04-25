"""
Tests finales para alcanzar 100% cobertura en compras.services
Cubre líneas: 80-81, 86-87, 196-199, branch 281->288
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, PropertyMock

from apps.compras.models import Compras, DetallesCompra, Proveedores
from apps.compras.services import CompraService
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles


class ValidarCompraStringConversionTest(TestCase):
    """Tests para cubrir excepciones en conversión de strings (L80-81, L86-87)"""
    
    def setUp(self):
        """Setup común"""
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=Decimal('10.00'),
            vigente_desde=timezone.now().date(),
            estado=True
        )
        self.categoria = Categorias.objects.create(nombre='Test', estado=True)
        self.unidad = UnidadesMedida.objects.create(nombre='Unidad', abreviatura='U')
        self.producto = Productos.objects.create(
            codigo_barra='PROD001',
            descripcion='Producto Test',
            stock_minimo=Decimal('10.000'),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad
        )
    
    @patch('apps.compras.services.Decimal')
    def test_validar_compra_cantidad_string_value_error(self, mock_decimal):
        """
        Cubrir L80-81: except (ValueError, TypeError) cuando Decimal()
        lanza ValueError al convertir cantidad
        """
        # Arrange: mock Decimal para lanzar ValueError
        def decimal_side_effect(value):
            if value == 'bad_cantidad':
                raise ValueError("Invalid cantidad")
            return Decimal(str(value))
        
        mock_decimal.side_effect = decimal_side_effect
        
        detalles = [
            {
                'id_producto': self.producto.id_producto,
                'cantidad': 'bad_cantidad',  # Trigger ValueError
                'precio_unitario': '1000.00'
            }
        ]
        
        # Act
        resultado = CompraService.validar_compra(detalles)
        
        # Assert: debe generar error porque cantidad es None
        self.assertFalse(resultado['valido'])
        self.assertTrue(len(resultado['errores']) > 0)
    
    @patch('apps.compras.services.Decimal')
    def test_validar_compra_precio_string_type_error(self, mock_decimal):
        """
        Cubrir L86-87: except (ValueError, TypeError) cuando Decimal()
        lanza TypeError al convertir precio_unitario
        """
        # Arrange: mock Decimal para lanzar TypeError
        def decimal_side_effect(value):
            if value == 'bad_precio':
                raise TypeError("Invalid precio")
            return Decimal(str(value))
        
        mock_decimal.side_effect = decimal_side_effect
        
        detalles = [
            {
                'id_producto': self.producto.id_producto,
                'cantidad': '5.0',
                'precio_unitario': 'bad_precio'  # Trigger TypeError
            }
        ]
        
        # Act
        resultado = CompraService.validar_compra(detalles)
        
        # Assert: debe generar error porque precio_unitario es None
        self.assertFalse(resultado['valido'])
        self.assertTrue(len(resultado['errores']) > 0)


class ConfirmarCompraSinEmpleadosTest(TestCase):
    """Tests para cubrir L196-199: confirmar sin empleados en sistema"""
    
    def setUp(self):
        """Setup común"""
        self.proveedor = Proveedores.objects.create(
            razon_social='Proveedor Test',
            ruc='12345678-9',
            fecha_registro=timezone.now(),
            estado=True
        )
        
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=Decimal('10.00'),
            vigente_desde=timezone.now().date(),
            estado=True
        )
        self.categoria = Categorias.objects.create(nombre='Test', estado=True)
        self.unidad = UnidadesMedida.objects.create(nombre='Unidad', abreviatura='U')
        self.producto = Productos.objects.create(
            codigo_barra='PROD002',
            descripcion='Producto Test 2',
            stock_minimo=Decimal('10.000'),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad
        )
        
        # Crear compra pendiente con detalles
        self.compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal('10000.00'),
            saldo_pendiente=Decimal('10000.00'),
            estado_pago='Pendiente',
            id_proveedor=self.proveedor
        )
        
        DetallesCompra.objects.create(
            id_compra=self.compra,
            id_producto=self.producto,
            cantidad=Decimal('10.000'),
            costo_unitario=Decimal('1000.00'),
            subtotal=Decimal('10000.00'),
            monto_iva=Decimal('0.00')
        )
    
    def test_confirmar_compra_sin_empleados_registrados(self):
        """
        Cubrir L196-199: cuando no hay empleados en el sistema,
        confirmar_compra retorna error específico
        """
        # Arrange: asegurar que no hay empleados en el sistema
        Empleados.objects.all().delete()
        
        # Act: intentar confirmar sin empleado y sin empleados en DB
        resultado = CompraService.confirmar_compra(
            id_compra=self.compra.id_compra,
            empleado=None
        )
        
        # Assert: debe retornar error específico
        self.assertFalse(resultado['exito'])
        self.assertIn('empleados registrados', resultado['error'].lower())
        self.assertEqual(resultado['id_compra'], self.compra.id_compra)
    
    def test_confirmar_compra_con_empleado_valido(self):
        """
        Cubrir branch 196->198: cuando empleado NO es None,
        salta el if de línea 196 y va directo a línea 198 (siguiente código)
        """
        # Arrange: crear rol y empleado
        rol = Roles.objects.create(
            nombre_rol='Gerente',
            descripcion='Rol de gerente',
            estado=True
        )
        
        empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Perez',
            usuario='jperez',
            contrasena_hash='hash123',
            fecha_ingreso=timezone.now(),
            id_rol=rol,
            estado=True
        )
        
        # Act: confirmar con empleado válido
        resultado = CompraService.confirmar_compra(
            id_compra=self.compra.id_compra,
            empleado=empleado
        )
        
        # Assert: debe confirmar exitosamente
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['id_compra'], self.compra.id_compra)
        
        # Verificar que la compra cambió a estado Confirmado
        self.compra.refresh_from_db()
        self.assertEqual(self.compra.estado_pago, 'Confirmado')


class CalcularTotalesIvaExentoTest(TestCase):
    """Tests para cubrir branch 281->288: IVA exento (0%)"""
    
    def setUp(self):
        """Setup común"""
        # Crear impuesto exento (0%)
        self.impuesto_exento = Impuestos.objects.create(
            nombre_impuesto='IVA 0% (Exento)',
            porcentaje=Decimal('0.00'),
            vigente_desde=timezone.now().date(),
            estado=True
        )
        
        self.categoria = Categorias.objects.create(nombre='Test', estado=True)
        self.unidad = UnidadesMedida.objects.create(nombre='Unidad', abreviatura='U')
        
        # Producto con IVA exento
        self.producto_exento = Productos.objects.create(
            codigo_barra='PROD_EXENTO',
            descripcion='Producto Exento',
            stock_minimo=Decimal('10.000'),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto_exento,
            id_unidad_medida=self.unidad
        )
    
    def test_calcular_totales_con_iva_exento(self):
        """
        Cubrir branch 281->288: cuando porcentaje_iva == 0.00,
        no entra en if ni elif, salta directo a subtotal += subtotal_linea
        """
        # Arrange: detalle con producto exento
        detalles = [
            {
                'id_producto': self.producto_exento.id_producto,
                'cantidad': 10,
                'precio_unitario': '2000.00'
            }
        ]
        
        # Act
        resultado = CompraService.calcular_totales_compra(detalles)
        
        # Assert: debe calcular totales con IVA 0
        self.assertEqual(resultado['subtotal'], Decimal('20000.00'))
        self.assertEqual(resultado['iva_5'], Decimal('0.00'))
        self.assertEqual(resultado['iva_10'], Decimal('0.00'))
        self.assertEqual(resultado['total'], Decimal('20000.00'))
    
    def test_calcular_totales_con_iva_diferente(self):
        """
        Cubrir branch 281->288: IVA con porcentaje diferente de 5% y 10%
        (ejemplo: 21%, 15%, etc.) tampoco entra en if/elif
        """
        # Arrange: crear impuesto con porcentaje no estándar
        impuesto_21 = Impuestos.objects.create(
            nombre_impuesto='IVA 21%',
            porcentaje=Decimal('21.00'),
            vigente_desde=timezone.now().date(),
            estado=True
        )
        
        producto_21 = Productos.objects.create(
            codigo_barra='PROD_21',
            descripcion='Producto 21%',
            stock_minimo=Decimal('10.000'),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=impuesto_21,
            id_unidad_medida=self.unidad
        )
        
        detalles = [
            {
                'id_producto': producto_21.id_producto,
                'cantidad': 5,
                'precio_unitario': '1000.00'
            }
        ]
        
        # Act
        resultado = CompraService.calcular_totales_compra(detalles)
        
        # Assert: no suma IVA porque no es 5% ni 10%
        self.assertEqual(resultado['subtotal'], Decimal('5000.00'))
        self.assertEqual(resultado['iva_5'], Decimal('0.00'))
        self.assertEqual(resultado['iva_10'], Decimal('0.00'))
        # Total = subtotal (sin IVA adicional)
        self.assertEqual(resultado['total'], Decimal('5000.00'))
