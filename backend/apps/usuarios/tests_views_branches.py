"""
Tests de cobertura de ramas para usuarios/views.py.
Cubre los branches faltantes: _get_client_ip (X-Forwarded-For),
cambiar_password (empleado no encontrado, admin check, Django User DoesNotExist).
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

import pytest


@pytest.mark.django_db
class GetClientIpForwardedForTest(TestCase):
    """
    Lines 211, 321, 395, 508: _get_client_ip branches when HTTP_X_FORWARDED_FOR is present.
    The `if x_forwarded_for:` branch (True path) is not covered by existing tests.
    """

    def setUp(self):
        from apps.usuarios.views import EmpleadosViewSet

        self.factory = RequestFactory()
        self.viewset = EmpleadosViewSet()

    def test_gets_ip_from_x_forwarded_for(self):
        """When HTTP_X_FORWARDED_FOR is set, use the first IP in the chain."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 10.0.0.1"
        result = self.viewset._get_client_ip(request)
        self.assertEqual(result, "203.0.113.1")

    def test_gets_ip_from_remote_addr_when_no_forwarded_for(self):
        """When HTTP_X_FORWARDED_FOR is absent, fallback to REMOTE_ADDR."""
        request = self.factory.get("/")
        # ensure no X-Forwarded-For header
        request.META.pop("HTTP_X_FORWARDED_FOR", None)
        request.META["REMOTE_ADDR"] = "192.168.1.50"
        result = self.viewset._get_client_ip(request)
        self.assertEqual(result, "192.168.1.50")

    def test_forwarded_for_single_ip(self):
        """X-Forwarded-For with a single IP (no comma)."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.99"
        result = self.viewset._get_client_ip(request)
        self.assertEqual(result, "10.0.0.99")


@pytest.mark.django_db
class OtherViewSetClientIpTest(TestCase):
    """Test _get_client_ip for TwoFactorViewSet, SesionesViewSet, PermisosViewSet, PasswordRecoveryViewSet"""

    def _get_ip(self, viewset_class, forwarded=None):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")
        if forwarded:
            request.META["HTTP_X_FORWARDED_FOR"] = forwarded
        else:
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
        vs = viewset_class.__new__(viewset_class)
        return vs._get_client_ip(request)

    def test_two_factor_viewset_forwarded_for(self):
        from apps.usuarios.views import TwoFactorViewSet

        ip = self._get_ip(TwoFactorViewSet, "1.2.3.4, 5.6.7.8")
        self.assertEqual(ip, "1.2.3.4")

    def test_sesiones_viewset_forwarded_for(self):
        from apps.usuarios.views import SesionesViewSet

        ip = self._get_ip(SesionesViewSet, "9.9.9.9")
        self.assertEqual(ip, "9.9.9.9")

    def test_password_recovery_viewset_forwarded_for(self):
        from apps.usuarios.views import PasswordRecoveryViewSet

        ip = self._get_ip(PasswordRecoveryViewSet, "100.100.100.100, 10.0.0.1")
        self.assertEqual(ip, "100.100.100.100")

    def test_auth_viewset_forwarded_for(self):
        """Branch 210->211: AuthViewSet._get_client_ip True arm (X-Forwarded-For present)."""
        from apps.usuarios.views import AuthViewSet

        ip = self._get_ip(AuthViewSet, "203.0.113.100, 10.10.0.1")
        self.assertEqual(ip, "203.0.113.100")

    def test_auth_viewset_no_forwarded_fallback(self):
        """AuthViewSet._get_client_ip False arm (REMOTE_ADDR fallback)."""
        from apps.usuarios.views import AuthViewSet

        ip = self._get_ip(AuthViewSet, None)
        self.assertIsNotNone(ip)


@pytest.mark.django_db
class CambiarPasswordBranchesTest(TestCase):
    """
    Lines 756, 801-802, 821-822, 838-839, 847 in EmpleadosViewSet.cambiar_password.

    Missing branches:
    - empleado_actual not found (Empleados.DoesNotExist) → 404
    - empleado_actual not admin → 403
    - Django User not found (User.DoesNotExist) → pass (line 838-839)
    - Valid password change with Django User existing → 200
    """

    def setUp(self):
        from django.utils import timezone

        from apps.usuarios.models import Empleados, Roles

        self.factory = RequestFactory()
        self.rol_admin, _ = Roles.objects.get_or_create(nombre_rol="Administrador", defaults={"descripcion": "Admin"})
        self.rol_cajero, _ = Roles.objects.get_or_create(nombre_rol="Cajero", defaults={"descripcion": "Cajero"})
        # Create Django admin user for authentication
        self.django_admin = User.objects.create_user(
            username="admin_view_branch_test",
            password="adminpass123",
        )
        self.django_cajero = User.objects.create_user(
            username="cajero_view_branch_test",
            password="cajeropass123",
        )
        # Create Empleados records
        self.empleado_admin = Empleados.objects.create(
            nombre="Admin",
            apellido="Test",
            usuario="admin_view_branch_test",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol_admin,
        )
        self.empleado_cajero = Empleados.objects.create(
            nombre="Cajero",
            apellido="Test",
            usuario="cajero_view_branch_test",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol_cajero,
        )
        self.empleado_target = Empleados.objects.create(
            nombre="Target",
            apellido="User",
            usuario="target_view_branch_test",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol_cajero,
        )

    def _build_request(self, user, data):
        import json

        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.post("/", data=json.dumps(data), content_type="application/json")
        request.user = user
        request.data = data
        return request

    def test_cambiar_password_empleado_no_encontrado(self):
        """Lines 821-822: Empleados.DoesNotExist → 404"""
        from apps.usuarios.views import EmpleadosViewSet

        # Create Django user but NO corresponding Empleados record
        orphan_user = User.objects.create_user(username="orphan_branch_test", password="orphanpass123")
        request = self._build_request(orphan_user, {"password": "NewPass1234!"})
        vs = EmpleadosViewSet()
        vs.kwargs = {}
        # Patch get_object to return the target empleado
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        # Should return 404 because orphan_user has no Empleados record
        self.assertEqual(response.status_code, 404)
        orphan_user.delete()

    def test_cambiar_password_no_admin_role(self):
        """Lines 801-802: cajero doesn't have Admin role → 403"""
        from apps.usuarios.views import EmpleadosViewSet

        request = self._build_request(self.django_cajero, {"password": "NewPass1234!"})
        vs = EmpleadosViewSet()
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        self.assertEqual(response.status_code, 403)

    def test_cambiar_password_missing_password_field(self):
        """Lines 756: no password provided → 400"""
        from apps.usuarios.views import EmpleadosViewSet

        request = self._build_request(self.django_admin, {})
        vs = EmpleadosViewSet()
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        self.assertEqual(response.status_code, 400)

    def test_cambiar_password_too_short(self):
        """Short password → 400"""
        from apps.usuarios.views import EmpleadosViewSet

        request = self._build_request(self.django_admin, {"password": "abc"})
        vs = EmpleadosViewSet()
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        self.assertEqual(response.status_code, 400)

    def test_cambiar_password_success_no_django_user(self):
        """Lines 838-839: Django User.DoesNotExist is silently passed; success 200"""
        from apps.usuarios.views import EmpleadosViewSet

        # Ensure target has no Django User
        User.objects.filter(username=self.empleado_target.usuario).delete()
        request = self._build_request(self.django_admin, {"password": "ValidPass123!"})
        vs = EmpleadosViewSet()
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        self.assertEqual(response.status_code, 200)

    def test_cambiar_password_success_with_django_user(self):
        """Line 847: Django User exists and password is updated → 200"""
        from apps.usuarios.views import EmpleadosViewSet

        # Create Django user for target
        User.objects.filter(username=self.empleado_target.usuario).delete()
        django_target = User.objects.create_user(username=self.empleado_target.usuario, password="oldpass123")
        request = self._build_request(self.django_admin, {"password": "ValidPass456!"})
        vs = EmpleadosViewSet()
        with patch.object(EmpleadosViewSet, "get_object", return_value=self.empleado_target):
            response = vs.cambiar_password(request, pk=self.empleado_target.pk)
        self.assertEqual(response.status_code, 200)
        django_target.delete()


@pytest.mark.django_db
class EmpleadosCreateSerializerInvalidTest(TestCase):
    """
    Branch 753->756: EmpleadosViewSet.create when serializer.is_valid() returns False.
    All manual field checks pass, but serializer rejects data (invalid FK for id_rol).
    """

    def setUp(self):
        self.django_user = User.objects.create_user(username="create_serial_test_user", password="test1234")

    def test_create_invalid_serializer_returns_400(self):
        """Branch 753->756: valid manual checks but invalid serializer → 400."""
        from rest_framework.test import APIRequestFactory

        from apps.usuarios.views import EmpleadosViewSet

        factory = APIRequestFactory()
        data = {
            "nombre": "Test",
            "apellido": "User",
            "usuario": "brand_new_unique_xyz123",
            "password": "SomePass123!",
            "fecha_ingreso": "2024-01-01",
            "id_rol": 99999,  # non-existent FK → serializer.is_valid() → False
        }
        request = factory.post("/api/v1/empleados/", data, format="json")
        request.user = self.django_user
        request.data = data
        vs = EmpleadosViewSet()
        vs.kwargs = {}
        response = vs.create(request)
        self.assertEqual(response.status_code, 400)


@pytest.mark.django_db
class PermisosViewSetBranchTest(TestCase):
    """Lines 538-541: PermisosViewSet.asignar_a_rol - Roles.DoesNotExist branch."""

    def setUp(self):
        from apps.usuarios.models import Roles

        self.factory = RequestFactory()
        self.rol, _ = Roles.objects.get_or_create(
            nombre_rol="Admin_perm_branch",
            defaults={"descripcion": "Admin"},
        )
        self.django_user = User.objects.create_user(username="perm_branch_test_user", password="test1234")

    def test_asignar_a_rol_not_found_returns_404(self):
        """Lines 538-541: Roles.DoesNotExist raises - 404 is returned"""
        from rest_framework.test import APIRequestFactory

        from apps.usuarios.views import PermisosViewSet

        factory = APIRequestFactory()
        request = factory.post("/", {"id_rol": 99999, "codigo_permiso": "ventas.crear"})
        request.user = self.django_user
        request.data = {"id_rol": 99999, "codigo_permiso": "ventas.crear"}
        vs = PermisosViewSet()
        vs.kwargs = {}
        response = vs.asignar_a_rol(request)
        self.assertEqual(response.status_code, 404)

    def test_listar_permisos_with_data_covers_loop_branches(self):
        """
        Branches 537->538 (loop body), 539->540 (new module), 539->541 (existing module).
        Creates permisos from 2 modules so the loop runs and both if arms are hit.
        """
        from rest_framework.test import APIRequestFactory

        from apps.usuarios.permissions import Permisos
        from apps.usuarios.views import PermisosViewSet

        # Create permisos from two modules, with 2 in the same module
        p1, _ = Permisos.objects.get_or_create(
            codigo_permiso="branch_test.ver",
            defaults={"nombre": "P1", "modulo": "branch_mod_a", "estado": True},
        )
        p2, _ = Permisos.objects.get_or_create(
            codigo_permiso="branch_test.crear",
            defaults={"nombre": "P2", "modulo": "branch_mod_a", "estado": True},  # same module
        )
        p3, _ = Permisos.objects.get_or_create(
            codigo_permiso="branch_test.eliminar",
            defaults={"nombre": "P3", "modulo": "branch_mod_b", "estado": True},  # different module
        )

        factory = APIRequestFactory()
        request = factory.get("/api/v1/permisos/")
        request.user = self.django_user
        vs = PermisosViewSet()
        vs.kwargs = {}
        response = vs.listar(request)
        self.assertEqual(response.status_code, 200)
        # Verify the grouping worked
        self.assertIn("permisos_por_modulo", response.data)
