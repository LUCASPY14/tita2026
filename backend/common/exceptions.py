"""
Excepciones personalizadas
"""
import logging
from rest_framework.exceptions import APIException, ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied, NotFound, MethodNotAllowed, Throttled
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Normaliza todas las respuestas de error a {"detail": ..., "code": ..., "field_errors": {...}}"""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception in %s", context.get("view"))
        return Response(
            {"detail": "Error interno del servidor.", "code": "server_error", "field_errors": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    normalized = {"detail": "", "code": "error", "field_errors": {}}

    if isinstance(exc, ValidationError):
        field_errors = {}
        non_field = []
        for key, value in data.items():
            messages = [str(v) for v in (value if isinstance(value, list) else [value])]
            if key == "non_field_errors":
                non_field.extend(messages)
            else:
                field_errors[key] = messages
        normalized["detail"] = "; ".join(non_field) if non_field else "Error de validación."
        normalized["code"] = "validation_error"
        normalized["field_errors"] = field_errors
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        normalized["detail"] = str(data.get("detail", "No autenticado."))
        normalized["code"] = "not_authenticated"
    elif isinstance(exc, PermissionDenied):
        normalized["detail"] = str(data.get("detail", "Permiso denegado."))
        normalized["code"] = "permission_denied"
    elif isinstance(exc, NotFound):
        normalized["detail"] = str(data.get("detail", "No encontrado."))
        normalized["code"] = "not_found"
    elif isinstance(exc, MethodNotAllowed):
        normalized["detail"] = str(data.get("detail", "Método no permitido."))
        normalized["code"] = "method_not_allowed"
    elif isinstance(exc, Throttled):
        normalized["detail"] = f"Demasiadas solicitudes. Reintente en {exc.wait} segundos." if exc.wait else "Demasiadas solicitudes."
        normalized["code"] = "throttled"
    elif isinstance(exc, APIException):
        normalized["detail"] = str(data.get("detail", str(exc)))
        normalized["code"] = getattr(exc, "default_code", "error")
    else:
        normalized["detail"] = str(data) if data else "Error desconocido."

    response.data = normalized
    return response


class CustomValidationError(APIException):
    """
    Excepción de validación personalizada
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error de validación'
    default_code = 'validation_error'


class BusinessLogicError(APIException):
    """
    Excepción para errores de lógica de negocio
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Error en lógica de negocio'
    default_code = 'business_logic_error'
