import pytest
from decimal import Decimal


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Maria",
        apellido="Pérez",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="TAR001",
        hijo=hijo,
        saldo_actual=Decimal("10000"),
    )


@pytest.fixture
def carga_saldo(db, tarjeta, cliente, usuario_cajero):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta,
        cliente_origen=cliente,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.CONFIRMADA,
        responsable=usuario_cajero,
    )


@pytest.fixture
def cuenta_mensual(db, hijo):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo,
        anio=2026,
        mes=5,
        cantidad_almuerzos=20,
        monto_total=Decimal("120000"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
    )


@pytest.fixture
def pago_almuerzo(db, cuenta_mensual, usuario_cajero):
    from apps.almuerzos.models import PagoCuentaAlmuerzo
    return PagoCuentaAlmuerzo.objects.create(
        cuenta=cuenta_mensual,
        monto=Decimal("120000"),
        medio_pago="EFECTIVO",
        registrado_por=usuario_cajero,
    )


@pytest.fixture
def recarga_almuerzo(db, hijo, usuario_cajero):
    from apps.almuerzos.models import RecargaSaldoAlmuerzo
    return RecargaSaldoAlmuerzo.objects.create(
        hijo=hijo,
        monto_cargado=Decimal("60000"),
        metodo_pago="EFECTIVO",
        estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
        registrado_por=usuario_cajero,
    )
