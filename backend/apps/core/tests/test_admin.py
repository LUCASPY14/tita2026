"""Tests para core/admin.py — changelist pages y display methods personalizados."""
import pytest
from decimal import Decimal


@pytest.fixture
def sa_client(db):
    """Superadmin Django test client."""
    from apps.usuarios.models import Usuario
    from django.test import Client
    u = Usuario.objects.create_user(
        email='superadmin_core@test.com',
        password='admin123',
        nombre='Super',
        apellido='Admin',
        rol=Usuario.Rol.ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    c = Client()
    c.force_login(u)
    return c


@pytest.fixture
def tarjeta_con_hijo(db, cliente):
    from apps.clientes.models import Hijo
    from apps.core.models import Tarjeta
    hijo = Hijo.objects.create(
        nombre='Pablo', apellido='Ruiz',
        cliente_responsable=cliente, activo=True,
    )
    return Tarjeta.objects.create(
        nro_tarjeta='ADMIN001',
        hijo=hijo,
        saldo_actual=Decimal('50000'),
        estado=Tarjeta.Estado.ACTIVA,
        permite_saldo_negativo=False,
        limite_credito=Decimal('0'),
    )


@pytest.fixture
def medio_pago(db):
    from apps.core.models import MedioPago
    return MedioPago.objects.create(
        descripcion='Efectivo Admin Test',
        activo=True,
        requiere_validacion=False,
    )


# ── Changelist pages ──────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize("url", [
    "/admin/core/tarjeta/",
    "/admin/core/movimientotarjeta/",
    "/admin/core/cargasaldo/",
    "/admin/core/mediopago/",
])
def test_admin_changelist_returns_200(sa_client, url):
    resp = sa_client.get(url)
    assert resp.status_code == 200


# ── TarjetaAdmin: métodos display ────────────────────────────────────────────

@pytest.mark.django_db
class TestTarjetaAdminDisplay:

    def test_saldo_display_positivo(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = str(a.saldo_display(tarjeta_con_hijo))
        assert '₲' in result
        assert '50' in result  # parte del monto formateado

    def test_saldo_display_negativo(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        tarjeta_con_hijo.saldo_actual = Decimal('-1000')
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = str(a.saldo_display(tarjeta_con_hijo))
        assert '#dc3545' in result  # color rojo

    def test_estado_badge_activa(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = str(a.estado_badge(tarjeta_con_hijo))
        assert '#28a745' in result  # verde para ACTIVA

    def test_estado_badge_bloqueada(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        tarjeta_con_hijo.estado = Tarjeta.Estado.BLOQUEADA
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = str(a.estado_badge(tarjeta_con_hijo))
        assert '#ffc107' in result  # amarillo para BLOQUEADA

    def test_limite_credito_display(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = a.limite_credito_display(tarjeta_con_hijo)
        assert '₲' in result

    def test_hijo_link_html(self, tarjeta_con_hijo):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta
        from django.contrib import admin as dj_admin
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        result = str(a.hijo_link(tarjeta_con_hijo))
        assert '<a' in result
        assert 'Pablo' in result


# ── TarjetaAdmin.save_model — genera MovimientoTarjeta al ajustar saldo ───────

class _FakeForm:
    def __init__(self, changed_data):
        self.changed_data = changed_data


@pytest.mark.django_db
class TestTarjetaAdminSaveModel:

    def test_editar_saldo_genera_movimiento_ajuste(self, tarjeta_con_hijo, usuario_admin):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta, MovimientoTarjeta
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        request = RequestFactory().post('/admin/core/tarjeta/1/change/')
        request.user = usuario_admin

        tarjeta_con_hijo.saldo_actual = Decimal('90000')  # antes: 50000
        a.save_model(request, tarjeta_con_hijo, _FakeForm(['saldo_actual']), change=True)

        mov = MovimientoTarjeta.objects.filter(tarjeta=tarjeta_con_hijo).order_by('-id_movimiento_tarjeta').first()
        assert mov is not None
        assert mov.tipo == MovimientoTarjeta.Tipo.AJUSTE
        assert mov.saldo_anterior == Decimal('50000')
        assert mov.saldo_resultante == Decimal('90000')
        assert mov.creado_por == usuario_admin
        assert 'admin' in mov.descripcion.lower()

    def test_editar_saldo_hacia_abajo_tambien_genera_movimiento(self, tarjeta_con_hijo, usuario_admin):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta, MovimientoTarjeta
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        request = RequestFactory().post('/admin/core/tarjeta/1/change/')
        request.user = usuario_admin

        tarjeta_con_hijo.saldo_actual = Decimal('10000')  # antes: 50000
        a.save_model(request, tarjeta_con_hijo, _FakeForm(['saldo_actual']), change=True)

        mov = MovimientoTarjeta.objects.filter(tarjeta=tarjeta_con_hijo).order_by('-id_movimiento_tarjeta').first()
        assert mov.saldo_anterior == Decimal('50000')
        assert mov.saldo_resultante == Decimal('10000')

    def test_editar_otro_campo_no_genera_movimiento(self, tarjeta_con_hijo, usuario_admin):
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta, MovimientoTarjeta
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        request = RequestFactory().post('/admin/core/tarjeta/1/change/')
        request.user = usuario_admin

        tarjeta_con_hijo.estado = Tarjeta.Estado.BLOQUEADA
        a.save_model(request, tarjeta_con_hijo, _FakeForm(['estado']), change=True)

        assert not MovimientoTarjeta.objects.filter(tarjeta=tarjeta_con_hijo).exists()

    def test_crear_tarjeta_nueva_no_genera_movimiento(self, cliente, usuario_admin):
        from apps.clientes.models import Hijo
        from apps.core.admin import TarjetaAdmin
        from apps.core.models import Tarjeta, MovimientoTarjeta
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        hijo = Hijo.objects.create(nombre='Nueva', apellido='Tarjeta', cliente_responsable=cliente, activo=True)
        nueva = Tarjeta(
            nro_tarjeta='ADMIN-NEW', hijo=hijo, saldo_actual=Decimal('0'),
            estado=Tarjeta.Estado.ACTIVA, permite_saldo_negativo=False, limite_credito=Decimal('0'),
        )
        a = TarjetaAdmin(Tarjeta, dj_admin.site)
        request = RequestFactory().post('/admin/core/tarjeta/add/')
        request.user = usuario_admin

        a.save_model(request, nueva, _FakeForm(['saldo_actual']), change=False)

        assert not MovimientoTarjeta.objects.filter(tarjeta=nueva).exists()


# ── MovimientoTarjetaAdmin: métodos display ───────────────────────────────────

@pytest.mark.django_db
class TestMovimientoTarjetaAdminDisplay:

    def test_tipo_badge_recarga(self, tarjeta_con_hijo):
        from apps.core.admin import MovimientoTarjetaAdmin
        from apps.core.models import MovimientoTarjeta
        from django.contrib import admin as dj_admin
        mov = MovimientoTarjeta(
            tarjeta=tarjeta_con_hijo, tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=Decimal('10000'), saldo_anterior=Decimal('0'), saldo_resultante=Decimal('10000'),
        )
        a = MovimientoTarjetaAdmin(MovimientoTarjeta, dj_admin.site)
        result = str(a.tipo_badge(mov))
        assert '#28a745' in result  # verde para RECARGA

    def test_monto_display_recarga(self, tarjeta_con_hijo):
        from apps.core.admin import MovimientoTarjetaAdmin
        from apps.core.models import MovimientoTarjeta
        from django.contrib import admin as dj_admin
        mov = MovimientoTarjeta(
            tarjeta=tarjeta_con_hijo, tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=Decimal('10000'), saldo_anterior=Decimal('0'), saldo_resultante=Decimal('10000'),
        )
        a = MovimientoTarjetaAdmin(MovimientoTarjeta, dj_admin.site)
        result = a.monto_display(mov)
        assert result.startswith('+')

    def test_monto_display_consumo(self, tarjeta_con_hijo):
        from apps.core.admin import MovimientoTarjetaAdmin
        from apps.core.models import MovimientoTarjeta
        from django.contrib import admin as dj_admin
        mov = MovimientoTarjeta(
            tarjeta=tarjeta_con_hijo, tipo=MovimientoTarjeta.Tipo.CONSUMO,
            monto=Decimal('5000'), saldo_anterior=Decimal('50000'), saldo_resultante=Decimal('45000'),
        )
        a = MovimientoTarjetaAdmin(MovimientoTarjeta, dj_admin.site)
        result = a.monto_display(mov)
        assert result.startswith('-')


# ── CargaSaldoAdmin: métodos display ─────────────────────────────────────────

@pytest.mark.django_db
class TestCargaSaldoAdminDisplay:

    def test_estado_badge_confirmada(self, tarjeta_con_hijo, cliente):
        from apps.core.admin import CargaSaldoAdmin
        from apps.core.models import CargaSaldo
        from django.contrib import admin as dj_admin
        carga = CargaSaldo(
            tarjeta=tarjeta_con_hijo, cliente_origen=cliente,
            monto_cargado=Decimal('50000'), estado='CONFIRMADA',
        )
        a = CargaSaldoAdmin(CargaSaldo, dj_admin.site)
        result = str(a.estado_badge(carga))
        assert '#28a745' in result

    def test_monto_display(self, tarjeta_con_hijo, cliente):
        from apps.core.admin import CargaSaldoAdmin
        from apps.core.models import CargaSaldo
        from django.contrib import admin as dj_admin
        carga = CargaSaldo(
            tarjeta=tarjeta_con_hijo, cliente_origen=cliente,
            monto_cargado=Decimal('100000'), estado='PENDIENTE',
        )
        a = CargaSaldoAdmin(CargaSaldo, dj_admin.site)
        result = a.monto_cargado_display(carga)
        assert '₲' in result
        assert '100' in result


# ── MedioPagoAdmin ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMedioPagoAdminDisplay:

    def test_requiere_validacion_badge_false(self, medio_pago):
        from apps.core.admin import MedioPagoAdmin
        from apps.core.models import MedioPago
        from django.contrib import admin as dj_admin
        a = MedioPagoAdmin(MedioPago, dj_admin.site)
        result = a.requiere_validacion_badge(medio_pago)
        assert result == '-'

    def test_requiere_validacion_badge_true(self, medio_pago):
        from apps.core.admin import MedioPagoAdmin
        from apps.core.models import MedioPago
        from django.contrib import admin as dj_admin
        medio_pago.requiere_validacion = True
        a = MedioPagoAdmin(MedioPago, dj_admin.site)
        result = str(a.requiere_validacion_badge(medio_pago))
        assert '✓' in result


# ── Changelist con datos reales ───────────────────────────────────────────────

@pytest.mark.django_db
def test_tarjeta_changelist_con_datos(sa_client, tarjeta_con_hijo):
    """El changelist de Tarjeta con un objeto ejercita todos los display methods."""
    resp = sa_client.get('/admin/core/tarjeta/')
    assert resp.status_code == 200
    assert b'ADMIN001' in resp.content

@pytest.mark.django_db
def test_medio_pago_changelist_con_datos(sa_client, medio_pago):
    resp = sa_client.get('/admin/core/mediopago/')
    assert resp.status_code == 200
    assert b'Efectivo Admin Test' in resp.content
