"""
Tests para inventario — stock alerts y movimientos.
"""
import pytest
from decimal import Decimal


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
