"""
Tests para core — TarjetaService (cargar_saldo).
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Lucas",
        apellido="García",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta_activa(db, hijo, cliente):
    from apps.core.models import Tarjeta
    from apps.core.services import TarjetaService
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="T001",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        limite_credito=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    TarjetaService.cargar_saldo(
        tarjeta=tarjeta,
        monto=Decimal("10000"),
        cliente_origen=cliente,
        responsable=None,
    )
    tarjeta.refresh_from_db()
    return tarjeta


@pytest.fixture
def tarjeta_bloqueada(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="T002",
        hijo=hijo,
        saldo_actual=Decimal("5000"),
        limite_credito=Decimal("0"),
        estado=Tarjeta.Estado.BLOQUEADA,
    )


@pytest.mark.django_db
class TestCargarSaldo:

    def test_carga_saldo_ok(self, tarjeta_activa, cliente, usuario_cajero):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        carga = TarjetaService.cargar_saldo(
            tarjeta=tarjeta_activa,
            monto=Decimal("5000"),
            cliente_origen=cliente,
            responsable=usuario_cajero,
        )

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("15000")
        assert MovimientoTarjeta.objects.filter(
            tarjeta=tarjeta_activa, tipo=MovimientoTarjeta.Tipo.RECARGA
        ).exists()
        assert carga.estado == "CONFIRMADA"

    def test_carga_tarjeta_bloqueada_falla(self, tarjeta_bloqueada, cliente, usuario_cajero):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="no esta activa"):
            TarjetaService.cargar_saldo(
                tarjeta=tarjeta_bloqueada,
                monto=Decimal("5000"),
                cliente_origen=cliente,
                responsable=usuario_cajero,
            )

    def test_carga_monto_cero_falla(self, tarjeta_activa, cliente, usuario_cajero):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="mayor a 0"):
            TarjetaService.cargar_saldo(
                tarjeta=tarjeta_activa,
                monto=Decimal("0"),
                cliente_origen=cliente,
                responsable=usuario_cajero,
            )

    def test_carga_con_cierre_caja_crea_movimiento_caja(
        self, tarjeta_activa, cliente, usuario_cajero
    ):
        """Cuando se pasa cierre_caja, se crea un MovimientoCaja INGRESO."""
        from apps.core.services import TarjetaService
        from apps.contabilidad.models import Caja, CierreCaja, MovimientoCaja

        caja = Caja.objects.create(nombre="Caja Test")
        cierre = CierreCaja.objects.create(
            caja=caja,
            empleado=usuario_cajero,
            estado=CierreCaja.Estado.ABIERTO,
        )

        TarjetaService.cargar_saldo(
            tarjeta=tarjeta_activa,
            monto=Decimal("3000"),
            cliente_origen=cliente,
            responsable=usuario_cajero,
            cierre_caja=cierre,
        )

        assert MovimientoCaja.objects.filter(
            cierre=cierre,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("3000"),
        ).exists()

    def test_whatsapp_exception_no_interrumpe_carga(
        self, tarjeta_activa, cliente, usuario_cajero
    ):
        """Si whatsapp_cliente lanza excepción, la carga igual se completa."""
        from unittest.mock import patch
        from apps.core.services import TarjetaService

        with patch(
            "apps.notificaciones.services.whatsapp_cliente",
            side_effect=RuntimeError("WAHA caído"),
        ):
            carga = TarjetaService.cargar_saldo(
                tarjeta=tarjeta_activa,
                monto=Decimal("2000"),
                cliente_origen=cliente,
                responsable=usuario_cajero,
            )

        assert carga.estado == "CONFIRMADA"
        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("12000")
