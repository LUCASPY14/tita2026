"""Tests para apps.clientes.tasks — alertar_saldo_negativo_prolongado,
resumen_mensual_deuda_clientes."""
import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_or_create_sistema_user():
    """Obtiene o crea un usuario ADMIN reutilizable para auditoría de movimientos."""
    from apps.usuarios.models import Usuario
    user, _ = Usuario.objects.get_or_create(
        email="sistema_test@test.com",
        defaults={
            "nombre": "Sistema",
            "apellido": "Test",
            "rol": Usuario.Rol.ADMIN,
            "is_staff": True,
        },
    )
    return user


def _mov(cliente, monto, dias_atras=0, tipo="DEBITO"):
    """
    Crea un movimiento de CuentaCorrienteCliente backdated.
    El modelo computa saldo_resultante automáticamente en save().
    - DEBITO: saldo_resultante = saldo_anterior + monto (aumenta deuda)
    - CREDITO: saldo_resultante = saldo_anterior - monto (reduce deuda)
    """
    from apps.clientes.models import CuentaCorrienteCliente
    fecha = timezone.now() - timedelta(days=dias_atras)
    return CuentaCorrienteCliente.objects.create(
        cliente=cliente,
        fecha=fecha,
        tipo=tipo,
        monto=Decimal(str(abs(monto))),
        creado_por=_get_or_create_sistema_user(),
    )


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def admin(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="admin_task@test.com",
        password="test1234",
        nombre="Admin",
        apellido="Task",
        rol=Usuario.Rol.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def cliente_con_deuda_antigua(db, tipo_cliente, lista_precio):
    """Cliente activo con deuda (saldo > 0) y último movimiento hace 10 días (> umbral de 7)."""
    from apps.clientes.models import Cliente
    c = Cliente.objects.create(
        nombres="Deuda", apellidos="Antigua",
        ruc_ci="DEUDA001",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )
    _mov(c, monto=50000, dias_atras=10)
    return c


@pytest.fixture
def cliente_con_deuda_reciente(db, tipo_cliente, lista_precio):
    """Cliente activo con deuda (saldo > 0) pero movimiento hace solo 3 días (< umbral)."""
    from apps.clientes.models import Cliente
    c = Cliente.objects.create(
        nombres="Deuda", apellidos="Reciente",
        ruc_ci="DEUDA002",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )
    _mov(c, monto=30000, dias_atras=3)
    return c


@pytest.fixture
def cliente_sin_deuda(db, tipo_cliente, lista_precio):
    """Cliente activo sin saldo pendiente (paga todo)."""
    from apps.clientes.models import Cliente
    c = Cliente.objects.create(
        nombres="Sin", apellidos="Deuda",
        ruc_ci="NODEUDA01",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )
    # DEBITO 10000, luego CREDITO 10000 → saldo_resultante final = 0
    _mov(c, monto=10000, dias_atras=20)
    _mov(c, monto=10000, dias_atras=15, tipo="CREDITO")
    return c


@pytest.fixture
def cliente_inactivo_con_deuda(db, tipo_cliente, lista_precio):
    """Cliente inactivo — no debe ser alertado aunque tenga deuda antigua."""
    from apps.clientes.models import Cliente
    c = Cliente.objects.create(
        nombres="Inactivo", apellidos="Deuda",
        ruc_ci="INACT001",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
        activo=False,
    )
    _mov(c, monto=20000, dias_atras=10)
    return c


@pytest.fixture
def cliente_con_portal(db, tipo_cliente, lista_precio):
    """Cliente activo con deuda antigua Y con usuario CLIENTE_WEB vinculado."""
    from apps.clientes.models import Cliente
    from apps.usuarios.models import Usuario
    c = Cliente.objects.create(
        nombres="Portal", apellidos="Deuda",
        ruc_ci="PORTAL01",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )
    _mov(c, monto=75000, dias_atras=8)
    Usuario.objects.create_user(
        email="portal_deuda@test.com",
        password="test1234",
        nombre="Portal",
        apellido="Deuda",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=c,
    )
    return c


# ── alertar_saldo_negativo_prolongado ──────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarSaldoNegativoProlongado:

    def test_sin_clientes_retorna_cero(self, db):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        result = alertar_saldo_negativo_prolongado()
        assert result == {"clientes_alertados": 0, "dias_umbral": 7}

    def test_cliente_sin_movimientos_no_alerta(self, db, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        Cliente.objects.create(
            nombres="Sin", apellidos="Movimientos",
            ruc_ci="SINMOV01",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0

    def test_deuda_antigua_genera_alerta(self, cliente_con_deuda_antigua, admin):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente"):
            result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 1

    def test_deuda_reciente_no_genera_alerta(self, cliente_con_deuda_reciente):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0

    def test_cliente_sin_deuda_no_genera_alerta(self, cliente_sin_deuda):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0

    def test_cliente_inactivo_no_genera_alerta(self, cliente_inactivo_con_deuda):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0

    def test_notificacion_admin_creada(self, cliente_con_deuda_antigua, admin):
        from apps.notificaciones.models import Notificacion
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente"):
            alertar_saldo_negativo_prolongado()
        assert Notificacion.objects.filter(
            usuario=admin,
            tipo=Notificacion.Tipo.SISTEMA,
        ).exists()

    def test_notificacion_portal_creada(self, cliente_con_portal, admin):
        from apps.notificaciones.models import Notificacion
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente"):
            alertar_saldo_negativo_prolongado()
        usuario_portal = cliente_con_portal.usuario_portal
        assert Notificacion.objects.filter(
            usuario=usuario_portal,
            tipo=Notificacion.Tipo.VENTA_DEUDA,
        ).exists()

    def test_whatsapp_llamado_por_cliente_alertado(self, cliente_con_deuda_antigua, admin):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente") as mock_wa:
            alertar_saldo_negativo_prolongado()
        mock_wa.assert_called_once()
        assert mock_wa.call_args[0][0] == cliente_con_deuda_antigua

    def test_whatsapp_error_no_interrumpe_tarea(self, cliente_con_deuda_antigua, admin):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente", side_effect=Exception("WAHA down")):
            result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 1

    def test_multiple_clientes_solo_con_deuda_antigua(
        self, cliente_con_deuda_antigua, cliente_con_deuda_reciente,
        cliente_sin_deuda, cliente_inactivo_con_deuda, admin,
    ):
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        with patch("apps.notificaciones.services._whatsapp_cliente"):
            result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 1

    def test_deuda_siete_dias_exactos_no_alerta(self, db, tipo_cliente, lista_precio):
        """
        Movimiento creado now()-7days tiene hora > 00:00, así que su timestamp
        supera el corte fecha_corte (hoy-7 days interpretado como medianoche).
        → NO alerta. El umbral efectivo son 8+ días calendario.
        """
        from apps.clientes.models import Cliente
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        c = Cliente.objects.create(
            nombres="Umbral", apellidos="Exacto",
            ruc_ci="UMBRAL01",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        _mov(c, monto=10000, dias_atras=7)
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0

    def test_deuda_seis_dias_no_alerta(self, db, tipo_cliente, lista_precio):
        """Movimiento con fecha == hoy - 6 days > fecha_corte → no alerta."""
        from apps.clientes.models import Cliente
        from apps.clientes.tasks import alertar_saldo_negativo_prolongado
        c = Cliente.objects.create(
            nombres="Umbral", apellidos="Seis",
            ruc_ci="UMBRAL02",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        _mov(c, monto=10000, dias_atras=6)
        result = alertar_saldo_negativo_prolongado()
        assert result["clientes_alertados"] == 0


# ── resumen_mensual_deuda_clientes ─────────────────────────────────────────────

@pytest.mark.django_db
class TestResumenMensualDeudaClientes:

    def test_sin_clientes_retorna_cero(self, db):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        result = resumen_mensual_deuda_clientes()
        assert result == {"clientes_con_deuda": 0}

    def test_cliente_sin_deuda_no_incluido(self, cliente_sin_deuda, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = []
        result = resumen_mensual_deuda_clientes()
        assert result == {"clientes_con_deuda": 0}

    def test_cliente_inactivo_no_incluido(self, cliente_inactivo_con_deuda, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = []
        result = resumen_mensual_deuda_clientes()
        assert result == {"clientes_con_deuda": 0}

    def test_cliente_con_deuda_incluido(self, cliente_con_deuda_antigua, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = []
        result = resumen_mensual_deuda_clientes()
        assert result["clientes_con_deuda"] == 1
        assert result["monto_total"] == 50000

    def test_emails_enviados_a_cada_admin(self, cliente_con_deuda_antigua, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = [
            ("Admin 1", "admin1@test.com"),
            ("Admin 2", "admin2@test.com"),
        ]
        with patch("apps.notificaciones.services.EmailService") as mock_email:
            mock_email.enviar_simple.return_value = None
            result = resumen_mensual_deuda_clientes()
        assert result["emails_enviados"] == 2
        assert mock_email.enviar_simple.call_count == 2

    def test_sin_admins_configurados_no_falla(self, cliente_con_deuda_antigua, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = []
        result = resumen_mensual_deuda_clientes()
        assert result["emails_enviados"] == 0
        assert result["clientes_con_deuda"] == 1

    def test_error_en_email_no_interrumpe_loop(self, cliente_con_deuda_antigua, settings):
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = [
            ("Admin 1", "ok@test.com"),
            ("Admin 2", "fail@test.com"),
        ]
        call_count = 0

        def enviar_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("SMTP error")

        with patch("apps.notificaciones.services.EmailService") as mock_email:
            mock_email.enviar_simple.side_effect = enviar_side_effect
            result = resumen_mensual_deuda_clientes()
        assert result["emails_enviados"] == 1

    def test_monto_total_suma_correctamente(self, db, tipo_cliente, lista_precio, settings):
        from apps.clientes.models import Cliente
        from apps.clientes.tasks import resumen_mensual_deuda_clientes
        settings.ADMINS = []
        c1 = Cliente.objects.create(
            nombres="A", apellidos="Uno",
            ruc_ci="SUM001",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        c2 = Cliente.objects.create(
            nombres="B", apellidos="Dos",
            ruc_ci="SUM002",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        _mov(c1, monto=30000)
        _mov(c2, monto=70000)
        result = resumen_mensual_deuda_clientes()
        assert result["clientes_con_deuda"] == 2
        assert result["monto_total"] == 100000
