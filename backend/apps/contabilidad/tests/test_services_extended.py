"""
Tests extendidos de servicios de contabilidad.
Cubre los caminos edge de CajaService y FacturacionService.emitir_para_origen.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


@pytest.fixture
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Svc Ext", activo=True)


@pytest.fixture
def cierre_abierto(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("50000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def cierre_cerrado(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    from django.utils import timezone
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("50000"),
        estado=CierreCaja.Estado.CERRADO,
        fecha_cierre=timezone.now(),
    )


# ── CajaService.abrir_caja ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAbrirCaja:

    def test_caja_ya_abierta_falla(self, caja, cierre_abierto, usuario_cajero):
        from apps.contabilidad.services import CajaService

        with pytest.raises(ValidationError, match="ya tiene un cierre abierto"):
            CajaService.abrir_caja(
                caja=caja,
                empleado=usuario_cajero,
                monto_inicial=Decimal("10000"),
            )


# ── CajaService.cerrar_caja ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestCerrarCaja:

    def test_cerrar_caja_ya_cerrada_falla(self, cierre_cerrado):
        from apps.contabilidad.services import CajaService

        with pytest.raises(ValidationError, match="no esta abierta"):
            CajaService.cerrar_caja(
                cierre=cierre_cerrado,
                monto_contado=Decimal("50000"),
            )


# ── CajaService.registrar_movimiento ─────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarMovimientoSvc:

    def test_monto_cero_falla(self, cierre_abierto):
        from apps.contabilidad.services import CajaService

        with pytest.raises(ValidationError, match="mayor a 0"):
            CajaService.registrar_movimiento(
                cierre=cierre_abierto,
                tipo="INGRESO",
                monto=Decimal("0"),
                medio_pago=None,
            )

    def test_tipo_invalido_falla(self, cierre_abierto):
        from apps.contabilidad.services import CajaService

        with pytest.raises(ValidationError, match="[Tt]ipo invalido"):
            CajaService.registrar_movimiento(
                cierre=cierre_abierto,
                tipo="INVALIDO",
                monto=Decimal("1000"),
                medio_pago=None,
            )

    def test_caja_cerrada_falla(self, cierre_cerrado):
        from apps.contabilidad.services import CajaService

        with pytest.raises(ValidationError, match="no esta abierta"):
            CajaService.registrar_movimiento(
                cierre=cierre_cerrado,
                tipo="INGRESO",
                monto=Decimal("1000"),
                medio_pago=None,
            )


# ── FacturacionService.emitir_factura — IntegrityError path ──────────────────

@pytest.mark.django_db
class TestEmitirFacturaIntegrityError:

    def test_integrity_error_convierte_a_validation_error(self, cliente):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        with patch.object(
            Factura.objects, "create",
            side_effect=IntegrityError("duplicate key"),
        ):
            with patch.object(
                Factura.objects, "filter",
                return_value=type("QS", (), {"exists": lambda s: False})(),
            ):
                with pytest.raises(ValidationError, match="ya fue registrada"):
                    FacturacionService.emitir_factura(
                        cliente=cliente,
                        nro_factura="001-001-9999999",
                        monto_total=Decimal("10000"),
                    )


# ── FacturacionService.emitir_para_origen — CargaSaldo sin cliente ────────────

@pytest.mark.django_db
class TestEmitirParaOrigenSinCliente:

    def test_carga_sin_cliente_origen_pero_con_hijo_usa_responsable(
        self, tarjeta, cliente
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.core.models import CargaSaldo

        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta,
            cliente_origen=None,
            monto_cargado=Decimal("20000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
        )

        factura = FacturacionService.emitir_para_origen(
            tipo="CARGA_SALDO",
            origen_id=carga.pk,
            nro_factura="001-001-8888881",
        )
        assert factura.monto_total == Decimal("20000")

    def test_carga_sin_cliente_ni_tarjeta_falla(self, db):
        from apps.contabilidad.services import FacturacionService
        from apps.core.models import CargaSaldo

        carga = CargaSaldo.objects.create(
            tarjeta=None,
            cliente_origen=None,
            monto_cargado=Decimal("10000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
        )

        with pytest.raises(ValidationError, match="no tiene cliente"):
            FacturacionService.emitir_para_origen(
                tipo="CARGA_SALDO",
                origen_id=carga.pk,
                nro_factura="001-001-8888882",
            )


# ── FacturacionService.emitir_para_origen — rama VENTA ───────────────────────

@pytest.mark.django_db
class TestEmitirParaOrigenVenta:

    def _crear_venta(self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto):
        from apps.ventas.services import VentaService
        from apps.ventas.models import Venta
        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{
                "producto": producto,
                "cantidad": Decimal("1"),
                "precio_unitario": Decimal("5000"),
            }],
            genera_factura_legal=True,
        )
        return venta

    def test_emitir_para_venta_ok(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        venta = self._crear_venta(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        factura = FacturacionService.emitir_para_origen(
            tipo="VENTA",
            origen_id=venta.pk,
            nro_factura="001-001-7001001",
        )
        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == venta.monto_total
        venta.refresh_from_db()
        assert venta.factura_id == factura.pk
        assert venta.nro_factura == "001-001-7001001"

    def test_venta_anulada_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, usuario_admin
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.ventas.services import VentaService

        venta = self._crear_venta(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        with pytest.raises(ValidationError, match="anulada"):
            FacturacionService.emitir_para_origen(
                tipo="VENTA",
                origen_id=venta.pk,
                nro_factura="001-001-7001002",
            )

    def test_venta_sin_factura_legal_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.ventas.services import VentaService

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{
                "producto": producto,
                "cantidad": Decimal("1"),
                "precio_unitario": Decimal("5000"),
            }],
            genera_factura_legal=False,
        )
        with pytest.raises(ValidationError, match="factura legal"):
            FacturacionService.emitir_para_origen(
                tipo="VENTA",
                origen_id=venta.pk,
                nro_factura="001-001-7001003",
            )

    def test_venta_ya_facturada_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService

        venta = self._crear_venta(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        FacturacionService.emitir_para_origen(
            tipo="VENTA",
            origen_id=venta.pk,
            nro_factura="001-001-7001004",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_para_origen(
                tipo="VENTA",
                origen_id=venta.pk,
                nro_factura="001-001-7001005",
            )


# ── FacturacionService.emitir_para_origen — rama PAGO_CREDITO ────────────────

@pytest.mark.django_db
class TestEmitirParaOrigenPagoCredito:

    def _crear_pago_cc(self, cliente, usuario_cajero, genera_factura=True):
        from apps.clientes.models import CuentaCorrienteCliente
        from decimal import Decimal
        return CuentaCorrienteCliente.objects.create(
            cliente=cliente,
            tipo=CuentaCorrienteCliente.Tipo.CREDITO,
            monto=Decimal("20000"),
            saldo_anterior=Decimal("20000"),
            saldo_resultante=Decimal("0"),
            descripcion="Pago test",
            genera_factura_legal=genera_factura,
            creado_por=usuario_cajero,
        )

    def test_emitir_para_pago_credito_ok(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        pago_cc = self._crear_pago_cc(cliente, usuario_cajero)
        factura = FacturacionService.emitir_para_origen(
            tipo="PAGO_CREDITO",
            origen_id=pago_cc.pk,
            nro_factura="001-001-6001001",
        )
        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == Decimal("20000")
        pago_cc.refresh_from_db()
        assert pago_cc.factura_id == factura.pk

    def test_pago_credito_sin_factura_legal_falla(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService

        pago_cc = self._crear_pago_cc(cliente, usuario_cajero, genera_factura=False)
        with pytest.raises(ValidationError, match="factura legal"):
            FacturacionService.emitir_para_origen(
                tipo="PAGO_CREDITO",
                origen_id=pago_cc.pk,
                nro_factura="001-001-6001002",
            )

    def test_pago_credito_ya_facturado_falla(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService

        pago_cc = self._crear_pago_cc(cliente, usuario_cajero)
        FacturacionService.emitir_para_origen(
            tipo="PAGO_CREDITO",
            origen_id=pago_cc.pk,
            nro_factura="001-001-6001003",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_para_origen(
                tipo="PAGO_CREDITO",
                origen_id=pago_cc.pk,
                nro_factura="001-001-6001004",
            )
