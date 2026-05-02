"""
Configuración para tests
"""

from .base import *

DEBUG = True

# Deshabilitar soporte de zona horaria en tests para simplificar la ejecución
# y evitar dependencias de configuración del motor SQL.
USE_TZ = False
TIME_ZONE = "UTC"

# Base de datos SQL Server para tests
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.environ.get("DB_NAME", "titadb"),
        "HOST": os.environ.get("DB_HOST", "np:localhost"),
        "PORT": os.environ.get("DB_PORT", "1433"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "ATOMIC_REQUESTS": False,
        "OPTIONS": {
            "driver": "ODBC Driver 18 for SQL Server",
            "extra_params": "TrustServerCertificate=yes;MARS_Connection=yes",
        },
        "TEST": {
            "NAME": os.environ.get("DB_TEST_NAME", "test_titadb"),
        },
    }
}


# Passwords más simples para tests
AUTH_PASSWORD_VALIDATORS = []

# Hasher rápido para tests (evita bcrypt lento y tests de rendimiento flaky)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email backend para tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Logging mínimo en tests
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
