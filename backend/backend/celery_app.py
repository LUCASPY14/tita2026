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
    # ── Core ──────────────────────────────────────────────────────────
    'expirar-recargas-pendientes': {
        'task': 'apps.core.tasks.expirar_recargas_pendientes',
        'schedule': crontab(hour=2, minute=0),          # Todos los días 02:00
    },
    # ── Notificaciones ────────────────────────────────────────────────
    'alertas-saldo-bajo': {
        'task': 'apps.notificaciones.tasks.generar_alertas_saldo_bajo',
        'schedule': crontab(hour=8, minute=0),          # Todos los días 08:00
    },
    'limpiar-notificaciones-antiguas': {
        'task': 'apps.notificaciones.tasks.limpiar_notificaciones_antiguas',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Domingos 03:00
    },
    # ── Inventario ────────────────────────────────────────────────────
    'alertar-stock-minimo': {
        'task': 'apps.inventario.tasks.alertar_stock_minimo',
        'schedule': crontab(hour=7, minute=0),          # Todos los días 07:00
    },
    'verificar-vencimientos-productos': {
        'task': 'apps.inventario.tasks.verificar_vencimientos',
        'schedule': crontab(hour=9, minute=0),          # Todos los días 09:00
    },
    'resumen-diario-stock': {
        'task': 'apps.inventario.tasks.generar_resumen_diario_stock',
        'schedule': crontab(hour=23, minute=55),        # Todos los días 23:55
    },
    # ── Ventas ────────────────────────────────────────────────────────
    'resumen-diario-ventas': {
        'task': 'apps.ventas.tasks.generar_resumen_diario_ventas',
        'schedule': crontab(hour=23, minute=50),        # Todos los días 23:50
    },
    'cierre-automatico-cajas': {
        'task': 'apps.ventas.tasks.cerrar_cajas_automatico',
        'schedule': crontab(minute=0),                  # Cada hora en punto
    },    # ── Almuerzos ─────────────────────────────────────────────────
    'generar-cuentas-almuerzos-mensuales': {
        'task': 'apps.almuerzos.tasks.generar_cuentas_mensuales',
        'schedule': crontab(hour=6, minute=0, day_of_month=1),  # Día 1 de cada mes 06:00
    },
    'alertar-cuentas-almuerzos-vencidas': {
        'task': 'apps.almuerzos.tasks.alertar_cuentas_vencidas',
        'schedule': crontab(hour=8, minute=0, day_of_month=10), # Día 10 de cada mes 08:00
    },
    # ── Reportes / KPIs ───────────────────────────────────────────────────────
    'calcular-kpis-diarios': {
        'task': 'apps.reportes.tasks.calcular_y_guardar_kpis_diarios',
        'schedule': crontab(hour=23, minute=45),       # Todos los días 23:45
    },
}

app.conf.timezone = 'America/Asuncion'  # Paraguay timezone

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug"""
    print(f'Request: {self.request!r}')
