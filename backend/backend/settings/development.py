"""
Configuración de desarrollo para Django
"""
from .base import *

DEBUG = True

# Database para desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dbcantinatita',
        'USER': 'root',
        'PASSWORD': 'L01G05S33Vice.42',
        'HOST': 'localhost',
        'PORT': '3306',
        'ATOMIC_REQUESTS': False,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# CORS más permisivo en desarrollo
CORS_ALLOW_ALL_ORIGINS = True

# CSRF - Deshabilitar para API (usamos JWT)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Email backend para desarrollo (consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Mostrar toolbar de debug (opcional, requiere django-debug-toolbar)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
