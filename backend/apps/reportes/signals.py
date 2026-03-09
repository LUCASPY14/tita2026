"""
Signals para la app de reportes
"""
from django.dispatch import Signal

# Signal que se dispara cuando se crea una plantilla de reporte
post_plantilla_created = Signal()
