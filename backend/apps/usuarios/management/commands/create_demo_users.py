"""
Crea (o actualiza) un usuario de prueba por cada rol del sistema.
Idempotente: si el email ya existe solo actualiza la contrasena.

Uso:
    python manage.py create_demo_users
    python manage.py create_demo_users --password MiClave123

Usuarios creados:
    admin@tita.local       / demo1234  (ADMIN)
    cajero@tita.local      / demo1234  (CAJERO)
    supervisor@tita.local  / demo1234  (SUPERVISOR)
    cobrador@tita.local    / demo1234  (COBRADOR)
    cocina@tita.local      / demo1234  (COCINA)
"""

from django.core.management.base import BaseCommand

from apps.usuarios.models import Usuario


DEMO_USERS = [
    {"email": "admin@tita.local",      "nombre": "Admin",      "apellido": "Demo", "rol": Usuario.Rol.ADMIN},
    {"email": "cajero@tita.local",     "nombre": "Cajero",     "apellido": "Demo", "rol": Usuario.Rol.CAJERO},
    {"email": "supervisor@tita.local", "nombre": "Supervisor", "apellido": "Demo", "rol": Usuario.Rol.SUPERVISOR},
    {"email": "cobrador@tita.local",   "nombre": "Cobrador",   "apellido": "Demo", "rol": Usuario.Rol.COBRADOR},
    {"email": "cocina@tita.local",     "nombre": "Cocina",     "apellido": "Demo", "rol": Usuario.Rol.COCINA},
]


class Command(BaseCommand):
    help = "Crea usuarios de prueba para cada rol del sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="demo1234",
            help="Contrasena para todos los usuarios demo (default: demo1234)",
        )

    def handle(self, *args, **options):
        password = options["password"]
        self.stdout.write(self.style.MIGRATE_HEADING("=== create_demo_users ==="))

        for spec in DEMO_USERS:
            user, created = Usuario.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "nombre": spec["nombre"],
                    "apellido": spec["apellido"],
                    "rol": spec["rol"],
                    "is_active": True,
                    "email_verificado": True,
                },
            )
            user.set_password(password)
            if not created:
                user.rol = spec["rol"]
                user.is_active = True
            user.save()

            action = "Creado" if created else "Actualizado"
            self.stdout.write(
                f"  {action}: {spec['email']:<30} rol={spec['rol']}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nListo. Contrasena: {password}"
        ))
