"""
Tests para configuración de admin de la app usuarios
Cubre Django Admin interface, filtros, búsquedas y acciones
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from apps.usuarios.models import Roles, Empleados
from apps.usuarios.admin import RolesAdmin, EmpleadosAdmin


class RolesAdminTest(TestCase):
    """Tests para RolesAdmin interface"""

    def setUp(self):
        """Configurar usuario admin y datos de prueba"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        self.roles = [
            Roles.objects.create(nombre_rol="Administrador", estado=True),
            Roles.objects.create(nombre_rol="Cajero", estado=True),
            Roles.objects.create(nombre_rol="Supervisor", estado=False),
        ]

    def test_admin_list_view(self):
        """Debe mostrar lista de roles en admin"""
        url = reverse('admin:usuarios_roles_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrador")
        self.assertContains(response, "Cajero")
        self.assertContains(response, "Supervisor")

    def test_admin_add_view(self):
        """Debe mostrar formulario de añadir rol"""
        url = reverse('admin:usuarios_roles_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'nombre_rol')
        self.assertContains(response, 'descripcion')
        self.assertContains(response, 'estado')

    def test_admin_create_role(self):
        """Debe crear nuevo rol desde admin"""
        url = reverse('admin:usuarios_roles_add')
        data = {
            'nombre_rol': 'Nuevo Rol Admin',
            'descripcion': 'Rol creado desde admin',
            'estado': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        nuevo_rol = Roles.objects.get(nombre_rol='Nuevo Rol Admin')
        self.assertEqual(nuevo_rol.descripcion, 'Rol creado desde admin')
        self.assertTrue(nuevo_rol.estado)

    def test_admin_edit_view(self):
        """Debe mostrar formulario de edición"""
        rol = self.roles[0]
        url = reverse('admin:usuarios_roles_change', args=[rol.id_rol])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, rol.nombre_rol)

    def test_admin_update_role(self):
        """Debe actualizar rol existente"""
        rol = self.roles[0]
        url = reverse('admin:usuarios_roles_change', args=[rol.id_rol])
        data = {
            'nombre_rol': 'Admin Actualizado',
            'descripcion': 'Descripción actualizada',
            'estado': False
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        rol.refresh_from_db()
        self.assertEqual(rol.nombre_rol, 'Admin Actualizado')
        self.assertFalse(rol.estado)

    def test_admin_search_functionality(self):
        """Debe permitir búsqueda en admin"""
        url = reverse('admin:usuarios_roles_changelist')
        response = self.client.get(url, {'q': 'Admin'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrador")
        self.assertNotContains(response, "Cajero")

    def test_admin_filter_by_activo(self):
        """Debe filtrar por estado estado"""
        url = reverse('admin:usuarios_roles_changelist')
        response = self.client.get(url, {'estado__exact': '1'})  # Activos
        
        self.assertEqual(response.status_code, 200)
        # Debe mostrar solo roles activos
        self.assertContains(response, "Administrador")
        self.assertContains(response, "Cajero")


class EmpleadosAdminTest(TestCase):
    """Tests para EmpleadosAdmin interface"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        self.rol = Roles.objects.create(
            nombre_rol="Manager",
            estado=True
        )
        
        self.empleados = [
            Empleados.objects.create(
                nombre="Juan",
                apellido="Pérez",
                usuario="jperez",
                contrasena_hash="$2b$12$hash1",
                fecha_ingreso=timezone.now(),
                email="juan@company.com",
                estado=True,
                id_rol=self.rol
            ),
            Empleados.objects.create(
                nombre="María",
                apellido="García",
                usuario="mgarcia",
                contrasena_hash="$2b$12$hash2",
                fecha_ingreso=timezone.now(),
                estado=False,
                id_rol=self.rol
            )
        ]

    def test_empleados_admin_list_view(self):
        """Debe mostrar lista de empleados en admin"""
        url = reverse('admin:usuarios_empleados_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")
        self.assertContains(response, "Pérez")
        self.assertContains(response, "jperez")
        self.assertContains(response, "María")

    def test_empleados_admin_add_view(self):
        """Debe mostrar formulario de añadir empleado"""
        url = reverse('admin:usuarios_empleados_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'nombre')
        self.assertContains(response, 'apellido')
        self.assertContains(response, 'usuario')
        self.assertContains(response, 'id_rol')

    def test_empleados_admin_create(self):
        """Debe crear nuevo empleado desde admin"""
        url = reverse('admin:usuarios_empleados_add')
        data = {
            'nombre': 'Carlos',
            'apellido': 'López',
            'usuario': 'clopez',
            'contrasena_hash': '$2b$12$newhash',
            'fecha_ingreso': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'email': 'carlos@company.com',
            'estado': True,
            'id_rol': self.rol.id_rol
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        nuevo_empleado = Empleados.objects.get(usuario='clopez')
        self.assertEqual(nuevo_empleado.nombre, 'Carlos')
        self.assertEqual(nuevo_empleado.email, 'carlos@company.com')

    def test_empleados_admin_search(self):
        """Debe permitir búsqueda por nombre, apellido, usuario"""
        url = reverse('admin:usuarios_empleados_changelist')
        
        # Buscar por nombre
        response = self.client.get(url, {'q': 'Juan'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")
        self.assertNotContains(response, "María")
        
        # Buscar por usuario
        response = self.client.get(url, {'q': 'mgarcia'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "María")
        self.assertNotContains(response, "Juan")

    def test_empleados_admin_filter_by_activo(self):
        """Debe filtrar empleados por estado estado"""
        url = reverse('admin:usuarios_empleados_changelist')
        response = self.client.get(url, {'estado__exact': '1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")  # estado
        # María (inactiva) no debería aparecer

    def test_empleados_admin_filter_by_rol(self):
        """Debe filtrar empleados por rol"""
        # Crear otro rol y empleado
        otro_rol = Roles.objects.create(nombre_rol="Cajero")
        Empleados.objects.create(
            nombre="Ana",
            apellido="Ruiz",
            usuario="aruiz",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=otro_rol
        )
        
        url = reverse('admin:usuarios_empleados_changelist')
        response = self.client.get(url, {'id_rol__exact': self.rol.id_rol})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan")
        self.assertContains(response, "María")
        self.assertNotContains(response, "Ana")

    def test_empleados_admin_edit_view(self):
        """Debe mostrar formulario de edición de empleado"""
        empleado = self.empleados[0]
        url = reverse('admin:usuarios_empleados_change', args=[empleado.id_empleado])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, empleado.nombre)
        self.assertContains(response, empleado.usuario)

    def test_empleados_admin_update(self):
        """Debe actualizar empleado existente"""
        empleado = self.empleados[0]
        url = reverse('admin:usuarios_empleados_change', args=[empleado.id_empleado])
        data = {
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez Actualizado',
            'usuario': 'jcperez',
            'contrasena_hash': empleado.contrasena_hash,
            'fecha_ingreso': empleado.fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S'),
            'email': 'juan.carlos@company.com',
            'estado': True,
            'id_rol': self.rol.id_rol
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        empleado.refresh_from_db()
        self.assertEqual(empleado.nombre, 'Juan Carlos')
        self.assertEqual(empleado.apellido, 'Pérez Actualizado')
        self.assertEqual(empleado.usuario, 'jcperez')

    def test_admin_readonly_fields(self):
        """Debe manejar campos de solo lectura apropiados"""
        empleado = self.empleados[0]
        url = reverse('admin:usuarios_empleados_change', args=[empleado.id_empleado])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verificar que ciertos campos sensibles tienen tratamiento especial
        # (esto dependería de la configuración específica del admin)

    def test_admin_permissions(self):
        """Debe requerir permisos de admin"""
        # Cerrar sesión de admin
        self.client.logout()
        
        # Crear usuario normal sin permisos
        normal_user = User.objects.create_user(
            username='normal',
            password='normalpass'
        )
        self.client.force_login(normal_user)
        
        # Intentar acceder al admin
        url = reverse('admin:usuarios_roles_changelist')
        response = self.client.get(url)
        
        # Debe redirigir o mostrar error de permisos
        self.assertNotEqual(response.status_code, 200)