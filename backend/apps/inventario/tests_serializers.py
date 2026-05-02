"""
Tests para serializers de la app inventario
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import StockUnico, MovimientosStock, AjustesInventario
from .serializers import (
    StockUnicoSerializer,
    MovimientosStockSerializer,
    AjustesInventarioSerializer,
)
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.usuarios.models import Empleados, Roles
from apps.contabilidad.models import Impuestos


class StockUnicoSerializerTest(TestCase):
    """Tests para StockUnicoSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", estado=True)

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7890123456789",
            descripcion="Coca Cola 500ml",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_serializar_stock_completo(self):
        """Test de serialización de stock con todos los campos"""
        stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

        serializer = StockUnicoSerializer(stock)
        data = serializer.data

        self.assertEqual(Decimal(data["cantidad"]), Decimal("100.000"))
        self.assertEqual(data["producto_nombre"], "Coca Cola 500ml")
        self.assertEqual(data["producto_categoria"], "Bebidas")

    def test_validar_stock_valido(self):
        """Test de validación de datos válidos de stock"""
        data = {"cantidad": "50.000", "id_producto": self.producto.id_producto}

        serializer = StockUnicoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_stock_sin_producto_invalido(self):
        """Test que valida que un stock sin producto es inválido"""
        data = {"cantidad": "30.000"}

        serializer = StockUnicoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("id_producto", serializer.errors)

    def test_actualizar_stock_parcialmente(self):
        """Test de actualización parcial de stock"""
        stock = StockUnico.objects.create(cantidad=Decimal("80.000"), id_producto=self.producto)

        data = {"cantidad": "120.000"}
        serializer = StockUnicoSerializer(stock, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        stock_actualizado = serializer.save()

        self.assertEqual(stock_actualizado.cantidad, Decimal("120.000"))


class MovimientosStockSerializerTest(TestCase):
    """Tests para MovimientosStockSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Encargado Inventario", estado=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Roberto",
            apellido="Pérez",
            usuario="roberto.perez",
            email="roberto@example.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Snacks", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Paquete", abreviatura="PKT", estado=True)

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7899876543210",
            descripcion="Papas Fritas",
            stock_minimo=Decimal("5.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_serializar_movimiento_completo(self):
        """Test de serialización de movimiento de stock completo"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("50.000"),
            stock_resultante=Decimal("150.000"),
            observaciones="Compra de mercadería",
            id_producto=self.producto,
            id_empleado_autoriza=self.empleado,
        )

        serializer = MovimientosStockSerializer(movimiento)
        data = serializer.data

        self.assertEqual(data["tipo_movimiento"], "Ingreso")
        self.assertEqual(Decimal(data["cantidad"]), Decimal("50.000"))
        self.assertEqual(data["producto_nombre"], "Papas Fritas")
        self.assertEqual(data["empleado_nombre"], "Roberto")

    def test_validar_movimiento_valido(self):
        """Test de validación de datos válidos de movimiento"""
        data = {
            "tipo_movimiento": "Egreso",
            "motivo": "venta",
            "cantidad": "20.000",
            "stock_resultante": "80.000",
            "observaciones": "Venta",
            "id_producto": self.producto.id_producto,
            "id_empleado_autoriza": self.empleado.id_empleado,
        }

        serializer = MovimientosStockSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_movimiento_sin_tipo_invalido(self):
        """Test que valida que un movimiento sin tipo es inválido"""
        data = {
            "cantidad": "15.000",
            "fecha_movimiento": timezone.now().isoformat(),
            "id_producto": self.producto.id_producto,
        }

        serializer = MovimientosStockSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tipo_movimiento", serializer.errors)


class AjustesInventarioSerializerTest(TestCase):
    """Tests para AjustesInventarioSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Administrador", estado=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Laura",
            apellido="González",
            usuario="laura.gonzalez",
            email="laura@example.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Alimentos", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Kilogramo", abreviatura="KG", estado=True)

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7891234567890",
            descripcion="Arroz Blanco",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_serializar_ajuste_completo(self):
        """Test de serialización de ajuste de inventario completo"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Merma",
            motivo="Merma por vencimiento",
            estado="Pendiente",
            id_empleado_solicita=self.empleado,
        )

        serializer = AjustesInventarioSerializer(ajuste)
        data = serializer.data

        self.assertEqual(data["tipo_ajuste"], "Merma")
        self.assertEqual(data["motivo"], "Merma por vencimiento")
        self.assertEqual(data["estado"], "Pendiente")

    def test_validar_ajuste_valido(self):
        """Test de validación de datos válidos de ajuste"""
        data = {
            "tipo_ajuste": "Aumento",
            "motivo": "Ajuste por inventario físico",
            "estado": "Pendiente",
            "id_empleado_solicita": self.empleado.id_empleado,
        }

        serializer = AjustesInventarioSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_crear_ajuste_desde_serializer(self):
        """Test de creación de ajuste usando el serializer"""
        data = {
            "tipo_ajuste": "Merma",
            "motivo": "Corrección de conteo",
            "estado": "Pendiente",
            "id_empleado_solicita": self.empleado.id_empleado,
        }

        serializer = AjustesInventarioSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        ajuste = serializer.save()
        self.assertIsNotNone(ajuste.id_ajuste)
        self.assertEqual(ajuste.motivo, "Corrección de conteo")
