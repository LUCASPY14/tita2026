"""
Tests para gaps de cobertura en notificaciones/services.py — lógica WhatsApp.
Cubre: _whatsapp_cliente (ramas NOTIFICACIONES_ACTIVAS, sin teléfono, excepción),
       NotificacionService._enviar_whatsapp, crear_solicitudes_cobro (rama WA),
       send_push_to_user (sin VAPID_PRIVATE_KEY), procesar_pendientes WHATSAPP.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


@pytest.fixture
def hijo_fixture(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Ana",
        apellido="Lopez",
        cliente_responsable=cliente,
    )


@pytest.fixture
def cliente_con_telefono(db, cliente):
    cliente.telefono = "595981234567"
    cliente.save(update_fields=["telefono"])
    return cliente


@pytest.fixture
def solicitud_whatsapp(db, cliente_con_telefono):
    from apps.notificaciones.models import Notificacion, SolicitudNotificacion
    return SolicitudNotificacion.objects.create(
        cliente=cliente_con_telefono,
        tipo="SALDO_BAJO",
        destino=Notificacion.Destino.WHATSAPP,
        mensaje="Su saldo es bajo.",
    )


@pytest.fixture
def solicitud_sin_telefono(db, cliente):
    from apps.notificaciones.models import Notificacion, SolicitudNotificacion
    return SolicitudNotificacion.objects.create(
        cliente=cliente,
        tipo="SALDO_BAJO",
        destino=Notificacion.Destino.WHATSAPP,
        mensaje="Su saldo es bajo.",
    )


# ── _whatsapp_cliente ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWhatsappClienteHelper:

    def test_no_envía_si_notificaciones_inactivas(self, cliente_con_telefono):
        from apps.notificaciones.services import _whatsapp_cliente
        with patch("apps.notificaciones.services.enviar_whatsapp") as mock_wa:
            with patch("django.conf.settings.NOTIFICACIONES_ACTIVAS", False):
                _whatsapp_cliente(cliente_con_telefono, "hola")
        mock_wa.assert_not_called()

    def test_no_envía_si_sin_telefono(self, cliente):
        from apps.notificaciones.services import _whatsapp_cliente
        cliente.telefono = ""
        with patch("apps.notificaciones.services.enviar_whatsapp") as mock_wa:
            with patch("django.conf.settings.NOTIFICACIONES_ACTIVAS", True):
                _whatsapp_cliente(cliente, "hola")
        mock_wa.assert_not_called()

    def test_silencia_excepcion(self, cliente_con_telefono):
        from apps.notificaciones.services import _whatsapp_cliente
        with patch("apps.notificaciones.services.enviar_whatsapp", side_effect=RuntimeError("error")):
            with patch("django.conf.settings.NOTIFICACIONES_ACTIVAS", True):
                # No debe lanzar excepción
                _whatsapp_cliente(cliente_con_telefono, "hola")

    def test_envía_si_activo_y_tiene_telefono(self, cliente_con_telefono):
        from apps.notificaciones.services import _whatsapp_cliente
        with patch("apps.notificaciones.services.enviar_whatsapp") as mock_wa:
            with patch("django.conf.settings.NOTIFICACIONES_ACTIVAS", True):
                _whatsapp_cliente(cliente_con_telefono, "mensaje test")
        mock_wa.assert_called_once_with("595981234567", "mensaje test")


# ── NotificacionService._enviar_whatsapp ──────────────────────────────────────

@pytest.mark.django_db
class TestEnviarWhatsappService:

    def test_lanza_error_sin_telefono(self, solicitud_sin_telefono):
        from apps.notificaciones.services import NotificacionService
        with pytest.raises(ValueError, match="no tiene teléfono"):
            NotificacionService._enviar_whatsapp(solicitud_sin_telefono)

    def test_llama_enviar_whatsapp_con_telefono(self, solicitud_whatsapp):
        from apps.notificaciones.services import NotificacionService
        with patch("apps.notificaciones.services.enviar_whatsapp") as mock_wa:
            NotificacionService._enviar_whatsapp(solicitud_whatsapp)
        mock_wa.assert_called_once_with("595981234567", "Su saldo es bajo.")

    def test_fallback_email_creado_cuando_waha_falla(self, solicitud_whatsapp):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion
        solicitud_whatsapp.cliente.email = "padre@test.com"
        solicitud_whatsapp.cliente.save(update_fields=["email"])

        with patch("apps.notificaciones.services.enviar_whatsapp", side_effect=RuntimeError("WAHA down")):
            with pytest.raises(RuntimeError):
                NotificacionService._enviar_whatsapp(solicitud_whatsapp)

        assert SolicitudNotificacion.objects.filter(
            cliente=solicitud_whatsapp.cliente,
            destino=Notificacion.Destino.EMAIL,
            tipo=solicitud_whatsapp.tipo,
            mensaje=solicitud_whatsapp.mensaje,
        ).exists()

    def test_fallback_no_crea_solicitud_sin_email(self, solicitud_whatsapp):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import SolicitudNotificacion
        solicitud_whatsapp.cliente.email = ""
        solicitud_whatsapp.cliente.save(update_fields=["email"])

        inicial = SolicitudNotificacion.objects.count()
        with patch("apps.notificaciones.services.enviar_whatsapp", side_effect=RuntimeError("WAHA down")):
            with pytest.raises(RuntimeError):
                NotificacionService._enviar_whatsapp(solicitud_whatsapp)

        assert SolicitudNotificacion.objects.count() == inicial


# ── procesar_pendientes con destino WHATSAPP ──────────────────────────────────

@pytest.mark.django_db
class TestProcesarPendientesWhatsapp:

    def test_whatsapp_exitoso_marca_enviada(self, solicitud_whatsapp):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import SolicitudNotificacion
        with patch("apps.notificaciones.services.enviar_whatsapp"):
            resultado = NotificacionService.procesar_pendientes()
        solicitud_whatsapp.refresh_from_db()
        assert solicitud_whatsapp.estado == SolicitudNotificacion.Estado.ENVIADA
        assert resultado["enviadas"] >= 1

    def test_whatsapp_falla_marca_fallida(self, solicitud_sin_telefono):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import SolicitudNotificacion
        resultado = NotificacionService.procesar_pendientes()
        solicitud_sin_telefono.refresh_from_db()
        assert solicitud_sin_telefono.estado == SolicitudNotificacion.Estado.FALLIDA
        assert resultado["fallidas"] >= 1


# ── crear_solicitudes_cobro — rama WhatsApp ───────────────────────────────────

@pytest.mark.django_db
class TestCrearSolicitudesCobro:

    def test_crea_solicitud_email_para_responsable(self, db, cliente, hijo_fixture, usuario_admin):
        from apps.clientes.models import AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro
        from apps.notificaciones.models import SolicitudNotificacion, Notificacion
        AlumnoResponsable.objects.create(
            hijo=hijo_fixture, cliente=cliente, parentesco="PADRE",
            es_titular=True, orden_cobro=1, agregado_por=usuario_admin,
            recibe_notificaciones=True, activo=True,
        )
        cliente.email = "padre@test.com"
        cliente.activo = True
        cliente.save(update_fields=["email", "activo"])

        n = crear_solicitudes_cobro([hijo_fixture])
        assert n >= 1
        assert SolicitudNotificacion.objects.filter(
            destino=Notificacion.Destino.EMAIL, tipo="COBRO_PENDIENTE"
        ).count() >= 1

    def test_crea_solicitud_wa_si_preferencia_activa(self, db, cliente, hijo_fixture, usuario_admin):
        from apps.clientes.models import AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro
        from apps.notificaciones.models import SolicitudNotificacion, Notificacion, PreferenciaNotificacion
        from apps.usuarios.models import Usuario

        # Crear usuario portal para el cliente (la relación se establece por FK en Usuario)
        usuario_portal = Usuario.objects.create_user(
            email="portal_cobro@test.com", password="x",
            nombre="Portal", apellido="Cobro",
            rol=Usuario.Rol.CLIENTE_WEB,
            cliente=cliente,
        )
        cliente.telefono = "595981111111"
        cliente.email = "padre@test.com"
        cliente.activo = True
        cliente.save(update_fields=["telefono", "email", "activo"])

        PreferenciaNotificacion.objects.create(
            usuario=usuario_portal,
            tipo_notificacion="COBRO_PENDIENTE",
            whatsapp_activo=True,
        )
        AlumnoResponsable.objects.create(
            hijo=hijo_fixture, cliente=cliente, parentesco="PADRE",
            es_titular=True, orden_cobro=1, agregado_por=usuario_admin,
            recibe_notificaciones=True, activo=True,
        )

        n = crear_solicitudes_cobro([hijo_fixture])
        assert SolicitudNotificacion.objects.filter(
            destino=Notificacion.Destino.WHATSAPP
        ).count() >= 1


# ── send_push_to_user ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSendPushToUser:

    def test_sin_vapid_key_retorna_silencioso(self):
        from apps.notificaciones.services import send_push_to_user
        with patch("django.conf.settings.VAPID_PRIVATE_KEY", ""):
            # No debe lanzar excepción
            send_push_to_user(999, "Título", "Cuerpo")

    def test_con_vapid_key_itera_suscripciones(self, db, usuario_admin):
        from apps.notificaciones.services import send_push_to_user
        from apps.notificaciones.models import PushSubscription
        PushSubscription.objects.create(
            usuario=usuario_admin,
            endpoint="https://push.example.com/test",
            p256dh="AAAA",
            auth="BBBB",
            activa=True,
        )
        with patch("apps.notificaciones.services.VAPID_PRIVATE_KEY", "fake_key", create=True):
            with patch("django.conf.settings.VAPID_PRIVATE_KEY", "fake_key"):
                with patch("pywebpush.webpush") as mock_wp:
                    send_push_to_user(usuario_admin.pk, "Test", "Cuerpo test")
