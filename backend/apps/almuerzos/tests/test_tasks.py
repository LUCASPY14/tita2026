"""Tests para apps.almuerzos.tasks — generar_cuentas_mensuales, alertar_cuentas_vencidas."""
import pytest
from decimal import Decimal
from datetime import date, timedelta


@pytest.fixture
def grado_t(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="Task Grado",
        defaults={"nivel": 5, "orden": 5, "activo": True},
    )
    return g


@pytest.fixture
def hijo_t(db, cliente, grado_t):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Task", apellido="Alm",
        cliente_responsable=cliente, grado=grado_t, activo=True,
    )


@pytest.fixture
def plan_t(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Task",
        activo=True,
        precio_mensual=Decimal("200000"),
        dias_semana_incluidos="LUN,MAR,MIE,JUE,VIE",
    )


@pytest.fixture
def suscripcion_activa_t(db, hijo_t, plan_t):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_t,
        plan=plan_t,
        fecha_inicio=date.today() - timedelta(days=30),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


@pytest.fixture
def usuario_portal_t(db, cliente):
    """CLIENTE_WEB vinculado al cliente del conftest."""
    from apps.usuarios.models import Usuario
    user = Usuario.objects.create_user(
        email="tarea_alm@test.com",
        password="test1234",
        nombre="Task",
        apellido="Portal",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente,
    )
    return user


@pytest.fixture
def cuenta_mes_anterior(db, hijo_t):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    hoy = date.today()
    mes_ant = hoy.month - 1 if hoy.month > 1 else 12
    anio_ant = hoy.year if hoy.month > 1 else hoy.year - 1
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_t,
        anio=anio_ant,
        mes=mes_ant,
        cantidad_almuerzos=3,
        monto_total=Decimal("45000"),
        monto_pagado=Decimal("0"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
        estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
    )


# ── generar_cuentas_mensuales ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestGenerarCuentasMensuales:

    def test_sin_suscripciones_retorna_cero(self, db):
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        result = generar_cuentas_mensuales()
        assert result["cuentas_creadas"] == 0

    def test_crea_cuenta_para_suscripcion_activa(self, suscripcion_activa_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        hoy = date.today()
        CuentaAlmuerzoMensual.objects.filter(
            hijo=suscripcion_activa_t.hijo, anio=hoy.year, mes=hoy.month
        ).delete()
        result = generar_cuentas_mensuales()
        assert result["cuentas_creadas"] >= 1
        assert CuentaAlmuerzoMensual.objects.filter(
            hijo=suscripcion_activa_t.hijo, anio=hoy.year, mes=hoy.month
        ).exists()

    def test_no_duplica_cuenta_existente(self, suscripcion_activa_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        hoy = date.today()
        CuentaAlmuerzoMensual.objects.get_or_create(
            hijo=suscripcion_activa_t.hijo, anio=hoy.year, mes=hoy.month,
            defaults={
                "cantidad_almuerzos": 0, "monto_total": 0, "monto_pagado": 0,
                "forma_cobro": CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
                "estado": CuentaAlmuerzoMensual.Estado.PENDIENTE,
            },
        )
        result = generar_cuentas_mensuales()
        assert result["cuentas_creadas"] == 0

    def test_retorna_anio_mes_correcto(self, db):
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        hoy = date.today()
        result = generar_cuentas_mensuales()
        assert result["mes"] == hoy.month
        assert result["anio"] == hoy.year


# ── alertar_cuentas_vencidas ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarCuentasVencidas:

    def test_sin_cuentas_pendientes_retorna_cero(self, db):
        from apps.almuerzos.tasks import alertar_cuentas_vencidas
        result = alertar_cuentas_vencidas()
        assert result == {"notificaciones_creadas": 0}

    def test_cuenta_mes_anterior_sin_usuario_portal_no_crea_notif(self, cuenta_mes_anterior):
        # cliente sin usuario_portal → AttributeError → continue
        from apps.almuerzos.tasks import alertar_cuentas_vencidas
        result = alertar_cuentas_vencidas()
        assert result["notificaciones_creadas"] == 0

    def test_cuenta_mes_anterior_con_usuario_portal_crea_notif(
        self, cuenta_mes_anterior, usuario_portal_t
    ):
        from apps.notificaciones.models import Notificacion
        from apps.almuerzos.tasks import alertar_cuentas_vencidas
        result = alertar_cuentas_vencidas()
        assert result["notificaciones_creadas"] >= 1
        assert Notificacion.objects.filter(tipo=Notificacion.Tipo.ALMUERZO).exists()

    def test_cuenta_del_mes_actual_no_genera_alerta(self, hijo_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import alertar_cuentas_vencidas
        hoy = date.today()
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=hoy.year, mes=hoy.month,
            cantidad_almuerzos=2, monto_total=Decimal("30000"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        result = alertar_cuentas_vencidas()
        assert result["notificaciones_creadas"] == 0
