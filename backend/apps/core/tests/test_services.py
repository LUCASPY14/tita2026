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


@pytest.mark.django_db
class TestAjustarSaldo:

    def test_ajuste_positivo_suma(self, tarjeta_activa, usuario_admin):
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        mov = TarjetaService.ajustar_saldo(
            tarjeta=tarjeta_activa, monto=Decimal("5000"),
            motivo="Corrección por reclamo de padre", usuario=usuario_admin,
        )

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("15000")
        assert mov.tipo == MovimientoTarjeta.Tipo.AJUSTE
        assert mov.saldo_anterior == Decimal("10000")
        assert mov.saldo_resultante == Decimal("15000")
        assert usuario_admin.email in mov.descripcion

    def test_ajuste_negativo_resta(self, tarjeta_activa, usuario_admin):
        from apps.core.services import TarjetaService

        TarjetaService.ajustar_saldo(
            tarjeta=tarjeta_activa, monto=Decimal("-3000"),
            motivo="Descuento aplicado dos veces", usuario=usuario_admin,
        )

        tarjeta_activa.refresh_from_db()
        assert tarjeta_activa.saldo_actual == Decimal("7000")

    def test_ajuste_funciona_en_tarjeta_bloqueada(self, tarjeta_bloqueada, usuario_admin):
        """A diferencia de cargar_saldo, el ajuste no exige tarjeta ACTIVA."""
        from apps.core.services import TarjetaService
        from apps.core.models import MovimientoTarjeta

        # El trigger de la base recalcula saldo_actual sumando los movimientos
        # reales de la tarjeta — el saldo_actual=5000 del fixture (seteado a
        # mano, sin movimiento) no sobrevive al primer movimiento real, así
        # que lo establecemos acá de forma consistente antes de ajustar.
        MovimientoTarjeta.objects.create(
            tarjeta=tarjeta_bloqueada, tipo=MovimientoTarjeta.Tipo.AJUSTE, monto=Decimal("5000"),
        )
        tarjeta_bloqueada.refresh_from_db()
        assert tarjeta_bloqueada.saldo_actual == Decimal("5000")

        TarjetaService.ajustar_saldo(
            tarjeta=tarjeta_bloqueada, monto=Decimal("1000"),
            motivo="Corrección de saldo previo al bloqueo", usuario=usuario_admin,
        )

        tarjeta_bloqueada.refresh_from_db()
        assert tarjeta_bloqueada.saldo_actual == Decimal("6000")

    def test_ajuste_monto_cero_falla(self, tarjeta_activa, usuario_admin):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="no puede ser cero"):
            TarjetaService.ajustar_saldo(
                tarjeta=tarjeta_activa, monto=Decimal("0"),
                motivo="motivo", usuario=usuario_admin,
            )

    def test_ajuste_sin_motivo_falla(self, tarjeta_activa, usuario_admin):
        from apps.core.services import TarjetaService

        with pytest.raises(ValidationError, match="motivo"):
            TarjetaService.ajustar_saldo(
                tarjeta=tarjeta_activa, monto=Decimal("1000"),
                motivo="   ", usuario=usuario_admin,
            )
