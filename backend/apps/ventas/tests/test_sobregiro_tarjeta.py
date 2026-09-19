"""
Sobregiro de la tarjeta de cantina.

- Sin "permite saldo negativo": prepago estricto (no puede quedar negativa).
- Con sobregiro y límite > 0: el límite es el tope máximo de deuda.
- Con sobregiro y límite 0: sin tope (misma convención que la cuenta corriente).
- La venta que superaría el tope se rechaza completa.
"""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(nombre="Tope", apellido="Prueba", cliente_responsable=cliente, activo=True)


def _tarjeta(hijo, nro, saldo, permite=True, limite=0):
    """Tarjeta cuyo saldo inicial entra por el libro mayor (un trigger de la base
    recalcula saldo_actual desde los movimientos; un saldo sin movimiento se pierde)."""
    from apps.core.models import MovimientoTarjeta, Tarjeta
    saldo = Decimal(str(saldo))
    t = Tarjeta.objects.create(
        nro_tarjeta=nro, hijo=hijo,
        permite_saldo_negativo=permite, limite_credito=Decimal(str(limite)),
        estado=Tarjeta.Estado.ACTIVA,
    )
    if saldo:
        tipo = MovimientoTarjeta.Tipo.RECARGA if saldo > 0 else MovimientoTarjeta.Tipo.CONSUMO
        MovimientoTarjeta.objects.create(
            tarjeta=t, tipo=tipo, monto=abs(saldo),
            saldo_anterior=Decimal("0"), saldo_resultante=saldo,
            descripcion="Saldo inicial de prueba",
        )
        t.refresh_from_db()
    return t


def _vender(cliente, cajero, producto, tarjeta, unidades):
    """Vende `unidades` del producto de prueba (3.000 Gs. cada una, según la lista de precios)."""
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente, cajero=cajero, tipo="CONTADO", tarjeta=tarjeta,
        items=[{"producto": producto, "cantidad": Decimal(str(unidades))}],
    )


@pytest.mark.django_db
class TestPropiedadesDeSobregiro:

    def test_prepago_no_puede_endeudarse(self, hijo):
        t = _tarjeta(hijo, "SB-1", 10000, permite=False)
        assert t.deuda_maxima == Decimal("0")
        assert not t.sobregiro_sin_tope
        assert t.puede_pagar(Decimal("10000")) is True
        assert t.puede_pagar(Decimal("10001")) is False

    def test_sobregiro_con_tope(self, hijo):
        t = _tarjeta(hijo, "SB-2", 10000, permite=True, limite=50000)
        assert t.deuda_maxima == Decimal("50000")
        assert not t.sobregiro_sin_tope
        assert t.saldo_disponible == Decimal("60000")
        assert t.puede_pagar(Decimal("60000")) is True
        assert t.puede_pagar(Decimal("60001")) is False

    def test_sobregiro_sin_tope_con_limite_cero(self, hijo):
        t = _tarjeta(hijo, "SB-3", 0, permite=True, limite=0)
        assert t.deuda_maxima is None
        assert t.sobregiro_sin_tope is True
        assert t.puede_pagar(Decimal("99999999")) is True

    def test_la_deuda_ya_existente_cuenta_para_el_tope(self, hijo):
        t = _tarjeta(hijo, "SB-4", -40000, permite=True, limite=50000)
        assert t.puede_pagar(Decimal("10000")) is True
        assert t.puede_pagar(Decimal("10001")) is False


@pytest.mark.django_db
class TestVentaRespetaElTope:
    """Cada unidad cuesta 3.000 Gs."""

    def test_dentro_del_tope_se_cobra_y_queda_en_negativo(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        t = _tarjeta(hijo, "SB-V1", 3000, limite=12000)
        _vender(cliente, usuario_cajero, producto, t, 3)  # 9.000
        t.refresh_from_db()
        assert t.saldo_actual == Decimal("-6000")

    def test_llegar_justo_al_tope_es_valido(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        t = _tarjeta(hijo, "SB-V2", 3000, limite=12000)
        _vender(cliente, usuario_cajero, producto, t, 5)  # 15.000 -> saldo -12.000
        t.refresh_from_db()
        assert t.saldo_actual == Decimal("-12000")

    def test_superar_el_tope_rechaza_la_venta_completa(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        from apps.ventas.models import Venta
        t = _tarjeta(hijo, "SB-V3", 3000, limite=12000)
        with pytest.raises(ValidationError, match="sobregiro autorizado"):
            _vender(cliente, usuario_cajero, producto, t, 6)  # 18.000 -> saldo -15.000
        t.refresh_from_db()
        assert t.saldo_actual == Decimal("3000")
        assert not Venta.objects.filter(tarjeta=t).exists()

    def test_el_error_informa_el_tope_y_el_saldo(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        t = _tarjeta(hijo, "SB-V4", 0, limite=6000)
        with pytest.raises(ValidationError) as exc:
            _vender(cliente, usuario_cajero, producto, t, 3)  # 9.000
        detalle = exc.value.detail
        assert str(detalle["limite_credito"]) == "6000"
        assert str(detalle["saldo_actual"]) == "0"

    def test_sin_tope_deja_pasar_cualquier_monto(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        t = _tarjeta(hijo, "SB-V5", 0, limite=0)
        _vender(cliente, usuario_cajero, producto, t, 40)  # 120.000
        t.refresh_from_db()
        assert t.saldo_actual == Decimal("-120000")

    def test_prepago_mantiene_el_mensaje_de_saldo_insuficiente(
        self, cliente, usuario_cajero, producto, stock_producto, hijo,
    ):
        t = _tarjeta(hijo, "SB-V6", 1000, permite=False)
        with pytest.raises(ValidationError, match="Saldo insuficiente"):
            _vender(cliente, usuario_cajero, producto, t, 1)
