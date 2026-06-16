"""
Elimina tokens de recuperación y verificación de email usados o expirados.

Uso recomendado (cron diario, ej 03:00):
    python manage.py limpiar_tokens
    python manage.py limpiar_tokens --dias 60
    python manage.py limpiar_tokens --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.usuarios.models import TokenRecuperacion, TokenVerificacion


class Command(BaseCommand):
    help = "Elimina tokens de recuperación y verificación usados o expirados con más de N días."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=30,
            help="Antigüedad mínima en días para eliminar el token (default: 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra cuántos tokens se eliminarían, sin borrar nada.",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        dry_run = options["dry_run"]
        corte = timezone.now() - timedelta(days=dias)

        # Tokens candidatos: usados O ya expirados, con más de `dias` de antigüedad
        qs_rec = TokenRecuperacion.objects.filter(
            fecha_creacion__lt=corte
        ).filter(Q(usado=True) | Q(fecha_expiracion__lt=timezone.now()))

        qs_ver = TokenVerificacion.objects.filter(
            fecha_creacion__lt=corte
        ).filter(Q(usado=True) | Q(expira_en__lt=timezone.now()))

        total_rec = qs_rec.count()
        total_ver = qs_ver.count()
        total = total_rec + total_ver

        if dry_run:
            self.stdout.write(
                f"[DRY RUN] Tokens recuperación a eliminar: {total_rec}\n"
                f"[DRY RUN] Tokens verificación a eliminar: {total_ver}\n"
                f"[DRY RUN] Total: {total} (ninguno fue eliminado)"
            )
            return

        qs_rec.delete()
        qs_ver.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Tokens eliminados: {total_rec} recuperación + {total_ver} verificación = {total} total."
            )
        )
