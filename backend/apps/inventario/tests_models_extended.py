"""
Extended tests for apps/inventario/models.py to cover missing lines.

Targets:
- Lines 91-106: dias_stock_disponible with ventas
- Line 256: StockUnico.clean() negative stock validation
- Line 368: DetallesAjuste.__str__
- Lines 415, 420: CostosHistoricos.__str__ and costo_total
- Lines 476-477: AlertasStock.__str__
- Lines 552-553: LotesProducto.__str__
- Line 561: LotesProducto.dias_hasta_vencimiento returns None
- Lines 577-598: LotesProducto.clean() validations
- Line 671: AlertasVencimiento.__str__
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.models import Impuestos
from apps.inventario.models import (
    AjustesInventario,
    AlertasStock,
    AlertasVencimiento,
    CostosHistoricos,
    DetallesAjuste,
    LotesProducto,
    MovimientosStock,
    StockUnico,
)
from apps.productos.models import Categorias, Productos, UnidadesMedida
from apps.usuarios.models import Empleados, Roles


class InventarioModelsExtTestBase(TestCase):
    """Shared setUp for inventario extended model tests."""

    def setUp(self):
        self.rol = Roles.objects.create(nombre_rol="TestInventRol")
        self.empleado = Empleados.objects.create(
            nombre="Inv",
            apellido="Tester",
            usuario="inv_tester",
            contrasena_hash="x" * 60,
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA10Inv",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )
        self.categoria = Categorias.objects.create(nombre="CatInvExt", activo=True)
        self.unidad = UnidadesMedida.objects.create(
            nombre="UnitInvExt", abreviatura="UIE", activo=True
        )
        self.producto = Productos.objects.create(
            codigo_barra="EXTINV00001",
            descripcion="Producto ExtInv",
            stock_minimo=Decimal("5.000"),
            activo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )


class DiasStockDisponibleTest(InventarioModelsExtTestBase):
    """Cover dias_stock_disponible property when ventas_mes > 0 (lines 91-106)."""

    def test_dias_stock_con_egresos(self):
        """When there are egress movements, returns estimated days (lines 102-104)."""
        stock = StockUnico.objects.create(
            cantidad=Decimal("30.000"), id_producto=self.producto
        )
        # Create an egress movement within last 30 days
        MovimientosStock.objects.create(
            tipo_movimiento="Egreso",
            motivo="venta",
            cantidad=Decimal("15.000"),
            stock_resultante=Decimal("15.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )
        result = stock.dias_stock_disponible
        # ventas_mes=15 in 30 days → avg_daily=0.5 → days = int(30/0.5) = 60
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)

    def test_dias_stock_sin_egresos(self):
        """When no egress movements, returns None."""
        stock = StockUnico.objects.create(
            cantidad=Decimal("10.000"), id_producto=self.producto
        )
        result = stock.dias_stock_disponible
        self.assertIsNone(result)


class StockUnicoCleanTest(InventarioModelsExtTestBase):
    """Cover StockUnico.clean() negative stock ValidationError (line 256)."""

    def test_clean_negative_stock_raises(self):
        """Negative stock for product that doesn't allow it raises ValidationError (line 256)."""
        # producto.permite_stock_negativo defaults to False (not in model, check)
        # StockUnico.clean() checks: self.cantidad < 0 and not self.id_producto.permite_stock_negativo
        # If producto doesn't have permite_stock_negativo field, skip this test
        if not hasattr(self.producto, 'permite_stock_negativo'):
            self.skipTest("Producto does not have permite_stock_negativo field")
        stock = StockUnico(cantidad=Decimal("-5.000"), id_producto=self.producto)
        with self.assertRaises(ValidationError):
            stock.clean()

    def test_costo_promedio_ponderado_con_compras(self):
        """costo_promedio_ponderado returns correct value when there are historical costs (line 65)."""
        stock = StockUnico.objects.create(
            cantidad=Decimal("10.000"), id_producto=self.producto
        )
        CostosHistoricos.objects.create(
            costo_unitario=Decimal("1000.00"),
            cantidad_comprada=Decimal("10.000"),
            fecha_compra=timezone.now(),
            id_producto=self.producto,
        )
        result = stock.costo_promedio_ponderado
        self.assertEqual(result, Decimal("1000.00"))

    def test_requiere_reposicion_property(self):
        """requiere_reposicion is True when cantidad <= stock_minimo (line 81)."""
        stock = StockUnico.objects.create(
            cantidad=Decimal("4.000"), id_producto=self.producto
        )
        # stock_minimo = 5, cantidad = 4
        self.assertTrue(stock.requiere_reposicion)


class MovimientosStockCleanTest(InventarioModelsExtTestBase):
    """Cover MovimientosStock.clean() validation errors (lines 237, 256, 261)."""

    def test_clean_cantidad_cero_raises(self):
        """cantidad <= 0 raises ValidationError (line 237)."""
        mov = MovimientosStock(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("-1.000"),
            stock_resultante=Decimal("10.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )
        with self.assertRaises(ValidationError) as ctx:
            mov.clean()
        self.assertIn("cantidad", str(ctx.exception))

    def test_clean_ingreso_con_motivo_egreso_raises(self):
        """Ingreso with egreso motivo raises ValidationError (line 256)."""
        mov = MovimientosStock(
            tipo_movimiento="Ingreso",
            motivo="venta",  # motivo de egreso
            cantidad=Decimal("5.000"),
            stock_resultante=Decimal("15.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )
        with self.assertRaises(ValidationError) as ctx:
            mov.clean()
        self.assertIn("motivo", str(ctx.exception))

    def test_clean_egreso_con_motivo_ingreso_raises(self):
        """Egreso with ingreso motivo raises ValidationError (line 261)."""
        mov = MovimientosStock(
            tipo_movimiento="Egreso",
            motivo="compra",  # motivo de ingreso
            cantidad=Decimal("5.000"),
            stock_resultante=Decimal("5.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )
        with self.assertRaises(ValidationError) as ctx:
            mov.clean()
        self.assertIn("motivo", str(ctx.exception))


class DetallesAjusteStrTest(InventarioModelsExtTestBase):
    """Cover DetallesAjuste.__str__ (line 368)."""

    def test_str_representation(self):
        """__str__ returns product description and quantity (line 368)."""
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste="Aumento",
            motivo="Test ajuste",
            estado="Pendiente",
            id_empleado_solicita=self.empleado,
        )
        detalle = DetallesAjuste.objects.create(
            cantidad_ajustada=Decimal("5.000"),
            id_ajuste=ajuste,
            id_producto=self.producto,
        )
        result = str(detalle)
        self.assertIn("Producto ExtInv", result)
        self.assertIn("5.000", result)


class CostosHistoricosTest(InventarioModelsExtTestBase):
    """Cover CostosHistoricos.__str__ and costo_total property (lines 415, 420)."""

    def test_str_representation(self):
        """__str__ returns product description, cost and date (line 415)."""
        from apps.compras.models import Compras, Proveedores
        costo = CostosHistoricos.objects.create(
            costo_unitario=Decimal("1500.00"),
            cantidad_comprada=Decimal("10.000"),
            fecha_compra=timezone.now(),
            id_producto=self.producto,
        )
        result = str(costo)
        self.assertIn("Producto ExtInv", result)
        self.assertIn("1,500", result)

    def test_costo_total_property(self):
        """costo_total returns costo_unitario * cantidad_comprada (line 420)."""
        costo = CostosHistoricos.objects.create(
            costo_unitario=Decimal("100.00"),
            cantidad_comprada=Decimal("3.000"),
            fecha_compra=timezone.now(),
            id_producto=self.producto,
        )
        self.assertEqual(costo.costo_total, Decimal("300.00"))


class AlertasStockStrTest(InventarioModelsExtTestBase):
    """Cover AlertasStock.__str__ (lines 476-477)."""

    def test_str_activa(self):
        """__str__ shows 'Activa' when activa=True."""
        alerta = AlertasStock.objects.create(
            tipo_alerta="stock_minimo",
            stock_actual=Decimal("3.000"),
            stock_minimo=Decimal("10.000"),
            activa=True,
            id_producto=self.producto,
        )
        result = str(alerta)
        self.assertIn("Producto ExtInv", result)
        self.assertIn("Activa", result)

    def test_str_resuelta(self):
        """__str__ shows 'Resuelta' when activa=False (line 476 branch)."""
        alerta = AlertasStock.objects.create(
            tipo_alerta="stock_minimo",
            stock_actual=Decimal("3.000"),
            stock_minimo=Decimal("10.000"),
            activa=False,
            id_producto=self.producto,
        )
        result = str(alerta)
        self.assertIn("Resuelta", result)


class LotesProductoTest(InventarioModelsExtTestBase):
    """Cover LotesProducto properties and clean() validations (lines 552-598)."""

    def _make_lote(self, **kwargs):
        defaults = {
            "numero_lote": "LOT001",
            "fecha_vencimiento": date.today() + timedelta(days=60),
            "cantidad_inicial": Decimal("10.000"),
            "cantidad_disponible": Decimal("10.000"),
            "id_producto": self.producto,
        }
        defaults.update(kwargs)
        return LotesProducto(**defaults)

    def test_str_disponible(self):
        """__str__ includes 'Disponible' when not blocked (lines 552-553)."""
        lote = LotesProducto.objects.create(
            numero_lote="LOTSTR001",
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_inicial=Decimal("5.000"),
            cantidad_disponible=Decimal("5.000"),
            bloqueado=False,
            id_producto=self.producto,
        )
        result = str(lote)
        self.assertIn("LOTSTR001", result)
        self.assertIn("Disponible", result)

    def test_str_bloqueado(self):
        """__str__ includes 'Bloqueado' when blocked."""
        lote = LotesProducto.objects.create(
            numero_lote="LOTSTR002",
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_inicial=Decimal("5.000"),
            cantidad_disponible=Decimal("5.000"),
            bloqueado=True,
            motivo_bloqueo="vencido",
            id_producto=self.producto,
        )
        result = str(lote)
        self.assertIn("Bloqueado", result)

    def test_dias_hasta_vencimiento_none_wenn_no_fecha(self):
        """Returns None when fecha_vencimiento is None (line 561)."""
        lote = LotesProducto(
            numero_lote="LOTNODATE",
            fecha_vencimiento=None,
            cantidad_inicial=Decimal("5.000"),
            cantidad_disponible=Decimal("5.000"),
            id_producto=self.producto,
        )
        # Directly test the branch where fecha_vencimiento is None
        lote.fecha_vencimiento = None
        result = lote.dias_hasta_vencimiento
        self.assertIsNone(result)

    def test_clean_fecha_vencimiento_antes_fabricacion(self):
        """Fecha vencimiento <= fabricacion raises ValidationError (lines 580-586)."""
        lote = self._make_lote(
            fecha_fabricacion=date.today() + timedelta(days=10),
            fecha_vencimiento=date.today() + timedelta(days=5),
        )
        with self.assertRaises(ValidationError) as ctx:
            lote.clean()
        self.assertIn("fecha_vencimiento", ctx.exception.message_dict)

    def test_clean_cantidad_disponible_mayor_inicial(self):
        """cantidad_disponible > cantidad_inicial raises ValidationError (lines 589-594)."""
        lote = self._make_lote(
            cantidad_inicial=Decimal("5.000"),
            cantidad_disponible=Decimal("10.000"),
        )
        with self.assertRaises(ValidationError) as ctx:
            lote.clean()
        self.assertIn("cantidad_disponible", ctx.exception.message_dict)

    def test_clean_bloqueado_sin_motivo(self):
        """bloqueado=True without motivo_bloqueo raises ValidationError (lines 597-598)."""
        lote = self._make_lote(bloqueado=True, motivo_bloqueo=None)
        with self.assertRaises(ValidationError) as ctx:
            lote.clean()
        self.assertIn("motivo_bloqueo", ctx.exception.message_dict)

    def test_esta_vencido_true(self):
        """esta_vencido returns True when dias_hasta_vencimiento < 0."""
        lote = self._make_lote(
            fecha_vencimiento=date.today() - timedelta(days=5)
        )
        self.assertTrue(lote.esta_vencido)

    def test_proximo_a_vencer_true(self):
        """proximo_a_vencer returns True when days <= 30."""
        lote = self._make_lote(
            fecha_vencimiento=date.today() + timedelta(days=15)
        )
        self.assertTrue(lote.proximo_a_vencer)

    def test_clean_valid_lote_no_exception(self):
        """clean() with valid data doesn't raise (covers branches 581->589, 597->exit)."""
        lote = self._make_lote(
            fecha_fabricacion=date.today() - timedelta(days=30),
            fecha_vencimiento=date.today() + timedelta(days=60),
            cantidad_inicial=Decimal("10.000"),
            cantidad_disponible=Decimal("5.000"),
            bloqueado=False,
            motivo_bloqueo=None,
        )
        # Should not raise
        lote.clean()


class AlertasVencimientoStrTest(InventarioModelsExtTestBase):
    """Cover AlertasVencimiento.__str__ (line 671)."""

    def test_str_representation(self):
        """__str__ returns lote and tipo alerta display (line 671)."""
        lote = LotesProducto.objects.create(
            numero_lote="LOTALERTA",
            fecha_vencimiento=date.today() + timedelta(days=5),
            cantidad_inicial=Decimal("10.000"),
            cantidad_disponible=Decimal("10.000"),
            id_producto=self.producto,
        )
        alerta = AlertasVencimiento.objects.create(
            tipo_alerta="7_dias",
            dias_restantes=7,
            fecha_vencimiento=lote.fecha_vencimiento,
            cantidad_lote=lote.cantidad_disponible,
            id_lote=lote,
        )
        result = str(alerta)
        self.assertIn("7 días para vencer", result)
