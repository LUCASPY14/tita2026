"""
Configuración de Celery para el proyecto Cantina Tita
"""
import os
from celery import Celery
from celery.schedules import crontab

# Establecer módulo de settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')

app = Celery('cantina_tita')

# Configuración desde settings de Django con namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks en todas las apps
app.autodiscover_tasks()

# Configuración de tareas periódicas (Celery Beat)
app.conf.beat_schedule = {
    'expirar-recargas-pendientes': {
        'task': 'apps.core.tasks.expirar_recargas_pendientes',
        'schedule': crontab(hour=2, minute=0),  # Todos los días a las 2 AM
    },
    'alertas-saldo-bajo': {
        'task': 'apps.notificaciones.tasks.generar_alertas_saldo_bajo',
        'schedule': crontab(hour=8, minute=0),  # Todos los días a las 8 AM
    },
    'alertas-vencimiento-productos': {
        'task': 'apps.inventario.tasks.verificar_vencimientos',
        'schedule': crontab(hour=9, minute=0),  # Todos los días a las 9 AM
    },
}

app.conf.timezone = 'America/Asuncion'  # Paraguay timezone

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug"""
    print(f'Request: {self.request!r}')
