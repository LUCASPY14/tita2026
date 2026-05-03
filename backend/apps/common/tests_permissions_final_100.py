"""
Tests finales para alcanzar 100% cobertura en common.permissions
Cubre líneas específicas: 16-19, 27-28, 51-52, 119, branch 15->23
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

import pytest
from rest_framework.test import APIRequestFactory

from apps.common.permissions import IsAdminOrReadOnly, IsClienteOrAdmin, _get_empleado_from_request
from apps.usuarios.models import Empleados, Roles

User = get_user_model()


@pytest.mark.django_db
class TestGetEmpleadoExceptionPaths:
    """Tests para cubrir excepciones en _get_empleado_from_request"""

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def user_regular(self):
        return User.objects.create_user(username="testuser", password="testpass123")

    def test_exception_al_buscar_empleado_en_db(self, factory, user_regular):
        """
        Cubrir líneas 16-19: excepción al ejecutar Empleados.objects.get()
        """
        # Arrange: mock request con auth que tiene payload pero empleado no existe
        request = factory.get("/api/test/")
        request.user = user_regular

        # Mock auth con payload que tiene id_empleado inválido
        mock_auth = Mock()
        mock_auth.payload = {"id_empleado": 9999}  # ID que no existe
        request.auth = mock_auth

        # Act: debe capturar la excepción DoesNotExist y retornar None
        resultado = _get_empleado_from_request(request)

        # Assert
        assert resultado is None

    def test_exception_en_fallback_getattr(self, factory):
        """
        Cubrir líneas 27-28: excepción en fallback cuando getattr falla
        """
        # Arrange: mock user que lanza excepción al acceder atributo
        request = factory.get("/api/test/")

        # Mock user que lanza excepción en getattr
        mock_user = Mock()
        mock_user.is_authenticated = True

        # Hacer que getattr lance excepción
        def side_effect(*args, **kwargs):
            raise AttributeError("Forzar error")

        request.user = mock_user
        request.auth = None  # No hay JWT

        # Act: con patch para forzar el error
        with patch("apps.common.permissions.getattr", side_effect=side_effect):
            resultado = _get_empleado_from_request(request)

        # Assert
        assert resultado is None

    def test_request_sin_auth_salta_directamente_a_fallback(self, factory, user_regular):
        """
        Cubrir branch 15->23: cuando request.auth es None
        """
        # Arrange
        request = factory.get("/api/test/")
        request.user = user_regular
        request.auth = None  # Sin JWT

        # El user no tiene atributo empleado
        # Act
        resultado = _get_empleado_from_request(request)

        # Assert: debe retornar None sin pasar por el bloque JWT
        assert resultado is None

    def test_id_empleado_cero_salta_a_fallback(self, factory, user_regular):
        """
        Cubrir branch 17->23: cuando id_empleado es falsy (0, "", False)
        """
        # Arrange: mock request con auth que tiene id_empleado = 0
        request = factory.get("/api/test/")
        request.user = user_regular

        # Mock auth con payload que tiene id_empleado falsy
        mock_auth = Mock()
        mock_auth.payload = {"id_empleado": 0}  # Falsy pero presente
        request.auth = mock_auth

        # Act: debe saltar el if id_empleado y pasar al fallback
        resultado = _get_empleado_from_request(request)

        # Assert: debe retornar None (no hay empleado)
        assert resultado is None


@pytest.mark.django_db
class TestIsAdminOrReadOnlyWithEmpleado:
    """Tests para cubrir líneas 51-52 en IsAdminOrReadOnly"""

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def user_regular(self):
        return User.objects.create_user(username="empleado_user", password="pass123")

    @pytest.fixture
    def rol_gerente(self):
        return Roles.objects.create(nombre_rol="Gerente", descripcion="Rol de gerente", estado=True)

    @pytest.fixture
    def empleado_gerente(self, rol_gerente):
        from datetime import datetime, timezone

        return Empleados.objects.create(
            nombre="Carlos",
            apellido="Gerente",
            usuario="cgerente",
            contrasena_hash="hash123",
            fecha_ingreso=datetime.now(timezone.utc),
            id_rol=rol_gerente,
            estado=True,
        )

    def test_empleado_gerente_puede_escribir(self, factory, user_regular, empleado_gerente):
        """
        Cubrir líneas 51-52: empleado con rol permitido puede escribir
        """
        # Arrange: POST request (no SAFE)
        request = factory.post("/api/test/")
        request.user = user_regular
        request.user.is_staff = False

        # Mock para que _get_empleado_from_request retorne el empleado
        request.user.empleado = empleado_gerente
        request.auth = None

        permission = IsAdminOrReadOnly()

        # Act
        has_permission = permission.has_permission(request, None)

        # Assert: debe tener permiso porque "gerente" está en roles_permitidos
        assert has_permission is True


@pytest.mark.django_db
class TestIsClienteOrAdminWithEmpleado:
    """Tests para cubrir línea 119 en IsClienteOrAdmin"""

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def user_regular(self):
        return User.objects.create_user(username="empleado_user2", password="pass456")

    @pytest.fixture
    def rol_vendedor(self):
        return Roles.objects.create(nombre_rol="Vendedor", descripcion="Rol de vendedor", estado=True)

    @pytest.fixture
    def empleado_vendedor(self, rol_vendedor):
        from datetime import datetime, timezone

        return Empleados.objects.create(
            nombre="Maria",
            apellido="Vendedora",
            usuario="mvendedora",
            contrasena_hash="hash456",
            fecha_ingreso=datetime.now(timezone.utc),
            id_rol=rol_vendedor,
            estado=True,
        )

    def test_empleado_autenticado_via_jwt_tiene_acceso(self, factory, user_regular, empleado_vendedor):
        """
        Cubrir línea 119: return True cuando empleado is not None
        """
        # Arrange
        request = factory.get("/api/test/")
        request.user = user_regular
        request.user.is_staff = False

        # Mock para que _get_empleado_from_request retorne el empleado
        request.user.empleado = empleado_vendedor
        request.auth = None

        permission = IsClienteOrAdmin()

        # Act
        has_permission = permission.has_permission(request, None)

        # Assert: debe tener permiso porque empleado is not None (línea 119)
        assert has_permission is True
