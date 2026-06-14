"""
Configuración base de Django para el proyecto Cantina Tita
Optimizado para desarrollo local (SQLite) y producción (PostgreSQL en HP Mini)
"""

import os
import warnings
from datetime import timedelta
from pathlib import Path

# Carga variables de entorno desde archivo .env (solo desarrollo)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================================================
# SEGURIDAD
# ==============================================================================

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False") == "True"

# En producción, exigir SECRET_KEY explícita
if not DEBUG and not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("SECRET_KEY es obligatoria cuando DEBUG=False")

# Fallback SOLO para desarrollo local
if DEBUG and not SECRET_KEY:
    SECRET_KEY = "django-insecure-dev-only-cantina-tita-2024"
    warnings.warn(
        "Usando SECRET_KEY insegura para desarrollo. Configurala en .env",
        RuntimeWarning,
    )

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ==============================================================================
# APLICACIONES
# ==============================================================================

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # Para invalidar refresh tokens
    "corsheaders",
    "django_filters",
    "simple_history",
    "drf_spectacular",
    # Local apps
    "apps.core",
    "apps.usuarios",
    "apps.clientes",
    "apps.productos",
    "apps.ventas",
    "apps.compras",
    "apps.inventario",
    "apps.almuerzos",
    "apps.contabilidad",
    "apps.notificaciones",
    "apps.api_integrations",
    "channels",
    "django_prometheus",
]

AUTH_USER_MODEL = "usuarios.Usuario"

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",  # debe ser el primero
    "common.middleware.RequestIDMiddleware",                    # X-Request-ID → logs + Sentry
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "apps.usuarios.middleware.AuditContextMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",   # debe ser el último
]

# ==============================================================================
# URLS Y WSGI
# ==============================================================================

ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

if os.environ.get("USE_REDIS_CHANNELS", "False") == "True":
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# BASE DE DATOS
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "cantina_tita"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================================
# INTERNACIONALIZACIÓN
# ==============================================================================

LANGUAGE_CODE = "es-py"
TIME_ZONE = "America/Asuncion"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Buscar estáticos en apps instaladas (jazzmin, admin, rest_framework)
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Media files (fotos de perfil de hijos, etc.)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Seguridad para archivos media (fotos de menores de edad)
MEDIA_UPLOAD_MAX_SIZE = 5 * 1024 * 1024  # 5 MB máximo por archivo
MEDIA_ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "common.permissions.IsStaffUser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "MAX_PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "200/hour",
        "user": "1000/hour",
        "auth": "5/min",
    },
    "DATETIME_FORMAT": "%d/%m/%Y %H:%M",
    "DATE_FORMAT": "%d/%m/%Y",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

# ==============================================================================
# DRF SPECTACULAR (OpenAPI / Swagger)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Cantina Tita API",
    "DESCRIPTION": "API REST para el sistema de gestión de Cantina Tita",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ==============================================================================
# CACHÉ (Redis cuando esté disponible, memoria local en desarrollo)
# ==============================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")

if os.environ.get("USE_REDIS_CACHE", "False") == "True":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "cantina",
            "TIMEOUT": 300,  # 5 minutos
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cantina-tita",
        }
    }

# ==============================================================================
# CORS
# ==============================================================================

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173",
).split(",")

CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# SIMPLE JWT
# ==============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "ISSUER": "cantina-tita",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ==============================================================================
# LOGGING SIMPLIFICADO
# ==============================================================================

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "common.middleware.RequestIDFilter",
        },
    },
    "formatters": {
        "simple": {
            "format": "[{levelname}] {asctime} | rid={request_id} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "[{levelname}] {asctime} | rid={request_id} | {name} | {module}:{lineno} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["request_id"],
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "cantina.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "file_errors": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 3,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file_errors"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

# ==============================================================================
# SIPAP — Pagos QR Paraguay (solo cuando se configure)
# ==============================================================================

SIPAP_AMBIENTE = os.environ.get("SIPAP_AMBIENTE", "sandbox")
SIPAP_MERCHANT_ID = os.environ.get("SIPAP_MERCHANT_ID", "")
SIPAP_API_KEY = os.environ.get("SIPAP_API_KEY", "")
SIPAP_API_SECRET = os.environ.get("SIPAP_API_SECRET", "")
SIPAP_BANCO_AGREGADOR = os.environ.get("SIPAP_BANCO_AGREGADOR", "")
SIPAP_QR_EXPIRACION_MINUTOS = int(os.environ.get("SIPAP_QR_EXPIRACION_MINUTOS", "15"))

# ==============================================================================
# BANCARD — Pagos con tarjeta de débito/crédito (Visa/Mastercard)
# Sandbox: https://vpos.infonet.com.py:8888
# Producción: https://vpos.infonet.com.py
# Obtener credenciales en: https://comercios.bancard.com.py
# ==============================================================================

BANCARD_SANDBOX = os.environ.get("BANCARD_SANDBOX", "True") == "True"
BANCARD_PUBLIC_KEY = os.environ.get("BANCARD_PUBLIC_KEY", "")
BANCARD_PRIVATE_KEY = os.environ.get("BANCARD_PRIVATE_KEY", "")
# URL base del frontend (para redirecciones post-pago)
BANCARD_RETURN_URL = os.environ.get(
    "BANCARD_RETURN_URL",
    "http://localhost:8000/api/v1/bancard/retorno/",
)
BANCARD_CANCEL_URL = os.environ.get(
    "BANCARD_CANCEL_URL",
    "http://localhost:5173/portal/carga-saldo?estado=cancelado",
)

# ==============================================================================
# EMAIL (solo cuando se configure SMTP)
# ==============================================================================

if DEBUG:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.console.EmailBackend",
    )
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.smtp.EmailBackend",
    )

EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Cantina Tita <noreply@cantinatita.com>",
)
PORTAL_FRONTEND_URL = os.environ.get("PORTAL_FRONTEND_URL", "http://localhost:5173")

# ==============================================================================
# NOTIFICACIONES
# ==============================================================================

NOTIFICACIONES_ACTIVAS = os.environ.get("NOTIFICACIONES_ACTIVAS", "True") == "True"
NOTIFICACION_SALDO_BAJO_DEFAULT = int(
    os.environ.get("NOTIFICACION_SALDO_BAJO", "10000")  # ₲10,000
)
NOTIFICACION_INTERVALO_MINIMO = int(
    os.environ.get("NOTIFICACION_INTERVALO", "24")  # horas
)
# ==============================================================================
# JAZZMIN SETTINGS
# ==============================================================================

JAZZMIN_SETTINGS = {
    "site_title": "Cantina Tita",
    "site_header": "La Cantina de Tita",
    "site_brand": "🍽️ Cantina Tita",
    "welcome_sign": "Bienvenido a La Cantina de Tita",
    "copyright": "Cantina Tita S.A.",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "ventas": "fas fa-cash-register",
        "compras": "fas fa-truck",
        "clientes": "fas fa-users",
        "core": "fas fa-credit-card",
        "productos": "fas fa-box",
        "inventario": "fas fa-warehouse",
        "almuerzos": "fas fa-utensils",
        "contabilidad": "fas fa-calculator",
        "usuarios": "fas fa-user-shield",
        "notificaciones": "fas fa-bell",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "theme": "default",
}