"""
Tests para views de notificaciones.
Cubre get_queryset staff/no-staff y EnviarNotificacionView.
"""
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient


@pytest.fixture
def api_staff(usuario_admin):
    api = APIClient()
    api.force_authenticate(user=usuario_admin)
    return api


@pytest.fixture
def api_cajero(usuario_cajero):
    api = APIClient()
    api.force_authenticate(user=usuario_cajero)
    return api


# ── NotificacionViewSet ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionViewSet:

    def test_staff_ve_todas_las_notificaciones(self, api_staff, usuario_cajero):
        """is_staff=True → qs.all() (línea 38 views.py)."""
        from apps.notificaciones.models import Notificacion
        Notificacion.objects.create(
            usuario=usuario_cajero,
            tipo=Notificacion.Tipo.SISTEMA,
            destino=Notificacion.Destino.SISTEMA,
            titulo="Test",
            mensaje="Msg",
        )
        resp = api_staff.get("/api/v1/notificaciones/notificaciones/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_no_staff_ve_solo_las_suyas(self, api_cajero, usuario_cajero, usuario_admin):
        """is_staff=False → qs.filter(usuario=request.user) (línea 39 views.py)."""
        from apps.notificaciones.models import Notificacion
        Notificacion.objects.create(
            usuario=usuario_admin,
            tipo=Notificacion.Tipo.SISTEMA,
            destino=Notificacion.Destino.SISTEMA,
            titulo="Admin notif",
            mensaje="Solo del admin",
        )
        Notificacion.objects.create(
            usuario=usuario_cajero,
            tipo=Notificacion.Tipo.SISTEMA,
            destino=Notificacion.Destino.SISTEMA,
            titulo="Cajero notif",
            mensaje="Del cajero",
        )
        resp = api_cajero.get("/api/v1/notificaciones/notificaciones/")
        assert resp.status_code == 200
        ids_usuarios = [n["usuario"] for n in resp.data["results"]]
        assert all(uid == usuario_cajero.pk for uid in ids_usuarios)


# ── PreferenciaNotificacionViewSet ────────────────────────────────────────────

@pytest.mark.django_db
class TestPreferenciaNotificacionViewSet:

    def test_staff_ve_todas_las_preferencias(self, api_staff, usuario_cajero):
        """is_staff=True → qs.all() (línea 51 views.py)."""
        from apps.notificaciones.models import PreferenciaNotificacion
        PreferenciaNotificacion.objects.create(
            usuario=usuario_cajero,
            tipo_notificacion="SALDO_BAJO",
        )
        resp = api_staff.get("/api/v1/notificaciones/preferencias/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_no_staff_ve_solo_las_suyas(self, api_cajero, usuario_cajero, usuario_admin):
        """is_staff=False → qs.filter(usuario=...) (línea 52 views.py)."""
        from apps.notificaciones.models import PreferenciaNotificacion
        PreferenciaNotificacion.objects.create(
            usuario=usuario_admin,
            tipo_notificacion="SALDO_BAJO",
        )
        PreferenciaNotificacion.objects.create(
            usuario=usuario_cajero,
            tipo_notificacion="SALDO_BAJO",
        )
        resp = api_cajero.get("/api/v1/notificaciones/preferencias/")
        assert resp.status_code == 200
        ids_usuarios = [p["usuario"] for p in resp.data["results"]]
        assert all(uid == usuario_cajero.pk for uid in ids_usuarios)


# ── EnviarNotificacionView ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEnviarNotificacionView:

    def test_sin_pendientes_retorna_207(self, api_staff):
        """enviadas=0 → HTTP 207 Multi-Status (líneas 87-91 views.py)."""
        resp = api_staff.post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code == 207

    def test_con_enviadas_retorna_200(self, api_staff):
        """enviadas > 0 → HTTP 200 OK (línea 90 rama True)."""
        with patch(
            "apps.notificaciones.services.NotificacionService.procesar_pendientes",
            return_value={"enviadas": 2, "fallidas": 0, "omitidas": 0},
        ):
            resp = api_staff.post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code == 200
        assert resp.data["enviadas"] == 2

    def test_con_solicitud_ids_especificos(self, api_staff):
        """Body con solicitud_ids → se pasan al service (línea 88)."""
        with patch(
            "apps.notificaciones.services.NotificacionService.procesar_pendientes",
            return_value={"enviadas": 1, "fallidas": 0, "omitidas": 0},
        ) as mock_proc:
            resp = api_staff.post(
                "/api/v1/notificaciones/enviar/",
                {"solicitud_ids": [1, 2]},
                format="json",
            )
        assert resp.status_code == 200
        mock_proc.assert_called_once_with(solicitud_ids=[1, 2])

    def test_requiere_autenticacion(self):
        api = APIClient()
        resp = api.post("/api/v1/notificaciones/enviar/", {}, format="json")
        assert resp.status_code in (401, 403)
