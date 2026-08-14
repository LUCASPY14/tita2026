"""
Tests para AlmuerzoService.registrar_consumo y get_precio_activo.
Cubre: validaciones de tarjeta, fecha futura, primer/segundo registro,
costo en cuenta mensual, límite de crédito mensual.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

# Fecha fija para todos los tests — evita fragilidad en inicio/fin de mes
# y garantiza que "mañana" sea siempre una fecha futura relativa al freeze.
HOY = date(2026, 7, 15)


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="2do grado",
        defaults={"nivel": 2, "orden": 2, "activo": True},
    )
    return g


@pytest.fixture
def hijo_almuerzo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="Almuerzo",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.fixture
def tarjeta_almuerzo(db, hijo_almuerzo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-001",
        hijo=hijo_almuerzo,
        saldo_actual=Decimal("50000"),
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def tarjeta_bloqueada_almuerzo(db, hijo_almuerzo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-002",
        hijo=hijo_almuerzo,
        saldo_actual=Decimal("10000"),
        estado=Tarjeta.Estado.BLOQUEADA,
    )


@pytest.fixture
def precio_almuerzo(db):
    from apps.almuerzos.models import PrecioAlmuerzo
    return PrecioAlmuerzo.objects.create(
        precio_unitario=Decimal("15000"),
        fecha_inicio_vigencia=HOY - timedelta(days=30),
        activo=True,
    )


@pytest.fixture
def plan_sin_limite(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Sin Límite",
        activo=True,
        precio_mensual=Decimal("200000"),
        limite_credito_mensual=None,
    )


@pytest.fixture
def plan_con_limite(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Con Límite",
        activo=True,
        precio_mensual=Decimal("200000"),
        limite_credito_mensual=Decimal("10000"),
    )


@pytest.fixture
def suscripcion_activa(db, hijo_almuerzo, plan_sin_limite):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        plan=plan_sin_limite,
        fecha_inicio=HOY,
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


# ── AlmuerzoService.get_precio_activo ─────────────────────────────────────────

@freeze_time("2026-07-15")
@pytest.mark.django_db
class TestGetPrecioActivo:

    def test_retorna_precio_vigente(self, precio_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        precio = AlmuerzoService.get_precio_activo()
        assert precio is not None
        assert precio.precio_unitario == Decimal("15000")

    def test_retorna_none_sin_precio_configurado(self, db):
        from apps.almuerzos.services import AlmuerzoService
        precio = AlmuerzoService.get_precio_activo()
        assert precio is None


# ── AlmuerzoService.registrar_consumo ─────────────────────────────────────────

@freeze_time("2026-07-15")
@pytest.mark.django_db
class TestRegistrarConsumo:

    def test_primer_registro_genera_costo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import CuentaAlmuerzoMensual

        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=HOY,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
        )

        assert registro.ya_cobrado is True
        assert registro.costo_almuerzo == Decimal("15000")
        cuenta = CuentaAlmuerzoMensual.objects.get(
            hijo=hijo_almuerzo, anio=HOY.year, mes=HOY.month
        )
        assert cuenta.cantidad_almuerzos == 1
        assert cuenta.monto_total == Decimal("15000")
        # Si no se marca, cerrar_cuentas_mes_anterior lo vuelve a sumar al cerrar el mes.
        assert registro.marcado_en_cuenta is True

    def test_segundo_registro_no_se_marca_en_cuenta(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from datetime import timedelta
        from apps.almuerzos.services import AlmuerzoService

        # La clase congela el reloj en un instante fijo (medianoche) — hay que
        # avanzarlo explícitamente para simular que pasaron 300s entre el 1er
        # y el 2do registro, sin restar del "ahora" (cruzaría medianoche).
        with freeze_time("2026-07-15 08:00:00") as frozen:
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )
            frozen.tick(delta=timedelta(seconds=300))
            segundo = AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )

        # No genera costo, así que nunca se acredita a la cuenta ni se marca.
        assert segundo.marcado_en_cuenta is False

    def test_segundo_registro_sin_costo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from datetime import timedelta
        from apps.almuerzos.services import AlmuerzoService

        with freeze_time("2026-07-15 08:00:00") as frozen:
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )
            frozen.tick(delta=timedelta(seconds=300))
            segundo = AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )

        assert segundo.ya_cobrado is False
        assert segundo.costo_almuerzo == Decimal("0")

    def test_tercer_registro_bloqueado(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from datetime import timedelta
        from apps.almuerzos.services import AlmuerzoService

        with freeze_time("2026-07-15 08:00:00") as frozen:
            for _ in range(2):
                AlmuerzoService.registrar_consumo(
                    hijo=hijo_almuerzo,
                    fecha_consumo=HOY,
                    nro_tarjeta=tarjeta_almuerzo,
                    registrado_por=usuario_cajero,
                    suscripcion=suscripcion_activa,
                )
                frozen.tick(delta=timedelta(seconds=300))

            with pytest.raises(ValidationError):
                AlmuerzoService.registrar_consumo(
                    hijo=hijo_almuerzo,
                    fecha_consumo=HOY,
                    nro_tarjeta=tarjeta_almuerzo,
                    registrado_por=usuario_cajero,
                    suscripcion=suscripcion_activa,
                )

    def test_tarjeta_bloqueada_falla(
        self, hijo_almuerzo, tarjeta_bloqueada_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="bloqueada"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_bloqueada_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_fecha_futura_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo
    ):
        from apps.almuerzos.services import AlmuerzoService

        manana = HOY + timedelta(days=1)
        with pytest.raises(ValidationError, match="futura"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=manana,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_sin_tarjeta_falla(self, hijo_almuerzo, usuario_cajero):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="tarjeta"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=None,
                registrado_por=usuario_cajero,
            )

    def test_sin_precio_configurado_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="precio"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_limite_credito_mensual_ya_no_bloquea(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, db
    ):
        """Almuerzo es cuenta corriente: el límite de crédito del plan ya no
        bloquea el registro — el saldo simplemente queda negativo."""
        from apps.almuerzos.models import PlanAlmuerzo, SuscripcionAlmuerzo, SaldoAlmuerzo
        from apps.almuerzos.services import AlmuerzoService

        # Precio = 15000, límite = 10000 → antes hubiera bloqueado en el primer intento
        plan = PlanAlmuerzo.objects.create(
            nombre="Plan Ajustado",
            activo=True,
            precio_mensual=Decimal("200000"),
            limite_credito_mensual=Decimal("10000"),
        )
        suscripcion = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            plan=plan,
            fecha_inicio=HOY,
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )

        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=HOY,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion,
        )

        assert registro.ya_cobrado is True
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("-15000")

    def test_suscripcion_inactiva_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, db
    ):
        from apps.almuerzos.models import PlanAlmuerzo, SuscripcionAlmuerzo
        from apps.almuerzos.services import AlmuerzoService

        plan = PlanAlmuerzo.objects.create(
            nombre="Plan Inactivo",
            activo=True,
            precio_mensual=Decimal("100000"),
        )
        suscripcion = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            plan=plan,
            fecha_inicio=HOY,
            estado=SuscripcionAlmuerzo.Estado.SUSPENDIDA,
        )

        with pytest.raises(ValidationError, match="[Aa]ctiva"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion,
            )

    def test_tarjeta_no_pertenece_al_hijo_falla(self, hijo_almuerzo, usuario_cajero, db):
        from apps.almuerzos.services import AlmuerzoService
        from apps.clientes.models import Hijo, Grado

        grado, _ = Grado.objects.get_or_create(
            nombre="5to grado", defaults={"nivel": 5, "orden": 5, "activo": True}
        )
        otro_hijo = Hijo.objects.create(
            nombre="Otro", apellido="Niño",
            cliente_responsable=hijo_almuerzo.cliente_responsable,
            grado=grado, activo=True,
        )
        from apps.core.models import Tarjeta
        tarjeta_otro = Tarjeta.objects.create(
            nro_tarjeta="OTRO-ALMZ-001",
            hijo=otro_hijo,
            saldo_actual=Decimal("50000"),
            estado=Tarjeta.Estado.ACTIVA,
        )

        with pytest.raises(ValidationError, match="pertenece"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=HOY,
                nro_tarjeta=tarjeta_otro,
                registrado_por=usuario_cajero,
            )

    def test_usa_tipo_almuerzo_si_no_hay_precio_activo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, db
    ):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import TipoAlmuerzo

        tipo = TipoAlmuerzo.objects.create(
            nombre="Almuerzo Básico Test",
            precio_unitario=Decimal("12000"),
            activo=True,
        )
        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=HOY,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
            tipo_almuerzo=tipo,
        )
        assert registro.costo_almuerzo == Decimal("12000")


# ── AlmuerzoService.recargar_saldo / confirmar_recarga ────────────────────────

@pytest.fixture
def cierre_caja_abierto(db, usuario_cajero):
    from apps.contabilidad.models import Caja, CierreCaja
    caja = Caja.objects.create(nombre="Caja Test Almuerzo")
    return CierreCaja.objects.create(
        caja=caja, empleado=usuario_cajero, estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.mark.django_db
class TestRecargarSaldo:

    def test_recarga_acredita_saldo_y_crea_movimiento(self, hijo_almuerzo, usuario_cajero):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo

        recarga = AlmuerzoService.recargar_saldo(
            hijo=hijo_almuerzo, monto=Decimal("50000"),
            registrado_por=usuario_cajero, metodo_pago="EFECTIVO",
        )

        assert recarga.estado == recarga.Estado.CONFIRMADA
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("50000")
        mov = MovimientoSaldoAlmuerzo.objects.get(recarga=recarga)
        assert mov.tipo == MovimientoSaldoAlmuerzo.Tipo.RECARGA
        assert mov.monto == Decimal("50000")
        assert mov.saldo_resultante == Decimal("50000")

    def test_recarga_sobre_saldo_existente_lo_acumula(self, hijo_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import SaldoAlmuerzo

        AlmuerzoService.recargar_saldo(hijo=hijo_almuerzo, monto=Decimal("30000"))
        AlmuerzoService.recargar_saldo(hijo=hijo_almuerzo, monto=Decimal("20000"))

        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("50000")

    def test_monto_cero_o_negativo_falla(self, hijo_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        with pytest.raises(ValidationError, match="mayor a 0"):
            AlmuerzoService.recargar_saldo(hijo=hijo_almuerzo, monto=Decimal("0"))

    def test_con_cierre_caja_crea_movimiento_caja(self, hijo_almuerzo, cierre_caja_abierto):
        from apps.almuerzos.services import AlmuerzoService
        from apps.contabilidad.models import MovimientoCaja

        AlmuerzoService.recargar_saldo(
            hijo=hijo_almuerzo, monto=Decimal("25000"),
            metodo_pago="EFECTIVO", cierre_caja=cierre_caja_abierto,
        )
        assert MovimientoCaja.objects.filter(
            cierre=cierre_caja_abierto, tipo=MovimientoCaja.Tipo.INGRESO, monto=Decimal("25000"),
        ).exists()


@pytest.mark.django_db
class TestConfirmarRecarga:

    def test_confirma_recarga_pendiente(self, hijo_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import RecargaSaldoAlmuerzo, SaldoAlmuerzo

        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("40000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        confirmada = AlmuerzoService.confirmar_recarga(recarga=recarga)

        assert confirmada.estado == RecargaSaldoAlmuerzo.Estado.CONFIRMADA
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("40000")

    def test_confirmar_recarga_no_pendiente_falla(self, hijo_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import RecargaSaldoAlmuerzo

        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("40000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
        )
        with pytest.raises(ValidationError, match="PENDIENTE"):
            AlmuerzoService.confirmar_recarga(recarga=recarga)

    def test_con_cierre_caja_crea_movimiento_caja(self, hijo_almuerzo, cierre_caja_abierto):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        from apps.contabilidad.models import MovimientoCaja

        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        AlmuerzoService.confirmar_recarga(recarga=recarga, cierre_caja=cierre_caja_abierto)
        assert MovimientoCaja.objects.filter(
            cierre=cierre_caja_abierto, tipo=MovimientoCaja.Tipo.INGRESO, monto=Decimal("15000"),
        ).exists()


@pytest.mark.django_db
class TestRevertirSaldoAlmuerzo:

    def test_anular_registro_revierte_saldo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa,
    ):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import SaldoAlmuerzo

        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo, fecha_consumo=HOY, nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero, suscripcion=suscripcion_activa,
        )
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("-15000")

        AlmuerzoService._revertir_saldo_almuerzo(registro)

        saldo.refresh_from_db()
        assert saldo.saldo_actual == Decimal("0")
