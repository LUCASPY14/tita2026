"""
Autenticación personalizada con verificación de timeout de sesión.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomTokenAuthentication(TokenAuthentication):
    """Autenticación de token — keyword Bearer (legado)."""

    keyword = "Bearer"


class SesionActivaJWTAuthentication(JWTAuthentication):
    """
    Extiende JWTAuthentication para validar inactividad de sesión.

    Si el usuario tiene todas sus SesionActiva con `ultima_actividad`
    más antigua que SESSION_IDLE_TIMEOUT_HOURS, la sesión se considera
    expirada y se devuelve 401, forzando nuevo login.

    En cada request válido actualiza `ultima_actividad` de la sesión más
    reciente del usuario.
    """

    IDLE_TIMEOUT_HOURS: int = getattr(settings, "SESSION_IDLE_TIMEOUT_HOURS", 8)

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result
        self._check_and_refresh_sesion(user)
        return user, validated_token

    def _check_and_refresh_sesion(self, user) -> None:
        from apps.usuarios.models import SesionActiva

        timeout = timedelta(hours=self.IDLE_TIMEOUT_HOURS)
        cutoff = timezone.now() - timeout

        sesion = (
            SesionActiva.objects.filter(usuario=user, activa=True)
            .order_by("-ultima_actividad")
            .first()
        )

        if sesion is None:
            raise AuthenticationFailed(
                "Sesión no encontrada. Iniciá sesión nuevamente.",
                code="sesion_no_encontrada",
            )

        if sesion.ultima_actividad < cutoff:
            # Expirar todas las sesiones activas del usuario
            SesionActiva.objects.filter(usuario=user, activa=True).update(activa=False)
            raise AuthenticationFailed(
                f"Sesión expirada por inactividad ({self.IDLE_TIMEOUT_HOURS} h). "
                "Iniciá sesión nuevamente.",
                code="sesion_expirada",
            )

        # Actualizar timestamp de actividad (bypass auto_now vía update directo)
        SesionActiva.objects.filter(pk=sesion.pk).update(
            ultima_actividad=timezone.now()
        )
