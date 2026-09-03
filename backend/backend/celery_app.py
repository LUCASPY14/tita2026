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
_PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://pushgateway:9091")

try:
    from prometheus_client import Counter as _Counter, push_to_gateway as _push_to_gateway, CollectorRegistry as _Registry
    _CELERY_REGISTRY = _Registry()
    CELERY_TASK_FAILURES = _Counter(
        "celery_task_failures_total",
        "Total de tareas Celery que fallaron tras agotar reintentos",
        ["task_name"],
        registry=_CELERY_REGISTRY,
    )
    CELERY_TASK_SUCCESS = _Counter(
        "celery_task_success_total",
        "Total de tareas Celery completadas exitosamente",
        ["task_name"],
        registry=_CELERY_REGISTRY,
    )
except Exception:
    CELERY_TASK_FAILURES = None
    CELERY_TASK_SUCCESS = None
    _push_to_gateway = None
    _CELERY_REGISTRY = None


def _push_metrics(job: str = "celery") -> None:
    """Envía métricas al PushGateway. Silencioso ante cualquier fallo."""
    if _push_to_gateway is None or _CELERY_REGISTRY is None:
        return
    try:
        _push_to_gateway(_PUSHGATEWAY_URL, job=job, registry=_CELERY_REGISTRY)
    except Exception:
        pass

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
    "procesar-solicitudes-notificacion": {
        "task": "apps.notificaciones.tasks.procesar_solicitudes_pendientes",
        "schedule": crontab(minute="*/15"),  # Cada 15 minutos
    },
    # ── Inventario ────────────────────────────────────────────────────
    "alertar-stock-minimo": {
        "task": "apps.inventario.tasks.alertar_stock_minimo",
        "schedule": crontab(hour=7, minute=0),  # Todos los días 07:00
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
    # "cierre-automatico-cajas" desactivado — el cierre de caja es manual.
    # ── Almuerzos ─────────────────────────────────────────────────
    "cerrar-cuentas-almuerzos-mes-anterior": {
        "task": "apps.almuerzos.tasks.cerrar_cuentas_mes_anterior",
        "schedule": crontab(hour=5, minute=0, day_of_month=1),  # Día 1 de cada mes 05:00 (antes de generar)
    },
    "generar-cuentas-almuerzos-mensuales": {
        "task": "apps.almuerzos.tasks.generar_cuentas_mensuales",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),  # Día 1 de cada mes 06:00
    },
    "avisar-deuda-almuerzo": {
        "task": "apps.almuerzos.tasks.avisar_deuda_almuerzo",
        "schedule": crontab(hour=8, minute=0, day_of_week=5),  # Todos los viernes 08:00
    },
    "alertar-saldo-almuerzo-negativo": {
        "task": "apps.almuerzos.tasks.alertar_saldo_almuerzo_negativo",
        "schedule": crontab(hour=9, minute=45),   # Todos los días 09:45
    },
    # ── Usuarios / Auditoría ──────────────────────────────────────────
    "limpiar-audit-logs": {
        "task": "apps.usuarios.tasks.limpiar_audit_logs",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),  # Día 1 de cada mes 01:00
    },
    # ── Contabilidad ──────────────────────────────────────────────────
    "refrescar-mv-balance-cliente": {
        "task": "apps.contabilidad.tasks.refrescar_mv_balance_cliente",
        "schedule": crontab(minute="*/15"),  # Cada 15 minutos
    },
    "recordar-facturacion-mensual-pendiente": {
        "task": "apps.contabilidad.tasks.recordar_facturacion_mensual_pendiente",
        "schedule": crontab(hour=8, minute=45, day_of_month=5),  # Día 5 de cada mes 08:45
    },
    # ── Compras ───────────────────────────────────────────────────────
    "alertar-ordenes-compra-pendientes": {
        "task": "apps.compras.tasks.alertar_ordenes_compra_pendientes",
        "schedule": crontab(hour=9, minute=30),   # Todos los días 09:30
    },
    "alertar-compras-pendientes-pago": {
        "task": "apps.compras.tasks.alertar_compras_pendientes_pago",
        "schedule": crontab(hour=10, minute=0),   # Todos los días 10:00
    },
    # ── Productos ─────────────────────────────────────────────────────────
    "sincronizar-costos-desde-compras": {
        "task": "apps.productos.tasks.sincronizar_costos_desde_compras",
        "schedule": crontab(hour=1, minute=30),   # Todos los días 01:30
    },
    # ── Clientes ──────────────────────────────────────────────────────
    "alertar-saldo-negativo-prolongado": {
        "task": "apps.clientes.tasks.alertar_saldo_negativo_prolongado",
        "schedule": crontab(hour=9, minute=15),   # Todos los días 09:15
    },
    "resumen-mensual-deuda-clientes": {
        "task": "apps.clientes.tasks.resumen_mensual_deuda_clientes",
        "schedule": crontab(hour=8, minute=30, day_of_month=5),  # Día 5 de cada mes 08:30
    },
    "dar-baja-alumnos-ultimo-curso": {
        "task": "apps.clientes.tasks.dar_baja_alumnos_ultimo_curso",
        "schedule": crontab(hour=5, minute=0, day_of_month=20, month_of_year=12),  # 20 dic 05:00
    },
    "marcar-alumnos-pendientes-purga": {
        "task": "apps.clientes.tasks.marcar_alumnos_pendientes_purga",
        "schedule": crontab(hour=7, minute=0, day_of_month=1),  # Día 1 de cada mes 07:00
    },

}

app.conf.timezone = "America/Asuncion"  # Paraguay timezone

# Tareas críticas que disparan alerta cuando fallan
_CRITICAL_TASKS = {
    "apps.almuerzos.tasks.cerrar_cuentas_mes_anterior",
    "apps.almuerzos.tasks.generar_cuentas_mensuales",
}


@app.on_after_finalize.connect
def setup_task_failure_handler(sender, **kwargs):
    """Registra signals task_failure y task_success para métricas y alertas."""
    from celery.signals import task_failure, task_success

    @task_failure.connect
    def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kw):
        task_name = getattr(sender, "name", "") or ""

        if CELERY_TASK_FAILURES is not None:
            try:
                CELERY_TASK_FAILURES.labels(task_name=task_name).inc()
                _push_metrics()
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

    @task_success.connect
    def on_task_success(sender=None, result=None, **kw):
        task_name = getattr(sender, "name", "") or ""
        if CELERY_TASK_SUCCESS is not None:
            try:
                CELERY_TASK_SUCCESS.labels(task_name=task_name).inc()
                _push_metrics()
            except Exception:
                pass


_logger = logging.getLogger(__name__)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug"""
    _logger.debug("Request: %s", self.request)
