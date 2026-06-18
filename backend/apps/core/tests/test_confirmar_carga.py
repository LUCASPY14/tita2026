"""
Tests para TarjetaService.confirmar_carga.
Cubre: carga pendiente confirmada, doble confirmación, tarjeta bloqueada,
y recarga con cierre de caja.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Facundo",
        apellido="García",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta(db, hijo, cliente):
    from apps.core.models import Tarjeta
    from apps.core.services import TarjetaService
    t = Tarjeta.objects.create(
        nro_tarjeta="CC-001",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    TarjetaService.cargar_saldo(
        tarjeta=t, monto=Decimal("20000"),
        cliente_origen=cliente, responsable=None,
    )
    t.refresh_from_db()
    return t


@pytest.fixture
def tarjeta_bloqueada(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="CC-002",
        hijo=hijo,
        saldo_actual=Decimal("5000"),
        estado=Tarjeta.Estado.BLOQUEADA,
    )


@pytest.fixture
def carga_pendiente(db, tarjeta, cliente):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta,
        cliente_origen=cliente,
        monto_cargado=Decimal("30000"),
        metodo_pago="BANCARD",
        estado=CargaSaldo.Estado.PENDIENTE,
    )


@pytest.fixture
def carga_pendiente_bloqueada(db, tarjeta_bloqueada, cliente):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta_bloqueada,
        cliente_origen=cliente,
        monto_cargado=Decimal("10000"),
        metodo_pago="BANCARD",
        estado=CargaSaldo.Estado.PENDIENTE,
    )


@pytest.mark.django_db
class TestConfirmarCarga:

    def test_confirma_y_acredita_saldo(self, tarjeta, carga_pendiente, usuario_cajero):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta, CargaSaldo

        TarjetaService.confirmar_carga(
            carga=carga_pendiente,
            responsable=usuario_cajero,
        )

        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == Decimal("50000")  # 20000 + 30000

        carga_pendiente.refresh_from_db()
        assert carga_pendiente.estado == CargaSaldo.Estado.CONFIRMADA
        assert carga_pendiente.responsable == usuario_cajero
        assert carga_pendiente.fecha_confirmacion is not None

        assert MovimientoTarjeta.objects.filter(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=Decimal("30000"),
        ).exists()

    def test_doble_confirmacion_falla(self, carga_pendiente, usuario_cajero):
        from apps.core.services import TarjetaService

        TarjetaService.confirmar_carga(carga=carga_pendiente, responsable=usuario_cajero)

        carga_pendiente.refresh_from_db()
        with pytest.raises(ValidationError, match="PENDIENTE"):
            TarjetaService.confirmar_carga(carga=carga_pendiente, responsable=usuario_cajero)

    def test_tarjeta_bloqueada_falla(self, carga_pendiente_bloqueada, usuario_cajero):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="activa"):
            TarjetaService.confirmar_carga(
                carga=carga_pendiente_bloqueada,
                responsable=usuario_cajero,
            )

    def test_saldo_anterior_correcto_en_movimiento(self, tarjeta, carga_pendiente, usuario_cajero):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        saldo_antes = tarjeta.saldo_actual
        TarjetaService.confirmar_carga(carga=carga_pendiente, responsable=usuario_cajero)

        # Filtrar por carga específica para no colisionar con el RECARGA del fixture
        mov = MovimientoTarjeta.objects.get(
            tarjeta=tarjeta, tipo=MovimientoTarjeta.Tipo.RECARGA,
            carga=carga_pendiente,
        )
        assert mov.saldo_anterior == saldo_antes
        assert mov.saldo_resultante == saldo_antes + Decimal("30000")

    def test_confirmar_con_cierre_caja_crea_movimiento_caja(
        self, tarjeta, carga_pendiente, usuario_cajero, db
    ):
        from apps.core.services import TarjetaService
        from apps.contabilidad.models import Caja, CierreCaja, MovimientoCaja

        caja = Caja.objects.create(nombre="Caja Test CC", activo=True)
        cierre = CierreCaja.objects.create(
            caja=caja,
            empleado=usuario_cajero,
            monto_inicial=Decimal("0"),
            estado=CierreCaja.Estado.ABIERTO,
        )

        TarjetaService.confirmar_carga(
            carga=carga_pendiente,
            responsable=usuario_cajero,
            cierre_caja=cierre,
        )

        assert MovimientoCaja.objects.filter(
            cierre=cierre,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("30000"),
        ).exists()
