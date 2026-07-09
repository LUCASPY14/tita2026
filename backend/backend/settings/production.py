"""
Configuración de producción para Cantina Tita
Incluye todas las medidas de seguridad requeridas para deployment.
Actualizado: Abril 2026
"""

import os
from datetime import timedelta
from pathlib import Path

# Cargar variables de entorno desde .env.production
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).resolve().parent.parent.parent / ".env.production"
    if env_file.exists():
        load_dotenv(env_file, override=True)
except ImportError:
    pass  # python-dotenv no está instalado, usar variables de sistema

from .base import *

# ==========================================
# SEGURIDAD CRÍTICA
# ==========================================

# 1. SECRET_KEY - DEBE ser configurado via variable de entorno
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY must be set in production! "
        'Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"'
    )

# 2. DEBUG - Siempre False en producción
DEBUG = False

# 3. ALLOWED_HOSTS - Dominios permitidos
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise ValueError("ALLOWED_HOSTS must be set in production!")

# ==========================================
# HTTPS/SSL CONFIGURATION
# ==========================================

# Redirigir todo tráfico HTTP a HTTPS
SECURE_SSL_REDIRECT = True

# Proxy SSL Header (para Nginx/Apache)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==========================================
# COOKIES SEGURAS
# ==========================================

# Session Cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_COOKIE_NAME = "cantina_sessionid"

# CSRF Cookies
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_NAME = "cantina_csrftoken"
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")

# ==========================================
# SECURITY HEADERS
# ==========================================

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# ==========================================
# CORS CONFIGURATION
# ==========================================

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True

# ==========================================
# DATABASE PRODUCTION CONFIG (PostgreSQL)
# ==========================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "cantina_tita"),
        "USER": os.environ.get("DB_USER", "cantina_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        # ATOMIC_REQUESTS + CONN_MAX_AGE=600 hacen innecesario PgBouncer a esta escala
        # (~8-12 conexiones reales). Si se superan 40-50 conexiones sostenidas, hay que
        # desactivar ambas ANTES de habilitar PgBouncer en modo transaction.
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": (
                "-c statement_timeout=15000ms "
                "-c lock_timeout=10000ms "
                "-c idle_in_transaction_session_timeout=10000ms"
            ),
        },
    }
}

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "request_id": {
            "()": "common.middleware.RequestIDFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} rid={request_id} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} rid={request_id} {message}",
            "style": "{",
        },
        "json": {
            "()": "common.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["request_id"],
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/django.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ==========================================
# EMAIL CONFIGURATION
# ==========================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@cantina-tita.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMINS = [
    ("Admin Team", os.environ.get("ADMIN_EMAIL", "admin@cantina-tita.com")),
]
MANAGERS = ADMINS

# ==========================================
# CACHE CONFIGURATION
# ==========================================

REDIS_URL = os.environ.get("REDIS_URL", None)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            },
            "KEY_PREFIX": "cantina",
            "TIMEOUT": 300,
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# ==========================================
# SENTRY CONFIGURATION
# ==========================================

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if not SENTRY_DSN:
    raise ValueError(
        "SENTRY_DSN must be set in production! "
        "Get the DSN from your Sentry project → Settings → Client Keys."
    )

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import logging as _logging


def _sentry_before_send(event: dict, hint: dict) -> "dict | None":
    # BrokenPipe / ConnectionReset — el cliente cortó la conexión; no es un bug
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type = exc_info[0]
        if exc_type is not None and issubclass(exc_type, (BrokenPipeError, ConnectionResetError)):
            return None

    # Silenciar eventos del health-check — ruido de uptime monitors
    url_path = event.get("request", {}).get("url", "")
    if "/api/health/" in url_path:
        return None

    # Añadir tags de contexto de negocio para facilitar búsqueda en Sentry
    event.setdefault("tags", {})
    event["tags"]["app"] = "cantina-tita"
    event["tags"]["component"] = "backend"

    return event


sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
    release=os.environ.get("SENTRY_RELEASE", os.environ.get("GIT_COMMIT_SHA", "unknown")),
    integrations=[
        DjangoIntegration(
            transaction_style="url",      # agrupa por URL pattern, no por función
            middleware_spans=True,
            signals_spans=False,          # demasiado ruido; activar si se investiga perf
            cache_spans=True,
        ),
        CeleryIntegration(
            monitor_beat_tasks=True,      # cron-monitor en Sentry para Beat tasks
            propagate_traces=True,        # vincula task al request que la originó
        ),
        RedisIntegration(),
        LoggingIntegration(
            level=_logging.INFO,          # captura INFO+ como breadcrumbs
            event_level=_logging.ERROR,   # convierte ERROR+ en Sentry events
        ),
    ],
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.05")),
    sample_rate=1.0,
    send_default_pii=False,
    attach_stacktrace=True,
    max_breadcrumbs=50,
    before_send=_sentry_before_send,
)

# ==========================================
# DRF CONFIGURATION
# ==========================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "60/hour",
    "user": "500/hour",
    "auth": "5/min",            # login: 5 intentos/minuto por IP
    "sensitive": "50/hour",     # carga de saldo, anulaciones
    "portal": "300/hour",       # portal de padres (internet-facing): ~5 requests/min
    "bancard_retorno": "20/hour", # retorno Bancard sin auth: máx 20 recargas/hora por IP
}

# ==========================================
# JWT CONFIGURATION
# ==========================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# ==========================================
# STATIC & MEDIA
# ==========================================

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}

# ==========================================
# INTEGRACIONES DE PAGO
# ==========================================

# Bancard: forzar producción — en prod NUNCA debe quedar en sandbox
BANCARD_SANDBOX = os.environ.get("BANCARD_SANDBOX", "False") == "True"


# ==========================================
# VALIDACIÓN
# ==========================================

_required_env_vars = ["SECRET_KEY", "ALLOWED_HOSTS", "DB_HOST", "DB_NAME"]
for var in _required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Environment variable {var} is required in production!")

# ==========================================
# LOGGING ESTRUCTURADO (JSON para ELK/Sentry)
# En producción el console handler emite JSON — Docker/Filebeat lo recolecta.
# ==========================================

LOGGING["handlers"]["console"]["formatter"] = "json"
LOGGING["handlers"]["file"]["formatter"]    = "json"
LOGGING["handlers"]["error_file"]["formatter"] = "json"

# ==========================================
# API DOCS — solo admin en producción
# ==========================================

SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"] = ["rest_framework.permissions.IsAdminUser"]
SPECTACULAR_SETTINGS["SERVE_AUTHENTICATION"] = [
    "rest_framework.authentication.SessionAuthentication",
    "rest_framework_simplejwt.authentication.JWTAuthentication",
]

# Production settings loaded successfully
