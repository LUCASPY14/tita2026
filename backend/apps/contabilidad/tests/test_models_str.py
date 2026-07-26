"""
Cobertura de __str__ en contabilidad/models.py:
  Caja, CierreCaja, MovimientoCaja, ConciliacionPago, Factura, DatosEmpresa
"""
import pytest
from decimal import Decimal


@pytest.fixture
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Central", activo=True)


@pytest.fixture
def cierre_caja(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("0"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.mark.django_db
class TestContabilidadModelsStr:

    def test_caja_str(self, caja):
        assert str(caja) == "Caja Central"

    def test_cierre_caja_str(self, cierre_caja):
        s = str(cierre_caja)
        assert "Cierre #" in s
        assert "Caja Central" in s
        assert "Abierto" in s

    def test_movimiento_caja_ingreso_str(self, cierre_caja):
        from apps.contabilidad.models import MovimientoCaja
        m = MovimientoCaja.objects.create(
            cierre=cierre_caja,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("50000"),
            descripcion="Venta efectivo",
        )
        assert str(m).startswith("+₲50,000")
        assert "Venta efectivo" in str(m)

    def test_movimiento_caja_egreso_str(self, cierre_caja):
        from apps.contabilidad.models import MovimientoCaja
        m = MovimientoCaja.objects.create(
            cierre=cierre_caja,
            tipo=MovimientoCaja.Tipo.EGRESO,
            monto=Decimal("20000"),
        )
        assert str(m).startswith("-₲20,000")
        # Cuando no hay descripción usa get_tipo_display
        assert "Egreso" in str(m)

    def test_conciliacion_pago_str(self, db, cliente, usuario_cajero):
        """ConciliacionPago.__str__ muestra el pk y el id del pago."""
        from apps.ventas.models import Venta, PagoVenta
        from apps.core.models import MedioPago
        from apps.contabilidad.models import ConciliacionPago
        mp = MedioPago.objects.create(descripcion="Transferencia", activo=True)
        v = Venta.objects.create(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo=Venta.Tipo.CONTADO,
            monto_total=Decimal("10000"),
        )
        pago = PagoVenta.objects.create(
            venta=v,
            medio_pago=mp,
            monto=Decimal("10000"),
            cajero=usuario_cajero,
            cliente=cliente,
        )
        conc = ConciliacionPago.objects.create(
            pago_venta=pago,
            estado=ConciliacionPago.Estado.PENDIENTE,
        )
        s = str(conc)
        assert "Conciliación #" in s
        assert f"Pago #{pago.pk}" in s

    def test_factura_str(self, db, cliente):
        from apps.contabilidad.models import Factura
        f = Factura.objects.create(
            nro_factura="001-001-0001234",
            monto_total=Decimal("75000"),
            cliente=cliente,
        )
        assert "001-001-0001234" in str(f)
        assert "₲75,000" in str(f)

    def test_datos_empresa_str(self, db):
        from apps.contabilidad.models import DatosEmpresa
        d = DatosEmpresa.objects.create(
            ruc="80012345-6",
            razon_social="Cantina Tita S.A.",
            activo=True,
        )
        assert str(d) == "Cantina Tita S.A. - RUC 80012345-6"
