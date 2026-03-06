"""
Middleware para capturar contexto de auditoría
Captura empleado actual e IP para uso en signals
"""

from threading import current_thread
from django.utils.deprecation import MiddlewareMixin


class AuditContextMiddleware(MiddlewareMixin):
    """
    Middleware que captura el empleado actual y la IP en cada request.
    Almacena esta información en thread-local para que sea accesible en signals.
    """

    def process_request(self, request):
        """
        Captura información del request y la almacena en thread-local.
        """
        # Obtener empleado actual
        empleado = None
        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                from apps.usuarios.models import Empleados

                empleado = Empleados.objects.get(id=request.user.id)
            except:
                empleado = None

        # Obtener IP del cliente
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")

        # Almacenar en thread-local
        thread = current_thread()
        thread.current_empleado = empleado
        thread.current_ip = ip

        return None

    def process_response(self, request, response):
        """
        Limpia thread-local después del request.
        """
        thread = current_thread()
        if hasattr(thread, "current_empleado"):
            delattr(thread, "current_empleado")
        if hasattr(thread, "current_ip"):
            delattr(thread, "current_ip")

        return response
