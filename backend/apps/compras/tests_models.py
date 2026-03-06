"""
Tests complementarios para modelos de compras
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.compras.models import Compras, DetallesCompra, Proveedores
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles


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
            activo=True,
        )

        self.assertIsNotNone(proveedor.id_proveedor)
        self.assertEqual(proveedor.razon_social, "Distribuidora ABC")
        self.assertTrue(proveedor.activo)

    def test_str_method(self):
        """Test del método __str__"""
        proveedor = Proveedores.objects.create(
            razon_social="Proveedor XYZ",
            ruc="80099999-9",
            fecha_registro=timezone.now(),
            activo=True,
        )

        self.assertIsNotNone(str(proveedor))


class ComprasModelTest(TestCase):
    """Tests para el modelo Compras"""

    def setUp(self):
        """Configuración inicial"""
        self.rol = Roles.objects.create(nombre_rol="Comprador", activo=True)
        self.empleado = Empleados.objects.create(
            nombre="Comprador",
            apellido="Test",
            usuario="comprador",
            email="comprador@test.com",
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol,
        )

        self.proveedor = Proveedores.objects.create(
            razon_social="Proveedor Test",
            ruc="80055555-5",
            fecha_registro=timezone.now(),
            activo=True,
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
