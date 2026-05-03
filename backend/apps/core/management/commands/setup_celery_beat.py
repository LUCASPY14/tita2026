"""
Management command: setup_celery_beat
Registra todas las tareas periódicas de Celery Beat en la base de datos.
Ejecutar una vez tras el deploy o cada vez que se agreguen nuevas tasks.
"""

import json

from django.core.management.base import BaseCommand

from django_celery_beat.models import CrontabSchedule, PeriodicTask

# Definición centralizada de las tareas periódicas
# (espeja el beat_schedule de celery_app.py)
PERIODIC_TASKS = [
    # ── Core ─────────────────────────────────────────────────────────────────
    {
        "name": "expirar-recargas-pendientes",
        "task": "apps.core.tasks.expirar_recargas_pendientes",
        "crontab": dict(hour="2", minute="0"),
        "description": "Expira recargas pendientes – todos los días 02:00",
    },
    # ── Notificaciones ────────────────────────────────────────────────────────
    {
        "name": "alertas-saldo-bajo",
        "task": "apps.notificaciones.tasks.generar_alertas_saldo_bajo",
        "crontab": dict(hour="8", minute="0"),
        "description": "Genera alertas de saldo bajo – todos los días 08:00",
    },
    {
        "name": "limpiar-notificaciones-antiguas",
        "task": "apps.notificaciones.tasks.limpiar_notificaciones_antiguas",
        "crontab": dict(hour="3", minute="0", day_of_week="0"),
        "description": "Limpia notificaciones antiguas – domingos 03:00",
    },
    # ── Inventario ────────────────────────────────────────────────────────────
    {
        "name": "alertar-stock-minimo",
        "task": "apps.inventario.tasks.alertar_stock_minimo",
        "crontab": dict(hour="7", minute="0"),
        "description": "Alerta stock mínimo – todos los días 07:00",
    },
    {
        "name": "verificar-vencimientos-productos",
        "task": "apps.inventario.tasks.verificar_vencimientos",
        "crontab": dict(hour="9", minute="0"),
        "description": "Verifica vencimientos de productos – todos los días 09:00",
    },
    {
        "name": "resumen-diario-stock",
        "task": "apps.inventario.tasks.generar_resumen_diario_stock",
        "crontab": dict(hour="23", minute="55"),
        "description": "Resumen diario de stock – todos los días 23:55",
    },
    # ── Ventas ───────────────────────────────────────────────────────────────
    {
        "name": "resumen-diario-ventas",
        "task": "apps.ventas.tasks.generar_resumen_diario_ventas",
        "crontab": dict(hour="23", minute="50"),
        "description": "Resumen diario de ventas – todos los días 23:50",
    },
    {
        "name": "cierre-automatico-cajas",
        "task": "apps.ventas.tasks.cerrar_cajas_automatico",
        "crontab": dict(minute="0"),
        "description": "Cierre automático de cajas abiertas >24h – cada hora",
    },  # ── Almuerzos ─────────────────────────────────────────────────
    {
        "name": "generar-cuentas-almuerzos-mensuales",
        "task": "apps.almuerzos.tasks.generar_cuentas_mensuales",
        "crontab": dict(hour="6", minute="0", day_of_month="1"),
        "description": "Genera cuentas mensuales de almuerzos – día 1 de cada mes 06:00",
    },
    {
        "name": "alertar-cuentas-almuerzos-vencidas",
        "task": "apps.almuerzos.tasks.alertar_cuentas_vencidas",
        "crontab": dict(hour="8", minute="0", day_of_month="10"),
        "description": "Alerta deudas de almuerzos vencidas – día 10 de cada mes 08:00",
    },
    # ── Reportes / KPIs ──────────────────────────────────────────────────────
    {
        "name": "calcular-kpis-diarios",
        "task": "apps.reportes.tasks.calcular_y_guardar_kpis_diarios",
        "crontab": dict(hour="23", minute="45"),
        "description": "Calcula y guarda KPIs del día – todos los días 23:45",
    },
]


class Command(BaseCommand):
    help = "Registra las tareas periódicas de Celery Beat en la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina y recrea todas las tareas (útil para actualizar schedules)",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        if reset:
            deleted, _ = PeriodicTask.objects.filter(name__in=[t["name"] for t in PERIODIC_TASKS]).delete()
            self.stdout.write(self.style.WARNING(f"  Eliminadas {deleted} tareas existentes."))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for task_def in PERIODIC_TASKS:
            crontab_kwargs = {
                "minute": task_def["crontab"].get("minute", "*"),
                "hour": task_def["crontab"].get("hour", "*"),
                "day_of_week": task_def["crontab"].get("day_of_week", "*"),
                "day_of_month": task_def["crontab"].get("day_of_month", "*"),
                "month_of_year": task_def["crontab"].get("month_of_year", "*"),
                "timezone": "America/Asuncion",
            }

            schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_kwargs)

            task_data = {
                "crontab": schedule,
                "task": task_def["task"],
                "enabled": True,
                "description": task_def.get("description", ""),
                "args": json.dumps([]),
                "kwargs": json.dumps({}),
            }

            existing = PeriodicTask.objects.filter(name=task_def["name"]).first()
            if existing:
                if reset:
                    # ya fue borrado arriba; crear nuevo
                    pass
                else:
                    # Actualizar schedule por si cambió
                    for field, value in task_data.items():
                        setattr(existing, field, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f'  ~ Actualizada: {task_def["name"]}')
                    continue

            PeriodicTask.objects.create(name=task_def["name"], **task_data)
            created_count += 1
            self.stdout.write(f'  + Creada:    {task_def["name"]}')

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo. Creadas: {created_count}  " f"Actualizadas: {updated_count}  " f"Omitidas: {skipped_count}"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Total en DB: {PeriodicTask.objects.count()} tarea(s) periódica(s)."))
