"""
Tests para modelos de la app inventario.
Cubre __str__, @property y clean() de todos los modelos.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def stock(db, producto, stock_producto):
    """Reutiliza stock_producto de conftest (cantidad=50)."""
    return stock_producto


# ── Stock ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStockModel:

    def test_str(self, stock, producto):
        """__str__ = 'Producto: cantidad' (línea 46)."""
        s = str(stock)
        assert "50" in s

    def test_costo_promedio_con_historico(self, stock, producto, usuario_cajero):
        """costo_promedio pondera compras históricas (línea 58)."""
        from apps.inventario.models import CostoHistorico
        CostoHistorico.objects.create(
            producto=producto,
            costo_unitario=Decimal("2000"),
            cantidad_comprada=Decimal("10"),
            fecha_compra=timezone.now(),
        )
        CostoHistorico.objects.create(
            producto=producto,
            costo_unitario=Decimal("4000"),
            cantidad_comprada=Decimal("10"),
            fecha_compra=timezone.now(),
        )
        # Promedio ponderado = (2000*10 + 4000*10) / 20 = 3000
        assert stock.costo_promedio == Decimal("3000")

    def test_costo_promedio_sin_historico(self, stock):
        assert stock.costo_promedio == Decimal("0")

    def test_dias_stock_disponible_con_ventas(self, stock, producto, usuario_cajero):
        """dias_stock_disponible calcula según ventas de los últimos 30 días (líneas 80-82)."""
        from apps.inventario.models import MovimientoStock
        MovimientoStock.objects.create(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.VENTA,
            cantidad=Decimal("30"),
            stock_resultante=Decimal("20"),
            autorizado_por=usuario_cajero,
        )
        dias = stock.dias_stock_disponible
        # 30 ventas en 30 días = 1/día, con stock=50 → ~50 días
        assert dias is not None
        assert dias > 0

    def test_dias_stock_disponible_sin_ventas(self, stock):
        """Sin egresos recientes → None (rama ventas_mes=0)."""
        assert stock.dias_stock_disponible is None

    def test_clean_cantidad_negativa_sin_permiso(self, stock, producto):
        """cantidad < 0 y no permite_stock_negativo → ValidationError (línea 87)."""
        stock.cantidad = Decimal("-1")
        with pytest.raises(ValidationError, match="stock negativo"):
            stock.clean()

    def test_clean_cantidad_negativa_con_permiso(self, stock, producto):
        """permite_stock_negativo=True → clean() no lanza."""
        producto.permite_stock_negativo = True
        producto.save()
        stock.cantidad = Decimal("-1")
        stock.clean()  # no debe lanzar

    def test_valor_inventario(self, stock, producto):
        """valor_inventario = cantidad * costo_promedio (línea 63)."""
        from apps.inventario.models import CostoHistorico
        from django.utils import timezone as tz
        CostoHistorico.objects.create(
            producto=producto,
            costo_unitario=Decimal("1000"),
            cantidad_comprada=Decimal("50"),
            fecha_compra=tz.now(),
        )
        assert stock.valor_inventario == Decimal("50000")

    def test_requiere_reposicion_true(self, stock, producto):
        """cantidad <= stock_minimo → requiere_reposicion=True (línea 67)."""
        producto.stock_minimo = Decimal("50")
        producto.save()
        assert stock.requiere_reposicion is True

    def test_requiere_reposicion_false(self, stock, producto):
        """cantidad > stock_minimo → requiere_reposicion=False (línea 67)."""
        producto.stock_minimo = Decimal("10")
        producto.save()
        assert stock.requiere_reposicion is False


# ── MovimientoStock ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMovimientoStockModel:

    def test_str_egreso(self, producto, usuario_cajero):
        """__str__ usa signo '-' para EGRESO (líneas 181-182)."""
        from apps.inventario.models import MovimientoStock
        m = MovimientoStock(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.VENTA,
            cantidad=Decimal("5"),
            stock_resultante=Decimal("45"),
            autorizado_por=usuario_cajero,
        )
        assert "-5" in str(m)

    def test_str_ingreso(self, producto, usuario_cajero):
        """__str__ usa signo '+' para INGRESO (líneas 181-182)."""
        from apps.inventario.models import MovimientoStock
        m = MovimientoStock(
            producto=producto,
            tipo=MovimientoStock.Tipo.INGRESO,
            motivo=MovimientoStock.Motivo.COMPRA,
            cantidad=Decimal("10"),
            stock_resultante=Decimal("60"),
            autorizado_por=usuario_cajero,
        )
        assert "+10" in str(m)

    def test_clean_cantidad_cero_falla(self, producto, usuario_cajero):
        """cantidad=0 → ValidationError (línea 186)."""
        from apps.inventario.models import MovimientoStock
        m = MovimientoStock(
            producto=producto,
            tipo=MovimientoStock.Tipo.INGRESO,
            motivo=MovimientoStock.Motivo.COMPRA,
            cantidad=Decimal("0"),
            stock_resultante=Decimal("50"),
            autorizado_por=usuario_cajero,
        )
        with pytest.raises(ValidationError, match="mayor a cero"):
            m.clean()

    def test_clean_ingreso_con_motivo_egreso_falla(self, producto, usuario_cajero):
        """INGRESO + motivo de egreso → ValidationError (línea 204)."""
        from apps.inventario.models import MovimientoStock
        m = MovimientoStock(
            producto=producto,
            tipo=MovimientoStock.Tipo.INGRESO,
            motivo=MovimientoStock.Motivo.VENTA,
            cantidad=Decimal("5"),
            stock_resultante=Decimal("45"),
            autorizado_por=usuario_cajero,
        )
        with pytest.raises(ValidationError, match="no válido para Ingreso"):
            m.clean()

    def test_clean_egreso_con_motivo_ingreso_falla(self, producto, usuario_cajero):
        """EGRESO + motivo de ingreso → ValidationError (línea 208)."""
        from apps.inventario.models import MovimientoStock
        m = MovimientoStock(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.COMPRA,
            cantidad=Decimal("5"),
            stock_resultante=Decimal("45"),
            autorizado_por=usuario_cajero,
        )
        with pytest.raises(ValidationError, match="no válido para Egreso"):
            m.clean()


# ── AjusteInventario ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAjusteInventarioModel:

    def test_str(self, db, usuario_cajero):
        """__str__ muestra pk, tipo y estado (línea 262)."""
        from apps.inventario.models import AjusteInventario
        aj = AjusteInventario.objects.create(
            tipo=AjusteInventario.TipoAjuste.AUMENTO,
            motivo="Test",
            solicitado_por=usuario_cajero,
        )
        assert "Aumento" in str(aj)
        assert "Pendiente" in str(aj)


# ── DetalleAjuste ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDetalleAjusteModel:

    def test_str(self, producto, usuario_cajero):
        """__str__ = 'Producto: cantidad' (línea 293)."""
        from apps.inventario.models import AjusteInventario, DetalleAjuste
        aj = AjusteInventario.objects.create(
            tipo=AjusteInventario.TipoAjuste.AUMENTO,
            motivo="Test",
            solicitado_por=usuario_cajero,
        )
        det = DetalleAjuste.objects.create(
            ajuste=aj, producto=producto, cantidad=Decimal("5")
        )
        assert "5" in str(det)


# ── CostoHistorico ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCostoHistoricoModel:

    def test_str(self, producto):
        """__str__ muestra producto, costo y fecha (línea 333)."""
        from apps.inventario.models import CostoHistorico
        ch = CostoHistorico.objects.create(
            producto=producto,
            costo_unitario=Decimal("5000"),
            cantidad_comprada=Decimal("10"),
            fecha_compra=timezone.now(),
        )
        assert "5.000" in str(ch) or "5,000" in str(ch)

    def test_costo_total(self, producto):
        """costo_total = costo_unitario * cantidad_comprada (línea 337)."""
        from apps.inventario.models import CostoHistorico
        ch = CostoHistorico.objects.create(
            producto=producto,
            costo_unitario=Decimal("5000"),
            cantidad_comprada=Decimal("3"),
            fecha_compra=timezone.now(),
        )
        assert ch.costo_total == Decimal("15000")
