"""
Configuración de Celery para el proyecto Cantina Tita
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab

# Contadores Prometheus para monitoreo de Celery.
# Se registran en el proceso del worker, no en el web process, por lo que
# Prometheus solo los verá si hay un PushGateway o si el worker expone /metrics.
# En esta arquitectura los usamos para logging estructurado y alertas Sentry.
try:
    from prometheus_client import Counter as _Counter
    CELERY_TASK_FAILURES = _Counter(
        "celery_task_failures_total",
        "Total de tareas Celery que fallaron tras agotar reintentos",
        ["task_name"],
    )
    CELERY_TASK_SUCCESS = _Counter(
        "celery_task_success_total",
        "Total de tareas Celery completadas exitosamente",
        ["task_name"],
    )
except Exception:
    CELERY_TASK_FAILURES = None
    CELERY_TASK_SUCCESS = None

logger = logging.getLogger(__name__)

# Establecer módulo de settings de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.base")

app = Celery("cantina_tita")

# Configuración desde settings de Django con namespace CELERY
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks en todas las apps
app.autodiscover_tasks()

# Configuración de tareas periódicas (Celery Beat)
app.conf.beat_schedule = {
    # ── Core ──────────────────────────────────────────────────────────
    "expirar-recargas-pendientes": {
        "task": "apps.core.tasks.expirar_recargas_pendientes",
        "schedule": crontab(hour=2, minute=0),  # Todos los días 02:00
    },
    # ── Notificaciones ────────────────────────────────────────────────
    "alertas-saldo-bajo": {
        "task": "apps.notificaciones.tasks.generar_alertas_saldo_bajo",
        "schedule": crontab(hour=8, minute=0),  # Todos los días 08:00
    },
    "limpiar-notificaciones-antiguas": {
        "task": "apps.notificaciones.tasks.limpiar_notificaciones_antiguas",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Domingos 03:00
    },
    "enviar-emails-pendientes": {
        "task": "apps.notificaciones.tasks.enviar_emails_pendientes",
        "schedule": crontab(minute="*/15"),  # Cada 15 minutos
    },
    # ── Inventario ────────────────────────────────────────────────────
    "alertar-stock-minimo": {
        "task": "apps.inventario.tasks.alertar_stock_minimo",
        "schedule": crontab(hour=7, minute=0),  # Todos los días 07:00
    },
    "verificar-vencimientos-productos": {
        "task": "apps.inventario.tasks.verificar_vencimientos",
        "schedule": crontab(hour=9, minute=0),  # Todos los días 09:00
    },
    "resumen-diario-stock": {
        "task": "apps.inventario.tasks.generar_resumen_diario_stock",
        "schedule": crontab(hour=23, minute=55),  # Todos los días 23:55
    },
    # ── Particionado DB ───────────────────────────────────────────────
    "crear-particion-anio-siguiente": {
        "task": "apps.core.tasks.crear_particion_anio_siguiente",
        "schedule": crontab(hour=4, minute=0, day_of_month=1, month_of_year=12),  # 1 dic 04:00
    },
    # ── Ventas ────────────────────────────────────────────────────────
    "resumen-diario-ventas": {
        "task": "apps.ventas.tasks.generar_resumen_diario_ventas",
        "schedule": crontab(hour=23, minute=50),  # Todos los días 23:50
    },
    "cierre-automatico-cajas": {
        "task": "apps.ventas.tasks.cerrar_cajas_automatico",
        "schedule": crontab(minute=0),  # Cada hora en punto
    },  # ── Almuerzos ─────────────────────────────────────────────────
    "cerrar-cuentas-almuerzos-mes-anterior": {
        "task": "apps.almuerzos.tasks.cerrar_cuentas_mes_anterior",
        "schedule": crontab(hour=5, minute=0, day_of_month=1),  # Día 1 de cada mes 05:00 (antes de generar)
    },
    "generar-cuentas-almuerzos-mensuales": {
        "task": "apps.almuerzos.tasks.generar_cuentas_mensuales",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),  # Día 1 de cada mes 06:00
    },
    "alertar-cuentas-almuerzos-vencidas": {
        "task": "apps.almuerzos.tasks.alertar_cuentas_vencidas",
        "schedule": crontab(hour=8, minute=0, day_of_month=10),  # Día 10 de cada mes 08:00
    },

}

app.conf.timezone = "America/Asuncion"  # Paraguay timezone

# Tareas críticas que disparan alerta cuando fallan
_CRITICAL_TASKS = {
    "apps.almuerzos.tasks.cerrar_cuentas_mes_anterior",
    "apps.almuerzos.tasks.generar_cuentas_mensuales",
    "apps.ventas.tasks.generar_resumen_diario_ventas",
    "apps.inventario.tasks.generar_resumen_diario_stock",
}


@app.on_after_finalize.connect
def setup_task_failure_handler(sender, **kwargs):
    """Registra el signal task_failure para alertar cuando fallen tareas críticas."""
    from celery.signals import task_failure

    @task_failure.connect
    def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kw):
        task_name = getattr(sender, "name", "") or ""

        if CELERY_TASK_FAILURES is not None:
            try:
                CELERY_TASK_FAILURES.labels(task_name=task_name).inc()
            except Exception:
                pass

        if task_name not in _CRITICAL_TASKS:
            return
        logger.error(
            "TAREA CRÍTICA FALLÓ | task=%s | id=%s | error=%s",
            task_name, task_id, exception,
        )
        try:
            import django
            from django.conf import settings as django_settings
            for _, admin_email in getattr(django_settings, "ADMINS", []):
                from apps.notificaciones.services import EmailService
                EmailService.enviar_simple(
                    destinatario_email=admin_email,
                    destinatario_nombre="Admin",
                    asunto=f"[Cantina Tita] Tarea crítica falló: {task_name}",
                    cuerpo=(
                        f"La tarea {task_name} (id={task_id}) falló.\n\n"
                        f"Error: {exception}\n\n"
                        f"Traceback:\n{einfo}"
                    ),
                )
        except Exception as e:
            logger.exception("No se pudo enviar alerta de fallo: %s", e)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug"""
    print(f"Request: {self.request!r}")
