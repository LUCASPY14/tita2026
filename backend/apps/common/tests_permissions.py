"""
Tests simplificados para permisos del módulo common
Tests básicos sin dependencias complejas de modelos
"""

from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.test import APIRequestFactory

from apps.common.permissions import IsAdminOrReadOnly, ReadOnly


class IsAdminOrReadOnlyTest(TestCase):
    """Tests para IsAdminOrReadOnly permission"""

    def setUp(self):
        """Setup users"""
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_user(username="admin", password="admin123", is_staff=True)
        self.normal_user = User.objects.create_user(username="user", password="user123", is_staff=False)

    def test_authenticated_user_can_read(self):
        """Usuario autenticado puede leer (GET)"""
        permission = IsAdminOrReadOnly()
        request = self.factory.get("/test/")
        request.user = self.normal_user

        self.assertTrue(permission.has_permission(request, None))

    def test_authenticated_user_cannot_write(self):
        """Usuario normal no puede escribir (POST)"""
        permission = IsAdminOrReadOnly()
        request = self.factory.post("/test/")
        request.user = self.normal_user

        self.assertFalse(permission.has_permission(request, None))

    def test_admin_can_write(self):
        """Administrador puede escribir"""
        permission = IsAdminOrReadOnly()
        request = self.factory.post("/test/")
        request.user = self.admin_user

        self.assertTrue(permission.has_permission(request, None))

    def test_admin_can_delete(self):
        """Administrador puede eliminar"""
        permission = IsAdminOrReadOnly()
        request = self.factory.delete("/test/")
        request.user = self.admin_user

        self.assertTrue(permission.has_permission(request, None))


class ReadOnlyTest(TestCase):
    """Tests para ReadOnly permission"""

    def setUp(self):
        """Setup users"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="test123")

    def test_authenticated_user_can_read(self):
        """Usuario autenticado puede leer"""
        permission = ReadOnly()
        request = self.factory.get("/test/")
        request.user = self.user

        self.assertTrue(permission.has_permission(request, None))

    def test_authenticated_user_cannot_write(self):
        """Usuario autenticado no puede escribir"""
        permission = ReadOnly()
        request = self.factory.post("/test/")
        request.user = self.user

        self.assertFalse(permission.has_permission(request, None))

    def test_head_method_allowed(self):
        """Método HEAD permitido"""
        permission = ReadOnly()
        request = self.factory.head("/test/")
        request.user = self.user

        self.assertTrue(permission.has_permission(request, None))

    def test_options_method_allowed(self):
        """Método OPTIONS permitido"""
        permission = ReadOnly()
        request = self.factory.options("/test/")
        request.user = self.user

        self.assertTrue(permission.has_permission(request, None))


class IsCajeroOrAdminTest(TestCase):
    """Tests para IsCajeroOrAdmin permission"""

    def setUp(self):
        from apps.common.permissions import IsCajeroOrAdmin

        self.factory = APIRequestFactory()
        self.permission = IsCajeroOrAdmin()
        self.admin_user = User.objects.create_user(username="cajero_admin", password="pass", is_staff=True)
        self.normal_user = User.objects.create_user(username="cajero_normal", password="pass", is_staff=False)

    def test_no_autenticado_retorna_false(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permission.has_permission(request, None))

    def test_admin_staff_retorna_true(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_usuario_sin_empleado_retorna_false(self):
        """Usuario sin atributo empleado: except devuelve False"""
        request = self.factory.get("/")
        request.user = self.normal_user
        # normal_user no tiene .empleado → exception → False
        self.assertFalse(self.permission.has_permission(request, None))

    def test_usuario_con_rol_cajero(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.is_staff = False
        rol_mock = MagicMock()
        rol_mock.nombre_rol = "Cajero"
        empleado_mock = MagicMock()
        empleado_mock.id_rol = rol_mock
        user.empleado = empleado_mock
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_usuario_con_rol_no_permitido(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.is_staff = False
        rol_mock = MagicMock()
        rol_mock.nombre_rol = "Supervisor"
        empleado_mock = MagicMock()
        empleado_mock.id_rol = rol_mock
        user.empleado = empleado_mock
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))


class IsOwnerOrAdminTest(TestCase):
    """Tests para IsOwnerOrAdmin permission"""

    def setUp(self):
        from apps.common.permissions import IsOwnerOrAdmin

        self.factory = APIRequestFactory()
        self.permission = IsOwnerOrAdmin()
        self.admin_user = User.objects.create_user(username="owner_admin", password="pass", is_staff=True)
        self.normal_user = User.objects.create_user(username="owner_normal", password="pass", is_staff=False)

    def test_admin_tiene_acceso_total(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = self.admin_user
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_objeto_con_id_cliente_correcto(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = self.normal_user
        obj = MagicMock()
        obj.id_cliente = MagicMock()
        obj.id_cliente.user = self.normal_user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_objeto_con_id_cliente_incorrecto(self):
        from unittest.mock import MagicMock

        other_user = User.objects.create_user(username="other_user", password="pass")
        request = self.factory.get("/")
        request.user = self.normal_user
        obj = MagicMock()
        obj.id_cliente = MagicMock()
        obj.id_cliente.user = other_user
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_objeto_con_usuario_correcto(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = self.normal_user
        obj = MagicMock(spec=["usuario"])
        obj.usuario = self.normal_user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_objeto_sin_id_cliente_ni_usuario(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = self.normal_user
        obj = MagicMock(spec=[])  # sin atributos
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class IsClienteOrAdminTest(TestCase):
    """Tests para IsClienteOrAdmin permission"""

    def setUp(self):
        from apps.common.permissions import IsClienteOrAdmin

        self.factory = APIRequestFactory()
        self.permission = IsClienteOrAdmin()
        self.admin_user = User.objects.create_user(username="cliente_admin", password="pass", is_staff=True)
        self.normal_user = User.objects.create_user(username="cliente_normal", password="pass", is_staff=False)

    def test_no_autenticado_retorna_false(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permission.has_permission(request, None))

    def test_admin_retorna_true(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_usuario_sin_cliente_retorna_false(self):
        """User sin atributo .cliente retorna True porque hasattr chequea existencia"""
        request = self.factory.get("/")
        request.user = self.normal_user
        # Django User doesn't have .cliente attr
        self.assertFalse(self.permission.has_permission(request, None))


class CanManageVentasTest(TestCase):
    """Tests para CanManageVentas permission"""

    def setUp(self):
        from apps.common.permissions import CanManageVentas

        self.factory = APIRequestFactory()
        self.permission = CanManageVentas()
        self.admin_user = User.objects.create_user(username="ventas_admin", password="pass", is_staff=True)
        self.normal_user = User.objects.create_user(username="ventas_normal", password="pass", is_staff=False)

    def test_no_autenticado_retorna_false(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permission.has_permission(request, None))

    def test_staff_retorna_true(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_cajero_retorna_true(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.is_staff = False
        rol_mock = MagicMock()
        rol_mock.nombre_rol = "Cajero"
        empleado_mock = MagicMock()
        empleado_mock.id_rol = rol_mock
        user.empleado = empleado_mock
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_sin_empleado_retorna_false(self):
        request = self.factory.get("/")
        request.user = self.normal_user
        self.assertFalse(self.permission.has_permission(request, None))


class CanManageInventarioTest(TestCase):
    """Tests para CanManageInventario permission"""

    def setUp(self):
        from apps.common.permissions import CanManageInventario

        self.factory = APIRequestFactory()
        self.permission = CanManageInventario()
        self.admin_user = User.objects.create_user(username="inv_admin", password="pass", is_staff=True)
        self.normal_user = User.objects.create_user(username="inv_normal", password="pass", is_staff=False)

    def test_no_autenticado_retorna_false(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permission.has_permission(request, None))

    def test_staff_retorna_true(self):
        request = self.factory.get("/")
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_gerente_retorna_true(self):
        from unittest.mock import MagicMock

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.is_staff = False
        rol_mock = MagicMock()
        rol_mock.nombre_rol = "Gerente"
        empleado_mock = MagicMock()
        empleado_mock.id_rol = rol_mock
        user.empleado = empleado_mock
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_sin_empleado_retorna_false(self):
        request = self.factory.get("/")
        request.user = self.normal_user
        self.assertFalse(self.permission.has_permission(request, None))
