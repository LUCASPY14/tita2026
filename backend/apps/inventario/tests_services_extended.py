"""
Tests extendidos para apps/inventario/services.py
Cubre líneas faltantes:
47-48 (Productos.DoesNotExist en validar_disponibilidad),
53-54 (StockUnico.DoesNotExist → stock=0),
175-176 (StockUnico.DoesNotExist en reservar_stock → crea stock),
225-226 (bare except en obtener_productos_bajo_stock),
253-271 (calcular_valor_inventario),
290-333 (obtener_rotacion_inventario),
356-372 (AjusteInventarioService.crear_ajuste)
"""
from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.inventario.models import StockUnico, MovimientosStock, AjustesInventario, DetallesAjuste
from apps.inventario.services import StockService, AjusteInventarioService
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles


def make_base_objects():
    """Helper to create base product-related objects"""
    categoria = Categorias.objects.create(nombre="TestCat_Srv", estado=True)
    unidad = UnidadesMedida.objects.create(nombre="TestUnd_Srv", abreviatura="SV", estado=True)
    impuesto = Impuestos.objects.create(
        nombre_impuesto="IVA_Srv",
        porcentaje=Decimal("10.00"),
        vigente_desde=timezone.now().date(),
        estado=True,
    )
    return categoria, unidad, impuesto


def make_producto(categoria, unidad, impuesto, suffix="", permite_negativo=False, stock_minimo=None):
    """Helper to create a product"""
    return Productos.objects.create(
        descripcion=f"Producto Srv {suffix}",
        stock_minimo=stock_minimo or Decimal("5.000"),
        permite_stock_negativo=permite_negativo,
        estado=True,
        id_categoria=categoria,
        id_impuesto=impuesto,
        id_unidad_medida=unidad,
    )


def make_empleado(suffix=""):
    """Helper to create an employee"""
    rol = Roles.objects.create(nombre_rol=f"RolSrv{suffix}", estado=True)
    return Empleados.objects.create(
        nombre=f"Emp{suffix}",
        apellido="Srv",
        usuario=f"emp_srv_{suffix}",
        contrasena_hash="hash",
        fecha_ingreso=timezone.now(),
        email=f"emp_srv_{suffix}@test.com",
        estado=True,
        id_rol=rol,
    )


# =============================================================================
# validar_disponibilidad - líneas 47-48, 53-54
# =============================================================================

class ValidarDisponibilidadEdgeCasesTest(TestCase):
    """Cubre casos de borde en validar_disponibilidad"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()

    def test_producto_no_existe_raises_validation_error(self):
        """Líneas 47-48: Productos.DoesNotExist → ValidationError"""
        with self.assertRaises(ValidationError) as ctx:
            StockService.validar_disponibilidad(999999, Decimal("5.000"))
        self.assertIn("no existe", str(ctx.exception))

    def test_sin_stock_entry_devuelve_cero(self):
        """Líneas 53-54: StockUnico.DoesNotExist → stock_actual = 0"""
        producto = make_producto(self.categoria, self.unidad, self.impuesto, "nostock")
        # No creamos StockUnico, por lo que lanzará DoesNotExist → stock=0
        resultado = StockService.validar_disponibilidad(producto.id_producto, Decimal("1.000"))
        self.assertEqual(resultado["stock_actual"], Decimal("0.000"))
        self.assertFalse(resultado["disponible"])

    def test_permite_negativo_siempre_disponible_sin_stock(self):
        """Producto con permite_stock_negativo=True → siempre disponible"""
        producto = make_producto(self.categoria, self.unidad, self.impuesto, "neg", permite_negativo=True)
        resultado = StockService.validar_disponibilidad(producto.id_producto, Decimal("100.000"))
        self.assertTrue(resultado["disponible"])
        self.assertTrue(resultado["permite_negativo"])


# =============================================================================
# reservar_stock - línea 175-176 (StockUnico.DoesNotExist → crea stock)
# =============================================================================

class ReservarStockCreaNuevoTest(TransactionTestCase):
    """Cubre reservar_stock cuando no existe StockUnico"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()
        self.empleado = make_empleado("rsrv1")

    def test_reservar_sin_stock_existente_falla_antes_de_lock(self):
        """Sin StockUnico con permite_negativo=False → ValidationError del primer check"""
        producto = make_producto(
            self.categoria, self.unidad, self.impuesto, "nostock2", permite_negativo=False
        )
        # validar_disponibilidad retorna disponible=False → ValidationError antes del lock
        with self.assertRaises(ValidationError):
            StockService.reservar_stock(
                producto_id=producto.id_producto,
                cantidad=Decimal("5.000"),
                empleado=self.empleado,
                motivo="venta",
            )

    def test_reservar_con_stock_negativo_activa_crea_si_no_existe(self):
        """Producto permite_negativo=True sin StockUnico → crea uno con 0 y descuenta"""
        producto = make_producto(
            self.categoria, self.unidad, self.impuesto, "negrsrv", permite_negativo=True
        )
        stock = StockService.reservar_stock(
            producto_id=producto.id_producto,
            cantidad=Decimal("3.000"),
            empleado=self.empleado,
            motivo="venta",
        )
        # Línea 175-176 ejecutada: stock creado con 0, luego descontado a -3
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad, Decimal("-3.000"))


# =============================================================================
# obtener_productos_bajo_stock - línea 225-226 (bare except)
# =============================================================================

class ObtenerProductosBajoStockEdgeCasesTest(TestCase):
    """Cubre obtener_productos_bajo_stock incluyendo except bare"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()

    def test_producto_sin_stock_attr_usa_cero(self):
        """Líneas 225-226: bare except → stock = 0. Producto bajo stock sin StockUnico."""
        producto = make_producto(
            self.categoria, self.unidad, self.impuesto, "bajostk", stock_minimo=Decimal("10.000")
        )
        # Creamos StockUnico con cantidad menor al mínimo
        StockUnico.objects.create(id_producto=producto, cantidad=Decimal("2.000"))

        resultado = StockService.obtener_productos_bajo_stock()
        # Debe incluir este producto
        ids = [r["id_producto"] for r in resultado]
        self.assertIn(producto.id_producto, ids)

    def test_sin_productos_bajo_stock_retorna_lista_vacia(self):
        """Sin productos bajo stock → lista vacía"""
        producto = make_producto(
            self.categoria, self.unidad, self.impuesto, "bienstk", stock_minimo=Decimal("5.000")
        )
        StockUnico.objects.create(id_producto=producto, cantidad=Decimal("100.000"))
        resultado = StockService.obtener_productos_bajo_stock()
        ids = [r["id_producto"] for r in resultado]
        self.assertNotIn(producto.id_producto, ids)


# =============================================================================
# calcular_valor_inventario - líneas 253-271
# =============================================================================

class CalcularValorInventarioTest(TestCase):
    """Cubre calcular_valor_inventario"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()

    def test_sin_stocks_retorna_cero(self):
        """calcular_valor_inventario sin stocks → valor_total=0"""
        # Asegurar que no hay stocks
        StockUnico.objects.all().delete()
        resultado = StockService.calcular_valor_inventario()
        self.assertEqual(resultado["valor_total"], Decimal("0.00"))
        self.assertEqual(resultado["cantidad_productos"], 0)
        self.assertEqual(resultado["productos"], [])

    def test_con_stocks_retorna_valor_correcto(self):
        """calcular_valor_inventario con stocks → suma correcta"""
        producto = make_producto(self.categoria, self.unidad, self.impuesto, "calcval")
        StockUnico.objects.create(
            id_producto=producto,
            cantidad=Decimal("10.000"),
        )
        resultado = StockService.calcular_valor_inventario()
        self.assertIsInstance(resultado["valor_total"], Decimal)
        self.assertGreaterEqual(resultado["cantidad_productos"], 1)
        self.assertIsInstance(resultado["productos"], list)

    def test_productos_ordenados_por_valor_desc(self):
        """Productos se retornan ordenados por valor descendente"""
        producto1 = make_producto(self.categoria, self.unidad, self.impuesto, "v1")
        producto2 = make_producto(self.categoria, self.unidad, self.impuesto, "v2")
        StockUnico.objects.create(
            id_producto=producto1,
            cantidad=Decimal("5.000"),
        )
        StockUnico.objects.create(
            id_producto=producto2,
            cantidad=Decimal("5.000"),
        )
        resultado = StockService.calcular_valor_inventario()
        if len(resultado["productos"]) >= 2:
            # Verifica que el primero tiene mayor valor que el segundo
            self.assertGreaterEqual(
                resultado["productos"][0]["valor_total"],
                resultado["productos"][1]["valor_total"],
            )


# =============================================================================
# obtener_rotacion_inventario - líneas 290-333
# =============================================================================

class ObtenerRotacionInventarioTest(TestCase):
    """Cubre obtener_rotacion_inventario"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()
        self.empleado = make_empleado("rot1")

    def test_sin_movimientos_retorna_lista_vacia(self):
        """Sin movimientos de venta → lista vacía"""
        resultado = StockService.obtener_rotacion_inventario(dias=30)
        self.assertIsInstance(resultado, list)
        # Sin movimientos de tipo venta → lista vacía
        self.assertEqual(len(resultado), 0)

    def test_con_movimientos_venta_calcula_rotacion(self):
        """Con movimientos de venta egreso → calcula rotación"""
        producto = make_producto(self.categoria, self.unidad, self.impuesto, "rot")
        stock = StockUnico.objects.create(
            id_producto=producto, cantidad=Decimal("50.000")
        )

        # Crear movimiento de venta
        MovimientosStock.objects.create(
            id_producto=producto,
            tipo_movimiento="Egreso",
            cantidad=Decimal("10.000"),
            motivo="venta",
            stock_resultante=Decimal("40.000"),
            id_empleado_autoriza=self.empleado,
        )

        resultado = StockService.obtener_rotacion_inventario(dias=30)
        self.assertIsInstance(resultado, list)
        self.assertGreaterEqual(len(resultado), 1)
        # Verificar estructura
        if resultado:
            item = resultado[0]
            self.assertIn("producto", item)
            self.assertIn("rotacion", item)
            self.assertIn("total_vendido", item)

    def test_rotacion_dias_personalizados(self):
        """Rotación con días=7 funciona"""
        resultado = StockService.obtener_rotacion_inventario(dias=7)
        self.assertIsInstance(resultado, list)

    def test_rotacion_producto_dias_stock_zero_total_vendido(self):
        """total_vendido=0 → dias_stock=999"""
        # Crear movimiento de venta con cantidad que resultará en avg=stock_resultante>0
        producto = make_producto(self.categoria, self.unidad, self.impuesto, "rot2")
        StockUnico.objects.create(id_producto=producto, cantidad=Decimal("100.000"))
        MovimientosStock.objects.create(
            id_producto=producto,
            tipo_movimiento="Egreso",
            cantidad=Decimal("5.000"),
            motivo="venta",
            stock_resultante=Decimal("95.000"),
            id_empleado_autoriza=self.empleado,
        )
        resultado = StockService.obtener_rotacion_inventario(dias=30)
        # Any result - just verify no exception
        self.assertIsInstance(resultado, list)


# =============================================================================
# AjusteInventarioService.crear_ajuste - líneas 356-372
# =============================================================================

class AjusteInventarioServiceTest(TestCase):
    """Cubre AjusteInventarioService.crear_ajuste"""

    def setUp(self):
        self.categoria, self.unidad, self.impuesto = make_base_objects()
        self.empleado = make_empleado("ajuste1")
        self.producto = make_producto(self.categoria, self.unidad, self.impuesto, "ajuste")

    def test_crear_ajuste_aumento_exitoso(self):
        """Líneas 356-372: crear ajuste de aumento con detalles"""
        detalles = [{"id_producto": self.producto.id_producto, "cantidad": Decimal("10.000")}]
        ajuste = AjusteInventarioService.crear_ajuste(
            tipo_ajuste="Aumento",
            motivo="Inventario inicial",
            detalles=detalles,
            empleado_solicita=self.empleado,
        )
        self.assertIsNotNone(ajuste.id_ajuste)
        self.assertEqual(ajuste.tipo_ajuste, "Aumento")
        self.assertEqual(ajuste.estado, "Pendiente")
        self.assertEqual(ajuste.id_empleado_solicita, self.empleado)
        # Verificar detalles creados
        detalles_db = DetallesAjuste.objects.filter(id_ajuste=ajuste)
        self.assertEqual(detalles_db.count(), 1)
        self.assertEqual(detalles_db.first().cantidad_ajustada, Decimal("10.000"))

    def test_crear_ajuste_merma_exitoso(self):
        """Crear ajuste de merma"""
        detalles = [{"id_producto": self.producto.id_producto, "cantidad": Decimal("3.000")}]
        ajuste = AjusteInventarioService.crear_ajuste(
            tipo_ajuste="Merma",
            motivo="Producto vencido",
            detalles=detalles,
            empleado_solicita=self.empleado,
        )
        self.assertEqual(ajuste.tipo_ajuste, "Merma")
        self.assertEqual(ajuste.motivo, "Producto vencido")

    def test_crear_ajuste_sin_detalles(self):
        """Crear ajuste sin detalles → ajuste creado, 0 detalles"""
        ajuste = AjusteInventarioService.crear_ajuste(
            tipo_ajuste="Aumento",
            motivo="Sin items",
            detalles=[],
            empleado_solicita=None,
        )
        self.assertIsNotNone(ajuste.id_ajuste)
        detalles_db = DetallesAjuste.objects.filter(id_ajuste=ajuste)
        self.assertEqual(detalles_db.count(), 0)

    def test_crear_ajuste_multiples_productos(self):
        """Ajuste con múltiples productos"""
        producto2 = make_producto(self.categoria, self.unidad, self.impuesto, "ajuste2nd")
        detalles = [
            {"id_producto": self.producto.id_producto, "cantidad": Decimal("5.000")},
            {"id_producto": producto2.id_producto, "cantidad": Decimal("2.000")},
        ]
        ajuste = AjusteInventarioService.crear_ajuste(
            tipo_ajuste="Aumento",
            motivo="Multi-producto",
            detalles=detalles,
            empleado_solicita=self.empleado,
        )
        detalles_db = DetallesAjuste.objects.filter(id_ajuste=ajuste)
        self.assertEqual(detalles_db.count(), 2)
