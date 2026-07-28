"""
Crea (o actualiza) el usuario administrador de producción.
Idempotente: si el email ya existe solo actualiza la contraseña.

Uso:
    python manage.py create_admin --email admin@miempresa.com --password MiClaveSegura

En Docker:
    docker compose exec backend python manage.py create_admin \
        --email admin@miempresa.com \
        --password MiClaveSegura
"""

from django.core.management.base import BaseCommand, CommandError

from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea o actualiza el usuario administrador de producción."

    def add_arguments(self, parser):
        parser.add_argument("--email",    required=True, help="Email del administrador")
        parser.add_argument("--password", required=True, help="Contraseña del administrador")
        parser.add_argument("--nombre",   default="Admin",    help="Nombre (default: Admin)")
        parser.add_argument("--apellido", default="Cantina",  help="Apellido (default: Cantina)")

    def handle(self, *args, **options):
        email    = options["email"].strip().lower()
        password = options["password"]
        nombre   = options["nombre"].strip()
        apellido = options["apellido"].strip()

        if len(password) < 8:
            raise CommandError("La contraseña debe tener al menos 8 caracteres.")

        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                "nombre":           nombre,
                "apellido":         apellido,
                "rol":              Usuario.Rol.ADMIN,
                "is_active":        True,
                "is_staff":         True,
                "email_verificado": True,
            },
        )

        user.set_password(password)
        if not created:
            user.rol              = Usuario.Rol.ADMIN
            user.is_active        = True
            user.is_staff         = True
            user.email_verificado = True
        user.save()

        action = "Creado" if created else "Actualizado"
        self.stdout.write(self.style.SUCCESS(
            f"{action} administrador: {email}"
        ))
        self.stdout.write(
            "  Podés crear el resto de usuarios desde el sistema en /usuarios."
        )
