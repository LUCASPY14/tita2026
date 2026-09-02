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

    def test_precio_de_la_lista_del_cliente_gana_al_del_payload(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto,
    ):
        """cliente.lista_precio (fixture 'lista_precio', no default) tiene un
        PrecioPorLista de 3000 para 'producto' — precio_overrides debe usar
        ese valor aunque el item mande otro precio distinto."""
        from apps.ventas.services import VentaService

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("9999")}],
        )

        assert venta.monto_total == Decimal("3000")
        detalle = venta.detalles.get(producto=producto)
        assert detalle.precio_unitario == Decimal("3000")

    def test_sin_precio_en_la_lista_del_cliente_usa_el_del_payload(
        self, cliente, usuario_cajero, medio_pago_efectivo, categoria,
    ):
        """Producto sin ningún PrecioPorLista cargado — precio_overrides
        queda vacío para él y registrar_venta cae al precio del payload."""
        from apps.productos.models import Producto
        from apps.ventas.services import VentaService

        producto_sin_lista = Producto.objects.create(
            descripcion="Sin precio en lista", categoria=categoria,
            requiere_stock=False, permite_stock_negativo=True, activo=True,
        )

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto_sin_lista, "cantidad": Decimal("1"), "precio_unitario": Decimal("7500")}],
        )

        assert venta.monto_total == Decimal("7500")

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
        assert cc.origen == CuentaCorrienteCliente.Origen.CANTINA


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
        assert ultimo_cc.origen == CuentaCorrienteCliente.Origen.CANTINA


@pytest.mark.django_db
class TestRegistrarVentaCalculaIvaDelProducto:
    """
    El IVA de cada línea se calcula desde el impuesto asignado al producto
    (ProductoImpuesto), nunca desde lo que mande el cliente del POS —
    ver bug real: ventas de agosto quedaron con iva_10/iva_5/monto_exenta
    en 0 porque el POS mandaba esos campos fijos en 0 y el backend confiaba
    en ellos.
    """

    def _producto_con_impuesto(self, nombre_impuesto, porcentaje, categoria, unidad_medida, lista_precio):
        from apps.productos.models import Producto, Impuesto, ProductoImpuesto
        from datetime import date

        producto = Producto.objects.create(
            descripcion=f"Producto {nombre_impuesto}",
            categoria=categoria, unidad_medida=unidad_medida,
            requiere_stock=False,
        )
        impuesto, _ = Impuesto.objects.get_or_create(
            nombre=nombre_impuesto,
            defaults={"porcentaje": Decimal(porcentaje), "vigente_desde": date(2026, 1, 1), "activo": True},
        )
        ProductoImpuesto.objects.create(producto=producto, impuesto=impuesto)
        return producto

    def test_producto_con_iva_10_calcula_iva_incluido(
        self, cliente, usuario_cajero, medio_pago_efectivo, categoria, unidad_medida, lista_precio
    ):
        from apps.ventas.services import VentaService

        producto = self._producto_con_impuesto("IVA 10%", "10", categoria, unidad_medida, lista_precio)
        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero, tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("11000")}],
        )
        assert venta.monto_total == Decimal("11000")
        assert venta.iva_10 == Decimal("1000")
        assert venta.iva_5 == Decimal("0")
        assert venta.monto_exenta == Decimal("0")

    def test_producto_con_iva_5_calcula_iva_incluido(
        self, cliente, usuario_cajero, medio_pago_efectivo, categoria, unidad_medida, lista_precio
    ):
        from apps.ventas.services import VentaService

        producto = self._producto_con_impuesto("IVA 5%", "5", categoria, unidad_medida, lista_precio)
        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero, tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("2500")}],
        )
        assert venta.iva_5 == Decimal("119")
        assert venta.iva_10 == Decimal("0")
        assert venta.monto_exenta == Decimal("0")

    def test_producto_sin_impuesto_asignado_es_exenta(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.ventas.services import VentaService

        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero, tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        assert venta.monto_exenta == Decimal("3000")
        assert venta.iva_10 == Decimal("0")
        assert venta.iva_5 == Decimal("0")
