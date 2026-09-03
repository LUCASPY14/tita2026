"""Tests para apps.notificaciones.tasks — generar_alertas_saldo_bajo,
limpiar_notificaciones_antiguas, enviar_emails_pendientes,
procesar_solicitudes_pendientes."""
import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone


@pytest.fixture
def cliente_portal(db, tipo_cliente, lista_precio):
    """Cliente con usuario CLIENTE_WEB vinculado."""
    from apps.clientes.models import Cliente
    from apps.usuarios.models import Usuario
    cliente = Cliente.objects.create(
        nombres="Portal", apellidos="Task",
        ruc_ci="NOTIF001",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )
    usuario = Usuario.objects.create_user(
        email="notif_task@test.com",
        password="test1234",
        nombre="Portal",
        apellido="Task",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente,
    )
    return cliente


@pytest.fixture
def hijo_notif(db, cliente_portal):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Notif", apellido="Task",
        cliente_responsable=cliente_portal, activo=True,
    )


@pytest.fixture
def tarjeta_en_alerta(db, hijo_notif):
    """Tarjeta ACTIVA con saldo_actual ≤ saldo_alerta."""
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALRT-TASK01",
        hijo=hijo_notif,
        saldo_actual=Decimal("5000"),
        saldo_alerta=Decimal("10000"),
        notificar_saldo_bajo=True,
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def tarjeta_sin_alerta(db, hijo_notif):
    """Tarjeta ACTIVA con saldo por encima del umbral."""
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALRT-TASK02",
        hijo=hijo_notif,
        saldo_actual=Decimal("50000"),
        saldo_alerta=Decimal("10000"),
        notificar_saldo_bajo=True,
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def notif_leida_antigua(db, usuario_cajero):
    from apps.notificaciones.models import Notificacion
    notif = Notificacion.objects.create(
        usuario=usuario_cajero,
        tipo=Notificacion.Tipo.SISTEMA,
        titulo="Vieja",
        mensaje="Msg",
        leida=True,
        destino=Notificacion.Destino.SISTEMA,
    )
    Notificacion.objects.filter(pk=notif.pk).update(
        fecha_creacion=timezone.now() - timedelta(days=91)
    )
    return notif


@pytest.fixture
def notif_email_pendiente(db, usuario_cajero):
    from apps.notificaciones.models import Notificacion
    return Notificacion.objects.create(
        usuario=usuario_cajero,
        tipo=Notificacion.Tipo.SISTEMA,
        titulo="Email pendiente",
        mensaje="Cuerpo del email",
        leida=False,
        destino=Notificacion.Destino.EMAIL,
    )


# ── generar_alertas_saldo_bajo ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestGenerarAlertasSaldoBajo:

    def test_sin_tarjetas_retorna_cero(self, db):
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        result = generar_alertas_saldo_bajo()
        assert result == {"notificaciones_creadas": 0}

    def test_tarjeta_en_alerta_con_usuario_portal_crea_notif(self, tarjeta_en_alerta):
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 1
        assert Notificacion.objects.filter(tipo=Notificacion.Tipo.SALDO_BAJO).exists()

    def test_tarjeta_sin_alerta_no_crea_notif(self, tarjeta_sin_alerta):
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 0

    def test_tarjeta_notificada_recientemente_no_duplica(self, tarjeta_en_alerta):
        from apps.core.models import Tarjeta
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        # Simular que ya fue notificada hace 1 hora
        Tarjeta.objects.filter(pk=tarjeta_en_alerta.pk).update(
            ultima_notificacion_saldo=timezone.now() - timedelta(hours=1)
        )
        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 0

    def test_tarjeta_notificada_hace_25h_vuelve_a_notificar(self, tarjeta_en_alerta):
        from apps.core.models import Tarjeta
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        Tarjeta.objects.filter(pk=tarjeta_en_alerta.pk).update(
            ultima_notificacion_saldo=timezone.now() - timedelta(hours=25)
        )
        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 1

    def test_tarjeta_sin_usuario_portal_no_crea_notif(self, db, cliente, hijo_t=None):
        # hijo de cliente sin CLIENTE_WEB vinculado
        from apps.clientes.models import Hijo
        from apps.core.models import Tarjeta
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        hijo = Hijo.objects.create(
            nombre="Sin", apellido="Portal",
            cliente_responsable=cliente, activo=True,
        )
        Tarjeta.objects.create(
            nro_tarjeta="SIN-PORTAL01",
            hijo=hijo,
            saldo_actual=Decimal("500"),
            saldo_alerta=Decimal("1000"),
            notificar_saldo_bajo=True,
            estado=Tarjeta.Estado.ACTIVA,
        )
        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 0


# ── limpiar_notificaciones_antiguas ───────────────────────────────────────────

@pytest.mark.django_db
class TestLimpiarNotificacionesAntiguas:

    def test_sin_notificaciones_retorna_cero(self, db):
        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas
        result = limpiar_notificaciones_antiguas()
        assert result == {"eliminadas": 0}

    def test_notif_leida_antigua_se_elimina(self, notif_leida_antigua):
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas
        pk = notif_leida_antigua.pk
        result = limpiar_notificaciones_antiguas()
        assert result["eliminadas"] >= 1
        assert not Notificacion.objects.filter(pk=pk).exists()

    def test_notif_reciente_no_se_elimina(self, usuario_cajero):
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas
        Notificacion.objects.create(
            usuario=usuario_cajero,
            tipo=Notificacion.Tipo.SISTEMA,
            titulo="Reciente",
            mensaje="Msg",
            leida=True,
            destino=Notificacion.Destino.SISTEMA,
        )
        result = limpiar_notificaciones_antiguas()
        assert result["eliminadas"] == 0

    def test_notif_no_leida_no_se_elimina(self, notif_leida_antigua):
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.tasks import limpiar_notificaciones_antiguas
        Notificacion.objects.filter(pk=notif_leida_antigua.pk).update(leida=False)
        result = limpiar_notificaciones_antiguas()
        assert result["eliminadas"] == 0


# ── enviar_emails_pendientes ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnviarEmailsPendientes:

    def test_sin_pendientes_retorna_cero(self, db):
        from apps.notificaciones.tasks import enviar_emails_pendientes
        result = enviar_emails_pendientes()
        assert result == {"enviados": 0, "errores": 0, "descartados": 0}

    def test_notif_email_enviada_y_marcada_leida(self, notif_email_pendiente):
        from apps.notificaciones.tasks import enviar_emails_pendientes
        with patch("apps.notificaciones.services.EmailService.enviar_simple") as mock_send:
            mock_send.return_value = None
            result = enviar_emails_pendientes()
        assert result["enviados"] == 1
        assert result["errores"] == 0
        notif_email_pendiente.refresh_from_db()
        assert notif_email_pendiente.leida is True
        assert mock_send.called

    def test_error_en_envio_incrementa_intentos_no_marca_leida(self, notif_email_pendiente):
        # Fallo: queda leida=False para reintentar; solo se incrementa email_intentos
        from apps.notificaciones.tasks import enviar_emails_pendientes
        with patch("apps.notificaciones.services.EmailService.enviar_simple") as mock_send:
            mock_send.side_effect = Exception("SMTP failure")
            result = enviar_emails_pendientes()
        assert result["errores"] == 1
        assert result["enviados"] == 0
        notif_email_pendiente.refresh_from_db()
        assert notif_email_pendiente.leida is False
        assert notif_email_pendiente.email_intentos == 1

    def test_notif_sin_email_usuario_cuenta_como_error(self, db, usuario_cajero):
        from apps.notificaciones.models import Notificacion
        from apps.usuarios.models import Usuario
        from apps.notificaciones.tasks import enviar_emails_pendientes
        # Usuario sin email (borramos el email)
        Usuario.objects.filter(pk=usuario_cajero.pk).update(email="")
        Notificacion.objects.create(
            usuario=usuario_cajero,
            tipo=Notificacion.Tipo.SISTEMA,
            titulo="Sin email",
            mensaje="Msg",
            leida=False,
            destino=Notificacion.Destino.EMAIL,
        )
        with patch("apps.notificaciones.services.EmailService.enviar_simple"):
            result = enviar_emails_pendientes()
        assert result["errores"] == 1

    def test_descarta_notif_tras_max_intentos(self, notif_email_pendiente):
        """Notificación con email_intentos >= MAX_EMAIL_INTENTOS se descarta."""
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.tasks import enviar_emails_pendientes, MAX_EMAIL_INTENTOS
        Notificacion.objects.filter(pk=notif_email_pendiente.pk).update(
            email_intentos=MAX_EMAIL_INTENTOS,
        )
        result = enviar_emails_pendientes()
        assert result["descartados"] == 1
        assert result["enviados"] == 0
        notif_email_pendiente.refresh_from_db()
        assert notif_email_pendiente.leida is True


# ── generar_alertas_saldo_bajo — ramas adicionales ────────────────────────────

@pytest.mark.django_db
class TestGenerarAlertasSaldoBajoRamas:

    def test_whatsapp_pref_activa_y_telefono_crea_solicitud(self, tarjeta_en_alerta, cliente_portal):
        """Con PreferenciaNotificacion whatsapp_activo=True y telefono, crea SolicitudNotificacion."""
        from apps.clientes.models import Cliente
        from apps.notificaciones.models import PreferenciaNotificacion, SolicitudNotificacion
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo

        usuario = cliente_portal.usuario_portal
        PreferenciaNotificacion.objects.create(
            usuario=usuario,
            tipo_notificacion="SALDO_BAJO",
            whatsapp_activo=True,
        )
        Cliente.objects.filter(pk=cliente_portal.pk).update(telefono="0981123456")

        result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] >= 1
        assert SolicitudNotificacion.objects.filter(tipo="SALDO_BAJO").exists()

    def test_usuario_portal_none_no_crea_notif(self, db, tipo_cliente, lista_precio):
        """usuario_portal retorna None (select_related cache) → rama `if not usuario` cubre línea 45."""
        from apps.clientes.models import Cliente, Hijo
        from apps.core.models import Tarjeta
        from apps.notificaciones.tasks import generar_alertas_saldo_bajo
        from unittest.mock import patch as _patch

        # Tarjeta real en alerta, pero mockeamos el acceso a usuario_portal
        # para que devuelva None sin lanzar AttributeError
        cliente_sin_user = Cliente.objects.create(
            nombres="Sin", apellidos="Usuario",
            ruc_ci="SINUSR002",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        hijo = Hijo.objects.create(
            nombre="Sin", apellido="Usuario",
            cliente_responsable=cliente_sin_user, activo=True,
        )
        Tarjeta.objects.create(
            nro_tarjeta="SINUSR002",
            hijo=hijo,
            saldo_actual=Decimal("3000"),
            saldo_alerta=Decimal("5000"),
            notificar_saldo_bajo=True,
            estado=Tarjeta.Estado.ACTIVA,
        )
        # Forzamos que la propiedad reversa devuelva None (cubre `if not usuario:`)
        with _patch(
            "apps.clientes.models.Cliente.usuario_portal",
            new=property(lambda self: None),
        ):
            result = generar_alertas_saldo_bajo()
        assert result["notificaciones_creadas"] == 0


# ── procesar_solicitudes_pendientes ─────────────────────────────────────────────

@pytest.mark.django_db
class TestProcesarSolicitudesPendientes:

    def test_sin_solicitudes_retorna_cero(self, db):
        from apps.notificaciones.tasks import procesar_solicitudes_pendientes
        result = procesar_solicitudes_pendientes()
        assert result["enviadas"] == 0
        assert result["fallidas"] == 0

    def test_solicitud_pendiente_se_procesa_y_marca_enviada(self, cliente_portal):
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion
        from apps.notificaciones.tasks import procesar_solicitudes_pendientes

        solicitud = SolicitudNotificacion.objects.create(
            cliente=cliente_portal,
            tipo=Notificacion.Tipo.SALDO_BAJO,
            mensaje="Saldo bajo en tarjeta.",
            destino=Notificacion.Destino.SISTEMA,
        )

        result = procesar_solicitudes_pendientes()

        assert result["enviadas"] == 1
        solicitud.refresh_from_db()
        assert solicitud.estado == SolicitudNotificacion.Estado.ENVIADA
        assert Notificacion.objects.filter(usuario=cliente_portal.usuario_portal).exists()
