"""
Tests para core/decorators.py
Cubre admin_required, api_admin_required, staff_required
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse


class AdminRequiredDecoratorTest(TestCase):
    """Tests para el decorador admin_required"""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin_dec', password='pass123', email='admin@test.com', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='normal_dec', password='pass123', email='normal@test.com', is_staff=False
        )

    def _make_view(self):
        from apps.core.decorators import admin_required

        @admin_required
        def sample_view(request):
            return JsonResponse({'ok': True})

        return sample_view

    def test_permite_acceso_a_admin(self):
        """Admin debe poder acceder"""
        view = self._make_view()
        request = self.factory.get('/')
        request.user = self.admin_user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_bloquea_usuario_sin_autenticar(self):
        """Usuario no autenticado debe recibir 401"""
        from django.contrib.auth.models import AnonymousUser
        view = self._make_view()
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_bloquea_usuario_normal(self):
        """Usuario sin permisos de admin debe recibir 403"""
        view = self._make_view()
        request = self.factory.get('/')
        request.user = self.normal_user
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_preserva_nombre_de_funcion(self):
        """El decorador debe preservar el nombre de la función original"""
        from apps.core.decorators import admin_required

        @admin_required
        def mi_vista_especial(request):
            return JsonResponse({'ok': True})

        self.assertEqual(mi_vista_especial.__name__, 'mi_vista_especial')


class ApiAdminRequiredDecoratorTest(TestCase):
    """Tests para el decorador api_admin_required (DRF)"""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='api_admin_dec', password='pass123', email='apiadmin@test.com', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='api_normal_dec', password='pass123', email='apinormal@test.com', is_staff=False
        )

    def _wrap_for_drf(self, request):
        """Convierte el request de Django a un request compatible con DRF mock."""
        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser
        drf_request = Request(request, parsers=[JSONParser()])
        return drf_request

    def test_bloquea_usuario_sin_autenticar(self):
        """api_admin_required debe bloquear requests sin autenticar"""
        from apps.core.decorators import api_admin_required
        from django.contrib.auth.models import AnonymousUser

        @api_admin_required
        def api_view(request):
            from rest_framework.response import Response
            return Response({'ok': True})

        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = api_view(request)
        self.assertEqual(response.status_code, 401)

    def test_bloquea_usuario_no_admin(self):
        """api_admin_required debe bloquear usuarios sin is_staff"""
        from apps.core.decorators import api_admin_required

        @api_admin_required
        def api_view(request):
            from rest_framework.response import Response
            return Response({'ok': True})

        request = self.factory.get('/')
        request.user = self.normal_user
        response = api_view(request)
        self.assertEqual(response.status_code, 403)

    def test_permite_admin(self):
        """api_admin_required debe permitir usuarios con is_staff"""
        from apps.core.decorators import api_admin_required
        from rest_framework.response import Response

        @api_admin_required
        def api_view(request):
            return Response({'ok': True})

        request = self.factory.get('/')
        request.user = self.admin_user
        response = api_view(request)
        self.assertEqual(response.status_code, 200)

    def test_preserva_nombre_funcion(self):
        """El decorador debe preservar el nombre de la función"""
        from apps.core.decorators import api_admin_required

        @api_admin_required
        def mi_api_vista(request):
            return None

        self.assertEqual(mi_api_vista.__name__, 'mi_api_vista')


class StaffRequiredDecoratorTest(TestCase):
    """Tests para el decorador staff_required"""

    def setUp(self):
        self.factory = RequestFactory()
        self.staff_user = User.objects.create_user(
            username='staff_dec', password='pass123', email='staff@test.com',
            is_staff=True, is_superuser=False
        )
        self.superuser = User.objects.create_superuser(
            username='super_dec', password='pass123', email='super@test.com'
        )
        self.normal_user = User.objects.create_user(
            username='norm_dec', password='pass123', email='norm@test.com',
            is_staff=False, is_superuser=False
        )

    def _make_view(self):
        from apps.core.decorators import staff_required

        @staff_required
        def sample_view(request):
            return JsonResponse({'ok': True})

        return sample_view

    def test_permite_staff(self):
        """Staff user debe poder acceder"""
        view = self._make_view()
        request = self.factory.get('/')
        request.user = self.staff_user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_permite_superuser(self):
        """Superuser debe poder acceder"""
        view = self._make_view()
        request = self.factory.get('/')
        request.user = self.superuser
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_bloquea_usuario_no_staff(self):
        """Usuario sin staff debe recibir 403"""
        view = self._make_view()
        request = self.factory.get('/')
        request.user = self.normal_user
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_bloquea_anonimo(self):
        """Anónimo debe recibir 401"""
        from django.contrib.auth.models import AnonymousUser
        view = self._make_view()
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_preserva_nombre_funcion(self):
        """El decorador debe preservar el nombre de la función"""
        from apps.core.decorators import staff_required

        @staff_required
        def mi_staff_vista(request):
            return None

        self.assertEqual(mi_staff_vista.__name__, 'mi_staff_vista')
