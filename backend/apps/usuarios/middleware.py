"""
Middleware para capturar contexto de auditoría
Captura usuario autenticado e IP para uso en signals
"""

import threading

from django.utils.deprecation import MiddlewareMixin

_local = threading.local()


def get_current_usuario():
    return getattr(_local, "usuario", None)


def get_current_ip():
    return getattr(_local, "ip", "127.0.0.1")


class AuditContextMiddleware(MiddlewareMixin):
    """
    Almacena el usuario autenticado y la IP del request en thread-local.
    Accesible desde signals mediante get_current_usuario() y get_current_ip().
    """

    def process_request(self, request):
        _local.usuario = (
            request.user
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        _local.ip = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR", "127.0.0.1")
        )

    def process_response(self, request, response):
        _local.usuario = None
        _local.ip = None
        return response
