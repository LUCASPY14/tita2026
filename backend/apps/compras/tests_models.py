"""
Tests complementarios para modelos de compras
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.compras.models import (
    Compras,
    DetallesCompra,
    Proveedores,
    PagosProveedores,
    AplicacionPagosCompras,
    NotasCreditoProveedor,
    DetallesNotaCreditoProveedor,
)
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles
from apps.core.models import MediosPago


class ProveedoresModelTest(TestCase):
    """Tests para el modelo Proveedores"""

    def test_crear_proveedor(self):
        """Test de creación de proveedor"""
        proveedor = Proveedores.objects.create(
            razon_social="Distribuidora ABC",
            ruc="80012345-6",
            telefono="0981123456",
            email="contacto@abc.com",
            fecha_registro=timezone.now(),
            estado=True,
        )

        self.assertIsNotNone(proveedor.id_proveedor)
        self.assertEqual(proveedor.razon_social, "Distribuidora ABC")
        self.assertTrue(proveedor.estado)

    def test_str_method(self):
        """Test del método __str__"""
        proveedor = Proveedores.objects.create(
            razon_social="Proveedor XYZ",
            ruc="80099999-9",
            fecha_registro=timezone.now(),
            estado=True,
        )

        self.assertIsNotNone(str(proveedor))


class ComprasModelTest(TestCase):
    """Tests para el modelo Compras"""

    def setUp(self):
        """Configuración inicial"""
        self.rol = Roles.objects.create(nombre_rol="Comprador", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Comprador",
            apellido="Test",
            usuario="comprador",
            email="comprador@test.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        self.proveedor = Proveedores.objects.create(
            razon_social="Proveedor Test",
            ruc="80055555-5",
            fecha_registro=timezone.now(),
            estado=True,
        )

    def test_crear_compra(self):
        """Test de creación de compra"""
        compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("500000.00"),
            estado_pago="pendiente",
            id_proveedor=self.proveedor,
        )

        self.assertIsNotNone(compra.id_compra)
        self.assertEqual(compra.monto_total, Decimal("500000.00"))
        self.assertEqual(compra.estado_pago, "pendiente")

    def test_str_method(self):
        """Test del método __str__"""
        compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("300000.00"),
            estado_pago="completada",
            id_proveedor=self.proveedor,
        )

        self.assertIsNotNone(str(compra))


class ModelosComprasAdicionalesTest(TestCase):
    """Tests __str__ para modelos adicionales de compras."""

    def setUp(self):
        self.proveedor = Proveedores.objects.create(
            razon_social="Prov Str Test",
            ruc="80077777-7",
            fecha_registro=timezone.now(),
            estado=True,
        )
        self.compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("100000"),
            saldo_pendiente=Decimal("100000"),
            estado_pago="pendiente",
            id_proveedor=self.proveedor,
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA Compras",
            porcentaje=10,
            vigente_desde=timezone.now().date(),
            estado=True,
        )
        self.cat = Categorias.objects.create(nombre="Cat Compras", estado=True)
        self.producto = Productos.objects.create(
            descripcion="Prod Compras Str",
            stock_minimo=0,
            estado=True,
            id_categoria=self.cat,
            id_impuesto=self.impuesto,
        )
        self.medio_pago = MediosPago.objects.create(
            nombre="Efectivo Compras",
            genera_comision=False,
            estado=True,
        )

    def test_str_detalles_compra(self):
        detalle = DetallesCompra.objects.create(
            costo_unitario=Decimal("5000"),
            cantidad=Decimal("10"),
            subtotal=Decimal("50000"),
            id_compra=self.compra,
            id_producto=self.producto,
        )
        self.assertIn("#", str(detalle))

    def test_str_pagos_proveedores(self):
        pago = PagosProveedores.objects.create(
            fecha_creacion=timezone.now(),
            id_medio_pago=self.medio_pago,
        )
        self.assertIn("#", str(pago))

    def test_str_aplicacion_pagos_compras(self):
        pago = PagosProveedores.objects.create(
            fecha_creacion=timezone.now(),
            id_medio_pago=self.medio_pago,
        )
        aplicacion = AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("50000"),
            id_compra=self.compra,
            id_pago_proveedor=pago,
        )
        self.assertIn("#", str(aplicacion))

    def test_str_notas_credito_proveedor(self):
        nota = NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("30000"),
            estado="Pendiente",
            fecha_creacion=timezone.now(),
            id_proveedor=self.proveedor,
        )
        self.assertIn("#", str(nota))

    def test_str_detalles_nota_credito_proveedor(self):
        nota = NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("20000"),
            estado="Pendiente",
            fecha_creacion=timezone.now(),
            id_proveedor=self.proveedor,
        )
        detalle_nc = DetallesNotaCreditoProveedor.objects.create(
            cantidad=Decimal("2"),
            precio_unitario=Decimal("10000"),
            subtotal=Decimal("20000"),
            id_nota_proveedor=nota,
            id_producto=self.producto,
        )
        self.assertIn("#", str(detalle_nc))
