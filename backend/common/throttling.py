from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """5 intentos/minuto por IP en el endpoint de login."""
    scope = "auth"


class SensitiveEndpointThrottle(UserRateThrottle):
    """50 peticiones/hora para endpoints sensibles (carga de saldo, anulaciones)."""
    scope = "sensitive"
