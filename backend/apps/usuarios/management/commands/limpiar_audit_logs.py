"""
Archiva o elimina registros de auditoría y logs de seguridad antiguos.

Política de retención por defecto:
  - auditoria_operaciones   → 365 días
  - intentos_login          → 90 días
  - intentos_2fa            → 90 días
  - renovaciones_sesion     → 90 días
  - historical_* (simple_history) → 365 días

Uso recomendado (cron mensual, ej 02:00 primer día del mes):
    python manage.py limpiar_audit_logs
    python manage.py limpiar_audit_logs --dias-operaciones 180 --dias-login 30
    python manage.py limpiar_audit_logs --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.usuarios.models import (
    AuditoriaOperacion,
    IntentoLogin,
    Intento2FA,
    RenovacionSesion,
)


class Command(BaseCommand):
    help = "Elimina registros de auditoría y logs de seguridad más antiguos que los umbrales configurados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias-operaciones",
            type=int,
            default=365,
            help="Días de retención para auditoria_operaciones (default: 365).",
        )
        parser.add_argument(
            "--dias-login",
            type=int,
            default=90,
            help="Días de retención para intentos_login e intentos_2fa (default: 90).",
        )
        parser.add_argument(
            "--dias-sesiones",
            type=int,
            default=90,
            help="Días de retención para renovaciones_sesion (default: 90).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra cuántos registros se eliminarían, sin borrar nada.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        ahora = timezone.now()

        cortes = {
            "auditoria_operaciones": ahora - timedelta(days=options["dias_operaciones"]),
            "intentos_login": ahora - timedelta(days=options["dias_login"]),
            "intentos_2fa": ahora - timedelta(days=options["dias_login"]),
            "renovaciones_sesion": ahora - timedelta(days=options["dias_sesiones"]),
        }

        targets = [
            ("auditoria_operaciones", AuditoriaOperacion, "fecha_operacion", cortes["auditoria_operaciones"]),
            ("intentos_login",        IntentoLogin,        "fecha_intento",   cortes["intentos_login"]),
            ("intentos_2fa",          Intento2FA,          "fecha_intento",   cortes["intentos_2fa"]),
            ("renovaciones_sesion",   RenovacionSesion,    "fecha_renovacion", cortes["renovaciones_sesion"]),
        ]

        total_general = 0
        for nombre, modelo, campo_fecha, corte in targets:
            qs = modelo.objects.filter(**{f"{campo_fecha}__lt": corte})
            cantidad = qs.count()
            total_general += cantidad

            if dry_run:
                self.stdout.write(f"[DRY RUN] {nombre}: {cantidad} registros a eliminar (antes de {corte.date()})")
            else:
                qs.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"  {nombre}: {cantidad} registros eliminados.")
                )

        if dry_run:
            self.stdout.write(f"\n[DRY RUN] Total: {total_general} registros (ninguno fue eliminado).")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nTotal eliminado: {total_general} registros de audit logs.")
            )
            self.stdout.write(
                "Nota: las tablas historical_* de simple_history requieren limpieza manual "
                "o configurar SIMPLE_HISTORY_REVERT_DISABLED=True para el modelo."
            )
