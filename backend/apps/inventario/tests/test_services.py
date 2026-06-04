"""
Tests para inventario — stock alerts y movimientos.
"""
import pytest
from decimal import Decimal


@pytest.fixture
def producto_con_stock_minimo(db, categoria, unidad_medida):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Producto test",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=False,
        activo=True,
        stock_minimo=Decimal("10"),
    )


@pytest.fixture
def stock_bajo(db, producto_con_stock_minimo):
    from apps.inventario.models import Stock
    return Stock.objects.create(
        producto=producto_con_stock_minimo,
        cantidad=Decimal("3"),
    )


@pytest.fixture
def stock_cero(db, producto_con_stock_minimo):
    from apps.inventario.models import Stock
    return Stock.objects.create(
        producto=producto_con_stock_minimo,
        cantidad=Decimal("0"),
    )


@pytest.fixture
def stock_ok(db, producto_con_stock_minimo):
    from apps.inventario.models import Stock
    return Stock.objects.create(
        producto=producto_con_stock_minimo,
        cantidad=Decimal("20"),
    )


@pytest.mark.django_db
class TestAlertarStockMinimo:

    def test_crea_alerta_stock_minimo(self, stock_bajo, producto_con_stock_minimo):
        from apps.inventario.tasks import alertar_stock_minimo
        from apps.inventario.models import AlertaStock

        result = alertar_stock_minimo()

        assert AlertaStock.objects.filter(
            producto=producto_con_stock_minimo, activa=True
        ).exists()
        assert result["alertas_creadas"] >= 1

    def test_crea_alerta_stock_cero(self, stock_cero, producto_con_stock_minimo):
        from apps.inventario.tasks import alertar_stock_minimo
        from apps.inventario.models import AlertaStock

        alertar_stock_minimo()

        alerta = AlertaStock.objects.get(producto=producto_con_stock_minimo, activa=True)
        assert alerta.tipo == AlertaStock.TipoAlerta.STOCK_CERO

    def test_resuelve_alerta_cuando_stock_sube(self, stock_bajo, producto_con_stock_minimo):
        from apps.inventario.tasks import alertar_stock_minimo
        from apps.inventario.models import AlertaStock, Stock

        alertar_stock_minimo()
        assert AlertaStock.objects.filter(
            producto=producto_con_stock_minimo, activa=True
        ).exists()

        Stock.objects.filter(producto=producto_con_stock_minimo).update(cantidad=Decimal("25"))
        alertar_stock_minimo()

        assert not AlertaStock.objects.filter(
            producto=producto_con_stock_minimo, activa=True
        ).exists()

    def test_no_duplica_alertas_del_mismo_tipo(self, stock_bajo, producto_con_stock_minimo):
        from apps.inventario.tasks import alertar_stock_minimo
        from apps.inventario.models import AlertaStock

        alertar_stock_minimo()
        alertar_stock_minimo()

        count = AlertaStock.objects.filter(
            producto=producto_con_stock_minimo, activa=True
        ).count()
        assert count == 1

    def test_sin_alertas_cuando_stock_suficiente(self, stock_ok, producto_con_stock_minimo):
        from apps.inventario.tasks import alertar_stock_minimo
        from apps.inventario.models import AlertaStock

        result = alertar_stock_minimo()

        assert not AlertaStock.objects.filter(
            producto=producto_con_stock_minimo, activa=True
        ).exists()
        assert result["alertas_creadas"] == 0


@pytest.mark.django_db
class TestMovimientoStock:

    def test_venta_crea_movimiento_egreso(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.ventas.services import VentaService
        from apps.inventario.models import MovimientoStock

        VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        )

        mov = MovimientoStock.objects.filter(
            producto=producto, tipo=MovimientoStock.Tipo.EGRESO
        ).first()
        assert mov is not None
        assert mov.cantidad == Decimal("2")

    def test_anulacion_crea_movimiento_devolucion(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, usuario_admin
    ):
        from apps.ventas.services import VentaService
        from apps.inventario.models import MovimientoStock

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        )
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        mov = MovimientoStock.objects.filter(
            producto=producto, tipo=MovimientoStock.Tipo.INGRESO,
            motivo=MovimientoStock.Motivo.DEVOLUCION_CLIENTE,
        ).first()
        assert mov is not None
        assert mov.cantidad == Decimal("2")
