"""
Resolución de la IP real del cliente a partir del request.

El backend nunca recibe conexiones directas: Nginx (contenedor `frontend`)
es el único proxy que llega a Daphne, así que request.META["REMOTE_ADDR"]
siempre es la IP interna de Docker del contenedor de Nginx (no la del
usuario), y encima cambia en cada recreación del contenedor. Nginx sí
reenvía la IP real del cliente en X-Real-IP en cada ubicación proxied
(ver frontend/nginx.conf) — es la fuente confiable acá.
"""


def get_client_ip(request) -> str:
    """IP real del cliente: X-Real-IP (seteado por Nginx) con fallback a
    REMOTE_ADDR (para runserver local, sin Nginx delante)."""
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "")
