"""
Excepciones personalizadas
"""
import logging
from django.db.models import ProtectedError
from rest_framework.exceptions import APIException, ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied, NotFound, MethodNotAllowed, Throttled
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Normaliza todas las respuestas de error a {"detail": ..., "code": ..., "field_errors": {...}}"""
    if isinstance(exc, ProtectedError):
        exc = ValidationError({"error": "No se puede eliminar: el registro está en uso por otros datos del sistema."})

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
        if isinstance(data, (str, list)):
            # ValidationError raised with a plain string or list
            msgs = data if isinstance(data, list) else [data]
            non_field.extend(str(m) for m in msgs)
        else:
            for key, value in data.items():
                messages = [str(v) for v in (value if isinstance(value, list) else [value])]
                if key in ("non_field_errors", "error", "detail"):
                    non_field.extend(messages)
                else:
                    field_errors[key] = messages
        if non_field:
            normalized["detail"] = "; ".join(non_field)
        elif field_errors:
            # Mostrar el mensaje real del primer error (antes: "Error de validación." genérico).
            # Si el mensaje no dice de qué campo se trata ("Este campo es obligatorio."),
            # se antepone el nombre del campo.
            key, msgs = next(iter(field_errors.items()))
            msg = msgs[0] if msgs else "Dato inválido."
            if "campo" in msg.lower() or "field" in msg.lower():
                msg = f"{key.replace('_', ' ').capitalize()}: {msg}"
            normalized["detail"] = msg
        else:
            normalized["detail"] = "Error de validación."
        normalized["code"] = "validation_error"
        normalized["field_errors"] = field_errors
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        normalized["detail"] = str(data.get("detail", "No autenticado."))
        detail_code = getattr(getattr(exc, "detail", None), "code", None)
        normalized["code"] = detail_code or "not_authenticated"
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
