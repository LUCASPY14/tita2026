"""
Management command para inicializar el sistema de usuarios
Crea permisos, roles y usuario admin inicial
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Empleados, Roles
from apps.usuarios.permissions import PermissionService
from apps.usuarios.services import AuthenticationService


class Command(BaseCommand):
    help = "Inicializa el sistema de usuarios: permisos, roles y usuario admin"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-admin",
            action="store_true",
            help="No crear usuario admin (solo permisos y roles)",
        )

        parser.add_argument(
            "--admin-password",
            type=str,
            default="Admin123!@#",
            help="Contraseña para el usuario admin (default: Admin123!@#)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Inicializando Sistema de Usuarios ===\n"))

        # 1. Inicializar permisos
        self.stdout.write("1. Inicializando permisos del sistema...")
        resultado = PermissionService.inicializar_permisos()

        if resultado["permisos_creados"] > 0:
            self.stdout.write(self.style.SUCCESS(f'   ✓ {resultado["permisos_creados"]} permisos creados'))
        if resultado["permisos_existentes"] > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠ {resultado["permisos_existentes"]} permisos ya existían'))

        self.stdout.write(self.style.SUCCESS(f'   ✓ Total de permisos en el sistema: {resultado["total"]}\n'))

        # 2. Crear roles base
        self.stdout.write("2. Creando roles base...")

        roles = [
            {
                "nombre_rol": "Administrador",
                "descripcion": "Acceso total al sistema",
                "permisos": ["admin.acceso_total"],
            },
            {
                "nombre_rol": "Gerente",
                "descripcion": "Gestión de ventas, inventario y personal",
                "permisos": [
                    "ventas.ver",
                    "ventas.crear",
                    "ventas.editar",
                    "ventas.ver_reportes",
                    "inventario.ver",
                    "inventario.ajustar",
                    "productos.ver",
                    "productos.editar",
                    "clientes.ver",
                    "clientes.crear",
                    "clientes.editar",
                    "usuarios.ver",
                    "reportes.ventas",
                    "reportes.inventario",
                ],
            },
            {
                "nombre_rol": "Vendedor",
                "descripcion": "Creación de ventas y atención al cliente",
                "permisos": [
                    "ventas.ver",
                    "ventas.crear",
                    "productos.ver",
                    "clientes.ver",
                    "clientes.crear",
                    "inventario.ver",
                ],
            },
            {
                "nombre_rol": "Bodeguero",
                "descripcion": "Gestión de inventario y compras",
                "permisos": [
                    "inventario.ver",
                    "inventario.ajustar",
                    "inventario.transferir",
                    "compras.ver",
                    "compras.crear",
                    "productos.ver",
                ],
            },
            {
                "nombre_rol": "Contador",
                "descripcion": "Acceso a reportes financieros y contabilidad",
                "permisos": [
                    "reportes.ventas",
                    "reportes.inventario",
                    "reportes.financieros",
                    "ventas.ver",
                    "compras.ver",
                    "inventario.ver_valorizado",
                    "configuracion.gestionar_impuestos",
                ],
            },
        ]

        for rol_data in roles:
            rol, created = Roles.objects.get_or_create(
                nombre_rol=rol_data["nombre_rol"],
                defaults={"descripcion": rol_data["descripcion"], "estado": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Rol creado: {rol_data["nombre_rol"]}'))

                # Asignar permisos al rol
                for permiso_codigo in rol_data["permisos"]:
                    PermissionService.asignar_permiso_a_rol(rol, permiso_codigo, None)

                self.stdout.write(f'     - {len(rol_data["permisos"])} permisos asignados')
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ Rol ya existía: {rol_data["nombre_rol"]}'))

        self.stdout.write("")

        # 3. Crear usuario admin
        if not options["skip_admin"]:
            self.stdout.write("3. Creando usuario administrador...")

            # Verificar si ya existe
            if Empleados.objects.filter(usuario="admin").exists():
                self.stdout.write(self.style.WARNING("   ⚠ Usuario admin ya existe\n"))
            else:
                rol_admin = Roles.objects.get(nombre_rol="Administrador")

                resultado = AuthenticationService.crear_empleado(
                    nombre="Administrador",
                    apellido="Sistema",
                    usuario="admin",
                    email="admin@cantinatita.com",
                    password=options["admin_password"],
                    id_rol=rol_admin.id_rol,  # Usar id_rol en lugar de id
                    creado_por=None,
                    ip_address="127.0.0.1",
                )

                if resultado["success"]:
                    self.stdout.write(self.style.SUCCESS("   ✓ Usuario admin creado exitosamente"))
                    self.stdout.write(f"     - Usuario: admin")
                    self.stdout.write(f'     - Password: {options["admin_password"]}')
                    self.stdout.write(f"     - Email: admin@cantinatita.com\n")
                else:  # pragma: no cover
                    self.stdout.write(self.style.ERROR(f'   ✗ Error al crear admin: {resultado["mensaje"]}\n'))

        # 4. Resumen
        self.stdout.write(self.style.MIGRATE_HEADING("=== Resumen de Inicialización ===\n"))

        total_permisos = PermissionService.inicializar_permisos()["total"]
        total_roles = Roles.objects.filter(estado=True).count()
        total_empleados = Empleados.objects.filter(estado=True).count()

        self.stdout.write(f"Permisos del sistema: {total_permisos}")
        self.stdout.write(f"Roles creados: {total_roles}")
        self.stdout.write(f"Empleados activos: {total_empleados}")

        self.stdout.write(self.style.SUCCESS("\n✅ Inicialización completada exitosamente\n"))

        # 5. Instrucciones
        self.stdout.write(self.style.MIGRATE_HEADING("=== Próximos Pasos ===\n"))
        self.stdout.write("1. Iniciar sesión con el usuario admin:")
        self.stdout.write("   POST /api/v1/usuarios/auth/login/")
        self.stdout.write('   {"usuario": "admin", "password": "' + options["admin_password"] + '"}\n')
        self.stdout.write("2. Cambiar la contraseña del admin:")
        self.stdout.write("   POST /api/v1/usuarios/auth/cambiar_password/\n")
        self.stdout.write("3. Habilitar 2FA para mayor seguridad:")
        self.stdout.write("   POST /api/v1/usuarios/2fa/habilitar/\n")
        self.stdout.write("4. Crear más empleados desde el admin panel o API\n")
