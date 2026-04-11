"""
Configuración de desarrollo para Django
"""
from .base import *

DEBUG = True

# Database para desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': os.environ.get('DB_NAME', 'titadb'),
        'HOST': os.environ.get('DB_HOST', 'np:localhost'),
        'ATOMIC_REQUESTS': False,
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'trusted_connection': 'yes',
            'extra_params': 'TrustServerCertificate=yes;MARS_Connection=yes',
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
