"""
Configuración de Django para ejecutar con Docker
"""

import os

from .base import *

DEBUG = os.getenv("DEBUG", "False") == "True"

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if not _allowed_hosts:
    raise ValueError(
        "La variable de entorno ALLOWED_HOSTS es requerida en el módulo de settings Docker. "
        "Ejemplo: ALLOWED_HOSTS=miservidor.local,127.0.0.1"
    )
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(",") if h.strip()]

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-this-key")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cantina_tita"),
        "USER": os.getenv("DB_USER", "cantina_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
    ]

CSRF_TRUSTED_ORIGINS = ["http://localhost", "http://127.0.0.1", "http://localhost:8000"]
extra = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if extra:
    CSRF_TRUSTED_ORIGINS.extend(extra.split(","))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
