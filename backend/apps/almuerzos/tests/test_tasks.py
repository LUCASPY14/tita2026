"""Tests para apps.almuerzos.tasks — cerrar_cuentas_mes_anterior, generar_cuentas_mensuales, avisar_deuda_almuerzo."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch
from freezegun import freeze_time

# Fecha congelada para TestGenerarCuentasMensuales — la fixture
# suscripcion_activa_t (nivel de módulo) también la usa, ver ahí por qué.
_HOY_CONGELADO = date(2026, 7, 15)


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
    # fecha_inicio relativa a _HOY_CONGELADO (no a date.today() real): esta
    # fixture es de nivel de módulo, no hereda el @freeze_time de la clase
    # que la consume — si usara date.today() real, con el paso de los meses
    # "hoy - 30 días" termina cayendo después de _HOY_CONGELADO y la
    # suscripción queda excluida (fecha_inicio__lte=ultimo_dia falla).
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_t,
        plan=plan_t,
        fecha_inicio=_HOY_CONGELADO - timedelta(days=30),
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


# ── generar_cuentas_mensuales ──────────────────────────────────────────────────

@freeze_time(_HOY_CONGELADO.isoformat())
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


# ── avisar_deuda_almuerzo ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestAvisarDeudaAlmuerzo:

    def test_sin_deudores_retorna_cero(self, db):
        from apps.almuerzos.tasks import avisar_deuda_almuerzo
        result = avisar_deuda_almuerzo()
        assert result == {"notificaciones_creadas": 0}

    def test_saldo_negativo_sin_usuario_portal_no_crea_notif(self, hijo_t):
        # cliente sin usuario_portal → AttributeError → continue
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import avisar_deuda_almuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("-15000"))
        result = avisar_deuda_almuerzo()
        assert result["notificaciones_creadas"] == 0

    def test_saldo_negativo_con_usuario_portal_crea_notif(
        self, hijo_t, usuario_portal_t
    ):
        from apps.notificaciones.models import Notificacion
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import avisar_deuda_almuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("-15000"))
        result = avisar_deuda_almuerzo()
        assert result["notificaciones_creadas"] >= 1
        assert Notificacion.objects.filter(tipo=Notificacion.Tipo.ALMUERZO).exists()

    def test_saldo_positivo_no_genera_alerta(self, hijo_t):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import avisar_deuda_almuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("30000"))
        result = avisar_deuda_almuerzo()
        assert result["notificaciones_creadas"] == 0


# ── alertar_saldo_almuerzo_negativo ─────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarSaldoAlmuerzoNegativo:

    def test_sin_deudores_retorna_cero(self, db):
        from apps.almuerzos.tasks import alertar_saldo_almuerzo_negativo
        result = alertar_saldo_almuerzo_negativo()
        assert result == {"alertados": 0}

    def test_deuda_bajo_el_umbral_no_alerta(self, hijo_t):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import alertar_saldo_almuerzo_negativo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("-50000"))
        result = alertar_saldo_almuerzo_negativo()
        assert result["alertados"] == 0

    def test_deuda_supera_el_umbral_alerta_a_admins(self, hijo_t, usuario_admin):
        from apps.notificaciones.models import Notificacion
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import alertar_saldo_almuerzo_negativo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("-150000"))
        result = alertar_saldo_almuerzo_negativo()
        assert result["alertados"] == 1
        notif = Notificacion.objects.get(usuario=usuario_admin)
        assert "Task Alm" in notif.titulo
        assert "150,000" in notif.mensaje

    def test_deuda_justo_en_el_umbral_alerta(self, hijo_t, usuario_admin):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import alertar_saldo_almuerzo_negativo, _MONTO_ALERTA_SALDO_ALMUERZO
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal(-_MONTO_ALERTA_SALDO_ALMUERZO))
        result = alertar_saldo_almuerzo_negativo()
        assert result["alertados"] == 1

    def test_no_notifica_si_no_hay_admins_activos(self, hijo_t):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.almuerzos.tasks import alertar_saldo_almuerzo_negativo
        SaldoAlmuerzo.objects.create(hijo=hijo_t, saldo_actual=Decimal("-150000"))
        result = alertar_saldo_almuerzo_negativo()
        assert result["alertados"] == 1  # el alumno cuenta igual, aunque no haya a quién notificar


# ── cerrar_cuentas_mes_anterior ───────────────────────────────────────────────

def _mes_anterior():
    hoy = date.today()
    mes_ant = hoy.month - 1 if hoy.month > 1 else 12
    anio_ant = hoy.year if hoy.month > 1 else hoy.year - 1
    return anio_ant, mes_ant


@freeze_time("2026-07-15")
@pytest.mark.django_db
class TestCerrarCuentasMesAnterior:

    def test_sin_cuentas_retorna_ceros(self, db):
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        result = cerrar_cuentas_mes_anterior()
        assert result["actualizadas"] == 0
        assert result["anuladas"] == 0

    def test_retorna_anio_mes_del_mes_anterior(self, db):
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        result = cerrar_cuentas_mes_anterior()
        assert result["mes"] == mes_ant
        assert result["anio"] == anio_ant

    def test_anula_cuenta_sin_consumos(self, hijo_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        cuenta = CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        result = cerrar_cuentas_mes_anterior()
        cuenta.refresh_from_db()
        assert cuenta.estado == CuentaAlmuerzoMensual.Estado.ANULADO
        assert result["anuladas"] == 1
        assert result["actualizadas"] == 0

    def test_actualiza_cuenta_con_registros_de_consumo(self, hijo_t, usuario_admin):
        """
        El task encuentra registros ya_cobrado=True/marcado_en_cuenta=False
        y los procesa (actualizadas=1). El trigger (migration 0014) sobreescribe
        cantidad_almuerzos/monto_total al final de la transacción, por lo que
        el valor definitivo en DB es el del trigger. Se verifica el marcado de
        los registros y el return del task.
        """
        from apps.almuerzos.models import CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        fecha_consumo = date(anio_ant, mes_ant, 1)
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        registro = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t,
            fecha_consumo=fecha_consumo,
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            marcado_en_cuenta=False,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        result = cerrar_cuentas_mes_anterior()
        # El task procesó la cuenta (no la anuló porque hay 1 registro nuevo)
        assert result["actualizadas"] == 1
        assert result["anuladas"] == 0
        # El registro quedó marcado como incluido en la cuenta
        registro.refresh_from_db()
        assert registro.marcado_en_cuenta is True

    def test_registros_quedan_marcados_en_cuenta(self, hijo_t, usuario_admin):
        from apps.almuerzos.models import CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        fecha_consumo = date(anio_ant, mes_ant, 1)
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        registro = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t,
            fecha_consumo=fecha_consumo,
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            marcado_en_cuenta=False,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        cerrar_cuentas_mes_anterior()
        registro.refresh_from_db()
        assert registro.marcado_en_cuenta is True

    def test_ignora_cuentas_ya_anuladas(self, hijo_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.ANULADO,
        )
        result = cerrar_cuentas_mes_anterior()
        assert result["actualizadas"] == 0
        assert result["anuladas"] == 0

    def test_no_procesa_registros_ya_marcados(self, hijo_t, usuario_admin):
        """
        Solo los registros marcado_en_cuenta=False se incluyen en el cierre.
        Con 1 registro ya marcado y 1 nuevo, el task cuenta solo el nuevo (actualizadas=1)
        y no re-procesa el que ya estaba marcado.
        """
        from apps.almuerzos.models import CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        fecha_consumo = date(anio_ant, mes_ant, 1)
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        # Registro ya procesado anteriormente — no debe contarse de nuevo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t,
            fecha_consumo=fecha_consumo,
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            marcado_en_cuenta=True,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        # Registro nuevo — sí debe contarse
        registro_nuevo = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t,
            fecha_consumo=fecha_consumo,
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            marcado_en_cuenta=False,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        result = cerrar_cuentas_mes_anterior()
        # Solo el registro nuevo se contó → actualizadas=1, no anulada
        assert result["actualizadas"] == 1
        assert result["anuladas"] == 0
        registro_nuevo.refresh_from_db()
        assert registro_nuevo.marcado_en_cuenta is True

    @patch("apps.notificaciones.services.EmailService.enviar_simple")
    def test_envia_email_al_admin_tras_cierre(self, mock_email, hijo_t):
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_t, anio=anio_ant, mes=mes_ant,
            cantidad_almuerzos=0, monto_total=Decimal("0"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
            estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
        )
        with patch("django.conf.settings.ADMINS", [("Admin", "admin@test.com")]):
            cerrar_cuentas_mes_anterior()
        mock_email.assert_called_once()
        kwargs = mock_email.call_args[1]
        assert kwargs["destinatario_email"] == "admin@test.com"
        assert "Cierre mensual" in kwargs["asunto"]
