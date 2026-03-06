"""
Tests para modelos de la app ventas
Sprint 2 - Backend Coverage Improvement
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import Ventas
from apps.clientes.models import Clientes, TiposCliente
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles
from apps.core.models import MediosPago


class VentasModelTest(TestCase):
    """Tests para el modelo Ventas y sus propiedades"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(
            nombre_rol='Cajero',
            activo=True
        )
        
        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre='Carlos',
            apellido='Mendoza',
            usuario='carlos.mendoza',
            email='carlos@example.com',
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol
        )
        
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista='Lista Minorista',
            moneda='PYG',
            activo=True
        )
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Regular',
            activo=True
        )
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres='María',
            apellidos='López',
            ruc_ci='8888888888',
            limite_credito=Decimal('500000.00'),
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente
        )
        
        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            descripcion='Efectivo',
            genera_comision=False,
            requiere_validacion=False,
            activo=True
        )

    def test_str_method(self):
        """Test del método __str__"""
        venta = Ventas.objects.create(
            monto_total=Decimal('100000.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='contado',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        expected = f"Venta #{venta.id_venta} - {self.cliente} ($100000.00)"
        self.assertEqual(str(venta), expected)

    def test_esta_pagada_true_por_saldo_cero(self):
        """Test de esta_pagada cuando saldo_pendiente es cero"""
        venta = Ventas.objects.create(
            monto_total=Decimal('50000.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='parcial',
            estado='activa',
            tipo_venta='contado',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertTrue(venta.esta_pagada)

    def test_esta_pagada_true_por_estado(self):
        """Test de esta_pagada cuando estado_pago es 'pagada'"""
        venta = Ventas.objects.create(
            monto_total=Decimal('75000.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='credito',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertTrue(venta.esta_pagada)

    def test_esta_pagada_false(self):
        """Test de esta_pagada cuando hay saldo pendiente"""
        venta = Ventas.objects.create(
            monto_total=Decimal('100000.00'),
            saldo_pendiente=Decimal('50000.00'),
            estado_pago='pendiente',
            estado='activa',
            tipo_venta='credito',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertFalse(venta.esta_pagada)

    def test_monto_pagado_con_saldo_pendiente(self):
        """Test de monto_pagado cuando hay saldo pendiente"""
        venta = Ventas.objects.create(
            monto_total=Decimal('200000.00'),
            saldo_pendiente=Decimal('80000.00'),
            estado_pago='parcial',
            estado='activa',
            tipo_venta='credito',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        # monto_pagado = monto_total - saldo_pendiente
        # 200000 - 80000 = 120000
        self.assertEqual(
            venta.monto_pagado,
            Decimal('120000.00')
        )

    def test_monto_pagado_sin_saldo_pendiente(self):
        """Test de monto_pagado cuando está completamente pagada"""
        venta = Ventas.objects.create(
            monto_total=Decimal('150000.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='contado',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertEqual(
            venta.monto_pagado,
            Decimal('150000.00')
        )

    def test_crear_venta_contado(self):
        """Test de creación de venta al contado"""
        venta = Ventas.objects.create(
            monto_total=Decimal('25000.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='contado',
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertEqual(venta.tipo_venta, 'contado')
        self.assertTrue(venta.esta_pagada)
        self.assertEqual(venta.monto_pagado, Decimal('25000.00'))

    def test_crear_venta_credito(self):
        """Test de creación de venta a crédito"""
        venta = Ventas.objects.create(
            monto_total=Decimal('300000.00'),
            saldo_pendiente=Decimal('300000.00'),
            estado_pago='pendiente',
            estado='activa',
            tipo_venta='credito',
            motivo_credito='Cliente frecuente',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertEqual(venta.tipo_venta, 'credito')
        self.assertFalse(venta.esta_pagada)
        self.assertEqual(venta.saldo_pendiente, Decimal('300000.00'))
        self.assertEqual(venta.monto_pagado, Decimal('0.00'))

    def test_venta_con_autorizacion(self):
        """Test de venta que requiere autorización"""
        supervisor = Empleados.objects.create(
            nombre='Supervisor',
            apellido='Jefe',
            usuario='supervisor',
            email='supervisor@example.com',
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol
        )
        
        venta = Ventas.objects.create(
            monto_total=Decimal('500000.00'),
            saldo_pendiente=Decimal('500000.00'),
            estado_pago='pendiente',
            estado='activa',
            tipo_venta='credito',
            autorizado_por=supervisor,
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago
        )
        
        self.assertIsNotNone(venta.autorizado_por)
        self.assertEqual(venta.autorizado_por, supervisor)
