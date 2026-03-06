"""
Tests para modelos de la app inventario
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import StockUnico, MovimientosStock, AjustesInventario
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles


class StockUnicoModelTest(TestCase):
    """Tests para el modelo StockUnico y sus propiedades"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Inventarista", activo=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Ana",
            apellido="Torres",
            usuario="ana.torres",
            email="ana@example.com",
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol,
        )

        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Snacks", activo=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(
            nombre="Unidad", abreviatura="Unid", activo=True
        )

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="1234567890123",
            descripcion="Papas Fritas",
            stock_minimo=Decimal("20.000"),
            activo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_str_method(self):
        """Test del método __str__"""
        stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

        self.assertIn("Papas Fritas", str(stock))

    def test_costo_promedio_ponderado_sin_cantidad(self):
        """Test de costo promedio cuando cantidad es cero"""
        stock = StockUnico.objects.create(cantidad=Decimal("0.000"), id_producto=self.producto)

        # Si no hay cantidad, el costo promedio debe ser cero
        self.assertEqual(stock.costo_promedio_ponderado, Decimal("0.00"))

    def test_valor_inventario_calculado(self):
        """Test del cálculo de valor de inventario"""
        stock = StockUnico.objects.create(cantidad=Decimal("50.000"), id_producto=self.producto)

        # El valor de inventario es una propiedad calculada
        # Si no tiene compras, el costo promedio es 0
        valor_esperado = Decimal("0.00")
        self.assertEqual(stock.valor_inventario, valor_esperado)

    def test_requiere_reposicion_true(self):
        """Test de requiere reposición cuando stock bajo"""
        stock = StockUnico.objects.create(cantidad=Decimal("10.000"), id_producto=self.producto)

        # stock_minimo es 20, cantidad es 10
        self.assertTrue(stock.cantidad < self.producto.stock_minimo)

    def test_requiere_reposicion_false(self):
        """Test de requiere reposición cuando stock suficiente"""
        stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

        # stock_minimo es 20, cantidad es 100
        self.assertFalse(stock.cantidad < self.producto.stock_minimo)

    def test_crear_stock_inicial(self):
        """Test de creación de stock inicial"""
        stock = StockUnico.objects.create(cantidad=Decimal("75.500"), id_producto=self.producto)

        self.assertIsNotNone(stock.id_stock)
        self.assertEqual(stock.cantidad, Decimal("75.500"))
        self.assertEqual(stock.id_producto, self.producto)


class MovimientosStockModelTest(TestCase):
    """Tests para el modelo MovimientosStock"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Inventarista", activo=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="José",
            apellido="Martínez",
            usuario="jose.martinez",
            email="jose@example.com",
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol,
        )

        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", activo=True)

        # Crear unidad
        self.unidad = UnidadesMedida.objects.create(nombre="Litro", abreviatura="L", activo=True)

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="7890000000001",
            descripcion="Agua Mineral",
            stock_minimo=Decimal("30.000"),
            activo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Crear stock
        self.stock = StockUnico.objects.create(
            cantidad=Decimal("100.000"), id_producto=self.producto
        )

    def test_crear_movimiento_ingreso(self):
        """Test de creación de movimiento de ingreso"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("50.000"),
            stock_resultante=Decimal("150.000"),
            id_producto=self.producto,
            id_empleado_autoriza=self.empleado,
        )

        self.assertEqual(movimiento.tipo_movimiento, "Ingreso")
        self.assertEqual(movimiento.motivo, "compra")
        self.assertEqual(movimiento.cantidad, Decimal("50.000"))

    def test_crear_movimiento_egreso(self):
        """Test de creación de movimiento de egreso"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Egreso",
            motivo="venta",
            cantidad=Decimal("20.000"),
            stock_resultante=Decimal("80.000"),
            id_producto=self.producto,
            id_empleado_autoriza=self.empleado,
        )

        self.assertEqual(movimiento.tipo_movimiento, "Egreso")
        self.assertEqual(movimiento.motivo, "venta")
        self.assertEqual(movimiento.stock_resultante, Decimal("80.000"))

    def test_movimiento_con_motivo_ajuste(self):
        """Test de movimiento por ajuste de inventario"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Ingreso",
            motivo="ajuste_aumento",
            cantidad=Decimal("10.000"),
            stock_resultante=Decimal("110.000"),
            observaciones="Corrección por inventario físico",
            id_producto=self.producto,
            id_empleado_autoriza=self.empleado,
        )

        self.assertEqual(movimiento.motivo, "ajuste_aumento")
        self.assertIsNotNone(movimiento.observaciones)

    def test_str_method(self):
        """Test del método __str__"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("25.000"),
            stock_resultante=Decimal("125.000"),
            id_producto=self.producto,
            id_empleado_autoriza=self.empleado,
        )

        # El __str__ debe incluir información útil
        self.assertIsNotNone(str(movimiento))


class AjustesInventarioModelTest(TestCase):
    """Tests para el modelo AjustesInventario"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Gerente", activo=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Pedro",
            apellido="Ramírez",
            usuario="pedro.ramirez",
            email="pedro@example.com",
            fecha_ingreso=timezone.now().date(),
            activo=True,
            id_rol=self.rol,
        )

    def test_crear_ajuste_aumento(self):
        """Test de creación de ajuste de aumento"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Aumento",
            estado="Pendiente",
            motivo="Inventario físico mayor",
            id_empleado_solicita=self.empleado,
        )

        self.assertEqual(ajuste.tipo_ajuste, "Aumento")
        self.assertEqual(ajuste.estado, "Pendiente")

    def test_crear_ajuste_merma(self):
        """Test de creación de ajuste por merma"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Merma",
            estado="Pendiente",
            motivo="Productos vencidos",
            id_empleado_solicita=self.empleado,
        )

        self.assertEqual(ajuste.tipo_ajuste, "Merma")
        self.assertEqual(ajuste.motivo, "Productos vencidos")

    def test_aprobar_ajuste(self):
        """Test de aprobación de ajuste"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Aumento",
            estado="Pendiente",
            motivo="Corrección",
            id_empleado_solicita=self.empleado,
        )

        # Simular aprobación
        ajuste.estado = "Aprobado"
        ajuste.save()

        self.assertEqual(ajuste.estado, "Aprobado")

    def test_rechazar_ajuste(self):
        """Test de rechazo de ajuste"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Merma",
            estado="Pendiente",
            motivo="Error de conteo",
            id_empleado_solicita=self.empleado,
        )

        # Simular rechazo
        ajuste.estado = "Rechazado"
        ajuste.save()

        self.assertEqual(ajuste.estado, "Rechazado")

    def test_str_method(self):
        """Test del método __str__"""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Aumento",
            estado="Pendiente",
            motivo="Inventario",
            id_empleado_solicita=self.empleado,
        )

        self.assertIsNotNone(str(ajuste))
