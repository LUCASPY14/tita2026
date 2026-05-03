"""
Tests para views/viewsets de la app usuarios
Cubre APIs, permisos, autenticación y endpoints customizados
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import Empleados, Roles


class RolesViewSetTest(APITestCase):
    """Tests para RolesViewSet API"""

    def setUp(self):
        """Configurar cliente de prueba y datos base"""
        self.client = APIClient()

        # Crear rol de prueba
        self.rol = Roles.objects.create(nombre_rol="Administrador", descripcion="Rol de prueba", estado=True)

        # Crear empleado para autenticación
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            email="test@test.com",
            estado=True,
            id_rol=self.rol,
        )

        # Autenticar cliente
        self.auth_user = User.objects.create_user(username="testuser_auth", password="testpass123")
        self.client.force_authenticate(user=self.auth_user)

    def test_listar_roles(self):
        """Debe listar todos los roles"""
        url = reverse("roles-list")  # Asumiendo router configurado
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nombre_rol"], "Administrador")

    def test_crear_rol_exitoso(self):
        """Debe crear rol con datos válidos"""
        url = reverse("roles-list")
        data = {"nombre_rol": "Nuevo Rol", "descripcion": "Descripción del nuevo rol", "estado": True}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Roles.objects.count(), 2)

        nuevo_rol = Roles.objects.get(nombre_rol="Nuevo Rol")
        self.assertEqual(nuevo_rol.descripcion, "Descripción del nuevo rol")
        self.assertTrue(nuevo_rol.estado)

    def test_crear_rol_sin_autenticacion(self):
        """Debe rechazar creación sin autenticación"""
        self.client.force_authenticate(user=None)

        url = reverse("roles-list")
        data = {
            "nombre_rol": "Rol No Autorizado",
            "descripcion": "No debe crearse",
        }

        response = self.client.post(url, data, format="json")

        # Dependiendo de configuración de permisos
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_obtener_rol_por_id(self):
        """Debe obtener rol específico por ID"""
        url = reverse("roles-detail", kwargs={"pk": self.rol.id_rol})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre_rol"], "Administrador")
        self.assertEqual(response.data["descripcion"], "Rol de prueba")

    def test_actualizar_rol(self):
        """Debe actualizar rol existente"""
        url = reverse("roles-detail", kwargs={"pk": self.rol.id_rol})
        data = {"nombre_rol": "Admin Actualizado", "descripcion": "Descripción actualizada", "estado": True}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.rol.refresh_from_db()
        self.assertEqual(self.rol.nombre_rol, "Admin Actualizado")
        self.assertEqual(self.rol.descripcion, "Descripción actualizada")

    def test_eliminar_rol(self):
        """Debe eliminar rol"""
        url = reverse("roles-detail", kwargs={"pk": self.rol.id_rol})
        response = self.client.delete(url)

        # Puede ser 204 (eliminado) o 403 (no permitido) según configuración
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_403_FORBIDDEN])

    def test_filtrar_roles_activos(self):
        """Debe filtrar roles por estado estado"""
        # Crear rol inactivo
        Roles.objects.create(nombre_rol="Rol Inactivo", estado=False)

        url = reverse("roles-list")
        response = self.client.get(url, {"estado": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Solo debe retornar roles activos
        for rol in response.data:
            self.assertTrue(rol["estado"])

    def test_buscar_roles(self):
        """Debe buscar roles por nombre"""
        # Crear roles adicionales
        Roles.objects.create(nombre_rol="Cajero")
        Roles.objects.create(nombre_rol="Supervisor")

        url = reverse("roles-list")
        response = self.client.get(url, {"search": "Admin"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nombre_rol"], "Administrador")


class EmpleadosViewSetTest(APITestCase):
    """Tests para EmpleadosViewSet API"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.client = APIClient()

        self.rol = Roles.objects.create(nombre_rol="Manager", descripcion="Rol de manager", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Manager",
            usuario="jmanager",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            email="juan@company.com",
            estado=True,
            id_rol=self.rol,
        )

        # Autenticar cliente
        self.auth_user = User.objects.create_user(username="emp_auth_user", password="testpass123")
        self.client.force_authenticate(user=self.auth_user)

    def test_listar_empleados(self):
        """Debe listar empleados con información del rol"""
        url = reverse("empleados-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        empleado_data = response.data[0]
        self.assertEqual(empleado_data["nombre"], "Juan")
        self.assertEqual(empleado_data["apellido"], "Manager")
        self.assertEqual(empleado_data["usuario"], "jmanager")
        self.assertEqual(empleado_data["email"], "juan@company.com")
        self.assertEqual(empleado_data["rol_nombre"], "Manager")

        # Contraseña no debe aparecer
        self.assertNotIn("contrasena_hash", empleado_data)

    def test_crear_empleado(self):
        """Debe crear empleado con datos válidos"""
        url = reverse("empleados-list")
        data = {
            "nombre": "María",
            "apellido": "Cajero",
            "usuario": "mcajero",
            "contrasena_hash": "hashedpassword123",
            "fecha_ingreso": timezone.now().isoformat(),
            "email": "maria@company.com",
            "estado": True,
            "id_rol": self.rol.id_rol,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Empleados.objects.count(), 2)

        nuevo_empleado = Empleados.objects.get(usuario="mcajero")
        self.assertEqual(nuevo_empleado.nombre, "María")
        self.assertEqual(nuevo_empleado.email, "maria@company.com")
        self.assertEqual(nuevo_empleado.id_rol, self.rol)

    def test_crear_empleado_usuario_duplicado(self):
        """Debe rechazar empleado con usuario duplicado"""
        url = reverse("empleados-list")
        data = {
            "nombre": "Pedro",
            "apellido": "Duplicado",
            "usuario": "jmanager",  # Usuario ya existe
            "contrasena_hash": "otrahash",
            "fecha_ingreso": timezone.now().isoformat(),
            "id_rol": self.rol.id_rol,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("usuario", response.data)

    def test_actualizar_empleado(self):
        """Debe actualizar empleado existente"""
        url = reverse("empleados-detail", kwargs={"pk": self.empleado.id_empleado})
        data = {
            "nombre": "Juan Carlos",
            "apellido": "Manager Senior",
            "usuario": "jcmanager",
            "fecha_ingreso": self.empleado.fecha_ingreso.isoformat(),
            "email": "juan.carlos@company.com",
            "estado": True,
            "id_rol": self.rol.id_rol,
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.nombre, "Juan Carlos")
        self.assertEqual(self.empleado.apellido, "Manager Senior")
        self.assertEqual(self.empleado.usuario, "jcmanager")
        self.assertEqual(self.empleado.email, "juan.carlos@company.com")

    def test_eliminar_empleado(self):
        """Debe eliminar empleado"""
        url = reverse("empleados-detail", kwargs={"pk": self.empleado.id_empleado})
        response = self.client.delete(url)

        # Dependiendo de configuración de permisos
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_403_FORBIDDEN])

    def test_filtrar_empleados_activos(self):
        """Debe filtrar empleados por estado estado"""
        # Crear empleado inactivo
        Empleados.objects.create(
            nombre="Inactivo",
            apellido="User",
            usuario="inactive",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            estado=False,
            id_rol=self.rol,
        )

        url = reverse("empleados-list")
        response = self.client.get(url, {"estado": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Solo debe retornar empleados activos
        for empleado in response.data:
            self.assertTrue(empleado["estado"])

    def test_buscar_empleados(self):
        """Debe buscar empleados por nombre o apellido"""
        # Crear empleados adicionales
        Empleados.objects.create(
            nombre="Ana",
            apellido="García",
            usuario="agarcia",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        url = reverse("empleados-list")
        response = self.client.get(url, {"search": "Juan"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nombre"], "Juan")

    def test_ordering_empleados(self):
        """Debe ordenar empleados correctamente"""
        # Crear más empleados
        Empleados.objects.create(
            nombre="Ana",
            apellido="García",
            usuario="agarcia",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        url = reverse("empleados-list")
        response = self.client.get(url, {"ordering": "nombre"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar orden por nombre
        nombres = [emp["nombre"] for emp in response.data]
        self.assertEqual(nombres, sorted(nombres))


class UsuariosPermissionsTest(TestCase):
    """Tests para permisos y autenticación"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.rol = Roles.objects.create(nombre_rol="Tester", estado=True)

    def test_acceso_sin_autenticacion(self):
        """Debe requerir autenticación para endpoints protegidos"""
        client = APIClient()

        protected_urls = [
            reverse("roles-list"),
            reverse("empleados-list"),
        ]

        for url in protected_urls:
            response = client.get(url)

            # Debe requerir autenticación
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_validacion_campos_requeridos(self):
        """Debe validar campos requeridos en creación"""
        client = APIClient()
        auth_user = User.objects.create_user(username="perm_test_user", password="testpass123")
        client.force_authenticate(user=auth_user)

        # Test para Roles
        url = reverse("roles-list")
        response = client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nombre_rol", response.data)

        # Test para Empleados
        url = reverse("empleados-list")
        response = client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        required_fields = ["nombre", "apellido", "usuario", "contrasena_hash", "fecha_ingreso", "id_rol"]

        for field in required_fields:
            self.assertIn(field, response.data)
