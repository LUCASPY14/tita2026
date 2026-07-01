"""
Crea usuarios CLIENTE_WEB para todos los clientes activos que no tengan uno.

Uso:
    python manage.py crear_usuarios_portal
    python manage.py crear_usuarios_portal --todos     # incluye clientes inactivos
    python manage.py crear_usuarios_portal --dry-run   # solo muestra qué haría
"""

from django.core.management.base import BaseCommand

from apps.clientes.models import Cliente
from apps.clientes.views import _crear_usuario_portal


class Command(BaseCommand):
    help = "Crea usuarios portal (CLIENTE_WEB) para clientes existentes sin usuario."

    def add_arguments(self, parser):
        parser.add_argument("--todos", action="store_true", help="Incluir clientes inactivos")
        parser.add_argument("--dry-run", action="store_true", help="Solo mostrar, no crear")

    def handle(self, *args, **options):
        qs = Cliente.objects.filter(usuario_portal__isnull=True)
        if not options["todos"]:
            qs = qs.filter(activo=True)

        total = qs.count()
        self.stdout.write(f"Clientes sin usuario portal: {total}")

        if options["dry_run"]:
            for c in qs:
                self.stdout.write(f"  [dry-run] {c.ruc_ci} — {c.nombre_completo}")
            return

        creados = 0
        errores = 0
        for cliente in qs:
            try:
                _crear_usuario_portal(cliente)
                self.stdout.write(f"  + {cliente.ruc_ci} — {cliente.nombre_completo}")
                creados += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ! {cliente.ruc_ci}: {e}"))
                errores += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nListo. Creados: {creados} | Errores: {errores}"
        ))
