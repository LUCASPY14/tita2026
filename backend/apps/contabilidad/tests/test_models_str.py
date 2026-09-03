"""
Cobertura de __str__ en contabilidad/models.py:
  Caja, CierreCaja, MovimientoCaja, Factura, DatosEmpresa
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
