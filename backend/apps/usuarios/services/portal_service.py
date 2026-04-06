"""
Servicio de autenticación para usuarios del portal (clientes).

Usa PyJWT directamente (no SimpleJWT) para emitir tokens con claim
`token_type: "portal"`, completamente separados del sistema de empleados.
"""
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from apps.usuarios.models import UsuariosPortal

PORTAL_TOKEN_LIFETIME = timedelta(hours=8)
PORTAL_TOKEN_TYPE = "portal"


class PortalAuthService:

    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Autentica un usuario del portal por email y contraseña.
        Retorna dict con 'token' y 'portal_user' info.
        Lanza ValueError si las credenciales son inválidas.
        """
        try:
            portal_user = UsuariosPortal.objects.select_related("id_cliente").get(
                email__iexact=email.strip()
            )
        except UsuariosPortal.DoesNotExist:
            raise ValueError("Credenciales incorrectas")

        if not portal_user.estado:
            raise ValueError("Cuenta desactivada")

        if not portal_user.check_password(password):
            raise ValueError("Credenciales incorrectas")

        portal_user.ultimo_acceso = timezone.now()
        portal_user.save(update_fields=["ultimo_acceso"])

        token = PortalAuthService._generar_token(portal_user)
        cliente = portal_user.id_cliente

        return {
            "token": token,
            "portal_user": {
                "id_usuario_portal": portal_user.id_usuario_portal,
                "email": portal_user.email,
                "email_verificado": portal_user.email_verificado,
                "id_cliente": cliente.id_cliente,
                "nombre_completo": cliente.nombre_completo,
                "ruc_ci": cliente.ruc_ci,
            },
        }

    @staticmethod
    def _generar_token(portal_user: UsuariosPortal) -> str:
        import time as _time
        now_ts = int(_time.time())
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": portal_user.id_usuario_portal,
            "id_cliente": portal_user.id_cliente_id,
            "email": portal_user.email,
            "exp": now_ts + int(PORTAL_TOKEN_LIFETIME.total_seconds()),
            "iat": now_ts,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verificar_token(token: str) -> UsuariosPortal:
        """
        Valida un token de portal y retorna el UsuariosPortal correspondiente.
        Lanza ValueError si el token es inválido, expirado, o el usuario no existe.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido")

        if payload.get("token_type") != PORTAL_TOKEN_TYPE:
            raise ValueError("Token inválido")

        try:
            return UsuariosPortal.objects.select_related("id_cliente").get(
                id_usuario_portal=payload["id_usuario_portal"],
                estado=True,
            )
        except UsuariosPortal.DoesNotExist:
            raise ValueError("Usuario de portal no encontrado o inactivo")
