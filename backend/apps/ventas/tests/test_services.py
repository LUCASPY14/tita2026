"""
Tests de VentaService — cubre los caminos críticos del flujo de ventas.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
class TestRegistrarVentaContado:

    def test_venta_contado_basica(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto):
        from apps.ventas.services import VentaService
        from apps.ventas.models import Venta

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        )

        assert venta.estado == Venta.Estado.ACTIVA
        assert venta.monto_total == Decimal("6000")
        assert venta.tipo == "CONTADO"
        assert venta.estado_pago == "PAGADO"

    def test_venta_descuenta_stock(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto):
        from apps.ventas.services import VentaService
        from apps.inventario.models import Stock

        VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("3"), "precio_unitario": Decimal("3000")}],
        )

        stock = Stock.objects.get(producto=producto)
        assert stock.cantidad == Decimal("47")

    def test_venta_sin_items_falla(self, cliente, usuario_cajero, medio_pago_efectivo):
        from apps.ventas.services import VentaService

        with pytest.raises(ValidationError, match="al menos un producto"):
            VentaService.registrar_venta(
                cliente=cliente,
                cajero=usuario_cajero,
                tipo="CONTADO",
                medio_pago=medio_pago_efectivo,
                items=[],
            )

    def test_venta_stock_insuficiente_falla(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto):
        from apps.ventas.services import VentaService

        with pytest.raises(ValidationError, match="Stock insuficiente"):
            VentaService.registrar_venta(
                cliente=cliente,
                cajero=usuario_cajero,
                tipo="CONTADO",
                medio_pago=medio_pago_efectivo,
                items=[{"producto": producto, "cantidad": Decimal("100"), "precio_unitario": Decimal("3000")}],
            )

    def test_venta_contado_sin_medio_pago_falla(self, cliente, usuario_cajero, producto, stock_producto):
        from apps.ventas.services import VentaService

        with pytest.raises(ValidationError, match="medio de pago"):
            VentaService.registrar_venta(
                cliente=cliente,
                cajero=usuario_cajero,
                tipo="CONTADO",
                medio_pago=None,
                items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
            )


@pytest.mark.django_db
class TestRegistrarVentaCredito:

    def test_venta_credito_genera_cuenta_corriente(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto):
        from apps.ventas.services import VentaService
        from apps.clientes.models import CuentaCorrienteCliente

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CREDITO",
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )

        cc = CuentaCorrienteCliente.objects.filter(cliente=cliente, venta=venta, tipo="DEBITO").first()
        assert cc is not None
        assert cc.monto == Decimal("3000")
        assert cc.saldo_resultante == Decimal("3000")


@pytest.mark.django_db
class TestAnularVenta:

    def _crear_venta(self, cliente, cajero, medio_pago, producto, stock_producto):
        from apps.ventas.services import VentaService
        return VentaService.registrar_venta(
            cliente=cliente,
            cajero=cajero,
            tipo="CONTADO",
            medio_pago=medio_pago,
            items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        )

    def test_anular_revierte_stock(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, usuario_admin):
        from apps.ventas.services import VentaService
        from apps.inventario.models import Stock

        venta = self._crear_venta(cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto)
        stock_post_venta = Stock.objects.get(producto=producto).cantidad

        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        stock_final = Stock.objects.get(producto=producto).cantidad
        assert stock_final == stock_post_venta + Decimal("2")

    def test_anular_dos_veces_falla(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, usuario_admin):
        from apps.ventas.services import VentaService

        venta = self._crear_venta(cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto)
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        with pytest.raises(ValidationError, match="ya está anulada"):
            VentaService.anular_venta(venta, anulado_por=usuario_admin)

    def test_anular_credito_revierte_cuenta_corriente(self, cliente, usuario_cajero, producto, stock_producto, usuario_admin):
        from apps.ventas.services import VentaService
        from apps.clientes.models import CuentaCorrienteCliente

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CREDITO",
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        ultimo_cc = (
            CuentaCorrienteCliente.objects
            .filter(cliente=cliente)
            .order_by("-id")
            .first()
        )
        assert ultimo_cc.tipo == "CREDITO"
        assert ultimo_cc.saldo_resultante == Decimal("0")
