"""
Tests para modelos de la app ventas
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import (
    Ventas, DetallesVenta, PagosVenta, AplicacionPagosVentas,
    NotasCreditoCliente, DetallesNotaCredito,
    Promociones, CategoriasPromocion, ProductosPromocion, PromocionesAplicadas,
    CondicionVenta,
)
from apps.clientes.models import Clientes, TiposCliente
from apps.productos.models import ListasPrecios, Productos, Categorias
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles
from apps.core.models import MediosPago
from apps.inventario.models import StockUnico


class VentasModelTest(TestCase):
    """Tests para el modelo Ventas y sus propiedades"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Cajero", estado=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Carlos",
            apellido="Mendoza",
            usuario="carlos.mendoza",
            email="carlos@example.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista="Lista Minorista", moneda="PYG", estado=True
        )

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="María",
            apellidos="López",
            ruc_ci="8888888888",
            limite_credito=Decimal("500000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, requiere_validacion=False, estado=True
        )

    def test_str_method(self):
        """Test del método __str__"""
        venta = Ventas.objects.create(
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        expected = f"Venta #{venta.id_venta} - {self.cliente} ($100000.00)"
        self.assertEqual(str(venta), expected)

    def test_esta_pagada_true_por_saldo_cero(self):
        """Test de esta_pagada cuando saldo_pendiente es cero"""
        venta = Ventas.objects.create(
            monto_total=Decimal("50000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="parcial",
            estado="activa",
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertTrue(venta.esta_pagada)

    def test_esta_pagada_true_por_estado(self):
        """Test de esta_pagada cuando estado_pago es 'pagada'"""
        venta = Ventas.objects.create(
            monto_total=Decimal("75000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertTrue(venta.esta_pagada)

    def test_esta_pagada_false(self):
        """Test de esta_pagada cuando hay saldo pendiente"""
        venta = Ventas.objects.create(
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("50000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertFalse(venta.esta_pagada)

    def test_monto_pagado_con_saldo_pendiente(self):
        """Test de monto_pagado cuando hay saldo pendiente"""
        venta = Ventas.objects.create(
            monto_total=Decimal("200000.00"),
            saldo_pendiente=Decimal("80000.00"),
            estado_pago="parcial",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        # monto_pagado = monto_total - saldo_pendiente
        # 200000 - 80000 = 120000
        self.assertEqual(venta.monto_pagado, Decimal("120000.00"))

    def test_monto_pagado_sin_saldo_pendiente(self):
        """Test de monto_pagado cuando está completamente pagada"""
        venta = Ventas.objects.create(
            monto_total=Decimal("150000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(venta.monto_pagado, Decimal("150000.00"))

    def test_crear_venta_contado(self):
        """Test de creación de venta al contado"""
        venta = Ventas.objects.create(
            monto_total=Decimal("25000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(venta.tipo_venta, "contado")
        self.assertTrue(venta.esta_pagada)
        self.assertEqual(venta.monto_pagado, Decimal("25000.00"))

    def test_crear_venta_credito(self):
        """Test de creación de venta a crédito"""
        venta = Ventas.objects.create(
            monto_total=Decimal("300000.00"),
            saldo_pendiente=Decimal("300000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            motivo_credito="Cliente frecuente",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(venta.tipo_venta, "credito")
        self.assertFalse(venta.esta_pagada)
        self.assertEqual(venta.saldo_pendiente, Decimal("300000.00"))
        self.assertEqual(venta.monto_pagado, Decimal("0.00"))

    def test_venta_con_autorizacion(self):
        """Test de venta que requiere autorización"""
        supervisor = Empleados.objects.create(
            nombre="Supervisor",
            apellido="Jefe",
            usuario="supervisor",
            email="supervisor@example.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        venta = Ventas.objects.create(
            monto_total=Decimal("500000.00"),
            saldo_pendiente=Decimal("500000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            autorizado_por=supervisor,
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertIsNotNone(venta.autorizado_por)
        self.assertEqual(venta.autorizado_por, supervisor)


class VentasModelsAdicionalesTest(TestCase):
    """Tests __str__ y propiedades de modelos adicionales de ventas."""

    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol='Cajero Str', estado=True)
        self.empleado = Empleados.objects.create(
            nombre='Emp', apellido='Str', usuario='emp_str',
            email='emp_str@test.com', fecha_ingreso=timezone.now().date(), estado=True, id_rol=self.rol,
        )
        self.lista = ListasPrecios.objects.create(nombre_lista='Lista Str Ventas', moneda='PYG', estado=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo='Tipo Str V', estado=True)
        self.cliente = Clientes.objects.create(
            nombres='CLI', apellidos='STR', ruc_ci='5000002',
            estado=True, id_lista=self.lista, id_tipo_cliente=self.tipo_cliente,
        )
        self.medio_pago = MediosPago.objects.create(
            nombre='Efectivo Str', genera_comision=False, estado=True,
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA Str V', porcentaje=10,
            vigente_desde=timezone.now().date(), estado=True,
        )
        self.cat = Categorias.objects.create(nombre='Cat Str V', estado=True)
        self.producto = Productos.objects.create(
            descripcion='Prod Str V', stock_minimo=0,
            estado=True, id_categoria=self.cat, id_impuesto=self.impuesto,
        )
        StockUnico.objects.create(id_producto=self.producto, cantidad=Decimal('50.000'))
        self.venta = Ventas.objects.create(
            monto_total=Decimal('10000'),
            estado_pago='pagada',
            estado='Activa',
            tipo_venta='contado',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

    def test_ventas_manager_total_venta_kwarg(self):
        """VentasManager.create() cuando se pasa total_venta pero no monto_total."""
        venta = Ventas.objects.create(
            total_venta=Decimal('5000'),
            estado_pago='pagada',
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )
        self.assertEqual(venta.monto_total, Decimal('5000'))

    def test_detalles_venta_manager_sin_subtotal(self):
        """DetallesVentaManager.create() calcula subtotal automáticamente."""
        detalle = DetallesVenta.objects.create(
            cantidad=Decimal('3'),
            precio_unitario=Decimal('2000'),
            id_producto=self.producto,
            id_venta=self.venta,
        )
        self.assertEqual(detalle.subtotal, Decimal('6000'))

    def test_str_pagos_venta(self):
        pago = PagosVenta.objects.create(
            monto=Decimal('10000'),
            monto_comision=Decimal('500'),
            fecha_pago=timezone.now(),
            estado='Confirmado',
            id_medio_pago=self.medio_pago,
            id_venta=self.venta,
        )
        self.assertIn('Pago #', str(pago))

    def test_pagos_venta_total_cobrado(self):
        pago = PagosVenta.objects.create(
            monto=Decimal('10000'),
            monto_comision=Decimal('500'),
            fecha_pago=timezone.now(),
            estado='Confirmado',
            id_medio_pago=self.medio_pago,
            id_venta=self.venta,
        )
        self.assertEqual(pago.total_cobrado, Decimal('10500'))

    def test_pagos_venta_porcentaje_comision(self):
        pago = PagosVenta.objects.create(
            monto=Decimal('10000'),
            monto_comision=Decimal('500'),
            fecha_pago=timezone.now(),
            estado='Confirmado',
            id_medio_pago=self.medio_pago,
            id_venta=self.venta,
        )
        self.assertEqual(pago.porcentaje_comision_aplicado, Decimal('5'))

    def test_str_aplicacion_pagos_ventas(self):
        pago = PagosVenta.objects.create(
            monto=Decimal('10000'), monto_comision=Decimal('0'),
            fecha_pago=timezone.now(), estado='Confirmado',
            id_medio_pago=self.medio_pago, id_venta=self.venta,
        )
        aplic = AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal('10000'),
            id_pago_venta=pago,
            id_venta=self.venta,
        )
        self.assertIn('#', str(aplic))

    def test_str_notas_credito_cliente(self):
        nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=1,
            fecha_emision=timezone.now(),
            motivo='Test str',
            monto_total=Decimal('5000'),
            estado='Emitida',
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
        )
        self.assertIn('#', str(nota))

    def test_str_detalles_nota_credito(self):
        nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=2,
            fecha_emision=timezone.now(),
            motivo='Test str detalle',
            monto_total=Decimal('3000'),
            estado='Emitida',
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
        )
        det = DetallesNotaCredito.objects.create(
            cantidad=Decimal('1'),
            precio_unitario=Decimal('3000'),
            subtotal=Decimal('3000'),
            id_nota=nota,
            id_producto=self.producto,
        )
        self.assertIn('#', str(det))

    def test_str_promociones(self):
        promo = Promociones.objects.create(
            nombre='Promo Str', tipo_promocion='porcentaje',
            valor_descuento=Decimal('10'), fecha_inicio=timezone.now().date(),
            aplica_a='todo', min_cantidad=1, monto_minimo=Decimal('0'),
            usos_actuales=0, prioridad=1, estado=True,
            requiere_codigo=False, fecha_creacion=timezone.now(),
        )
        self.assertIn('#', str(promo))

    def test_str_categorias_promocion(self):
        promo = Promociones.objects.create(
            nombre='Promo Cat Str', tipo_promocion='porcentaje',
            valor_descuento=Decimal('5'), fecha_inicio=timezone.now().date(),
            aplica_a='categorias', min_cantidad=1, monto_minimo=Decimal('0'),
            usos_actuales=0, prioridad=2, estado=True,
            requiere_codigo=False, fecha_creacion=timezone.now(),
        )
        cp = CategoriasPromocion.objects.create(id_categoria=self.cat, id_promocion=promo)
        self.assertIn('#', str(cp))

    def test_str_productos_promocion(self):
        promo = Promociones.objects.create(
            nombre='Promo Prod Str', tipo_promocion='monto_fijo',
            valor_descuento=Decimal('1000'), fecha_inicio=timezone.now().date(),
            aplica_a='productos', min_cantidad=1, monto_minimo=Decimal('0'),
            usos_actuales=0, prioridad=3, estado=True,
            requiere_codigo=False, fecha_creacion=timezone.now(),
        )
        pp = ProductosPromocion.objects.create(id_producto=self.producto, id_promocion=promo)
        self.assertIn('#', str(pp))

    def test_str_promociones_aplicadas(self):
        promo = Promociones.objects.create(
            nombre='Promo Aplic Str', tipo_promocion='porcentaje',
            valor_descuento=Decimal('10'), fecha_inicio=timezone.now().date(),
            aplica_a='todo', min_cantidad=1, monto_minimo=Decimal('0'),
            usos_actuales=1, prioridad=4, estado=True,
            requiere_codigo=False, fecha_creacion=timezone.now(),
        )
        pa = PromocionesAplicadas.objects.create(
            monto_descontado=Decimal('1000'),
            fecha_aplicacion=timezone.now(),
            id_promocion=promo,
            id_venta=self.venta,
        )
        self.assertIn('#', str(pa))
    
    def test_str_condicion_venta(self):
        """Test para __str__ de CondicionVenta - Cubrir línea 511"""
        condicion = CondicionVenta.objects.create(nombre='Contado')
        self.assertEqual(str(condicion), 'Contado')
