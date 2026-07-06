"""Tests para apps.compras.models — propiedades, __str__, save() de CuentaCorrienteProveedor."""
import pytest
from decimal import Decimal


@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(ruc="80000001-0", razon_social="Dist. Test S.A.")


@pytest.fixture
def compra_contado(db, proveedor, usuario_cajero):
    from apps.compras.models import Compra
    return Compra.objects.create(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago=Compra.TipoPago.CONTADO,
        monto_total=Decimal("500000"),
        estado_pago=Compra.EstadoPago.PAGADO,
        estado_entrega=Compra.EstadoEntrega.RECIBIDA,
    )


@pytest.fixture
def compra_credito(db, proveedor, usuario_cajero):
    from apps.compras.models import Compra
    return Compra.objects.create(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago=Compra.TipoPago.CREDITO,
        monto_total=Decimal("500000"),
        estado_pago=Compra.EstadoPago.PENDIENTE,
        estado_entrega=Compra.EstadoEntrega.PENDIENTE,
    )


@pytest.fixture
def pago_proveedor(db, proveedor, usuario_cajero, medio_pago_efectivo):
    from apps.compras.models import PagoProveedor
    return PagoProveedor.objects.create(
        proveedor=proveedor,
        monto_total=Decimal("200000"),
        medio_pago=medio_pago_efectivo,
        creado_por=usuario_cajero,
    )


@pytest.fixture
def aplicacion_pago(db, pago_proveedor, compra_credito):
    from apps.compras.models import AplicacionPagoCompra
    return AplicacionPagoCompra.objects.create(
        pago=pago_proveedor,
        compra=compra_credito,
        monto_aplicado=Decimal("200000"),
    )


@pytest.fixture
def nota_credito(db, proveedor, usuario_cajero):
    from apps.compras.models import NotaCreditoProveedor
    return NotaCreditoProveedor.objects.create(
        proveedor=proveedor,
        monto_total=Decimal("50000"),
        creado_por=usuario_cajero,
    )


@pytest.fixture
def detalle_nc(db, nota_credito, producto):
    from apps.compras.models import DetalleNotaCreditoProveedor
    return DetalleNotaCreditoProveedor.objects.create(
        nota_credito=nota_credito,
        producto=producto,
        cantidad=Decimal("2"),
        precio_unitario=Decimal("25000"),
        subtotal=Decimal("50000"),
    )


@pytest.fixture
def detalle_compra(db, compra_contado, producto):
    from apps.compras.models import DetalleCompra
    return DetalleCompra.objects.create(
        compra=compra_contado,
        producto=producto,
        cantidad=Decimal("10"),
        costo_unitario=Decimal("50000"),
        subtotal=Decimal("500000"),
    )


# ── Proveedor ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProveedor:
    def test_str(self, proveedor):
        assert str(proveedor) == "Dist. Test S.A."

    def test_saldo_sin_movimientos(self, proveedor):
        assert proveedor.saldo_cuenta_corriente == Decimal("0")

    def test_saldo_con_movimiento(self, proveedor, usuario_cajero):
        from apps.compras.models import CuentaCorrienteProveedor
        CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
            monto=Decimal("300000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("300000"),
            creado_por=usuario_cajero,
        )
        assert proveedor.saldo_cuenta_corriente == Decimal("300000")


# ── CuentaCorrienteProveedor ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestCuentaCorrienteProveedor:
    def test_save_debito_calcula_saldo(self, proveedor, usuario_cajero):
        from apps.compras.models import CuentaCorrienteProveedor
        cc = CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
            monto=Decimal("100000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        assert cc.saldo_anterior == Decimal("0")
        assert cc.saldo_resultante == Decimal("100000")

    def test_save_credito_resta_saldo(self, proveedor, usuario_cajero):
        from apps.compras.models import CuentaCorrienteProveedor
        CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
            monto=Decimal("100000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        pago = CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.CREDITO,
            monto=Decimal("40000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        assert pago.saldo_anterior == Decimal("100000")
        assert pago.saldo_resultante == Decimal("60000")

    def test_str(self, proveedor, usuario_cajero):
        from apps.compras.models import CuentaCorrienteProveedor
        cc = CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
            monto=Decimal("100000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        assert "Dist. Test S.A." in str(cc)


# ── Compra ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompra:
    def test_str(self, compra_contado):
        assert "Dist. Test S.A." in str(compra_contado)

    # CONTADO: saldo siempre 0 (pagado al momento de la compra)
    def test_contado_total_pagado_es_monto_total(self, compra_contado):
        assert compra_contado.total_pagado == Decimal("500000")

    def test_contado_saldo_pendiente_es_cero(self, compra_contado):
        assert compra_contado.saldo_pendiente == Decimal("0")

    # CREDITO: saldo se calcula en base a aplicaciones de pago
    def test_credito_total_pagado_sin_pagos(self, compra_credito):
        assert compra_credito.total_pagado == Decimal("0")

    def test_credito_total_pagado_con_aplicacion(self, compra_credito, aplicacion_pago):
        compra_credito.refresh_from_db()
        assert compra_credito.total_pagado == Decimal("200000")

    def test_credito_saldo_pendiente(self, compra_credito, aplicacion_pago):
        compra_credito.refresh_from_db()
        assert compra_credito.saldo_pendiente == Decimal("300000")

    def test_credito_total_pagado_usa_cached_si_existe(self, compra_credito):
        compra_credito._total_pagado = Decimal("999")
        assert compra_credito.total_pagado == Decimal("999")


# ── Otros modelos ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOtrosStr:
    def test_detalle_compra_str(self, detalle_compra):
        s = str(detalle_compra)
        assert "Agua mineral" in s or "10" in s

    def test_pago_proveedor_str(self, pago_proveedor):
        assert "Dist. Test S.A." in str(pago_proveedor)

    def test_aplicacion_pago_str(self, aplicacion_pago):
        assert "200" in str(aplicacion_pago)

    def test_nota_credito_str(self, nota_credito):
        assert "Dist. Test S.A." in str(nota_credito)

    def test_detalle_nc_str(self, detalle_nc):
        s = str(detalle_nc)
        assert "Agua mineral" in s or "NC" in s
