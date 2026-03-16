"""
Configuración para tests
"""
from .base import *

DEBUG = True

# Deshabilitar soporte de zona horaria en tests para evitar dependencia
# de tablas mysql_tzinfo (CONVERT_TZ retorna NULL si no están instaladas)
USE_TZ = False
TIME_ZONE = 'UTC'

# Base de datos MySQL para tests (igual que producción)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'dbcantinatita'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'L01G05S33Vice.42'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'ATOMIC_REQUESTS': False,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
            'NAME': os.environ.get('DB_TEST_NAME', 'test_dbcantinatita'),
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}

# Passwords más simples para tests
AUTH_PASSWORD_VALIDATORS = []

# Hasher rápido para tests (evita bcrypt lento y tests de rendimiento flaky)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend para tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Logging mínimo en tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}
