"""
Cierre de cuentas de egresados — servicio y API.

Matriz de autorización:
  cobro                       ADMIN, SUPERVISOR, CAJERO, COBRADOR (ingreso, sin aprobación)
  traspaso / compensación /   ADMIN o SUPERVISOR (ejecutan al momento)
  traslado a cta. cte.
  devolución / condonación    SUPERVISOR solicita; solo ADMIN aprueba. Si la pide un
                              ADMIN, se ejecuta al momento.
"""
from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.cierre_cuentas.models import CierreCuentaAlumno, ResolucionSaldo
from apps.cierre_cuentas.services import CierreCuentaService

Tipo = ResolucionSaldo.Tipo
Estado = ResolucionSaldo.Estado
BASE = "/api/v1/cierre-cuentas"


def _api(usuario):
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario_supervisor(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="sup_cierre@test.com", password="test1234", nombre="Sup", apellido="Cierre",
        rol=Usuario.Rol.SUPERVISOR,
    )


@pytest.fixture
def usuario_cobrador(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="cob_cierre@test.com", password="test1234", nombre="Cob", apellido="Cierre",
        rol=Usuario.Rol.COBRADOR,
    )


@pytest.fixture
def grado_ultimo(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="3° AÑO CIERRE", nivel=5, orden=33, es_ultimo=True)


@pytest.fixture
def grado_normal(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="4° Grado CIERRE", nivel=3, orden=8, es_ultimo=False)


def _alumno(cliente, grado, nombre, nro, cantina=0, almuerzo=0, activo=True):
    """Alumno con tarjeta. El saldo entra por el libro mayor: un trigger de la base
    recalcula tarjeta.saldo_actual desde los movimientos."""
    from apps.almuerzos.models import SaldoAlmuerzo
    from apps.clientes.models import Hijo
    from apps.core.models import MovimientoTarjeta, Tarjeta

    hijo = Hijo.objects.create(
        nombre=nombre, apellido="Egresado", cliente_responsable=cliente, grado=grado, activo=activo,
    )
    tarjeta = Tarjeta.objects.create(nro_tarjeta=nro, hijo=hijo)
    if cantina:
        MovimientoTarjeta.objects.create(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.RECARGA if cantina > 0 else MovimientoTarjeta.Tipo.CONSUMO,
            monto=Decimal(abs(cantina)), saldo_anterior=Decimal(0), saldo_resultante=Decimal(cantina),
            descripcion="Saldo inicial de prueba",
        )
    if almuerzo:
        SaldoAlmuerzo.objects.create(hijo=hijo, saldo_actual=Decimal(almuerzo))
    return hijo


def _saldos(hijo):
    return CierreCuentaService.saldos(hijo)


def _abrir_caja(usuario):
    from apps.contabilidad.models import Caja, CierreCaja
    caja = Caja.objects.create(nombre=f"Caja cierre {usuario.pk}")
    return CierreCaja.objects.create(caja=caja, empleado=usuario, estado=CierreCaja.Estado.ABIERTO)


def _resolver(cierre, usuario, tipo, bolsillo="CANTINA", monto=1000, **extra):
    return CierreCuentaService.registrar_resolucion(
        cierre=cierre, usuario=usuario, tipo=tipo, bolsillo_origen=bolsillo, monto=monto, **extra,
    )


@pytest.fixture
def favor(cliente, grado_ultimo):
    """Egresado con saldo a favor: cantina 80.000 y almuerzo 50.000."""
    return _alumno(cliente, grado_ultimo, "Favor", "CI-F", cantina=80000, almuerzo=50000)


@pytest.fixture
def deudor(cliente, grado_ultimo):
    """Egresado con deuda: cantina -30.000 y almuerzo -60.000."""
    return _alumno(cliente, grado_ultimo, "Deudor", "CI-D", cantina=-30000, almuerzo=-60000)


@pytest.fixture
def hermano(cliente, grado_normal):
    return _alumno(cliente, grado_normal, "Hermano", "CI-H", cantina=10000, almuerzo=5000)


# ── Apertura ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApertura:

    def test_snapshot_de_saldos_y_estado_abierto(self, favor, usuario_admin):
        cierre, creado = CierreCuentaService.abrir(favor, 2026, usuario_admin)
        assert creado
        assert cierre.saldo_cantina_inicial == Decimal("80000")
        assert cierre.saldo_almuerzo_inicial == Decimal("50000")
        assert cierre.estado == CierreCuentaAlumno.Estado.ABIERTO

    def test_sin_saldos_nace_resuelto(self, cliente, grado_ultimo):
        cierre, _ = CierreCuentaService.abrir(_alumno(cliente, grado_ultimo, "Cero", "CI-Z"), 2026)
        assert cierre.estado == CierreCuentaAlumno.Estado.RESUELTO
        assert cierre.fecha_cierre is not None

    def test_es_idempotente(self, favor):
        a, creado_a = CierreCuentaService.abrir(favor, 2026)
        b, creado_b = CierreCuentaService.abrir(favor, 2026)
        assert a.pk == b.pk and creado_a and not creado_b

    def test_masivo_toma_el_ultimo_curso_y_los_dados_de_baja_del_anio(
        self, cliente, grado_ultimo, grado_normal,
    ):
        from django.utils import timezone
        activo_ultimo = _alumno(cliente, grado_ultimo, "Ultimo", "CI-U", cantina=1000)
        normal = _alumno(cliente, grado_normal, "Normal", "CI-N", cantina=1000)
        baja = _alumno(cliente, grado_normal, "Baja", "CI-B", cantina=1000, activo=False)
        baja.fecha_baja = timezone.make_aware(timezone.datetime(2026, 3, 1))
        baja.save(update_fields=["fecha_baja"])
        baja_otro_anio = _alumno(cliente, grado_normal, "BajaVieja", "CI-BV", cantina=1000, activo=False)
        baja_otro_anio.fecha_baja = timezone.make_aware(timezone.datetime(2025, 3, 1))
        baja_otro_anio.save(update_fields=["fecha_baja"])

        res = CierreCuentaService.abrir_masivo(2026)
        assert res == {"anio": 2026, "creados": 2, "existentes": 0}
        assert set(CierreCuentaAlumno.objects.values_list("hijo_id", flat=True)) == {activo_ultimo.pk, baja.pk}
        assert not CierreCuentaAlumno.objects.filter(hijo=normal).exists()
        assert CierreCuentaService.abrir_masivo(2026)["creados"] == 0

    def test_api_solo_admin_o_supervisor_abren(self, favor, usuario_cajero, usuario_supervisor):
        assert _api(usuario_cajero).post(f"{BASE}/cierres/abrir/", {"hijo": favor.pk}, format="json").status_code == 403
        r = _api(usuario_supervisor).post(f"{BASE}/cierres/abrir/", {"hijo": favor.pk}, format="json")
        assert r.status_code == 201
        assert _api(usuario_supervisor).post(f"{BASE}/cierres/abrir/", {"hijo": favor.pk}, format="json").status_code == 200


# ── Devolución ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDevolucion:

    def test_admin_en_efectivo_deja_ajuste_negativo_y_egreso_de_caja(
        self, favor, usuario_admin, medio_pago_efectivo,
    ):
        from apps.contabilidad.models import MovimientoCaja
        from apps.core.models import MovimientoTarjeta
        caja = _abrir_caja(usuario_admin)
        cierre, _ = CierreCuentaService.abrir(favor, 2026)

        res, adv = _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 30000, metodo_pago="EFECTIVO")

        assert res.estado == Estado.EJECUTADA and adv is None
        assert _saldos(favor)[0] == Decimal("50000")
        mov = MovimientoTarjeta.objects.get(pk=res.movimiento_tarjeta_origen_id)
        assert (mov.tipo, mov.monto, mov.saldo_anterior, mov.saldo_resultante) == (
            "AJUSTE", Decimal("-30000"), Decimal("80000"), Decimal("50000"))
        caja_mov = MovimientoCaja.objects.get(pk=res.movimiento_caja_id)
        assert caja_mov.tipo == MovimientoCaja.Tipo.EGRESO and caja_mov.monto == Decimal("30000")
        assert caja_mov.cierre_id == caja.pk
        assert res.decidido_por == usuario_admin and res.solicitado_por == usuario_admin

    def test_efectivo_sin_caja_abierta_falla_y_no_toca_nada(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="Abrí tu caja"):
            _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 30000, metodo_pago="EFECTIVO")
        assert _saldos(favor)[0] == Decimal("80000")
        assert cierre.resoluciones.filter(estado=Estado.EJECUTADA).count() == 0

    def test_por_transferencia_exige_referencia_y_no_mueve_caja(self, favor, usuario_admin):
        from apps.contabilidad.models import MovimientoCaja
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError):
            _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 30000, metodo_pago="TRANSFERENCIA")
        res, _ = _resolver(
            cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-123",
        )
        assert res.estado == Estado.EJECUTADA and res.movimiento_caja is None
        assert not MovimientoCaja.objects.exists()

    def test_devolucion_del_saldo_de_almuerzo(self, favor, usuario_admin):
        from apps.almuerzos.models import MovimientoSaldoAlmuerzo
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_admin, Tipo.DEVOLUCION, "ALMUERZO", 50000,
            metodo_pago="TRANSFERENCIA", referencia="TR-9",
        )
        assert _saldos(favor)[1] == Decimal("0")
        mov = res.movimiento_almuerzo_origen
        assert (mov.tipo, mov.monto, mov.saldo_resultante) == (
            MovimientoSaldoAlmuerzo.Tipo.AJUSTE, Decimal("-50000"), Decimal("0"))

    def test_no_se_puede_devolver_mas_que_el_saldo_ni_sin_saldo_a_favor(self, favor, deudor, usuario_admin):
        c_favor, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="supera el saldo a favor"):
            _resolver(c_favor, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 80001,
                      metodo_pago="TRANSFERENCIA", referencia="x")
        c_deudor, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError, match="no tiene saldo a favor"):
            _resolver(c_deudor, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 1000,
                      metodo_pago="TRANSFERENCIA", referencia="x")

    def test_supervisor_solo_solicita_y_avisa_a_los_admin(self, favor, usuario_supervisor, usuario_admin):
        from apps.notificaciones.models import Notificacion
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, adv = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1", motivo="Egresó",
        )
        assert res.estado == Estado.SOLICITADA
        assert _saldos(favor)[0] == Decimal("80000")  # nada se movió
        n = Notificacion.objects.get(usuario=usuario_admin)
        assert "Aprobación pendiente" in n.titulo and "30,000" in n.mensaje

    def test_el_admin_aprueba_y_queda_registrado_quien_decidio(self, favor, usuario_supervisor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1",
        )
        res, _ = CierreCuentaService.aprobar(res, usuario_admin)
        assert res.estado == Estado.EJECUTADA
        assert res.solicitado_por == usuario_supervisor and res.decidido_por == usuario_admin
        assert _saldos(favor)[0] == Decimal("50000")

    def test_el_supervisor_no_puede_aprobar(self, favor, usuario_supervisor):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1",
        )
        from rest_framework.exceptions import PermissionDenied
        with pytest.raises(PermissionDenied):
            CierreCuentaService.aprobar(res, usuario_supervisor)

    def test_rechazo_exige_motivo_avisa_al_solicitante_y_no_mueve_saldo(
        self, favor, usuario_supervisor, usuario_admin,
    ):
        from apps.notificaciones.models import Notificacion
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1",
        )
        with pytest.raises(ValidationError):
            CierreCuentaService.rechazar(res, usuario_admin, "  ")
        res = CierreCuentaService.rechazar(res, usuario_admin, "Falta documentación")
        assert res.estado == Estado.RECHAZADA and res.decidido_por == usuario_admin
        assert _saldos(favor)[0] == Decimal("80000")
        assert "Falta documentación" in Notificacion.objects.get(usuario=usuario_supervisor).mensaje

    def test_no_se_puede_aprobar_dos_veces(self, favor, usuario_supervisor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 30000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1",
        )
        CierreCuentaService.aprobar(res, usuario_admin)
        with pytest.raises(ValidationError, match="ya fue procesada"):
            CierreCuentaService.aprobar(res, usuario_admin)
        assert _saldos(favor)[0] == Decimal("50000")

    def test_al_aprobar_se_revalidan_los_saldos(self, favor, usuario_supervisor, usuario_admin):
        # Entre la solicitud y la aprobación el alumno gastó el saldo.
        from apps.core.models import MovimientoTarjeta, Tarjeta
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 70000,
            metodo_pago="TRANSFERENCIA", referencia="TR-1",
        )
        t = Tarjeta.objects.get(hijo=favor)
        MovimientoTarjeta.objects.create(
            tarjeta=t, tipo="CONSUMO", monto=Decimal(50000),
            saldo_anterior=Decimal(80000), saldo_resultante=Decimal(30000),
        )
        with pytest.raises(ValidationError, match="supera el saldo a favor"):
            CierreCuentaService.aprobar(res, usuario_admin)

    def test_cajero_y_cobrador_no_pueden_solicitar(self, favor, usuario_cajero, usuario_cobrador):
        from rest_framework.exceptions import PermissionDenied
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        for usuario in (usuario_cajero, usuario_cobrador):
            with pytest.raises(PermissionDenied):
                _resolver(cierre, usuario, Tipo.DEVOLUCION, "CANTINA", 1000,
                          metodo_pago="TRANSFERENCIA", referencia="x")


# ── Traspaso a hermano ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTraspaso:

    def test_cantina_a_cantina_deja_dos_movimientos(self, favor, hermano, usuario_supervisor):
        from apps.core.models import MovimientoTarjeta
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(cierre, usuario_supervisor, Tipo.TRASPASO_HERMANO, "CANTINA", 20000, hijo_destino=hermano)
        assert res.estado == Estado.EJECUTADA
        assert _saldos(favor)[0] == Decimal("60000")
        assert _saldos(hermano)[0] == Decimal("30000")
        assert MovimientoTarjeta.objects.get(pk=res.movimiento_tarjeta_origen_id).monto == Decimal("-20000")
        assert MovimientoTarjeta.objects.get(pk=res.movimiento_tarjeta_destino_id).monto == Decimal("20000")

    def test_de_almuerzo_a_cantina_del_hermano(self, favor, hermano, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(
            cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "ALMUERZO", 15000,
            hijo_destino=hermano, bolsillo_destino="CANTINA",
        )
        assert _saldos(favor)[1] == Decimal("35000")
        assert _saldos(hermano)[0] == Decimal("25000")
        assert res.movimiento_almuerzo_origen is not None and res.movimiento_tarjeta_destino_id

    def test_solo_a_un_hermano_del_mismo_responsable(self, favor, cliente, grado_normal, usuario_admin):
        from apps.clientes.models import Cliente
        otro_cliente = Cliente.objects.create(
            nombres="Otro", apellidos="Resp", ruc_ci="3330001",
            tipo_cliente=cliente.tipo_cliente, lista_precio=cliente.lista_precio,
        )
        ajeno = _alumno(otro_cliente, grado_normal, "Ajeno", "CI-AJ", cantina=1000)
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="mismo responsable"):
            _resolver(cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "CANTINA", 1000, hijo_destino=ajeno)
        assert _saldos(favor)[0] == Decimal("80000")

    def test_no_a_si_mismo_ni_a_un_hermano_de_baja(self, favor, cliente, grado_normal, usuario_admin):
        de_baja = _alumno(cliente, grado_normal, "Baja", "CI-BJ", cantina=1000, activo=False)
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="otro alumno"):
            _resolver(cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "CANTINA", 1000, hijo_destino=favor)
        with pytest.raises(ValidationError, match="dado de baja"):
            _resolver(cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "CANTINA", 1000, hijo_destino=de_baja)

    def test_requiere_hermano_destino(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="hermano"):
            _resolver(cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "CANTINA", 1000)

    def test_cajero_no_puede_traspasar(self, favor, hermano, usuario_cajero):
        from rest_framework.exceptions import PermissionDenied
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(PermissionDenied):
            _resolver(cierre, usuario_cajero, Tipo.TRASPASO_HERMANO, "CANTINA", 1000, hijo_destino=hermano)


# ── Compensación ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompensacion:

    @pytest.fixture
    def mixto(self, cliente, grado_ultimo):
        """Renata: 53.000 a favor en cantina y 425.000 de deuda de almuerzo."""
        return _alumno(cliente, grado_ultimo, "Renata", "CI-R", cantina=53000, almuerzo=-425000)

    def test_el_favor_de_cantina_paga_deuda_de_almuerzo(self, mixto, usuario_supervisor):
        cierre, _ = CierreCuentaService.abrir(mixto, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.COMPENSACION, "CANTINA", 53000, bolsillo_destino="ALMUERZO",
        )
        assert res.estado == Estado.EJECUTADA
        assert _saldos(mixto) == (Decimal("0"), Decimal("-372000"))

    def test_el_monto_no_supera_el_favor_ni_la_deuda(self, mixto, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(mixto, 2026)
        with pytest.raises(ValidationError, match="supera el saldo a favor"):
            _resolver(cierre, usuario_admin, Tipo.COMPENSACION, "CANTINA", 60000, bolsillo_destino="ALMUERZO")

    def test_requiere_el_otro_bolsillo_con_deuda(self, favor, mixto, usuario_admin):
        c_mixto, _ = CierreCuentaService.abrir(mixto, 2026)
        with pytest.raises(ValidationError, match="otro bolsillo"):
            _resolver(c_mixto, usuario_admin, Tipo.COMPENSACION, "CANTINA", 1000, bolsillo_destino="CANTINA")
        c_favor, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="no tiene deuda"):
            _resolver(c_favor, usuario_admin, Tipo.COMPENSACION, "CANTINA", 1000, bolsillo_destino="ALMUERZO")


# ── Cobro ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCobro:

    def test_cobro_de_cantina_en_efectivo_ingresa_a_caja(self, deudor, usuario_cajero, medio_pago_efectivo):
        from apps.contabilidad.models import MovimientoCaja
        caja = _abrir_caja(usuario_cajero)
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        res, adv = _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 30000, metodo_pago="EFECTIVO")
        assert res.estado == Estado.EJECUTADA and adv is None
        assert _saldos(deudor)[0] == Decimal("0")
        assert res.carga_saldo is not None and res.carga_saldo.estado == "CONFIRMADA"
        ingreso = MovimientoCaja.objects.get(cierre=caja)
        assert ingreso.tipo == MovimientoCaja.Tipo.INGRESO and ingreso.monto == Decimal("30000")

    def test_cobro_parcial_deja_el_expediente_parcial(self, deudor, usuario_cobrador):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        _resolver(cierre, usuario_cobrador, Tipo.COBRO, "ALMUERZO", 20000, metodo_pago="EFECTIVO")
        cierre.refresh_from_db()
        assert cierre.estado == CierreCuentaAlumno.Estado.PARCIAL
        assert _saldos(deudor)[1] == Decimal("-40000")

    def test_cobro_sin_caja_avisa(self, deudor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        res, adv = _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 10000, metodo_pago="EFECTIVO")
        assert res.estado == Estado.EJECUTADA and "caja" in adv.lower()

    def test_cobro_de_almuerzo_crea_la_recarga(self, deudor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        res, _ = _resolver(cierre, usuario_cajero, Tipo.COBRO, "ALMUERZO", 60000, metodo_pago="EFECTIVO")
        assert res.recarga_almuerzo is not None and res.recarga_almuerzo.estado == "CONFIRMADA"
        assert _saldos(deudor)[1] == Decimal("0")

    def test_el_cobro_no_supera_la_deuda(self, deudor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError, match="supera la deuda"):
            _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 30001, metodo_pago="EFECTIVO")

    def test_no_se_cobra_si_no_hay_deuda(self, favor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        with pytest.raises(ValidationError, match="no tiene deuda"):
            _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 1000, metodo_pago="EFECTIVO")

    def test_transferencia_exige_referencia_y_medio_valido(self, deudor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError):
            _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 1000, metodo_pago="TRANSFERENCIA")
        with pytest.raises(ValidationError):
            _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 1000, metodo_pago="CHEQUE")


# ── Traslado a cuenta corriente y condonación ────────────────────────────────

@pytest.mark.django_db
class TestTrasladoYCondonacion:

    def test_traslado_pasa_la_deuda_a_la_cuenta_corriente_familiar(self, deudor, cliente, usuario_supervisor):
        from apps.clientes.models import CuentaCorrienteCliente
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        res, _ = _resolver(cierre, usuario_supervisor, Tipo.TRASLADO_CC, "ALMUERZO", 60000)
        assert _saldos(deudor)[1] == Decimal("0")
        cc = CuentaCorrienteCliente.objects.get(pk=res.movimiento_cc_id)
        assert cc.tipo == "DEBITO" and cc.monto == Decimal("60000") and cc.origen == "ALMUERZO"
        assert cc.cliente_id == cliente.pk

    def test_traslado_exige_cuenta_corriente_habilitada(self, deudor, cliente, usuario_admin):
        cliente.permite_cuenta_corriente = False
        cliente.save(update_fields=["permite_cuenta_corriente"])
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError, match="cuenta corriente"):
            _resolver(cierre, usuario_admin, Tipo.TRASLADO_CC, "ALMUERZO", 60000)
        assert _saldos(deudor)[1] == Decimal("-60000")

    def test_traslado_respeta_el_limite_de_credito(self, deudor, cliente, usuario_admin):
        cliente.limite_credito = Decimal("50000")
        cliente.save(update_fields=["limite_credito"])
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError, match="límite de crédito"):
            _resolver(cierre, usuario_admin, Tipo.TRASLADO_CC, "ALMUERZO", 60000)

    def test_condonacion_del_admin_se_ejecuta_y_exige_motivo(self, deudor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(ValidationError, match="motivo"):
            _resolver(cierre, usuario_admin, Tipo.CONDONACION, "CANTINA", 30000, motivo="corto")
        res, _ = _resolver(
            cierre, usuario_admin, Tipo.CONDONACION, "CANTINA", 30000,
            motivo="Familia con dificultades económicas comprobadas",
        )
        assert res.estado == Estado.EJECUTADA
        assert _saldos(deudor)[0] == Decimal("0")
        assert res.movimiento_caja is None and res.carga_saldo is None  # no hay dinero

    def test_condonacion_pedida_por_supervisor_queda_pendiente(self, deudor, usuario_supervisor):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        res, _ = _resolver(
            cierre, usuario_supervisor, Tipo.CONDONACION, "CANTINA", 30000,
            motivo="Familia con dificultades económicas comprobadas",
        )
        assert res.estado == Estado.SOLICITADA
        assert _saldos(deudor)[0] == Decimal("-30000")


# ── Estado del expediente y cierre con saldo ─────────────────────────────────

@pytest.mark.django_db
class TestEstadoYCierre:

    def test_resuelto_cuando_los_dos_bolsillos_quedan_en_cero(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        for bolsillo, monto in (("CANTINA", 80000), ("ALMUERZO", 50000)):
            _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, bolsillo, monto,
                      metodo_pago="TRANSFERENCIA", referencia="TR")
        cierre.refresh_from_db()
        assert cierre.estado == CierreCuentaAlumno.Estado.RESUELTO
        assert cierre.fecha_cierre is not None and cierre.saldo_cantina_final == Decimal("0")

    def test_cerrar_con_saldo_solo_admin_con_motivo(self, deudor, usuario_supervisor, usuario_admin):
        from rest_framework.exceptions import PermissionDenied
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        with pytest.raises(PermissionDenied):
            CierreCuentaService.cerrar_con_saldo(cierre, usuario_supervisor, "no cobrable")
        with pytest.raises(ValidationError):
            CierreCuentaService.cerrar_con_saldo(cierre, usuario_admin, "")
        cierre = CierreCuentaService.cerrar_con_saldo(cierre, usuario_admin, "Se retiró del país")
        assert cierre.estado == CierreCuentaAlumno.Estado.CERRADO_CON_SALDO
        assert cierre.saldo_cantina_final == Decimal("-30000")
        assert cierre.saldo_almuerzo_final == Decimal("-60000")
        assert cierre.cerrado_por == usuario_admin

    def test_no_bloquea_la_baja_ni_toca_los_saldos(self, deudor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        CierreCuentaService.cerrar_con_saldo(cierre, usuario_admin, "Se retiró del país")
        assert _saldos(deudor) == (Decimal("-30000"), Decimal("-60000"))

    def test_no_se_cierra_con_resoluciones_pendientes(self, favor, usuario_supervisor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        _resolver(cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 1000,
                  metodo_pago="TRANSFERENCIA", referencia="x")
        with pytest.raises(ValidationError, match="pendientes"):
            CierreCuentaService.cerrar_con_saldo(cierre, usuario_admin, "motivo")

    def test_un_expediente_cerrado_no_acepta_resoluciones(self, deudor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        cierre = CierreCuentaService.cerrar_con_saldo(cierre, usuario_admin, "Se retiró del país")
        with pytest.raises(ValidationError, match="ya fue cerrado"):
            _resolver(cierre, usuario_admin, Tipo.COBRO, "CANTINA", 1000, metodo_pago="EFECTIVO")


# ── Trazabilidad ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTrazabilidad:

    def test_el_libro_mayor_de_la_tarjeta_queda_consistente(self, favor, hermano, usuario_admin):
        from django.db.models import Sum
        from apps.core.models import MovimientoTarjeta, Tarjeta
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        _resolver(cierre, usuario_admin, Tipo.TRASPASO_HERMANO, "CANTINA", 20000, hijo_destino=hermano)
        _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 10000,
                  metodo_pago="TRANSFERENCIA", referencia="TR")
        for h in (favor, hermano):
            t = Tarjeta.objects.get(hijo=h)
            ajustes = MovimientoTarjeta.objects.filter(tarjeta=t)
            neto = sum(
                (m.monto if m.tipo != "CONSUMO" else -m.monto) for m in ajustes
            )
            assert neto == t.saldo_actual
        assert Tarjeta.objects.get(hijo=favor).saldo_actual == Decimal("50000")

    def test_auditoria_de_cada_paso(self, favor, usuario_supervisor, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion
        cierre, _ = CierreCuentaService.abrir(favor, 2026, usuario_admin)
        res, _ = _resolver(cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 1000,
                           metodo_pago="TRANSFERENCIA", referencia="TR")
        CierreCuentaService.aprobar(res, usuario_admin)
        operaciones = set(AuditoriaOperacion.objects.values_list("operacion", flat=True))
        assert {
            "CIERRE_CUENTA_ABRIR", "CIERRE_CUENTA_DEVOLUCION_SOLICITADA", "CIERRE_CUENTA_DEVOLUCION_EJECUTADA",
        } <= operaciones

    def test_avisa_a_la_familia_cuando_se_ejecuta(self, favor, cliente, usuario_admin):
        from apps.notificaciones.models import Notificacion
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_cierre@test.com", password="x12345678", nombre="P", apellido="C",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 30000,
                  metodo_pago="TRANSFERENCIA", referencia="TR")
        n = Notificacion.objects.get(usuario=padre)
        assert "devolución" in n.mensaje and "30,000" in n.mensaje and "cantina" in n.mensaje


# ── API ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApi:

    def test_listado_con_saldos_vivos_y_filtros(self, favor, deudor, usuario_cajero):
        CierreCuentaService.abrir(favor, 2026)
        CierreCuentaService.abrir(deudor, 2026)
        r = _api(usuario_cajero).get(f"{BASE}/cierres/", {"anio": 2026})
        assert r.status_code == 200 and r.data["count"] == 2
        por_nombre = {c["hijo_nombre"].split()[0]: c for c in r.data["results"]}
        assert por_nombre["Favor"]["saldo_cantina_actual"] == 80000
        assert por_nombre["Favor"]["a_favor_pendiente"] == 130000
        assert por_nombre["Deudor"]["deuda_pendiente"] == 90000
        assert por_nombre["Deudor"]["nro_tarjeta"] == "CI-D"
        buscar = _api(usuario_cajero).get(f"{BASE}/cierres/", {"search": "Deudor"})
        assert buscar.data["count"] == 1

    def test_detalle_trae_las_resoluciones(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 1000,
                  metodo_pago="TRANSFERENCIA", referencia="TR")
        r = _api(usuario_admin).get(f"{BASE}/cierres/{cierre.pk}/")
        assert len(r.data["resoluciones"]) == 1
        assert r.data["resoluciones"][0]["tipo_display"] == "Devolución"

    def test_registrar_por_api_y_advertencia_sin_caja(self, deudor, usuario_cajero):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        r = _api(usuario_cajero).post(
            f"{BASE}/cierres/{cierre.pk}/resoluciones/",
            {"tipo": "COBRO", "bolsillo_origen": "CANTINA", "monto": 30000, "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["resolucion"]["estado"] == "EJECUTADA"
        assert "caja" in r.data["advertencia"].lower()

    def test_errores_de_negocio_dan_400_legible(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        r = _api(usuario_admin).post(
            f"{BASE}/cierres/{cierre.pk}/resoluciones/",
            {"tipo": "DEVOLUCION", "bolsillo_origen": "CANTINA", "monto": 999999,
             "metodo_pago": "TRANSFERENCIA", "referencia": "x"},
            format="json",
        )
        assert r.status_code == 400
        assert "supera el saldo a favor" in str(r.data)

    def test_aprobar_y_rechazar_por_api_solo_admin(self, favor, usuario_supervisor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        res, _ = _resolver(cierre, usuario_supervisor, Tipo.DEVOLUCION, "CANTINA", 1000,
                           metodo_pago="TRANSFERENCIA", referencia="TR")
        url = f"{BASE}/resoluciones/{res.pk}/"
        assert _api(usuario_supervisor).post(f"{url}aprobar/").status_code == 403
        assert _api(usuario_supervisor).post(f"{url}rechazar/", {"motivo": "x"}, format="json").status_code == 403
        r = _api(usuario_admin).post(f"{url}aprobar/")
        assert r.status_code == 200 and r.data["resolucion"]["estado"] == "EJECUTADA"

    def test_historial_de_resoluciones_filtrable(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        _resolver(cierre, usuario_admin, Tipo.DEVOLUCION, "CANTINA", 1000,
                  metodo_pago="TRANSFERENCIA", referencia="TR")
        r = _api(usuario_admin).get(f"{BASE}/resoluciones/", {"cierre": cierre.pk, "estado": "EJECUTADA"})
        assert r.data["count"] == 1 and r.data["results"][0]["solicitado_por_nombre"]

    def test_resumen(self, favor, deudor, usuario_supervisor, usuario_cajero):
        CierreCuentaService.abrir(favor, 2026)
        c_d, _ = CierreCuentaService.abrir(deudor, 2026)
        _resolver(c_d, usuario_supervisor, Tipo.CONDONACION, "CANTINA", 1000,
                  motivo="Familia con dificultades económicas comprobadas")
        r = _api(usuario_cajero).get(f"{BASE}/cierres/resumen/", {"anio": 2026})
        assert r.data["alumnos"] == 2
        assert r.data["saldo_a_devolver"] == 130000
        assert r.data["deuda_a_cobrar"] == 90000
        assert r.data["resoluciones_pendientes"] == 1
        assert r.data["por_estado"]["ABIERTO"] == 2

    def test_cerrar_por_api(self, deudor, usuario_admin, usuario_supervisor):
        cierre, _ = CierreCuentaService.abrir(deudor, 2026)
        url = f"{BASE}/cierres/{cierre.pk}/cerrar/"
        assert _api(usuario_supervisor).post(url, {"motivo": "x"}, format="json").status_code == 403
        r = _api(usuario_admin).post(url, {"motivo": "Se retiró del país"}, format="json")
        assert r.status_code == 200 and r.data["estado"] == "CERRADO_CON_SALDO"

    def test_cocina_y_padres_no_acceden(self, favor, cliente):
        from apps.usuarios.models import Usuario
        cocina = Usuario.objects.create_user(
            email="cocina_cierre@test.com", password="x12345678", nombre="C", apellido="C", rol=Usuario.Rol.COCINA,
        )
        padre = Usuario.objects.create_user(
            email="padre2_cierre@test.com", password="x12345678", nombre="P", apellido="P",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        CierreCuentaService.abrir(favor, 2026)
        for usuario in (cocina, padre):
            assert _api(usuario).get(f"{BASE}/cierres/").status_code == 403
            assert _api(usuario).get(f"{BASE}/resoluciones/").status_code == 403

    def test_no_se_escribe_por_los_verbos_genericos(self, favor, usuario_admin):
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        api = _api(usuario_admin)
        assert api.post(f"{BASE}/cierres/", {"hijo": favor.pk}, format="json").status_code == 405
        assert api.patch(f"{BASE}/cierres/{cierre.pk}/", {"estado": "RESUELTO"}, format="json").status_code == 405
        assert api.delete(f"{BASE}/cierres/{cierre.pk}/").status_code == 405


# ── Integración con las tareas del año lectivo ───────────────────────────────

@pytest.mark.django_db
class TestTareas:

    def test_el_aviso_abre_los_expedientes_del_ultimo_curso(self, favor):
        from apps.clientes.tasks import avisar_cierre_ultimo_curso
        with freeze_time("2026-10-05 12:00:00"):  # dentro del período, fuera de la cadencia semanal
            avisar_cierre_ultimo_curso()
        assert CierreCuentaAlumno.objects.filter(hijo=favor, anio=2026).exists()

    def test_la_baja_deja_el_expediente_abierto_para_resolver(self, deudor):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        with freeze_time("2027-01-01 08:00:00"):
            dar_baja_alumnos_ultimo_curso()
        deudor.refresh_from_db()
        assert deudor.activo is False
        cierre = CierreCuentaAlumno.objects.get(hijo=deudor, anio=2026)
        assert cierre.estado == CierreCuentaAlumno.Estado.ABIERTO

    def test_se_puede_cobrar_a_un_egresado_ya_dado_de_baja(self, deudor, usuario_cajero):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        with freeze_time("2027-01-01 08:00:00"):
            dar_baja_alumnos_ultimo_curso()
        cierre = CierreCuentaAlumno.objects.get(hijo=deudor, anio=2026)
        res, _ = _resolver(cierre, usuario_cajero, Tipo.COBRO, "CANTINA", 30000, metodo_pago="EFECTIVO")
        assert res.estado == Estado.EJECUTADA and _saldos(deudor)[0] == Decimal("0")


# ── Datos para las pantallas ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestDatosParaLaPantalla:

    def test_el_detalle_lista_solo_hermanos_activos_del_mismo_responsable(
        self, favor, hermano, cliente, grado_normal, usuario_admin,
    ):
        from apps.clientes.models import Cliente
        _alumno(cliente, grado_normal, "Baja", "CI-HB", activo=False)
        otro_cliente = Cliente.objects.create(
            nombres="Otro", apellidos="Familia", ruc_ci="3330002",
            tipo_cliente=cliente.tipo_cliente, lista_precio=cliente.lista_precio,
        )
        _alumno(otro_cliente, grado_normal, "Ajeno", "CI-AJ2")
        cierre, _ = CierreCuentaService.abrir(favor, 2026)
        r = _api(usuario_admin).get(f"{BASE}/cierres/{cierre.pk}/")
        assert [h["id_hijo"] for h in r.data["hermanos"]] == [hermano.pk]
        assert r.data["hermanos"][0]["nro_tarjeta"] == "CI-H"

    def test_informa_el_responsable_y_si_tiene_cuenta_corriente(self, favor, cliente, usuario_cajero):
        CierreCuentaService.abrir(favor, 2026)
        r = _api(usuario_cajero).get(f"{BASE}/cierres/")
        fila = r.data["results"][0]
        assert fila["cliente_id"] == cliente.pk
        assert fila["cliente_permite_cuenta_corriente"] is True
