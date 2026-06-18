"""
Tests para core — TarjetaService (cargar_saldo, consumir_saldo).
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


@pytest.mark.django_db
class TestConsumirSaldo:

    def test_consumo_ok(self, tarjeta_activa, usuario_cajero):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        TarjetaService.consumir_saldo(
            tarjeta=tarjeta_activa,
            monto=Decimal("3000"),
            registrado_por=usuario_cajero,
            detalle="Almuerzo",
        )

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("7000")
        assert MovimientoTarjeta.objects.filter(
            tarjeta=tarjeta_activa, tipo=MovimientoTarjeta.Tipo.CONSUMO
        ).exists()

    def test_consumo_saldo_insuficiente_falla(self, tarjeta_activa, usuario_cajero):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="Saldo insuficiente"):
            TarjetaService.consumir_saldo(
                tarjeta=tarjeta_activa,
                monto=Decimal("20000"),
                registrado_por=usuario_cajero,
            )

    def test_consumo_tarjeta_bloqueada_falla(self, tarjeta_bloqueada, usuario_cajero):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="no esta activa"):
            TarjetaService.consumir_saldo(
                tarjeta=tarjeta_bloqueada,
                monto=Decimal("1000"),
                registrado_por=usuario_cajero,
            )
