"""
Throttling personalizado para la API REST
Controla la tasa de solicitudes por usuario/IP
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Permite ráfagas cortas de solicitudes
    """

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """
    Limita las solicitudes sostenidas en el tiempo
    """

    scope = "sustained"


class VentasRateThrottle(UserRateThrottle):
    """
    Throttling específico para endpoints de ventas
    """

    scope = "ventas"


class AuthRateThrottle(AnonRateThrottle):
    """
    Throttling para endpoints de autenticación
    Previene ataques de fuerza bruta
    """

    scope = "auth"


class ReportesRateThrottle(UserRateThrottle):
    """
    Throttling para generación de reportes
    Los reportes son operaciones costosas
    """

    scope = "reportes"
