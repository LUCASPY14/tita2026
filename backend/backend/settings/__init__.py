"""
Importa la configuración según el entorno
"""
import os

environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'test':
    from .test import *
else:
    from .development import *
