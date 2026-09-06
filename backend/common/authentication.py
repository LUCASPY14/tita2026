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
    Extiende JWTAuthentication para validar la sesión concurrente y la
    inactividad.

    El access/refresh token lleva un claim `session_key` (ver
    `apps.usuarios.views._emitir_tokens_con_sesion`) que identifica a qué
    SesionActiva pertenece ese token. En cada request se valida que ESA
    sesión puntual siga activa — no solo que el usuario tenga alguna sesión
    activa — para que el límite de sesiones concurrentes por rol
    (`_MAX_SESIONES`) realmente invalide el dispositivo anterior en vez de
    solo marcarlo inactivo en la base sin efecto práctico.

    Si la sesión de este token ya no está activa (porque se cerró al
    iniciar sesión en otro dispositivo, o por logout) se devuelve 401 con
    code="sesion_reemplazada". Si además todas las sesiones del usuario
    llevan más de SESSION_IDLE_TIMEOUT_HOURS sin actividad, se expiran todas
    y se devuelve code="sesion_expirada".

    Tokens emitidos antes de este cambio no llevan el claim `session_key`
    — para esos se mantiene el chequeo anterior (alguna sesión activa del
    usuario) hasta que expiren naturalmente.
    """

    IDLE_TIMEOUT_HOURS: int = getattr(settings, "SESSION_IDLE_TIMEOUT_HOURS", 8)

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result
        self._check_and_refresh_sesion(user, validated_token)
        return user, validated_token

    def _check_and_refresh_sesion(self, user, validated_token) -> None:
        from apps.usuarios.models import SesionActiva

        timeout = timedelta(hours=self.IDLE_TIMEOUT_HOURS)
        cutoff = timezone.now() - timeout
        session_key = validated_token.get("session_key")

        if session_key:
            sesion = SesionActiva.objects.filter(
                usuario=user, session_key=session_key, activa=True,
            ).first()
            if sesion is None:
                raise AuthenticationFailed(
                    "Tu sesión se cerró porque iniciaste sesión en otro dispositivo. "
                    "Iniciá sesión nuevamente.",
                    code="sesion_reemplazada",
                )
        else:
            # Token viejo sin claim session_key — comportamiento anterior.
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
