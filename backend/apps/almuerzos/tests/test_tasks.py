"""Tests para apps.almuerzos.tasks — cerrar_cuentas_mes_anterior, avisar_deuda_almuerzo."""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch
from freezegun import freeze_time


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
    """Resumen mensual informativo — ya no cierra ni actualiza ninguna
    CuentaAlmuerzoMensual, solo agrega RegistroConsumoAlmuerzo y avisa."""

    def test_sin_consumos_retorna_cero(self, db):
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        result = cerrar_cuentas_mes_anterior()
        assert result["enviados"] == 0

    def test_retorna_anio_mes_del_mes_anterior(self, db):
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        result = cerrar_cuentas_mes_anterior()
        assert result["mes"] == mes_ant
        assert result["anio"] == anio_ant

    @patch("apps.notificaciones.services.whatsapp_cliente")
    def test_envia_whatsapp_por_hijo_con_consumo(self, mock_wa, hijo_t, usuario_admin):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t, fecha_consumo=date(anio_ant, mes_ant, 1),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        result = cerrar_cuentas_mes_anterior()
        assert result["enviados"] == 1
        mock_wa.assert_called_once()
        mensaje = mock_wa.call_args[0][1]
        assert "Resumen de almuerzos" in mensaje
        assert "15,000" in mensaje

    def test_ignora_registros_que_no_cobraron(self, hijo_t, usuario_admin):
        # El "repite" del mismo día (ya_cobrado=False) no debe contarse.
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t, fecha_consumo=date(anio_ant, mes_ant, 1),
            costo_almuerzo=Decimal("0"), ya_cobrado=False,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        result = cerrar_cuentas_mes_anterior()
        assert result["enviados"] == 0

    def test_ignora_consumos_de_otros_meses(self, hijo_t, usuario_admin):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        # Mes actual (congelado en 2026-07-15), no el mes anterior
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t, fecha_consumo=date(2026, 7, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        result = cerrar_cuentas_mes_anterior()
        assert result["enviados"] == 0

    def test_suma_todos_los_consumos_del_hijo_en_el_mes(self, hijo_t, usuario_admin):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        for dia in (1, 2, 3):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_t, fecha_consumo=date(anio_ant, mes_ant, dia),
                costo_almuerzo=Decimal("15000"), ya_cobrado=True,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
                registrado_por=usuario_admin,
            )
        result = cerrar_cuentas_mes_anterior()
        # 1 sola familia notificada, aunque haya comido 3 veces
        assert result["enviados"] == 1

    @patch("apps.notificaciones.services.EmailService.enviar_simple")
    def test_envia_email_al_admin_tras_cierre(self, mock_email, hijo_t, usuario_admin):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.tasks import cerrar_cuentas_mes_anterior
        anio_ant, mes_ant = _mes_anterior()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_t, fecha_consumo=date(anio_ant, mes_ant, 1),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            registrado_por=usuario_admin,
        )
        with patch("django.conf.settings.ADMINS", [("Admin", "admin@test.com")]):
            cerrar_cuentas_mes_anterior()
        mock_email.assert_called_once()
        kwargs = mock_email.call_args[1]
        assert kwargs["destinatario_email"] == "admin@test.com"
        assert "Resumen mensual" in kwargs["asunto"]
