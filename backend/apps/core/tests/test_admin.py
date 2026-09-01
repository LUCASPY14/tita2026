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
    "/admin/core/consumotarjeta/",
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
