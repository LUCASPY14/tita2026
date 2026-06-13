"""
Tests para NotificacionService, EmailService, crear_solicitudes_cobro
y push_ws_notificacion.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def cliente_con_usuario(db, tipo_cliente, lista_precio):
    from decimal import Decimal
    from apps.clientes.models import Cliente
    from apps.usuarios.models import Usuario

    usuario = Usuario.objects.create_user(
        email="portal_notif@test.com",
        password="test1234",
        nombre="Padre",
        apellido="Test",
        rol=Usuario.Rol.CLIENTE_WEB,
    )
    cliente = Cliente.objects.create(
        nombres="Padre",
        apellidos="Test",
        ruc_ci="8888888",
        email="portal_notif@test.com",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
        limite_credito=Decimal("0"),
    )
    usuario.cliente = cliente
    usuario.save(update_fields=["cliente"])
    return cliente


@pytest.fixture
def cliente_sin_usuario(db, tipo_cliente, lista_precio):
    from decimal import Decimal
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="Sin",
        apellidos="Usuario",
        ruc_ci="7777777",
        email="singusuario@test.com",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
        limite_credito=Decimal("0"),
    )


@pytest.fixture
def solicitud_sistema(db, cliente_con_usuario):
    from apps.notificaciones.models import Notificacion, SolicitudNotificacion
    return SolicitudNotificacion.objects.create(
        cliente=cliente_con_usuario,
        tipo=Notificacion.Tipo.SALDO_BAJO,
        mensaje="Saldo bajo en tarjeta DEMO-001.",
        destino=Notificacion.Destino.SISTEMA,
    )


@pytest.fixture
def solicitud_email(db, cliente_con_usuario):
    from apps.notificaciones.models import Notificacion, SolicitudNotificacion
    return SolicitudNotificacion.objects.create(
        cliente=cliente_con_usuario,
        tipo="COBRO_PENDIENTE",
        mensaje="Tiene saldo pendiente en la cantina.",
        destino=Notificacion.Destino.EMAIL,
    )


# ── NotificacionService.procesar_pendientes ───────────────────────────────────

@pytest.mark.django_db
class TestProcesarPendientes:

    def test_sistema_crea_notificacion_y_marca_enviada(self, solicitud_sistema):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion

        resultado = NotificacionService.procesar_pendientes()

        assert resultado["enviadas"] == 1
        assert resultado["fallidas"] == 0
        solicitud_sistema.refresh_from_db()
        assert solicitud_sistema.estado == SolicitudNotificacion.Estado.ENVIADA
        assert Notificacion.objects.filter(
            usuario=solicitud_sistema.cliente.usuario_portal
        ).exists()

    def test_email_envia_y_registra_enviado(self, solicitud_email):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import SolicitudNotificacion, EmailEnviado

        resultado = NotificacionService.procesar_pendientes()

        assert resultado["enviadas"] == 1
        solicitud_email.refresh_from_db()
        assert solicitud_email.estado == SolicitudNotificacion.Estado.ENVIADA
        assert EmailEnviado.objects.filter(
            destinatario_email=solicitud_email.cliente.email
        ).exists()

    def test_filtra_por_ids(self, solicitud_sistema, solicitud_email):
        from apps.notificaciones.services import NotificacionService
        from apps.notificaciones.models import SolicitudNotificacion

        NotificacionService.procesar_pendientes(
            solicitud_ids=[solicitud_sistema.pk]
        )

        solicitud_sistema.refresh_from_db()
        solicitud_email.refresh_from_db()
        assert solicitud_sistema.estado == SolicitudNotificacion.Estado.ENVIADA
        assert solicitud_email.estado == SolicitudNotificacion.Estado.PENDIENTE

    def test_sin_usuario_marca_fallida(self, db, cliente_sin_usuario):
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion
        from apps.notificaciones.services import NotificacionService

        sol = SolicitudNotificacion.objects.create(
            cliente=cliente_sin_usuario,
            tipo=Notificacion.Tipo.SISTEMA,
            mensaje="Sin usuario vinculado.",
            destino=Notificacion.Destino.SISTEMA,
        )
        resultado = NotificacionService.procesar_pendientes()

        sol.refresh_from_db()
        assert sol.estado == SolicitudNotificacion.Estado.FALLIDA
        assert resultado["fallidas"] == 1

    def test_sin_email_registra_fallida(self, db, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion
        from apps.notificaciones.services import NotificacionService

        cliente_vacio = Cliente.objects.create(
            nombres="Sin",
            apellidos="Email",
            ruc_ci="6666666",
            email="",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        sol = SolicitudNotificacion.objects.create(
            cliente=cliente_vacio,
            tipo=Notificacion.Tipo.SISTEMA,
            mensaje="Sin email.",
            destino=Notificacion.Destino.EMAIL,
        )
        resultado = NotificacionService.procesar_pendientes()
        sol.refresh_from_db()
        assert sol.estado == SolicitudNotificacion.Estado.FALLIDA


# ── crear_solicitudes_cobro ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestCrearSolicitudesCobro:

    def test_crea_solicitudes_para_responsables_activos(self, cliente_con_usuario):
        from apps.clientes.models import Hijo, AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro
        from apps.notificaciones.models import SolicitudNotificacion

        hijo = Hijo.objects.create(
            nombre="Test",
            apellido="Hijo",
            cliente_responsable=cliente_con_usuario,
            activo=True,
        )
        AlumnoResponsable.objects.create(
            hijo=hijo,
            cliente=cliente_con_usuario,
            parentesco=AlumnoResponsable.Parentesco.PADRE,
            es_titular=True,
            recibe_notificaciones=True,
            activo=True,
        )

        count = crear_solicitudes_cobro([hijo])

        assert count == 1
        assert SolicitudNotificacion.objects.filter(cliente=cliente_con_usuario).count() == 1

    def test_ignora_responsables_sin_notificaciones(self, cliente_con_usuario):
        from apps.clientes.models import Hijo, AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro

        hijo = Hijo.objects.create(
            nombre="TestB",
            apellido="HijoB",
            cliente_responsable=cliente_con_usuario,
            activo=True,
        )
        AlumnoResponsable.objects.create(
            hijo=hijo,
            cliente=cliente_con_usuario,
            parentesco=AlumnoResponsable.Parentesco.MADRE,
            recibe_notificaciones=False,
            activo=True,
        )

        count = crear_solicitudes_cobro([hijo])
        assert count == 0

    def test_lista_vacia_retorna_cero(self):
        from apps.notificaciones.services import crear_solicitudes_cobro
        assert crear_solicitudes_cobro([]) == 0

    def test_ignora_cliente_sin_email_e_inactivo(self, db, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente, Hijo, AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro

        cliente_inactivo = Cliente.objects.create(
            nombres="Inactivo",
            apellidos="SinEmail",
            ruc_ci="5555551",
            email="",
            activo=False,
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        hijo = Hijo.objects.create(
            nombre="NiñoX", apellido="Test",
            cliente_responsable=cliente_inactivo, activo=True,
        )
        AlumnoResponsable.objects.create(
            hijo=hijo,
            cliente=cliente_inactivo,
            parentesco=AlumnoResponsable.Parentesco.PADRE,
            recibe_notificaciones=True,
            activo=True,
        )

        count = crear_solicitudes_cobro([hijo])
        assert count == 0

    def test_mensaje_template_personalizado(self, cliente_con_usuario):
        from apps.clientes.models import Hijo, AlumnoResponsable
        from apps.notificaciones.services import crear_solicitudes_cobro
        from apps.notificaciones.models import SolicitudNotificacion

        hijo = Hijo.objects.create(
            nombre="TestC",
            apellido="HijoC",
            cliente_responsable=cliente_con_usuario,
            activo=True,
        )
        AlumnoResponsable.objects.create(
            hijo=hijo,
            cliente=cliente_con_usuario,
            parentesco=AlumnoResponsable.Parentesco.TUTOR,
            recibe_notificaciones=True,
            activo=True,
        )

        crear_solicitudes_cobro([hijo], mensaje_template=lambda h, r: "Mensaje custom")

        sol = SolicitudNotificacion.objects.filter(cliente=cliente_con_usuario).first()
        assert sol.mensaje == "Mensaje custom"


# ── push_ws_notificacion ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPushWsNotificacion:

    def test_sin_channel_layer_no_crashea(self, solicitud_sistema):
        from apps.notificaciones.services import push_ws_notificacion
        from apps.notificaciones.models import Notificacion

        notif = Notificacion.objects.create(
            usuario=solicitud_sistema.cliente.usuario_portal,
            tipo="SISTEMA",
            titulo="Test",
            mensaje="Test mensaje",
            destino="SISTEMA",
        )
        push_ws_notificacion(notif)  # no debe lanzar excepción

    def test_con_channel_layer_envia_grupo(self, solicitud_sistema):
        from apps.notificaciones.services import push_ws_notificacion
        from apps.notificaciones.models import Notificacion

        notif = Notificacion.objects.create(
            usuario=solicitud_sistema.cliente.usuario_portal,
            tipo="SISTEMA",
            titulo="Test WS",
            mensaje="Mensaje WS",
            destino="SISTEMA",
        )

        mock_layer = MagicMock()
        with patch("channels.layers.get_channel_layer", return_value=mock_layer):
            with patch("asgiref.sync.async_to_sync") as mock_a2s:
                mock_a2s.return_value = MagicMock()
                push_ws_notificacion(notif)
                mock_a2s.assert_called_once()

    def test_channel_layer_none_retorna_silencioso(self, solicitud_sistema):
        from apps.notificaciones.services import push_ws_notificacion
        from apps.notificaciones.models import Notificacion

        notif = Notificacion.objects.create(
            usuario=solicitud_sistema.cliente.usuario_portal,
            tipo="SISTEMA",
            titulo="Test None",
            mensaje="Sin layer",
            destino="SISTEMA",
        )
        with patch("channels.layers.get_channel_layer", return_value=None):
            push_ws_notificacion(notif)  # debe retornar sin lanzar excepción

    def test_group_send_exception_se_ignora(self, solicitud_sistema):
        from apps.notificaciones.services import push_ws_notificacion
        from apps.notificaciones.models import Notificacion

        notif = Notificacion.objects.create(
            usuario=solicitud_sistema.cliente.usuario_portal,
            tipo="SISTEMA",
            titulo="Test Exc",
            mensaje="Excepción ignorada",
            destino="SISTEMA",
        )
        mock_layer = MagicMock()
        with patch("channels.layers.get_channel_layer", return_value=mock_layer):
            with patch("asgiref.sync.async_to_sync", side_effect=RuntimeError("fallo ws")):
                push_ws_notificacion(notif)  # debe ignorar la excepción


# ── EmailService ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmailService:

    def test_enviar_simple_registra_email_enviado(self):
        from apps.notificaciones.services import EmailService
        from apps.notificaciones.models import EmailEnviado

        EmailService.enviar_simple(
            destinatario_email="dest@test.com",
            destinatario_nombre="Destinatario Test",
            asunto="Test Asunto",
            cuerpo="Cuerpo del mensaje.",
        )

        registro = EmailEnviado.objects.filter(destinatario_email="dest@test.com").first()
        assert registro is not None
        assert registro.estado == EmailEnviado.Estado.ENVIADO
        assert registro.asunto == "Test Asunto"
