"""
Management command para crear roles iniciales del sistema.

Este comando debe ejecutarse antes de setup_limites_inicial.

Uso:
    python manage.py crear_roles_iniciales
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.usuarios.models import Roles


class Command(BaseCommand):
    help = "Crea los roles iniciales del sistema (Admin, Gerente, Cajero, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--recrear",
            action="store_true",
            help="Eliminar y recrear todos los roles (¡CUIDADO: puede romper relaciones!)",
        )

    def handle(self, *args, **options):
        recrear = options.get("recrear", False)

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("CREAR ROLES INICIALES"))
        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write("")

        # Definir roles a crear
        roles_iniciales = [
            {
                "nombre_rol": "Admin",
                "descripcion": "Administrador del sistema con acceso completo",
                "estado": True,
            },
            {
                "nombre_rol": "Gerente",
                "descripcion": "Gerente con autorización de operaciones altas",
                "estado": True,
            },
            {
                "nombre_rol": "Cajero",
                "descripcion": "Cajero de ventas con límites básicos",
                "estado": True,
            },
            {
                "nombre_rol": "Encargado Compras",
                "descripcion": "Encargado de gestión de compras y proveedores",
                "estado": True,
            },
            {
                "nombre_rol": "Encargado Inventario",
                "descripcion": "Encargado de control de stock y almacén",
                "estado": True,
            },
        ]

        if recrear:
            self.stdout.write(self.style.WARNING("⚠️  Modo RECREAR activado - Se eliminarán roles existentes"))
            confirmar = input('¿Está seguro? (escriba "SI" para confirmar): ')
            if confirmar != "SI":
                self.stdout.write(self.style.ERROR("Operación cancelada"))
                return

            # Eliminar roles existentes
            eliminados = Roles.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"   ✓ {eliminados[0]} roles eliminados"))
            self.stdout.write("")

        # Crear o actualizar roles
        with transaction.atomic():
            creados = 0
            actualizados = 0

            for datos_rol in roles_iniciales:
                rol, created = Roles.objects.update_or_create(
                    nombre_rol=datos_rol["nombre_rol"],
                    defaults={
                        "descripcion": datos_rol["descripcion"],
                        "estado": datos_rol["estado"],
                    },
                )

                if created:
                    creados += 1
                    self.stdout.write(self.style.SUCCESS(f"   ✓ Creado: {rol.nombre_rol}"))
                else:
                    actualizados += 1
                    self.stdout.write(self.style.WARNING(f"   ↻ Actualizado: {rol.nombre_rol}"))

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("─" * 70))
        self.stdout.write(self.style.WARNING("RESUMEN"))
        self.stdout.write(self.style.WARNING("─" * 70))
        self.stdout.write(f"   Roles creados:       {creados}")
        self.stdout.write(f"   Roles actualizados:  {actualizados}")
        self.stdout.write(f"   Total en sistema:    {Roles.objects.count()}")
        self.stdout.write("")

        # Listar todos los roles
        self.stdout.write(self.style.SUCCESS("✅ Roles disponibles en el sistema:"))
        self.stdout.write("")
        for rol in Roles.objects.all().order_by("nombre_rol"):
            icono = "✓" if rol.estado else "✗"
            estado = "estado" if rol.estado else "Inactivo"
            self.stdout.write(f"   {icono} [{rol.id_rol:2d}] {rol.nombre_rol:25s} - {rol.descripcion} ({estado})")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("✅ Comando completado exitosamente"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("PRÓXIMO PASO:"))
        self.stdout.write("   python manage.py setup_limites_inicial")
        self.stdout.write("")
