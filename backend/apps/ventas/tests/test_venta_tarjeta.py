"""
Tests para ventas realizadas con tarjeta prepago del estudiante.
Cubre: descuento de saldo en tarjeta, venta con saldo insuficiente,
venta con tarjeta bloqueada, reverso de saldo al anular.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Sofía",
        apellido="López",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta_activa(db, hijo, cliente):
    from apps.core.models import Tarjeta
    from apps.core.services import TarjetaService
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="VENTA_T01",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    TarjetaService.cargar_saldo(
        tarjeta=tarjeta,
        monto=Decimal("15000"),
        cliente_origen=cliente,
        responsable=None,
    )
    tarjeta.refresh_from_db()
    return tarjeta


@pytest.fixture
def tarjeta_bloqueada(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="VENTA_T02",
        hijo=hijo,
        saldo_actual=Decimal("10000"),
        estado=Tarjeta.Estado.BLOQUEADA,
    )


@pytest.fixture
def tarjeta_vacia(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="VENTA_T03",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )


def _registrar_venta_tarjeta(cliente, cajero, producto, stock_producto, tarjeta, cantidad=1, precio=3000):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=cajero,
        tipo="CONTADO",
        tarjeta=tarjeta,
        items=[{
            "producto": producto,
            "cantidad": Decimal(str(cantidad)),
            "precio_unitario": Decimal(str(precio)),
        }],
    )


@pytest.mark.django_db
class TestVentaConTarjeta:

    def test_venta_tarjeta_descuenta_saldo(
        self, cliente, usuario_cajero, producto, stock_producto, tarjeta_activa
    ):
        _registrar_venta_tarjeta(cliente, usuario_cajero, producto, stock_producto, tarjeta_activa)
        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("12000")

    def test_venta_tarjeta_crea_movimiento_consumo(
        self, cliente, usuario_cajero, producto, stock_producto, tarjeta_activa
    ):
        from apps.core.models import MovimientoTarjeta
        _registrar_venta_tarjeta(cliente, usuario_cajero, producto, stock_producto, tarjeta_activa)
        mov = MovimientoTarjeta.objects.filter(
            tarjeta=tarjeta_activa, tipo=MovimientoTarjeta.Tipo.CONSUMO
        ).first()
        assert mov is not None
        assert mov.monto == Decimal("3000")

    def test_venta_tarjeta_saldo_insuficiente_falla(
        self, cliente, usuario_cajero, producto, stock_producto, tarjeta_vacia
    ):
        with pytest.raises(ValidationError):
            _registrar_venta_tarjeta(
                cliente, usuario_cajero, producto, stock_producto, tarjeta_vacia
            )

    def test_venta_tarjeta_bloqueada_falla(
        self, cliente, usuario_cajero, producto, stock_producto, tarjeta_bloqueada
    ):
        with pytest.raises(ValidationError):
            _registrar_venta_tarjeta(
                cliente, usuario_cajero, producto, stock_producto, tarjeta_bloqueada
            )

    def test_anular_venta_tarjeta_revierte_saldo(
        self, cliente, usuario_cajero, usuario_admin, producto, stock_producto, tarjeta_activa
    ):
        from apps.ventas.services import VentaService
        from apps.core.models import MovimientoTarjeta
        saldo_antes = tarjeta_activa.saldo_actual

        venta = _registrar_venta_tarjeta(
            cliente, usuario_cajero, producto, stock_producto, tarjeta_activa
        )
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == saldo_antes

        # Debe existir un REVERSO
        reverso = MovimientoTarjeta.objects.filter(
            tarjeta=tarjeta_activa, tipo=MovimientoTarjeta.Tipo.REVERSO
        ).first()
        assert reverso is not None
        assert reverso.monto == Decimal("3000")

    def test_venta_multiples_productos_descuenta_total(
        self, cliente, usuario_cajero, producto, stock_producto, tarjeta_activa
    ):
        from apps.ventas.services import VentaService
        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            tarjeta=tarjeta_activa,
            items=[
                {"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")},
                {"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")},
            ],
        )
        assert venta.monto_total == Decimal("9000")
        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("6000")
