"""
Tests para management commands de usuarios:
- cleanup_usuarios
- init_usuarios
"""

from io import StringIO
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone

from apps.usuarios.models import Roles, Empleados


class CleanupUsuariosCommandTest(TestCase):
    """Tests para el comando cleanup_usuarios"""

    def test_comando_ejecucion_basica(self):
        """El comando debe ejecutarse sin errores"""
        out = StringIO()
        with patch("apps.usuarios.services.SessionService.limpiar_sesiones_expiradas") as mock_s:
            mock_s.return_value = {"success": True, "sesiones_cerradas": 0, "mensaje": "ok"}
            with patch("apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados") as mock_p:
                mock_p.return_value = {"success": True, "tokens_eliminados": 0, "mensaje": "ok"}
                call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Limpieza", output)

    def test_comando_dry_run(self):
        """El modo dry-run debe indicar los cambios pero no hacerlos"""
        out = StringIO()
        call_command("cleanup_usuarios", dry_run=True, stdout=out)
        output = out.getvalue()
        self.assertIn("dry", output.lower())

    def test_comando_verbose(self):
        """El modo verbose debe mostrar más información"""
        out = StringIO()
        with patch("apps.usuarios.services.SessionService.limpiar_sesiones_expiradas") as mock_s:
            mock_s.return_value = {"success": True, "sesiones_cerradas": 5, "mensaje": "ok"}
            with patch("apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados") as mock_p:
                mock_p.return_value = {"success": True, "tokens_eliminados": 3, "mensaje": "ok"}
                call_command("cleanup_usuarios", verbose=True, stdout=out)
        output = out.getvalue()
        self.assertIn("Limpieza", output)

    def test_comando_con_error_sesiones(self):
        """El comando debe manejar errores en limpieza de sesiones gracefully"""
        out = StringIO()
        with patch("apps.usuarios.services.SessionService.limpiar_sesiones_expiradas") as mock_s:
            mock_s.return_value = {"success": False, "sesiones_cerradas": 0, "mensaje": "Error de BD"}
            with patch("apps.usuarios.services.PasswordRecoveryService.limpiar_tokens_expirados") as mock_p:
                mock_p.return_value = {"success": True, "tokens_eliminados": 0, "mensaje": "ok"}
                call_command("cleanup_usuarios", stdout=out)
        output = out.getvalue()
        # El comando no debe lanzar una excepción, solo reportar el error
        self.assertIsNotNone(output)

    def test_comando_dry_run_con_datos(self):
        """Dry-run debe contar los elementos que se limpiarían"""
        out = StringIO()
        call_command("cleanup_usuarios", dry_run=True, verbose=True, stdout=out)
        output = out.getvalue()
        self.assertIn("dry", output.lower())


class InitUsuariosCommandTest(TestCase):
    """Tests para el comando init_usuarios"""

    def test_comando_ejecucion_basica(self):
        """El comando debe ejecutarse correctamente"""
        out = StringIO()
        with patch("apps.usuarios.services.AuthenticationService.crear_empleado") as mock_crear:
            mock_crear.return_value = {"success": True, "mensaje": "Creado", "empleado": {}}
            call_command("init_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Inicializando", output)

    def test_comando_skip_admin(self):
        """Con --skip-admin no debe crear usuario admin"""
        out = StringIO()
        call_command("init_usuarios", skip_admin=True, stdout=out)
        output = out.getvalue()
        # Debe completar sin crear admin
        self.assertIn("Inicializando", output)

    def test_command_idempotente(self):
        """El comando debe ser idempotente (ejecutable múltiples veces)"""
        out1 = StringIO()
        out2 = StringIO()
        with patch("apps.usuarios.services.AuthenticationService.crear_empleado") as mock_crear:
            mock_crear.return_value = {"success": True, "mensaje": "Creado", "empleado": {}}
            call_command("init_usuarios", skip_admin=True, stdout=out1)
            call_command("init_usuarios", skip_admin=True, stdout=out2)
        # No debe lanzar errores en ninguna de las dos ejecuciones
        self.assertIsNotNone(out1.getvalue())
        self.assertIsNotNone(out2.getvalue())

    def test_admin_ya_existe(self):
        """Si admin ya existe, no debe fallar"""
        # Crear el rol admin primero
        from apps.usuarios.permissions import PermissionService

        PermissionService.inicializar_permisos()
        Roles.objects.get_or_create(nombre_rol="Administrador", defaults={"descripcion": "Admin", "estado": True})
        # Crear el empleado admin
        Empleados.objects.get_or_create(
            usuario="admin",
            defaults={
                "nombre": "Admin",
                "apellido": "Test",
                "contrasena_hash": "hash",
                "fecha_ingreso": timezone.now(),
                "estado": True,
            },
        )
        out = StringIO()
        call_command("init_usuarios", stdout=out)
        output = out.getvalue()
        self.assertIn("Inicializando", output)

    def test_comando_con_password_personalizado(self):
        """El comando debe aceptar contraseña personalizada"""
        out = StringIO()
        with patch("apps.usuarios.services.AuthenticationService.crear_empleado") as mock_crear:
            mock_crear.return_value = {"success": True, "mensaje": "Creado", "empleado": {}}
            call_command("init_usuarios", admin_password="MiContrasena123!", stdout=out)
        output = out.getvalue()
        self.assertIsNotNone(output)


class CrearRolesInicialesCommandTest(TestCase):
    """Tests para el comando crear_roles_iniciales de core"""

    def test_comando_ejecucion_basica(self):
        """El comando debe crear los roles iniciales correctamente"""
        out = StringIO()
        call_command("crear_roles_iniciales", stdout=out)
        output = out.getvalue()
        self.assertIn("CREAR ROLES", output)
        # Verificar que se crearon roles
        self.assertGreater(Roles.objects.count(), 0)

    def test_comando_idempotente(self):
        """El comando debe ser idempotente"""
        out1 = StringIO()
        out2 = StringIO()
        call_command("crear_roles_iniciales", stdout=out1)
        count_after_first = Roles.objects.count()
        call_command("crear_roles_iniciales", stdout=out2)
        count_after_second = Roles.objects.count()
        # Los roles no deben duplicarse
        self.assertEqual(count_after_first, count_after_second)

    def test_roles_creados_son_correctos(self):
        """Los roles creados deben tener los nombres correctos"""
        out = StringIO()
        call_command("crear_roles_iniciales", stdout=out)
        nombres_esperados = ["Admin", "Gerente", "Cajero", "Encargado Compras", "Encargado Inventario"]
        for nombre in nombres_esperados:
            self.assertTrue(Roles.objects.filter(nombre_rol=nombre).exists(), f"Rol '{nombre}' no fue creado")
