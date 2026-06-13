"""
Tests adicionales de VentaService y PagoService.
Cubre: hijo-ajeno, límite de crédito, PIN de autorización, stock get_or_create,
MovimientoCaja con cierre, anulación con factura EMITIDA, PagoService.registrar_pago.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo_del_cliente(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Sofía",
        apellido="López",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def cliente_sin_credito(db, tipo_cliente, lista_precio):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="Bloqueado",
        apellidos="Test",
        ruc_ci="NOCRED001",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
        limite_credito=Decimal("0"),
    )


@pytest.fixture
def cliente_externo(db, tipo_cliente, lista_precio):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="Externo",
        apellidos="Test",
        ruc_ci="EXT001",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )


@pytest.fixture
def producto_negativo(db, categoria, unidad_medida, lista_precio):
    """Producto que permite stock negativo — no necesita Stock preexistente."""
    from apps.productos.models import Producto, PrecioPorLista
    p = Producto.objects.create(
        descripcion="Café especial",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=True,
        activo=True,
    )
    PrecioPorLista.objects.create(producto=p, lista=lista_precio, precio_unitario=Decimal("2000"))
    return p


@pytest.fixture
def cierre_abierto(db, usuario_cajero):
    from apps.contabilidad.models import Caja, CierreCaja
    caja = Caja.objects.create(nombre="Caja SvcExt", activo=True)
    return CierreCaja.objects.create(
        caja=caja, empleado=usuario_cajero,
        monto_inicial=Decimal("0"),
        estado=CierreCaja.Estado.ABIERTO,
    )


def _venta(cliente, cajero, medio_pago, producto, cantidad=1, precio=3000, **kw):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente, cajero=cajero,
        tipo="CONTADO", medio_pago=medio_pago,
        items=[{
            "producto": producto,
            "cantidad": Decimal(str(cantidad)),
            "precio_unitario": Decimal(str(precio)),
        }],
        **kw,
    )


# ── Validaciones ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestValidacionesVenta:

    def test_hijo_de_otro_cliente_falla(
        self, cliente, cliente_externo, usuario_cajero, medio_pago_efectivo,
        producto, stock_producto
    ):
        """hijo pertenece a otro cliente → ValidationError (línea 60 services.py)."""
        from apps.ventas.services import VentaService
        from apps.clientes.models import Hijo
        hijo_ajeno = Hijo.objects.create(
            nombre="Ajeno", apellido="Test",
            cliente_responsable=cliente_externo, activo=True,
        )
        with pytest.raises(ValidationError, match="no pertenece al cliente"):
            VentaService.registrar_venta(
                cliente=cliente, cajero=usuario_cajero,
                tipo="CONTADO", medio_pago=medio_pago_efectivo,
                hijo=hijo_ajeno,
                items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
            )

    def test_credito_excede_limite_falla(
        self, cliente_sin_credito, usuario_cajero, producto, stock_producto
    ):
        """Venta a crédito supera límite_credito=0 → ValidationError (línea 160)."""
        from apps.ventas.services import VentaService
        with pytest.raises(ValidationError, match="límite de crédito"):
            VentaService.registrar_venta(
                cliente=cliente_sin_credito, cajero=usuario_cajero,
                tipo="CREDITO",
                items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
            )

    def test_stock_no_preexistente_se_crea_via_get_or_create(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto_negativo
    ):
        """Sin Stock en DB, se usa get_or_create y la venta queda con stock negativo (línea 220)."""
        from apps.ventas.services import VentaService
        from apps.inventario.models import Stock
        assert not Stock.objects.filter(producto=producto_negativo).exists()
        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero,
            tipo="CONTADO", medio_pago=medio_pago_efectivo,
            items=[{
                "producto": producto_negativo,
                "cantidad": Decimal("2"),
                "precio_unitario": Decimal("2000"),
            }],
        )
        assert venta is not None
        stock = Stock.objects.get(producto=producto_negativo)
        assert stock.cantidad == Decimal("-2")


# ── PIN de autorización ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPINAutorizacion:

    def _tarjeta_baja(self, hijo, nro, saldo=100, limite=50000):
        from apps.core.models import Tarjeta
        return Tarjeta.objects.create(
            nro_tarjeta=nro, hijo=hijo,
            saldo_actual=Decimal(str(saldo)),
            limite_credito=Decimal(str(limite)),
            estado=Tarjeta.Estado.ACTIVA,
        )

    def test_pin_incorrecto_falla(
        self, cliente, usuario_cajero, producto, stock_producto, hijo_del_cliente
    ):
        """Saldo insuficiente + PIN incorrecto → error (línea 174 services.py)."""
        from apps.ventas.services import VentaService
        tarjeta = self._tarjeta_baja(hijo_del_cliente, "PIN_BAD_01")
        with pytest.raises(ValidationError, match="PIN de autorización incorrecto"):
            VentaService.registrar_venta(
                cliente=cliente, cajero=usuario_cajero,
                tipo="CONTADO", tarjeta=tarjeta, pin_autorizacion="WRONG",
                items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
            )

    def test_pin_valido_excede_limite_credito_falla(
        self, cliente, usuario_cajero, producto, stock_producto, hijo_del_cliente
    ):
        """PIN correcto pero déficit > limite_credito → error (líneas 176-181)."""
        from apps.ventas.services import VentaService
        tarjeta = self._tarjeta_baja(hijo_del_cliente, "PIN_OVER_01", saldo=0, limite=100)
        with pytest.raises(ValidationError, match="límite de crédito autorizado"):
            VentaService.registrar_venta(
                cliente=cliente, cajero=usuario_cajero,
                tipo="CONTADO", tarjeta=tarjeta, pin_autorizacion="0000",
                items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
            )

    def test_pin_valido_dentro_limite_ok(
        self, cliente, usuario_cajero, producto, stock_producto, hijo_del_cliente
    ):
        """PIN correcto + dentro del límite → venta registrada (líneas 172-182)."""
        from apps.ventas.services import VentaService
        from apps.ventas.models import Venta
        tarjeta = self._tarjeta_baja(hijo_del_cliente, "PIN_OK_01", saldo=0, limite=10000)
        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero,
            tipo="CONTADO", tarjeta=tarjeta, pin_autorizacion="0000",
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        assert venta.estado == Venta.Estado.ACTIVA


# ── Venta con tarjeta y cierre ────────────────────────────────────────────────

@pytest.mark.django_db
class TestVentaTarjetaConCierre:

    def test_venta_tarjeta_con_cierre_crea_movimiento_caja(
        self, cliente, usuario_cajero, producto, stock_producto,
        hijo_del_cliente, cierre_abierto
    ):
        """Venta pagada con tarjeta + cierre_caja → MovimientoCaja (líneas 296-297)."""
        from apps.ventas.services import VentaService
        from apps.contabilidad.models import MovimientoCaja
        from apps.core.models import Tarjeta
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="CIERRE_T01", hijo=hijo_del_cliente,
            saldo_actual=Decimal("20000"), estado=Tarjeta.Estado.ACTIVA,
        )
        VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero,
            tipo="CONTADO", tarjeta=tarjeta, cierre_caja=cierre_abierto,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        mov = MovimientoCaja.objects.filter(cierre=cierre_abierto).first()
        assert mov is not None
        assert mov.monto == Decimal("3000")


# ── Anulación edge cases ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnularVentaEdgeCases:

    def test_anular_con_factura_emitida_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo,
        producto, stock_producto, usuario_admin
    ):
        """Venta con factura EMITIDA no puede anularse → ValidationError (línea 323)."""
        from apps.ventas.services import VentaService
        from apps.contabilidad.models import Factura
        from apps.ventas.models import Venta

        venta = _venta(cliente, usuario_cajero, medio_pago_efectivo, producto)
        factura = Factura.objects.create(
            nro_factura="001-001-0000001",
            monto_total=Decimal("3000"),
            estado=Factura.Estado.EMITIDA,
            cliente=cliente,
        )
        Venta.objects.filter(pk=venta.pk).update(factura=factura)
        venta.refresh_from_db()

        with pytest.raises(ValidationError, match="factura EMITIDA"):
            VentaService.anular_venta(venta, anulado_por=usuario_admin)


# ── PagoService ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPagoService:

    def test_registrar_pago_venta_credito_ok(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        """Flujo completo: PagoService.registrar_pago para venta a crédito (líneas 415-476)."""
        from apps.ventas.services import VentaService, PagoService
        from apps.ventas.models import Venta, PagoVenta

        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero, tipo="CREDITO",
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        pago = PagoService.registrar_pago(
            cliente=cliente, monto=Decimal("3000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero, venta=venta,
        )
        assert isinstance(pago, PagoVenta)
        venta.refresh_from_db()
        assert venta.estado_pago == Venta.EstadoPago.PAGADO

    def test_pago_excede_saldo_pendiente_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.ventas.services import VentaService, PagoService

        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero, tipo="CREDITO",
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        with pytest.raises(ValidationError, match="saldo pendiente"):
            PagoService.registrar_pago(
                cliente=cliente, monto=Decimal("9999"),
                medio_pago=medio_pago_efectivo, cajero=usuario_cajero, venta=venta,
            )

    def test_pago_a_venta_contado_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.ventas.services import VentaService, PagoService

        venta = VentaService.registrar_venta(
            cliente=cliente, cajero=usuario_cajero,
            tipo="CONTADO", medio_pago=medio_pago_efectivo,
            items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        )
        with pytest.raises(ValidationError, match="credito"):
            PagoService.registrar_pago(
                cliente=cliente, monto=Decimal("3000"),
                medio_pago=medio_pago_efectivo, cajero=usuario_cajero, venta=venta,
            )

    def test_pago_sin_venta_registra_en_cuenta_corriente(
        self, cliente, usuario_cajero, medio_pago_efectivo
    ):
        """Pago sin venta específica (abono a cuenta corriente)."""
        from apps.ventas.services import PagoService
        from apps.clientes.models import CuentaCorrienteCliente

        pago = PagoService.registrar_pago(
            cliente=cliente, monto=Decimal("10000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero, venta=None,
        )
        assert pago is not None
        cc = CuentaCorrienteCliente.objects.filter(cliente=cliente, pago=pago).first()
        assert cc is not None
        assert cc.monto == Decimal("10000")
