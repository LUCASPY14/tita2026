from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """5 intentos/minuto por IP en el endpoint de login."""
    scope = "auth"


class SensitiveEndpointThrottle(UserRateThrottle):
    """50 peticiones/hora para endpoints sensibles (carga de saldo, anulaciones)."""
    scope = "sensitive"


class PortalRateThrottle(UserRateThrottle):
    """
    Rate limit para endpoints del portal de padres expuesto a internet.
    Más estricto que el UserRateThrottle global para limitar scraping y abuso.
    Tasa configurada en DEFAULT_THROTTLE_RATES['portal'].
    """
    scope = "portal"


class BancardRetornoThrottle(AnonRateThrottle):
    """
    Rate limit para GET /api/v1/core/bancard/retorno/ (endpoint sin auth).
    Previene spam con shop_process_id inventados.
    Tasa configurada en DEFAULT_THROTTLE_RATES['bancard_retorno'].
    """
    scope = "bancard_retorno"
