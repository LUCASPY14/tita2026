"""
Tests para modelos de la app inventario.
Cubre __str__, @property y clean() de todos los modelos.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def stock(db, producto, stock_producto):
    """Reutiliza stock_producto de conftest (cantidad=50)."""
    return stock_producto


@pytest.fixture
def lote(db, producto):
    from apps.inventario.models import LoteProducto
    return LoteProducto.objects.create(
        producto=producto,
        numero_lote="L001",
        fecha_vencimiento=date.today() + timedelta(days=60),
        cantidad_inicial=Decimal("100"),
        cantidad_disponible=Decimal("100"),
    )


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
        from apps.inventario.models import Stock
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


# ── AlertaStock ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlertaStockModel:

    def test_str_activa(self, producto, stock_producto):
        """activa=True → 'Activa' en __str__ (líneas 375-376)."""
        from apps.inventario.models import AlertaStock
        alerta = AlertaStock.objects.create(
            producto=producto,
            tipo=AlertaStock.TipoAlerta.STOCK_MINIMO,
            stock_actual=Decimal("5"),
            stock_minimo=Decimal("10"),
            activa=True,
        )
        assert "Activa" in str(alerta)

    def test_str_resuelta(self, producto, stock_producto):
        """activa=False → 'Resuelta' en __str__ (línea 375)."""
        from apps.inventario.models import AlertaStock
        alerta = AlertaStock.objects.create(
            producto=producto,
            tipo=AlertaStock.TipoAlerta.STOCK_CERO,
            stock_actual=Decimal("0"),
            stock_minimo=Decimal("10"),
            activa=False,
        )
        assert "Resuelta" in str(alerta)


# ── LoteProducto ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoteProductoModel:

    def test_str_disponible(self, lote):
        """bloqueado=False → 'Disponible' (líneas 426-427)."""
        assert "Disponible" in str(lote)
        assert "L001" in str(lote)

    def test_str_bloqueado(self, lote):
        """bloqueado=True → 'Bloqueado' (línea 426)."""
        lote.bloqueado = True
        lote.motivo_bloqueo = lote.MotivoBloqueo.VENCIDO
        lote.save()
        assert "Bloqueado" in str(lote)

    def test_dias_hasta_vencimiento_futuro(self, lote):
        """fecha_vencimiento en el futuro → días positivos (líneas 431-433)."""
        dias = lote.dias_hasta_vencimiento
        assert dias is not None
        assert dias > 0

    def test_dias_hasta_vencimiento_sin_fecha(self, producto):
        """fecha_vencimiento=None → None (línea 432) — instancia sin guardar."""
        from apps.inventario.models import LoteProducto
        lote_sin_fecha = LoteProducto(
            producto=producto,
            numero_lote="L_NOFEC",
            fecha_vencimiento=None,
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("10"),
        )
        assert lote_sin_fecha.dias_hasta_vencimiento is None

    def test_esta_vencido_false(self, lote):
        """fecha_vencimiento futura → esta_vencido=False (línea 437)."""
        assert lote.esta_vencido is False

    def test_esta_vencido_true(self, producto):
        """fecha_vencimiento pasada → esta_vencido=True (línea 437)."""
        from apps.inventario.models import LoteProducto
        lote_viejo = LoteProducto(
            producto=producto,
            numero_lote="L_OLD",
            fecha_vencimiento=date.today() - timedelta(days=1),
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("10"),
        )
        assert lote_viejo.esta_vencido is True

    def test_proximo_a_vencer_true(self, producto):
        """0 <= dias <= 30 → proximo_a_vencer=True (líneas 441-442)."""
        from apps.inventario.models import LoteProducto
        lote_pronto = LoteProducto(
            producto=producto,
            numero_lote="L_SOON",
            fecha_vencimiento=date.today() + timedelta(days=15),
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("10"),
        )
        assert lote_pronto.proximo_a_vencer is True

    def test_proximo_a_vencer_false(self, lote):
        """días > 30 → proximo_a_vencer=False (líneas 441-442)."""
        assert lote.proximo_a_vencer is False

    def test_clean_fecha_vencimiento_antes_fabricacion(self, producto):
        """fecha_vencimiento <= fecha_fabricacion → ValidationError (líneas 445-449)."""
        from apps.inventario.models import LoteProducto
        lote = LoteProducto(
            producto=producto,
            numero_lote="L_BAD",
            fecha_fabricacion=date.today(),
            fecha_vencimiento=date.today() - timedelta(days=1),
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("10"),
        )
        with pytest.raises(ValidationError, match="posterior a la fecha de fabricación"):
            lote.clean()

    def test_clean_cantidad_disponible_mayor_inicial(self, producto):
        """cantidad_disponible > cantidad_inicial → ValidationError (líneas 450-453)."""
        from apps.inventario.models import LoteProducto
        lote = LoteProducto(
            producto=producto,
            numero_lote="L_QTY",
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("15"),
        )
        with pytest.raises(ValidationError, match="mayor a la cantidad inicial"):
            lote.clean()

    def test_clean_bloqueado_sin_motivo(self, producto):
        """bloqueado=True sin motivo → ValidationError (líneas 454-455)."""
        from apps.inventario.models import LoteProducto
        lote = LoteProducto(
            producto=producto,
            numero_lote="L_BLK",
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_inicial=Decimal("10"),
            cantidad_disponible=Decimal("10"),
            bloqueado=True,
            motivo_bloqueo=None,
        )
        with pytest.raises(ValidationError, match="motivo"):
            lote.clean()


# ── AlertaVencimiento ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlertaVencimientoModel:

    def test_str(self, lote):
        """__str__ = 'Lote - tipo_display' (línea 513)."""
        from apps.inventario.models import AlertaVencimiento
        av = AlertaVencimiento.objects.create(
            lote=lote,
            tipo=AlertaVencimiento.TipoAlerta.DIAS_30,
            dias_restantes=30,
            fecha_vencimiento=lote.fecha_vencimiento,
            cantidad_lote=Decimal("100"),
        )
        assert "30 días" in str(av)
