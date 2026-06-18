"""
Configuración de tests — única config activa (PostgreSQL).
Base de datos: cantina_tita_test (configurable vía DB_TEST_NAME).
"""

from .base import *

DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_TEST_NAME", "cantina_tita_test"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "ATOMIC_REQUESTS": False,
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "TEST": {
            "NAME": os.environ.get("DB_TEST_NAME", "cantina_tita_test"),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = []

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DummyCache: los throttles de DRF usan el caché para contar requests;
# con DummyCache nunca se acumula estado entre tests → sin falsos 429.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

BANCARD_PUBLIC_KEY = "test_public_key_xxx"
BANCARD_PRIVATE_KEY = "test_private_key_xxx"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}
