"""
Tests de vistas extendidas de la app notificaciones.
Cubre: VapidPublicKeyView (503 sin key, 200 con key), PushSubscriptionView
       (POST create/update, DELETE, errores), EnviarNotificacionView (POST).
"""
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient


@pytest.fixture
def api_admin(usuario_admin):
    client = APIClient()
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def api_cajero(usuario_cajero):
    client = APIClient()
    client.force_authenticate(user=usuario_cajero)
    return client


# ── VapidPublicKeyView ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVapidPublicKeyView:

    def test_503_sin_vapid_configurado(self, api_cajero):
        with patch("django.conf.settings.VAPID_PUBLIC_KEY", ""):
            resp = api_cajero.get("/api/v1/notificaciones/vapid-public-key/")
        assert resp.status_code == 503
        assert "error" in resp.data

    def test_200_con_vapid_configurado(self, api_cajero):
        with patch("django.conf.settings.VAPID_PUBLIC_KEY", "BPublicKeyABC123"):
            resp = api_cajero.get("/api/v1/notificaciones/vapid-public-key/")
        assert resp.status_code == 200
        assert resp.data["publicKey"] == "BPublicKeyABC123"

    def test_requiere_autenticacion(self):
        resp = APIClient().get("/api/v1/notificaciones/vapid-public-key/")
        assert resp.status_code in (401, 403)


# ── PushSubscriptionView ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPushSubscriptionView:

    VALID_PAYLOAD = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "keys": {
            "p256dh": "BNVkPKey1234",
            "auth": "AuthKey5678",
        },
    }

    def test_post_crea_suscripcion(self, api_cajero):
        resp = api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            self.VALID_PAYLOAD,
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["ok"] is True

    def test_post_actualiza_suscripcion_existente(self, api_cajero):
        # Primera llamada crea, segunda actualiza
        api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            self.VALID_PAYLOAD,
            format="json",
        )
        resp = api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            {**self.VALID_PAYLOAD, "keys": {"p256dh": "NewKey", "auth": "NewAuth"}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_post_sin_endpoint_retorna_400(self, api_cajero):
        resp = api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            {"keys": {"p256dh": "x", "auth": "y"}},
            format="json",
        )
        assert resp.status_code == 400

    def test_post_sin_keys_retorna_400(self, api_cajero):
        resp = api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            {"endpoint": "https://example.com/push"},
            format="json",
        )
        assert resp.status_code == 400

    def test_delete_elimina_suscripcion(self, api_cajero):
        api_cajero.post(
            "/api/v1/notificaciones/push-subscription/",
            self.VALID_PAYLOAD,
            format="json",
        )
        resp = api_cajero.delete(
            "/api/v1/notificaciones/push-subscription/",
            {"endpoint": self.VALID_PAYLOAD["endpoint"]},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_delete_sin_endpoint_retorna_400(self, api_cajero):
        resp = api_cajero.delete(
            "/api/v1/notificaciones/push-subscription/",
            {},
            format="json",
        )
        assert resp.status_code == 400

    def test_requiere_autenticacion(self):
        resp = APIClient().post(
            "/api/v1/notificaciones/push-subscription/",
            self.VALID_PAYLOAD,
            format="json",
        )
        assert resp.status_code in (401, 403)


# ── EnviarNotificacionView ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnviarNotificacionView:

    def test_sin_solicitudes_pendientes_retorna_207(self, api_admin):
        resp = api_admin.post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code in (200, 207)
        assert "enviadas" in resp.data
        assert "fallidas" in resp.data

    def test_procesa_solicitudes_especificas(self, api_admin, db, cliente):
        from apps.notificaciones.models import Notificacion, SolicitudNotificacion
        sol = SolicitudNotificacion.objects.create(
            cliente=cliente,
            tipo="SALDO_BAJO",
            destino=Notificacion.Destino.EMAIL,
            mensaje="Saldo bajo test.",
        )
        cliente.email = "padre@test.com"
        cliente.save(update_fields=["email"])
        with patch("apps.notificaciones.services.send_mail"):
            resp = api_admin.post(
                "/api/v1/notificaciones/enviar/",
                {"solicitud_ids": [sol.pk]},
                format="json",
            )
        assert resp.status_code in (200, 207)

    def test_no_staff_no_puede_enviar(self, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="cliente_notif@test.com", password="x",
            nombre="C", apellido="W",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code == 403

    def test_requiere_autenticacion(self):
        resp = APIClient().post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code in (401, 403)
