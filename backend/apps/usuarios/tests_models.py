"""
Tests para modelos de la app usuarios
Cubre validaciones, métodos y comportamientos de Empleados y Roles
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.usuarios.models import Empleados, Roles


class RolesModelTest(TestCase):
    """Tests para el modelo Roles"""

    def test_crear_rol_exitoso(self):
        """Debe crear un rol con datos válidos"""
        rol = Roles.objects.create(nombre_rol="Administrador", descripcion="Rol con permisos completos", estado=True)

        self.assertEqual(rol.nombre_rol, "Administrador")
        self.assertEqual(rol.descripcion, "Rol con permisos completos")
        self.assertTrue(rol.estado)
        self.assertIsNotNone(rol.id_rol)

    def test_str_representation(self):
        """Debe retornar representación string correcta"""
        rol = Roles.objects.create(nombre_rol="Cajero")
        expected = f"Roles #{rol.id_rol}"
        self.assertEqual(str(rol), expected)

    def test_nombre_rol_unique(self):
        """Debe validar unicidad de nombre_rol"""
        Roles.objects.create(nombre_rol="Supervisor")

        with self.assertRaises(IntegrityError):
            Roles.objects.create(nombre_rol="Supervisor")

    def test_rol_activo_por_defecto(self):
        """Debe crear rol estado por defecto"""
        rol = Roles.objects.create(nombre_rol="Vendedor")
        self.assertTrue(rol.estado)

    def test_descripcion_opcional(self):
        """Debe permitir descripción opcional"""
        rol = Roles.objects.create(nombre_rol="Temporal")
        self.assertIsNone(rol.descripcion)

    def test_max_length_nombre_rol(self):
        """Debe validar longitud máxima de nombre_rol"""
        nombre_largo = "A" * 51  # Excede los 50 caracteres
        rol = Roles(nombre_rol=nombre_largo)

        with self.assertRaises(ValidationError):
            rol.full_clean()


class EmpleadosModelTest(TestCase):
    """Tests para el modelo Empleados"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.rol = Roles.objects.create(nombre_rol="Tester", descripcion="Rol para pruebas")

    def test_crear_empleado_exitoso(self):
        """Debe crear empleado con datos válidos"""
        empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Pérez",
            usuario="jperez",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            email="juan@test.com",
            estado=True,
            id_rol=self.rol,
        )

        self.assertEqual(empleado.nombre, "Juan")
        self.assertEqual(empleado.apellido, "Pérez")
        self.assertEqual(empleado.usuario, "jperez")
        self.assertEqual(empleado.email, "juan@test.com")
        self.assertTrue(empleado.estado)
        self.assertEqual(empleado.id_rol, self.rol)

    def test_str_representation(self):
        """Debe retornar representación string correcta"""
        empleado = Empleados.objects.create(
            nombre="María",
            apellido="García",
            usuario="mgarcia",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )
        expected = f"Empleados #{empleado.id_empleado}"
        self.assertEqual(str(empleado), expected)

    def test_usuario_unique(self):
        """Debe validar unicidad de usuario"""
        Empleados.objects.create(
            nombre="Juan",
            apellido="Uno",
            usuario="usuario1",
            contrasena_hash="hash1",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        with self.assertRaises(IntegrityError):
            Empleados.objects.create(
                nombre="Pedro",
                apellido="Dos",
                usuario="usuario1",  # Usuario duplicado
                contrasena_hash="hash2",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )

    def test_empleado_activo_por_defecto(self):
        """Debe crear empleado estado por defecto"""
        empleado = Empleados.objects.create(
            nombre="Luis",
            apellido="Sánchez",
            usuario="lsanchez",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )
        self.assertTrue(empleado.estado)

    def test_campos_opcionales(self):
        """Debe permitir campos opcionales como null"""
        empleado = Empleados.objects.create(
            nombre="Ana",
            apellido="López",
            usuario="alopez",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Campos opcionales deben ser None por defecto
        self.assertIsNone(empleado.direccion)
        self.assertIsNone(empleado.ciudad)
        self.assertIsNone(empleado.pais)
        self.assertIsNone(empleado.telefono)
        self.assertIsNone(empleado.email)
        self.assertIsNone(empleado.fecha_baja)

    def test_relacion_con_rol(self):
        """Debe mantener relación correcta con Rol"""
        empleado = Empleados.objects.create(
            nombre="Roberto",
            apellido="Díaz",
            usuario="rdiaz",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Verificar acceso al rol relacionado
        self.assertEqual(empleado.id_rol.nombre_rol, "Tester")
        self.assertEqual(empleado.id_rol.descripcion, "Rol para pruebas")

    def test_fecha_baja_opcional(self):
        """Debe permitir fecha_baja como opcional"""
        empleado = Empleados.objects.create(
            nombre="Carlos",
            apellido="Vargas",
            usuario="cvargas",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Inicialmente sin fecha de baja
        self.assertIsNone(empleado.fecha_baja)

        # Asignar fecha de baja
        empleado.fecha_baja = timezone.now()
        empleado.save()
        self.assertIsNotNone(empleado.fecha_baja)

    def test_max_length_campos_texto(self):
        """Debe validar longitudes máximas"""
        with self.assertRaises(ValidationError):
            empleado = Empleados(
                nombre="A" * 101,  # Excede 100 caracteres
                apellido="Pérez",
                usuario="test",
                contrasena_hash="hash",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )
            empleado.full_clean()

        with self.assertRaises(ValidationError):
            empleado = Empleados(
                nombre="Juan",
                apellido="A" * 101,  # Excede 100 caracteres
                usuario="test",
                contrasena_hash="hash",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )
            empleado.full_clean()

    def test_usuario_max_length(self):
        """Debe validar longitud máxima de usuario"""
        with self.assertRaises(ValidationError):
            empleado = Empleados(
                nombre="Juan",
                apellido="Pérez",
                usuario="A" * 51,  # Excede 50 caracteres
                contrasena_hash="hash",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )
            empleado.full_clean()

    def test_eliminacion_cascada_rol(self):
        """Debe manejar eliminación de rol relacionado"""
        empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Eliminar rol debe fallar debido a DO_NOTHING
        with self.assertRaises(Exception):
            self.rol.delete()

        # Empleado debe seguir existiendo
        self.assertTrue(Empleados.objects.filter(id_empleado=empleado.id_empleado).exists())
