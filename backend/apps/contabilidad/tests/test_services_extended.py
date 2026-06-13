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
