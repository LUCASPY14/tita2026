"""
Tests para serializers de la app usuarios
Cubre validación, serialización y deserialización de datos
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.usuarios.models import Roles, Empleados
from apps.usuarios.serializers import RolesSerializer, EmpleadosSerializer


class RolesSerializerTest(TestCase):
    """Tests para RolesSerializer"""

    def test_serializacion_rol_exitosa(self):
        """Debe serializar un rol correctamente"""
        rol = Roles.objects.create(
            nombre_rol="Administrador",
            descripcion="Rol con permisos completos",
            estado=True
        )
        
        serializer = RolesSerializer(rol)
        data = serializer.data
        
        self.assertEqual(data['nombre_rol'], "Administrador")
        self.assertEqual(data['descripcion'], "Rol con permisos completos")
        self.assertTrue(data['estado'])
        self.assertEqual(data['id_rol'], rol.id_rol)

    def test_deserializacion_rol_valida(self):
        """Debe deserializar datos válidos correctamente"""
        data = {
            'nombre_rol': 'Cajero',
            'descripcion': 'Rol de cajero',
            'estado': True
        }
        
        serializer = RolesSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        rol = serializer.save()
        self.assertEqual(rol.nombre_rol, 'Cajero')
        self.assertEqual(rol.descripcion, 'Rol de cajero')
        self.assertTrue(rol.estado)

    def test_validacion_nombre_rol_requerido(self):
        """Debe validar que nombre_rol es requerido"""
        data = {
            'descripcion': 'Rol sin nombre',
            'estado': True
        }
        
        serializer = RolesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nombre_rol', serializer.errors)

    def test_validacion_nombre_rol_unico(self):
        """Debe validar unicidad de nombre_rol"""
        # Crear rol existente
        Roles.objects.create(nombre_rol="Existente")
        
        data = {
            'nombre_rol': 'Existente',
            'descripcion': 'Rol duplicado'
        }
        
        serializer = RolesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nombre_rol', serializer.errors)

    def test_descripcion_opcional(self):
        """Debe permitir descripción opcional"""
        data = {
            'nombre_rol': 'RolSinDescripcion',
            'estado': True
        }
        
        serializer = RolesSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        rol = serializer.save()
        self.assertEqual(rol.nombre_rol, 'RolSinDescripcion')
        self.assertIsNone(rol.descripcion)

    def test_actualizacion_rol(self):
        """Debe actualizar rol existente correctamente"""
        rol = Roles.objects.create(nombre_rol="Original")
        
        data = {
            'nombre_rol': 'Actualizado',
            'descripcion': 'Nueva descripción',
            'estado': False
        }
        
        serializer = RolesSerializer(rol, data=data)
        self.assertTrue(serializer.is_valid())
        
        rol_actualizado = serializer.save()
        self.assertEqual(rol_actualizado.nombre_rol, 'Actualizado')
        self.assertEqual(rol_actualizado.descripcion, 'Nueva descripción')
        self.assertFalse(rol_actualizado.estado)


class EmpleadosSerializerTest(TestCase):
    """Tests para EmpleadosSerializer"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.rol = Roles.objects.create(
            nombre_rol="Tester",
            descripcion="Rol para pruebas"
        )

    def test_serializacion_empleado_exitosa(self):
        """Debe serializar un empleado correctamente"""
        empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Pérez",
            usuario="jperez",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            email="juan@test.com",
            estado=True,
            id_rol=self.rol
        )
        
        serializer = EmpleadosSerializer(empleado)
        data = serializer.data
        
        self.assertEqual(data['nombre'], "Juan")
        self.assertEqual(data['apellido'], "Pérez")
        self.assertEqual(data['usuario'], "jperez")
        self.assertEqual(data['email'], "juan@test.com")
        self.assertTrue(data['estado'])
        self.assertEqual(data['id_rol'], self.rol.id_rol)
        self.assertEqual(data['rol_nombre'], "Tester")
        
        # Contraseña no debe aparecer en serialización
        self.assertNotIn('contrasena_hash', data)

    def test_deserializacion_empleado_valida(self):
        """Debe deserializar datos válidos correctamente"""
        data = {
            'nombre': 'María',
            'apellido': 'García',
            'usuario': 'mgarcia',
            'contrasena_hash': 'hashedpass',
            'fecha_ingreso': timezone.now().isoformat(),
            'email': 'maria@test.com',
            'estado': True,
            'id_rol': self.rol.id_rol
        }
        
        serializer = EmpleadosSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        empleado = serializer.save()
        self.assertEqual(empleado.nombre, 'María')
        self.assertEqual(empleado.apellido, 'García')
        self.assertEqual(empleado.usuario, 'mgarcia')
        self.assertEqual(empleado.email, 'maria@test.com')
        self.assertTrue(empleado.estado)
        self.assertEqual(empleado.id_rol, self.rol)

    def test_validacion_campos_requeridos(self):
        """Debe validar campos requeridos"""
        data = {}
        
        serializer = EmpleadosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['nombre', 'apellido', 'usuario', 'contrasena_hash', 'fecha_ingreso', 'id_rol']
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_validacion_usuario_unico(self):
        """Debe validar unicidad de usuario"""
        # Crear empleado existente
        Empleados.objects.create(
            nombre="Existente",
            apellido="Usuario",
            usuario="existente",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        data = {
            'nombre': 'Nuevo',
            'apellido': 'Usuario',
            'usuario': 'existente',  # Usuario duplicado
            'contrasena_hash': 'newhash',
            'fecha_ingreso': timezone.now().isoformat(),
            'id_rol': self.rol.id_rol
        }
        
        serializer = EmpleadosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('usuario', serializer.errors)

    def test_contrasena_write_only(self):
        """Debe marcar contraseña como write_only"""
        data = {
            'nombre': 'Test',
            'apellido': 'User',
            'usuario': 'testuser',
            'contrasena_hash': 'secrethash',
            'fecha_ingreso': timezone.now().isoformat(),
            'id_rol': self.rol.id_rol
        }
        
        serializer = EmpleadosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        empleado = serializer.save()
        
        # Al serializar de vuelta, no debe incluir contraseña
        output_serializer = EmpleadosSerializer(empleado)
        self.assertNotIn('contrasena_hash', output_serializer.data)

    def test_campo_rol_nombre_read_only(self):
        """Debe incluir nombre del rol como campo de solo lectura"""
        empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        serializer = EmpleadosSerializer(empleado)
        data = serializer.data
        
        self.assertEqual(data['rol_nombre'], "Tester")
        
        # Verificar que es read_only (no afecta deserialización)
        input_data = {
            'nombre': 'Updated',
            'apellido': 'Name',
            'usuario': 'updated',
            'rol_nombre': 'Hacker',  # Esto debe ser ignorado
            'fecha_ingreso': timezone.now().isoformat(),
            'id_rol': self.rol.id_rol
        }
        
        update_serializer = EmpleadosSerializer(empleado, data=input_data)
        self.assertTrue(update_serializer.is_valid())
        updated_empleado = update_serializer.save()
        
        # El nombre del rol no debe haber cambiado
        self.assertEqual(updated_empleado.id_rol.nombre_rol, "Tester")

    def test_campos_opcionales(self):
        """Debe manejar campos opcionales correctamente"""
        data = {
            'nombre': 'Minimal',
            'apellido': 'User',
            'usuario': 'minimal',
            'contrasena_hash': 'hash',
            'fecha_ingreso': timezone.now().isoformat(),
            'id_rol': self.rol.id_rol
        }
        
        serializer = EmpleadosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        empleado = serializer.save()
        self.assertIsNone(empleado.direccion)
        self.assertIsNone(empleado.ciudad)
        self.assertIsNone(empleado.pais)
        self.assertIsNone(empleado.telefono)
        self.assertIsNone(empleado.email)
        self.assertIsNone(empleado.fecha_baja)

    def test_actualizacion_parcial(self):
        """Debe permitir actualización parcial"""
        empleado = Empleados.objects.create(
            nombre="Original",
            apellido="Name",
            usuario="original",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Actualizar solo email
        data = {'email': 'nuevo@email.com'}
        
        serializer = EmpleadosSerializer(empleado, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        empleado_actualizado = serializer.save()
        self.assertEqual(empleado_actualizado.email, 'nuevo@email.com')
        self.assertEqual(empleado_actualizado.nombre, 'Original')  # No debe cambiar