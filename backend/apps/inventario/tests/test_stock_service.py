"""
Tests para StockService.
Cubre: validar_disponibilidad, reservar_stock, obtener_productos_bajo_stock,
calcular_valor_inventario, obtener_rotacion_inventario, ajustar_stock.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError


@pytest.fixture
def producto_sin_stock(db, categoria, unidad_medida):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Sin stock test",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=False,
        activo=True,
        stock_minimo=Decimal("5"),
    )


@pytest.fixture
def producto_negativo(db, categoria, unidad_medida):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Permite negativo",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=True,
        activo=True,
    )


@pytest.fixture
def stock_normal(db, producto_sin_stock):
    from apps.inventario.models import Stock
    return Stock.objects.create(
        producto=producto_sin_stock,
        cantidad=Decimal("20"),
    )


# ── StockService.validar_disponibilidad ───────────────────────────────────────

@pytest.mark.django_db
class TestValidarDisponibilidad:

    def test_producto_inexistente_lanza_error(self):
        from apps.inventario.services import StockService
        with pytest.raises(ValidationError, match="no existe"):
            StockService.validar_disponibilidad(9999, Decimal("1"))

    def test_disponible_cuando_stock_suficiente(self, stock_normal, producto_sin_stock):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad(producto_sin_stock.pk, Decimal("10"))
        assert result["disponible"] is True
        assert result["faltante"] == Decimal("0.000")

    def test_no_disponible_cuando_stock_insuficiente(self, stock_normal, producto_sin_stock):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad(producto_sin_stock.pk, Decimal("50"))
        assert result["disponible"] is False
        assert result["faltante"] == Decimal("30.000")

    def test_siempre_disponible_si_permite_negativo(self, db, producto_negativo):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad(producto_negativo.pk, Decimal("9999"))
        assert result["disponible"] is True
        assert result["permite_negativo"] is True

    def test_stock_cero_retorna_stock_actual_cero(self, producto_sin_stock):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad(producto_sin_stock.pk, Decimal("1"))
        assert result["stock_actual"] == Decimal("0.000")
        assert result["disponible"] is False


@pytest.mark.django_db
class TestValidarDisponibilidadMultiple:

    def test_todo_disponible(self, stock_normal, producto_sin_stock):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad_multiple([
            {"producto_id": producto_sin_stock.pk, "cantidad": Decimal("5")},
        ])
        assert result["todo_disponible"] is True
        assert len(result["productos_faltantes"]) == 0

    def test_detecta_faltante(self, stock_normal, producto_sin_stock):
        from apps.inventario.services import StockService
        result = StockService.validar_disponibilidad_multiple([
            {"producto_id": producto_sin_stock.pk, "cantidad": Decimal("100")},
        ])
        assert result["todo_disponible"] is False
        assert len(result["productos_faltantes"]) == 1
        assert result["items"][0]["producto"]["id"] == producto_sin_stock.pk


# ── StockService.reservar_stock ───────────────────────────────────────────────

@pytest.mark.django_db
class TestReservarStock:

    def test_reserva_descuenta_stock_y_crea_movimiento(self, stock_normal, producto_sin_stock, usuario_cajero):
        from apps.inventario.services import StockService
        from apps.inventario.models import MovimientoStock

        stock = StockService.reservar_stock(
            producto_id=producto_sin_stock.pk,
            cantidad=Decimal("5"),
            autorizado_por=usuario_cajero,
        )

        assert stock.cantidad == Decimal("15")
        mov = MovimientoStock.objects.filter(
            producto=producto_sin_stock, tipo=MovimientoStock.Tipo.EGRESO
        ).first()
        assert mov is not None
        assert mov.cantidad == Decimal("5")

    def test_cantidad_cero_falla(self, stock_normal, producto_sin_stock, usuario_cajero):
        from apps.inventario.services import StockService
        with pytest.raises(ValidationError, match="mayor a 0"):
            StockService.reservar_stock(
                producto_id=producto_sin_stock.pk,
                cantidad=Decimal("0"),
                autorizado_por=usuario_cajero,
            )

    def test_stock_insuficiente_falla(self, stock_normal, producto_sin_stock, usuario_cajero):
        from apps.inventario.services import StockService
        with pytest.raises(ValidationError, match="insuficiente"):
            StockService.reservar_stock(
                producto_id=producto_sin_stock.pk,
                cantidad=Decimal("999"),
                autorizado_por=usuario_cajero,
            )


# ── StockService.obtener_productos_bajo_stock ─────────────────────────────────

@pytest.mark.django_db
class TestProductosBajoStock:

    def test_detecta_producto_bajo_minimo(self, db, categoria, unidad_medida):
        from apps.productos.models import Producto
        from apps.inventario.models import Stock
        from apps.inventario.services import StockService

        p = Producto.objects.create(
            descripcion="Bajo stock",
            categoria=categoria,
            unidad_medida=unidad_medida,
            requiere_stock=True,
            activo=True,
            stock_minimo=Decimal("10"),
        )
        Stock.objects.create(producto=p, cantidad=Decimal("3"))

        resultado = StockService.obtener_productos_bajo_stock()
        ids = [r["producto_id"] for r in resultado]
        assert p.pk in ids

    def test_producto_critico_stock_cero(self, db, categoria, unidad_medida):
        from apps.productos.models import Producto
        from apps.inventario.models import Stock
        from apps.inventario.services import StockService

        p = Producto.objects.create(
            descripcion="Stock cero",
            categoria=categoria,
            unidad_medida=unidad_medida,
            requiere_stock=True,
            activo=True,
            stock_minimo=Decimal("5"),
        )
        Stock.objects.create(producto=p, cantidad=Decimal("0"))

        resultado = StockService.obtener_productos_bajo_stock()
        item = next(r for r in resultado if r["producto_id"] == p.pk)
        assert item["critico"] is True


# ── StockService.calcular_valor_inventario ────────────────────────────────────

@pytest.mark.django_db
class TestCalcularValorInventario:

    def test_valor_correcto(self, stock_normal, producto_sin_stock):
        from apps.inventario.services import StockService

        resultado = StockService.calcular_valor_inventario()
        assert "valor_total" in resultado
        assert resultado["cantidad_productos"] >= 1
        assert isinstance(resultado["valor_total"], Decimal)

    def test_sin_stock_valor_cero(self, db):
        from apps.inventario.services import StockService
        resultado = StockService.calcular_valor_inventario()
        assert resultado["valor_total"] == Decimal("0")


# ── StockService.obtener_rotacion_inventario ──────────────────────────────────

@pytest.mark.django_db
class TestRotacionInventario:

    def test_rotacion_con_ventas(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.ventas.services import VentaService
        from apps.inventario.services import StockService

        VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("5"), "precio_unitario": Decimal("3000")}],
        )

        resultado = StockService.obtener_rotacion_inventario(dias=30)
        assert len(resultado) >= 1
        assert resultado[0]["total_vendido"] == Decimal("5")

    def test_sin_ventas_retorna_lista_vacia(self, db):
        from apps.inventario.services import StockService
        resultado = StockService.obtener_rotacion_inventario(dias=30)
        assert resultado == []


# ── StockService.ajustar_stock ────────────────────────────────────────────────

@pytest.mark.django_db
class TestAjustarStock:

    def test_ingreso_aumenta_stock_y_crea_movimiento(self, producto_sin_stock, usuario_admin):
        from apps.inventario.services import StockService
        from apps.inventario.models import MovimientoStock, Stock

        movimiento = StockService.ajustar_stock(
            producto=producto_sin_stock,
            cantidad=Decimal("10"),
            tipo=MovimientoStock.Tipo.INGRESO,
            motivo=MovimientoStock.Motivo.AJUSTE_AUMENTO,
            autorizado_por=usuario_admin,
        )

        stock = Stock.objects.get(producto=producto_sin_stock)
        assert stock.cantidad == Decimal("10")
        assert movimiento.stock_resultante == Decimal("10")
        assert movimiento.tipo == MovimientoStock.Tipo.INGRESO

    def test_egreso_descuenta_stock(self, stock_normal, producto_sin_stock, usuario_admin):
        from apps.inventario.services import StockService
        from apps.inventario.models import MovimientoStock, Stock

        StockService.ajustar_stock(
            producto=producto_sin_stock,
            cantidad=Decimal("4"),
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.AJUSTE_MERMA,
            autorizado_por=usuario_admin,
        )

        stock = Stock.objects.get(producto=producto_sin_stock)
        assert stock.cantidad == Decimal("16")

    def test_egreso_sin_stock_suficiente_falla(self, producto_sin_stock, usuario_admin):
        from apps.inventario.services import StockService
        from apps.inventario.models import MovimientoStock

        with pytest.raises(ValidationError, match="insuficiente"):
            StockService.ajustar_stock(
                producto=producto_sin_stock,
                cantidad=Decimal("5"),
                tipo=MovimientoStock.Tipo.EGRESO,
                motivo=MovimientoStock.Motivo.AJUSTE_MERMA,
                autorizado_por=usuario_admin,
            )


# ── Edge cases para cobertura 100% ────────────────────────────────────────────

@pytest.mark.django_db
class TestReservarStockSegundaValidacion:
    """Cubre la segunda validación con lock (línea 149)."""

    def test_segunda_validacion_falla_cuando_stock_cambia(self, producto, usuario_cajero):
        from unittest.mock import patch
        from apps.inventario.services import StockService
        from apps.inventario.models import Stock

        Stock.objects.filter(producto=producto).update(cantidad=Decimal("0"))

        with patch.object(
            StockService, "validar_disponibilidad",
            return_value={"disponible": True, "stock_actual": Decimal("0"), "faltante": Decimal("0")},
        ):
            with pytest.raises(ValidationError, match="insuficiente"):
                StockService.reservar_stock(
                    producto_id=producto.pk,
                    cantidad=Decimal("5"),
                    autorizado_por=usuario_cajero,
                )


@pytest.mark.django_db
class TestProductosBajoStockSinStock:
    """Cubre el except Stock.DoesNotExist en obtener_productos_bajo_stock (líneas 185-186)."""

    def test_producto_sin_relacion_stock_retorna_zero(self, producto_sin_stock):
        from unittest.mock import patch, MagicMock, PropertyMock
        from apps.inventario.services import StockService
        from apps.inventario.models import Stock
        from apps.productos.models import Producto

        mock_p = MagicMock(spec=Producto)
        mock_p.pk = producto_sin_stock.pk
        mock_p.descripcion = "Mock sin stock"
        mock_p.codigo_barra = None
        mock_p.stock_minimo = Decimal("5")
        type(mock_p).stock = PropertyMock(side_effect=Stock.DoesNotExist)

        mock_qs = MagicMock()
        mock_qs.select_related.return_value.order_by.return_value = [mock_p]

        with patch.object(Producto.objects, "filter", return_value=mock_qs):
            resultado = StockService.obtener_productos_bajo_stock()

        assert len(resultado) == 1
        assert resultado[0]["stock_actual"] == Decimal("0.000")
        assert resultado[0]["critico"] is True


@pytest.mark.django_db
class TestRotacionProductoEliminado:
    """Cubre el except Producto.DoesNotExist en obtener_rotacion_inventario (líneas 254-255)."""

    def test_movimiento_con_producto_inexistente_se_omite(self, producto, stock_producto, usuario_cajero):
        from unittest.mock import patch
        from apps.inventario.services import StockService
        from apps.inventario.models import MovimientoStock
        from apps.productos.models import Producto

        MovimientoStock.objects.create(
            producto=producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            motivo=MovimientoStock.Motivo.VENTA,
            cantidad=Decimal("1"),
            stock_resultante=Decimal("49"),
            autorizado_por=usuario_cajero,
        )

        with patch.object(Producto.objects, "get", side_effect=Producto.DoesNotExist):
            resultado = StockService.obtener_rotacion_inventario(dias=30)

        assert resultado == []
