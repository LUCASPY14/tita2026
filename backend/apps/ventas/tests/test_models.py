"""
Tests de modelos de ventas.
Cubre: __str__, @property, clean(), anular().
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError


@pytest.fixture
def venta_credito(db, cliente, usuario_cajero):
    """Venta directa sin auto-pago: total_pagado == 0."""
    from apps.ventas.models import Venta
    return Venta.objects.create(
        cliente=cliente,
        cajero=usuario_cajero,
        tipo="CREDITO",
        estado_pago=Venta.EstadoPago.PENDIENTE,
        monto_total=Decimal("5000"),
    )


@pytest.fixture
def venta_simple(db, cliente, usuario_cajero, producto, stock_producto, medio_pago_efectivo):
    from apps.contabilidad.models import Caja, CierreCaja
    from apps.ventas.services import VentaService

    caja = Caja.objects.create(nombre="Caja Venta Simple", activo=True)
    cierre = CierreCaja.objects.create(
        caja=caja, empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=usuario_cajero,
        tipo="CONTADO",
        medio_pago=medio_pago_efectivo,
        items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        cierre_caja=cierre,
    )


@pytest.fixture
def pago(db, cliente, venta_simple, medio_pago_efectivo, usuario_cajero):
    from apps.ventas.models import PagoVenta
    return PagoVenta.objects.create(
        cliente=cliente,
        venta=venta_simple,
        monto=Decimal("6000"),
        medio_pago=medio_pago_efectivo,
        cajero=usuario_cajero,
        estado=PagoVenta.Estado.PENDIENTE,
    )


# ── Venta __str__ y properties ────────────────────────────────────────────────

@pytest.mark.django_db
class TestVentaModel:

    def test_str(self, venta_simple):
        s = str(venta_simple)
        assert "Venta" in s

    def test_total_pagado_sin_pagos(self, venta_credito):
        assert venta_credito.total_pagado == Decimal("0")

    def test_total_pagado_con_pago(self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente):
        from apps.ventas.models import PagoVenta, AplicacionPago
        p = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito,
            monto=Decimal("5000"), medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
        )
        AplicacionPago.objects.create(pago=p, venta=venta_credito, monto_aplicado=Decimal("5000"))
        assert venta_credito.total_pagado == Decimal("5000")

    def test_esta_pagada_false(self, venta_credito):
        assert venta_credito.esta_pagada is False

    def test_esta_pagada_true(self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente):
        from apps.ventas.models import PagoVenta, AplicacionPago
        p = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito,
            monto=Decimal("5000"), medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
        )
        AplicacionPago.objects.create(pago=p, venta=venta_credito, monto_aplicado=Decimal("5000"))
        assert venta_credito.esta_pagada is True


# ── DetalleVenta __str__ ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDetalleVentaStr:

    def test_str(self, venta_simple):
        detalle = venta_simple.detalles.first()
        s = str(detalle)
        assert "₲" in s or "x" in s


# ── PagoVenta __str__, total_cobrado, anular ──────────────────────────────────

@pytest.mark.django_db
class TestPagoVentaModel:

    def test_str_con_venta(self, pago):
        s = str(pago)
        assert "Pago" in s

    def test_str_sin_venta(self, db, cliente, medio_pago_efectivo, usuario_cajero):
        from apps.ventas.models import PagoVenta
        p = PagoVenta.objects.create(
            cliente=cliente,
            venta=None,
            monto=Decimal("5000"),
            medio_pago=medio_pago_efectivo,
            cajero=usuario_cajero,
        )
        s = str(p)
        assert "cuenta" in s.lower() or "Pago" in s

    def test_total_cobrado(self, pago):
        assert pago.total_cobrado == pago.monto + pago.monto_comision

    def test_anular_pendiente_ok(self, pago, venta_simple):
        pago.anular()
        pago.refresh_from_db()
        from apps.ventas.models import PagoVenta
        assert pago.estado == PagoVenta.Estado.ANULADO

    def test_anular_ya_anulado_falla(self, pago):
        pago.anular()
        with pytest.raises(ValidationError, match="[Aa]nulado"):
            pago.anular()

    def test_anular_conciliado_falla(self, db, cliente, venta_simple, medio_pago_efectivo, usuario_cajero):
        from apps.ventas.models import PagoVenta
        p = PagoVenta.objects.create(
            cliente=cliente,
            venta=venta_simple,
            monto=Decimal("6000"),
            medio_pago=medio_pago_efectivo,
            cajero=usuario_cajero,
            estado=PagoVenta.Estado.CONCILIADO,
        )
        with pytest.raises(ValidationError, match="[Cc]onciliado"):
            p.anular()

    def test_anular_con_aplicaciones_recalcula_pendiente(
        self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente
    ):
        from apps.ventas.models import PagoVenta, AplicacionPago, Venta
        p = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito, monto=Decimal("5000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
            estado=PagoVenta.Estado.PENDIENTE,
        )
        AplicacionPago.objects.create(pago=p, venta=venta_credito, monto_aplicado=Decimal("5000"))
        p.anular()  # removes aplicacion → total_pagado=0 → PENDIENTE
        venta_credito.refresh_from_db()
        assert venta_credito.estado_pago == Venta.EstadoPago.PENDIENTE

    def test_anular_con_aplicaciones_recalcula_pagado(
        self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente
    ):
        from apps.ventas.models import PagoVenta, AplicacionPago, Venta
        p_anular = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito, monto=Decimal("1000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
            estado=PagoVenta.Estado.PENDIENTE,
        )
        p_keep = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito, monto=Decimal("5000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
            estado=PagoVenta.Estado.PENDIENTE,
        )
        AplicacionPago.objects.create(pago=p_anular, venta=venta_credito, monto_aplicado=Decimal("1000"))
        AplicacionPago.objects.create(pago=p_keep, venta=venta_credito, monto_aplicado=Decimal("5000"))
        p_anular.anular()  # removes p_anular aplicacion → total_pagado=5000 >= 5000 → PAGADO
        venta_credito.refresh_from_db()
        assert venta_credito.estado_pago == Venta.EstadoPago.PAGADO

    def test_anular_con_aplicaciones_recalcula_parcial(
        self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente
    ):
        from apps.ventas.models import PagoVenta, AplicacionPago, Venta
        p_anular = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito, monto=Decimal("3000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
            estado=PagoVenta.Estado.PENDIENTE,
        )
        p_keep = PagoVenta.objects.create(
            cliente=cliente, venta=venta_credito, monto=Decimal("1000"),
            medio_pago=medio_pago_efectivo, cajero=usuario_cajero,
            estado=PagoVenta.Estado.PENDIENTE,
        )
        AplicacionPago.objects.create(pago=p_anular, venta=venta_credito, monto_aplicado=Decimal("3000"))
        AplicacionPago.objects.create(pago=p_keep, venta=venta_credito, monto_aplicado=Decimal("1000"))
        p_anular.anular()  # removes p_anular → total_pagado=1000, 0 < 1000 < 5000 → PARCIAL
        venta_credito.refresh_from_db()
        assert venta_credito.estado_pago == Venta.EstadoPago.PARCIAL


# ── AplicacionPago clean ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAplicacionPagoClean:

    def test_str(self, db, pago, venta_simple):
        from apps.ventas.models import AplicacionPago
        ap = AplicacionPago.objects.create(
            pago=pago, venta=venta_simple, monto_aplicado=Decimal("1000")
        )
        assert "₲" in str(ap)

    def test_clean_monto_cero_falla(self, db, pago, venta_simple):
        from apps.ventas.models import AplicacionPago
        ap = AplicacionPago(pago=pago, venta=venta_simple, monto_aplicado=Decimal("0"))
        with pytest.raises(ValidationError):
            ap.clean()

    def test_clean_monto_supera_saldo_venta_falla(self, db, pago, venta_simple):
        from apps.ventas.models import AplicacionPago
        ap = AplicacionPago(
            pago=pago, venta=venta_simple,
            monto_aplicado=Decimal("99999999"),
        )
        with pytest.raises(ValidationError):
            ap.clean()

    def test_clean_monto_supera_saldo_pago_falla(
        self, db, venta_credito, medio_pago_efectivo, usuario_cajero, cliente
    ):
        from apps.ventas.models import AplicacionPago, PagoVenta
        pago_chico = PagoVenta.objects.create(
            cliente=cliente,
            venta=venta_credito,
            monto=Decimal("100"),
            medio_pago=medio_pago_efectivo,
            cajero=usuario_cajero,
        )
        # venta_credito saldo=5000 > 200 (venta check passes), but pago monto=100 < 200
        ap = AplicacionPago(
            pago=pago_chico, venta=venta_credito,
            monto_aplicado=Decimal("200"),
        )
        with pytest.raises(ValidationError, match="[Ss]aldo"):
            ap.clean()


# ── Otros modelos __str__ ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOtrosModelos:

    def test_nota_credito_str(self, db, cliente, usuario_admin):
        from apps.ventas.models import NotaCredito
        nc = NotaCredito.objects.create(
            cliente=cliente,
            nro_nota_credito="NC-001",
            monto_total=Decimal("10000"),
            motivo="Devolución test",
            empleado_autoriza=usuario_admin,
        )
        assert "NC-001" in str(nc)

    def test_detalle_nota_credito_str(self, db, cliente, usuario_admin, producto):
        from apps.ventas.models import NotaCredito, DetalleNotaCredito
        nc = NotaCredito.objects.create(
            cliente=cliente,
            nro_nota_credito="NC-002",
            monto_total=Decimal("5000"),
            motivo="Test",
            empleado_autoriza=usuario_admin,
        )
        d = DetalleNotaCredito.objects.create(
            nota_credito=nc,
            producto=producto,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("5000"),
            subtotal=Decimal("5000"),
        )
        assert "NC" in str(d) or str(producto.pk) in str(d) or "x" in str(d)
