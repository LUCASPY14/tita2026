"""
Excepciones personalizadas
"""
from rest_framework.exceptions import APIException
from rest_framework import status


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
