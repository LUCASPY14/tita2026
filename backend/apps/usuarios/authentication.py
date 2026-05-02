"""
Clase de autenticación DRF para usuarios del portal (clientes).

Registrada junto a JWTAuthentication en la configuración de cada vista portal.
"""

import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.usuarios.services.portal_service import (
    PORTAL_TOKEN_TYPE,
    PortalAuthService,
)


class PortalUserProxy:
    """
    Wrapper mínimo de UsuariosPortal para satisfacer el contrato
    de request.user de DRF (necesita is_authenticated).
    """

    def __init__(self, portal_user):
        self.portal_user = portal_user
        self.is_authenticated = True
        self.pk = portal_user.id_usuario_portal

    def __str__(self):
        return self.portal_user.email


class PortalJWTAuthentication(BaseAuthentication):
    """
    Autentica usuarios del portal a partir de tokens JWT con
    claim `token_type: "portal"`.

    Si el token no tiene tipo portal, devuelve None para que
    el siguiente autenticador (JWTAuthentication de empleados) lo intente.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        # Peek at token type without full verification to avoid interfering
        # with employee tokens (which also use Bearer)
        try:
            unverified = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256"],
            )
            if unverified.get("token_type") != PORTAL_TOKEN_TYPE:
                return None
        except Exception:
            return None

        # Full verification
        try:
            portal_user = PortalAuthService.verificar_token(token)
        except ValueError as exc:
            raise AuthenticationFailed(str(exc))

        return (PortalUserProxy(portal_user), token)

    def authenticate_header(self, request):
        return "Bearer"
