"""
Tests de SesionActivaJWTAuthentication — el refresco de ultima_actividad por
request y el throttle de 30s que evita contención de locks bajo polling
frecuente (ver LockNotAvailable en sesiones_activas, 22-oct-2026).
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

ME_URL = "/api/v1/usuarios/usuarios/me/"


@pytest.mark.django_db
class TestRefrescoSesionActiva:

    def _login(self, api_client, email):
        resp = api_client.post("/api/token/", {"email": email, "password": "test1234"}, format="json")
        assert resp.status_code == 200
        return resp.data["session_key"], resp.data["access"]

    def test_primer_request_refresca_ultima_actividad(self, usuario_cajero):
        from apps.usuarios.models import SesionActiva

        client = APIClient()
        session_key, access = self._login(client, "cajero@test.com")
        sesion = SesionActiva.objects.get(usuario=usuario_cajero, session_key=session_key)

        # Retroceder ultima_actividad para simular que pasó tiempo desde el login.
        vieja = timezone.now() - timedelta(minutes=5)
        SesionActiva.objects.filter(pk=sesion.pk).update(ultima_actividad=vieja)

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = client.get(ME_URL)
        assert resp.status_code == 200

        sesion.refresh_from_db()
        assert sesion.ultima_actividad > vieja

    def test_requests_dentro_de_30s_no_reescriben_ultima_actividad(self, usuario_cajero):
        """Bajo polling frecuente desde la misma pestaña (varios requests en
        pocos segundos), solo el primero debe escribir — los siguientes no
        deben tocar la fila, para no competir por su lock."""
        from apps.usuarios.models import SesionActiva

        client = APIClient()
        session_key, access = self._login(client, "cajero@test.com")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        sesion = SesionActiva.objects.get(usuario=usuario_cajero, session_key=session_key)
        valor_fijo = timezone.now() - timedelta(seconds=5)
        SesionActiva.objects.filter(pk=sesion.pk).update(ultima_actividad=valor_fijo)

        for _ in range(3):
            resp = client.get(ME_URL)
            assert resp.status_code == 200

        sesion.refresh_from_db()
        # Sigue siendo (casi) el valor fijado a mano — ningún request de los
        # 3 llegó a pisarlo porque faltaba menos de 30s desde ese valor.
        assert abs((sesion.ultima_actividad - valor_fijo).total_seconds()) < 1

    def test_request_despues_de_30s_si_refresca(self, usuario_cajero):
        from apps.usuarios.models import SesionActiva

        client = APIClient()
        session_key, access = self._login(client, "cajero@test.com")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        sesion = SesionActiva.objects.get(usuario=usuario_cajero, session_key=session_key)
        vieja = timezone.now() - timedelta(seconds=31)
        SesionActiva.objects.filter(pk=sesion.pk).update(ultima_actividad=vieja)

        resp = client.get(ME_URL)
        assert resp.status_code == 200

        sesion.refresh_from_db()
        assert sesion.ultima_actividad > vieja
