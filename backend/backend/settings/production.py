"""
Configuración de producción para Cantina Tita
Incluye todas las medidas de seguridad requeridas para deployment.
Actualizado: Abril 2026
"""

import os
from pathlib import Path
from datetime import timedelta

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
# DATABASE PRODUCTION CONFIG (SQL SERVER)
# ==========================================

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.environ.get("DB_NAME", "titadb"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "1433"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "OPTIONS": {
            "driver": "ODBC Driver 18 for SQL Server",
            "extra_params": (
                "TrustServerCertificate=yes;" "MARS_Connection=yes;" "Encrypt=yes;" "Connection Timeout=30;"
            ),
        },
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 600,  # 10 min
        "CONN_HEALTH_CHECKS": True,
    }
}

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/django.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
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

SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        sample_rate=1.0,
        environment="production",
        release=os.environ.get("GIT_COMMIT_SHA", "unknown"),
        send_default_pii=False,
        attach_stacktrace=True,
        max_breadcrumbs=50,
    )

# ==========================================
# DRF CONFIGURATION
# ==========================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "100/hour",
    "user": "1000/hour",
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
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ==========================================
# VALIDACIÓN
# ==========================================

_required_env_vars = ["SECRET_KEY", "ALLOWED_HOSTS", "DB_HOST", "DB_NAME"]
for var in _required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Environment variable {var} is required in production!")

# Production settings loaded successfully
