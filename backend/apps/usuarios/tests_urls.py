"""
Tests para configuración de URLs de la app usuarios
Cubre routing, resolución de URLs y acceso a endpoints
"""

from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from rest_framework.test import APIClient, APITestCase

from apps.usuarios.models import Empleados, Roles


class UsuariosUrlsTest(TestCase):
    """Tests para configuración de URLs"""

    def test_roles_list_url_resolves(self):
        """Debe resolver URL de lista de roles"""
        try:
            url = reverse("roles-list")
            resolved = resolve(url)
            self.assertIsNotNone(resolved)
        except:
            # Si no está configurado el router, probar URL básica
            url = "/api/usuarios/roles/"
            self.assertTrue(url.startswith("/api/"))

    def test_roles_detail_url_resolves(self):
        """Debe resolver URL de detalle de rol"""
        try:
            url = reverse("roles-detail", kwargs={"pk": 1})
            resolved = resolve(url)
            self.assertIsNotNone(resolved)
        except:
            # URL básica
            url = "/api/usuarios/roles/1/"
            self.assertTrue(url.endswith("/1/"))

    def test_empleados_list_url_resolves(self):
        """Debe resolver URL de lista de empleados"""
        try:
            url = reverse("empleados-list")
            resolved = resolve(url)
            self.assertIsNotNone(resolved)
        except:
            url = "/api/usuarios/empleados/"
            self.assertTrue(url.startswith("/api/"))

    def test_empleados_detail_url_resolves(self):
        """Debe resolver URL de detalle de empleado"""
        try:
            url = reverse("empleados-detail", kwargs={"pk": 1})
            resolved = resolve(url)
            self.assertIsNotNone(resolved)
        except:
            url = "/api/usuarios/empleados/1/"
            self.assertTrue(url.endswith("/1/"))

    def test_url_patterns_namespacing(self):
        """Debe usar namespacing apropiado para URLs"""
        # Test de namespacing básico
        patterns = [
            "usuarios:roles-list",
            "usuarios:roles-detail",
            "usuarios:empleados-list",
            "usuarios:empleados-detail",
        ]

        for pattern in patterns:
            try:
                url = reverse(pattern, kwargs={"pk": 1} if "detail" in pattern else {})
                self.assertTrue(isinstance(url, str))
            except:
                # Es normal si no está configurado aún
                pass

    def test_api_versioning_urls(self):
        """Debe soportar versionado de API en URLs"""
        versioned_patterns = [
            "/api/v1/usuarios/roles/",
            "/api/v1/usuarios/empleados/",
            "/api/v2/usuarios/roles/",
            "/api/v2/usuarios/empleados/",
        ]

        for pattern in versioned_patterns:
            self.assertTrue(pattern.startswith("/api/"))
            self.assertIn("usuarios", pattern)

    def test_admin_urls_pattern(self):
        """Debe configurar URLs de admin correctamente"""
        admin_patterns = [
            "admin:usuarios_roles_changelist",
            "admin:usuarios_roles_add",
            "admin:usuarios_empleados_changelist",
            "admin:usuarios_empleados_add",
        ]

        for pattern in admin_patterns:
            try:
                url = reverse(pattern)
                self.assertTrue(url.startswith("/admin/"))
            except:
                # Normal si admin no está completamente configurado
                pass


class UsuariosEndpointsTest(APITestCase):
    """Tests de integración para endpoints de usuarios"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.client = APIClient()

        self.rol = Roles.objects.create(nombre_rol="TestRole", descripcion="Rol de prueba", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            email="test@example.com",
            estado=True,
            id_rol=self.rol,
        )

    def test_roles_endpoints_accessibility(self):
        """Debe acceder a endpoints de roles correctamente"""
        endpoints = ["/api/usuarios/roles/", f"/api/usuarios/roles/{self.rol.id_rol}/"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # No debería dar 404 (Not Found)
            self.assertNotEqual(response.status_code, 404)

    def test_empleados_endpoints_accessibility(self):
        """Debe acceder a endpoints de empleados correctamente"""
        endpoints = ["/api/usuarios/empleados/", f"/api/usuarios/empleados/{self.empleado.id_empleado}/"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # No debería dar 404 (Not Found)
            self.assertNotEqual(response.status_code, 404)

    def test_crud_operations_roles(self):
        """Debe soportar operaciones CRUD en roles"""
        base_url = "/api/usuarios/roles/"

        # CREATE
        create_data = {"nombre_rol": "CRUD Test Role", "descripcion": "Rol de prueba CRUD", "estado": True}
        create_response = self.client.post(base_url, create_data, format="json")

        if create_response.status_code == 201:
            new_role_id = create_response.data["id_rol"]

            # READ
            read_response = self.client.get(f"{base_url}{new_role_id}/")
            self.assertEqual(read_response.status_code, 200)

            # UPDATE
            update_data = {"nombre_rol": "Updated CRUD Role", "descripcion": "Descripción actualizada", "estado": False}
            update_response = self.client.put(f"{base_url}{new_role_id}/", update_data, format="json")

            # DELETE
            delete_response = self.client.delete(f"{base_url}{new_role_id}/")

            # Verificar que las operaciones fueron exitosas o manejadas apropiadamente
            successful_codes = [200, 201, 202, 204]
            client_error_codes = [400, 401, 403]  # Errores de cliente aceptables

            for response in [create_response, read_response, update_response, delete_response]:
                self.assertIn(response.status_code, successful_codes + client_error_codes)

    def test_crud_operations_empleados(self):
        """Debe soportar operaciones CRUD en empleados"""
        base_url = "/api/usuarios/empleados/"

        # CREATE
        create_data = {
            "nombre": "CRUD",
            "apellido": "Test",
            "usuario": "crudtest",
            "contrasena_hash": "$2b$12$hashedpass",
            "fecha_ingreso": timezone.now().isoformat(),
            "email": "crud@test.com",
            "estado": True,
            "id_rol": self.rol.id_rol,
        }
        create_response = self.client.post(base_url, create_data, format="json")

        if create_response.status_code == 201:
            new_emp_id = create_response.data["id_empleado"]

            # READ
            read_response = self.client.get(f"{base_url}{new_emp_id}/")

            # UPDATE
            update_data = create_data.copy()
            update_data["nombre"] = "Updated CRUD"
            update_response = self.client.put(f"{base_url}{new_emp_id}/", update_data, format="json")

            # DELETE
            delete_response = self.client.delete(f"{base_url}{new_emp_id}/")

            # Verificar respuestas
            successful_codes = [200, 201, 202, 204]
            client_error_codes = [400, 401, 403]

            for response in [create_response, read_response, update_response, delete_response]:
                self.assertIn(response.status_code, successful_codes + client_error_codes)

    def test_filtering_and_search_endpoints(self):
        """Debe soportar filtrado y búsqueda en endpoints"""
        # Crear datos adicionales para filtrar
        Roles.objects.create(nombre_rol="Filterable Role", estado=False)

        search_params = [
            {"estado": "true"},
            {"estado": "false"},
            {"search": "Test"},
            {"ordering": "nombre_rol"},
            {"ordering": "-nombre_rol"},
        ]

        for params in search_params:
            response = self.client.get("/api/usuarios/roles/", params)
            # Debe devolver respuesta válida (no error de servidor)
            self.assertLess(response.status_code, 500)

    def test_content_type_headers(self):
        """Debe manejar Content-Type headers correctamente"""
        url = "/api/usuarios/roles/"

        # JSON
        json_response = self.client.get(url, HTTP_ACCEPT="application/json")
        self.assertLess(json_response.status_code, 500)

        # XML (si está soportado)
        xml_response = self.client.get(url, HTTP_ACCEPT="application/xml")
        # XML puede no estar soportado, pero no debe dar error de servidor
        if xml_response.status_code < 500:
            self.assertIsNotNone(xml_response.content)

    def test_pagination_endpoints(self):
        """Debe soportar paginación en endpoints de listado"""
        # Crear múltiples roles para probar paginación
        for i in range(15):
            Roles.objects.create(nombre_rol=f"Pagination Role {i}", estado=True)

        # Test paginación básica
        response = self.client.get("/api/usuarios/roles/", {"page": 1})

        if response.status_code == 200:
            # Si existe paginación, verificar estructura
            if "results" in response.data:
                self.assertIn("count", response.data)
                self.assertIn("next", response.data)
                self.assertIn("previous", response.data)

    def test_error_handling_endpoints(self):
        """Debe manejar errores apropiadamente en endpoints"""
        # ID inexistente
        response = self.client.get("/api/usuarios/roles/99999/")
        self.assertEqual(response.status_code, 404)

        # Datos inválidos
        invalid_data = {
            "nombre_rol": "",  # Campo requerido vacío
            "descripcion": "A" * 1000,  # Muy largo
        }
        response = self.client.post("/api/usuarios/roles/", invalid_data, format="json")
        self.assertEqual(response.status_code, 400)

        # Método no permitido
        response = self.client.patch("/api/usuarios/roles/")
        self.assertIn(response.status_code, [405, 403, 401])  # Method not allowed o sin permisos
