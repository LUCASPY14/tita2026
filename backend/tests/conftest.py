"""
Configuración de pytest
"""
import pytest
import django
from django.conf import settings
from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Configurar base de datos para tests"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    # Ejecutar migraciones
    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb', verbosity=0)
