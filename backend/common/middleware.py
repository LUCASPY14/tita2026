"""
RequestIDMiddleware — propaga X-Request-ID por todo el ciclo de vida del request.

Flujo:
  1. Si el cliente envía X-Request-ID se reutiliza (útil en cadenas de microservicios).
  2. Caso contrario se genera un UUID4 aleatorio.
  3. El ID se guarda en thread-local para que los log formatters lo incluyan.
  4. Se añade como tag de Sentry (si Sentry está activo) para correlacionar eventos.
  5. La respuesta siempre incluye X-Request-ID para que el cliente pueda rastrearlo.
"""

import logging
import threading
import uuid

logger = logging.getLogger(__name__)

_request_id_local = threading.local()


def get_current_request_id() -> str:
    """Devuelve el Request-ID del request activo en este thread, o '-' si no hay ninguno."""
    return getattr(_request_id_local, "request_id", "-")


class RequestIDFilter(logging.Filter):
    """Inyecta request_id en cada LogRecord para que el formatter pueda incluirlo."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_current_request_id()
        return True


class RequestIDMiddleware:
    """
    Middleware ASGI/WSGI compatible (new-style) que gestiona el X-Request-ID.
    Debe colocarse inmediatamente después de PrometheusBeforeMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (
            request.META.get("HTTP_X_REQUEST_ID")
            or str(uuid.uuid4())
        )
        request.request_id = request_id
        _request_id_local.request_id = request_id

        self._set_sentry_tag(request_id)

        response = self.get_response(request)
        response["X-Request-ID"] = request_id

        _request_id_local.request_id = "-"
        return response

    @staticmethod
    def _set_sentry_tag(request_id: str) -> None:
        try:
            import sentry_sdk
            sentry_sdk.set_tag("request_id", request_id)
        except Exception:
            pass
