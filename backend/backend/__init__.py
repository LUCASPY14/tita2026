"""
Backend de Cantina Tita
"""

# Importar Celery para que Django lo cargue al iniciar
from .celery import app as celery_app

__all__ = ('celery_app',)
