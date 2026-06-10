"""
Backfill Venta.hijo desde Venta.tarjeta.hijo para ventas anteriores al fix
que garantiza la auto-población del FK hijo en el service layer.

Uso:
    python manage.py backfill_ventas_hijo           # ejecuta el backfill
    python manage.py backfill_ventas_hijo --dry-run # solo muestra qué se actualizaría
"""

from django.core.management.base import BaseCommand

from apps.ventas.models import Venta


class Command(BaseCommand):
    help = "Rellena Venta.hijo desde tarjeta.hijo donde hijo es null"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios sin aplicarlos",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        qs = (
            Venta.objects
            .filter(hijo__isnull=True, tarjeta__isnull=False)
            .select_related("tarjeta", "tarjeta__hijo")
        )

        total_candidatas = qs.count()
        self.stdout.write(f"Ventas con hijo=null y tarjeta asignada: {total_candidatas}")

        actualizadas = 0
        sin_hijo_en_tarjeta = 0

        for venta in qs.iterator(chunk_size=500):
            hijo = venta.tarjeta.hijo if venta.tarjeta else None
            if not hijo:
                sin_hijo_en_tarjeta += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [dry-run] Venta #{venta.id} "
                    f"tarjeta={venta.tarjeta_id} -> hijo={hijo}"
                )
            else:
                venta.hijo = hijo
                venta.save(update_fields=["hijo"])

            actualizadas += 1

        accion = "Actualizaría" if dry_run else "Actualizadas"
        self.stdout.write(
            self.style.SUCCESS(
                f"{accion} {actualizadas} ventas. "
                f"Tarjetas sin hijo asignado: {sin_hijo_en_tarjeta}."
            )
        )
