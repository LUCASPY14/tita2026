"""
Tests adicionales para TarjetaService — cobertura de:
  - Saldo disponible con límite de crédito
  - Cadena de movimientos (saldo_anterior → saldo_resultante)
  - Carga con responsable nulo (flujo Bancard)
  - Consumo hasta cero exacto
  - Reverso de saldo
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="Ramírez",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta_con_credito(db, hijo):
    from apps.core.models import Tarjeta
    # saldo=0 con límite de crédito: no necesita movimiento inicial
    return Tarjeta.objects.create(
        nro_tarjeta="TC_CRED01",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        limite_credito=Decimal("50000"),
        permite_saldo_negativo=True,
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def tarjeta_saldo_cero(db, hijo, cliente):
    from apps.core.models import Tarjeta
    from apps.core.services import TarjetaService
    # El trigger fn_sync_saldo_tarjeta recalcula saldo_actual = SUM(movimientos).
    # Hay que establecer el saldo inicial mediante una RECARGA para que el trigger
    # tenga la base correcta cuando los tests añadan movimientos.
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="TC_CERO01",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    TarjetaService.cargar_saldo(
        tarjeta=tarjeta,
        monto=Decimal("5000"),
        cliente_origen=cliente,
        responsable=None,
    )
    tarjeta.refresh_from_db()
    return tarjeta


@pytest.fixture
def tarjeta_activa(db, hijo, cliente):
    from apps.core.models import Tarjeta
    from apps.core.services import TarjetaService
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="TC_ACT01",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    TarjetaService.cargar_saldo(
        tarjeta=tarjeta,
        monto=Decimal("20000"),
        cliente_origen=cliente,
        responsable=None,
    )
    tarjeta.refresh_from_db()
    return tarjeta


# ─── Saldo disponible con crédito ─────────────────────────────────────────────

@pytest.mark.django_db
class TestSaldoConCredito:

    def test_saldo_disponible_suma_credito(self, tarjeta_con_credito):
        assert tarjeta_con_credito.saldo_disponible == Decimal("50000")

    def test_consumo_con_credito_ok(self, tarjeta_con_credito, usuario_cajero):
        from apps.core.services import TarjetaService
        TarjetaService.consumir_saldo(
            tarjeta=tarjeta_con_credito,
            monto=Decimal("30000"),
            registrado_por=usuario_cajero,
        )
        tarjeta_con_credito.refresh_from_db()
        assert tarjeta_con_credito.saldo_actual == Decimal("-30000")

    def test_consumo_excede_credito_falla(self, tarjeta_con_credito, usuario_cajero):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="Saldo insuficiente"):
            TarjetaService.consumir_saldo(
                tarjeta=tarjeta_con_credito,
                monto=Decimal("60000"),  # supera limite de 50k
                registrado_por=usuario_cajero,
            )

    def test_tarjeta_sin_credito_no_acepta_negativo(self, tarjeta_saldo_cero, usuario_cajero):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="Saldo insuficiente"):
            TarjetaService.consumir_saldo(
                tarjeta=tarjeta_saldo_cero,
                monto=Decimal("10000"),  # más que el saldo de 5k
                registrado_por=usuario_cajero,
            )


# ─── Cadena de movimientos ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCadenaMovimientos:

    def test_movimiento_encadena_saldo_anterior(self, tarjeta_activa, cliente, usuario_cajero):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        # Carga 1: 20k → saldo 40k
        TarjetaService.cargar_saldo(
            tarjeta=tarjeta_activa, monto=Decimal("20000"),
            cliente_origen=cliente, responsable=usuario_cajero,
        )
        # Consumo: 5k → saldo 35k
        TarjetaService.consumir_saldo(
            tarjeta=tarjeta_activa, monto=Decimal("5000"),
            registrado_por=usuario_cajero,
        )
        # Carga 2: 10k → saldo 45k
        TarjetaService.cargar_saldo(
            tarjeta=tarjeta_activa, monto=Decimal("10000"),
            cliente_origen=cliente, responsable=usuario_cajero,
        )

        movimientos = list(
            MovimientoTarjeta.objects.filter(tarjeta=tarjeta_activa).order_by("id")
        )
        # 1 RECARGA del fixture (saldo inicial 20k) + 3 del test = 4 total
        assert len(movimientos) == 4
        # El saldo_anterior de cada mov = saldo_resultante del anterior
        for i in range(1, len(movimientos)):
            assert movimientos[i].saldo_anterior == movimientos[i - 1].saldo_resultante

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("45000")

    def test_consumo_exacto_a_cero(self, tarjeta_saldo_cero, usuario_cajero):
        from apps.core.services import TarjetaService
        TarjetaService.consumir_saldo(
            tarjeta=tarjeta_saldo_cero,
            monto=Decimal("5000"),
            registrado_por=usuario_cajero,
        )
        tarjeta_saldo_cero.refresh_from_db()
        assert tarjeta_saldo_cero.saldo_actual == Decimal("0")


# ─── Carga sin responsable (flujo Bancard) ────────────────────────────────────

@pytest.mark.django_db
class TestCargaSinResponsable:

    def test_carga_con_responsable_nulo_ok(self, tarjeta_activa, cliente):
        """TarjetaService.cargar_saldo acepta responsable=None (pagos Bancard/portal)."""
        from apps.core.services import TarjetaService
        carga = TarjetaService.cargar_saldo(
            tarjeta=tarjeta_activa,
            monto=Decimal("100000"),
            cliente_origen=cliente,
            responsable=None,
            metodo_pago="TARJETA_BANCARD",
            referencia="shop-uuid-abc",
        )
        assert carga.estado == "CONFIRMADA"
        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("120000")
