"""
Tests para throttling (limitación de tasa) del módulo common
Verifica los 5 throttles implementados para DRF
"""

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.common.throttling import (
    AuthRateThrottle,
    BurstRateThrottle,
    ReportesRateThrottle,
    SustainedRateThrottle,
    VentasRateThrottle,
)


class BaseThrottleTest(TestCase):
    """Clase base para tests de throttling"""

    def setUp(self):
        """Setup común"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="testuser", password="test123")

    def create_request(self, method="GET", user=None):
        """Helper para crear requests con usuario configurado"""
        request = getattr(self.factory, method.lower())("/test/")
        # Siempre configurar el atributo user
        if user:
            request.user = user
        else:
            request.user = AnonymousUser()
        return request


class BurstRateThrottleTest(BaseThrottleTest):
    """Tests para BurstRateThrottle"""

    def test_throttle_tiene_scope_correcto(self):
        """BurstRateThrottle tiene scope 'burst'"""
        throttle = BurstRateThrottle()
        self.assertEqual(throttle.scope, "burst")

    def test_throttle_hereda_de_user_rate_throttle(self):
        """BurstRateThrottle hereda de UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = BurstRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)

    def test_throttle_se_puede_instanciar(self):
        """BurstRateThrottle se puede instanciar correctamente"""
        throttle = BurstRateThrottle()
        self.assertIsNotNone(throttle)

    def test_throttle_permite_request_unico(self):
        """BurstRateThrottle permite un request único"""
        throttle = BurstRateThrottle()
        request = self.create_request("GET", self.user)

        # Primer request siempre debe ser permitido
        # (o depende de configuración en settings.py)
        self.assertIsNotNone(throttle.get_cache_key(request, None))


class SustainedRateThrottleTest(BaseThrottleTest):
    """Tests para SustainedRateThrottle"""

    def test_throttle_tiene_scope_correcto(self):
        """SustainedRateThrottle tiene scope 'sustained'"""
        throttle = SustainedRateThrottle()
        self.assertEqual(throttle.scope, "sustained")

    def test_throttle_hereda_de_user_rate_throttle(self):
        """SustainedRateThrottle hereda de UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = SustainedRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)

    def test_throttle_se_puede_instanciar(self):
        """SustainedRateThrottle se puede instanciar correctamente"""
        throttle = SustainedRateThrottle()
        self.assertIsNotNone(throttle)

    def test_throttle_funciona_para_usuarios_autenticados(self):
        """SustainedRateThrottle funciona para usuarios autenticados"""
        throttle = SustainedRateThrottle()
        request = self.create_request("GET", self.user)

        # Debe generar cache key para usuarios autenticados
        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        self.assertIn("sustained", cache_key)


class VentasRateThrottleTest(BaseThrottleTest):
    """Tests para VentasRateThrottle"""

    def test_throttle_tiene_scope_correcto(self):
        """VentasRateThrottle tiene scope 'ventas'"""
        throttle = VentasRateThrottle()
        self.assertEqual(throttle.scope, "ventas")

    def test_throttle_hereda_de_user_rate_throttle(self):
        """VentasRateThrottle hereda de UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = VentasRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)

    def test_throttle_se_puede_instanciar(self):
        """VentasRateThrottle se puede instanciar correctamente"""
        throttle = VentasRateThrottle()
        self.assertIsNotNone(throttle)

    def test_throttle_permite_configuracion_personalizada(self):
        """VentasRateThrottle permite configuración específica para ventas"""
        throttle = VentasRateThrottle()
        request = self.create_request("POST", self.user)

        # Debe generar cache key única para ventas
        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        self.assertIn("ventas", cache_key)


class AuthRateThrottleTest(BaseThrottleTest):
    """Tests para AuthRateThrottle"""

    def test_throttle_tiene_scope_correcto(self):
        """AuthRateThrottle tiene scope 'auth'"""
        throttle = AuthRateThrottle()
        self.assertEqual(throttle.scope, "auth")

    def test_throttle_hereda_de_anon_rate_throttle(self):
        """AuthRateThrottle hereda de AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = AuthRateThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)

    def test_throttle_se_puede_instanciar(self):
        """AuthRateThrottle se puede instanciar correctamente"""
        throttle = AuthRateThrottle()
        self.assertIsNotNone(throttle)

    def test_throttle_funciona_para_usuarios_anonimos(self):
        """AuthRateThrottle funciona para usuarios anónimos"""
        throttle = AuthRateThrottle()
        request = self.create_request("POST")  # Sin usuario

        # Debe generar cache key basada en IP para anónimos
        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        self.assertIn("auth", cache_key)

    def test_throttle_previene_brute_force(self):
        """AuthRateThrottle es útil para prevenir brute force en endpoints de auth"""
        throttle = AuthRateThrottle()

        # Simular múltiples requests de autenticación fallidos
        request = self.create_request("POST")

        # Verificar que genera cache key consistente para misma IP
        cache_key_1 = throttle.get_cache_key(request, None)
        cache_key_2 = throttle.get_cache_key(request, None)

        self.assertEqual(cache_key_1, cache_key_2)


class ReportesRateThrottleTest(BaseThrottleTest):
    """Tests para ReportesRateThrottle"""

    def test_throttle_tiene_scope_correcto(self):
        """ReportesRateThrottle tiene scope 'reportes'"""
        throttle = ReportesRateThrottle()
        self.assertEqual(throttle.scope, "reportes")

    def test_throttle_hereda_de_user_rate_throttle(self):
        """ReportesRateThrottle hereda de UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = ReportesRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)

    def test_throttle_se_puede_instanciar(self):
        """ReportesRateThrottle se puede instanciar correctamente"""
        throttle = ReportesRateThrottle()
        self.assertIsNotNone(throttle)

    def test_throttle_funciona_para_operaciones_costosas(self):
        """ReportesRateThrottle está diseñado para operaciones costosas"""
        throttle = ReportesRateThrottle()
        request = self.create_request("GET", self.user)

        # Debe generar cache key para limitar reportes costosos
        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
        self.assertIn("reportes", cache_key)

    def test_throttle_diferencia_usuarios(self):
        """ReportesRateThrottle diferencia entre usuarios"""
        throttle = ReportesRateThrottle()

        # Usuario 1
        request1 = self.create_request("GET", self.user)
        cache_key_1 = throttle.get_cache_key(request1, None)

        # Usuario 2
        user2 = User.objects.create_user(username="user2", password="pass123")
        request2 = self.create_request("GET", user2)
        cache_key_2 = throttle.get_cache_key(request2, None)

        # Las cache keys deben ser diferentes
        self.assertNotEqual(cache_key_1, cache_key_2)


class ThrottleIntegrationTest(BaseThrottleTest):
    """Tests de integración para throttles"""

    def test_diferentes_throttles_tienen_scopes_unicos(self):
        """Cada throttle tiene su propio scope único"""
        scopes = {
            BurstRateThrottle().scope,
            SustainedRateThrottle().scope,
            VentasRateThrottle().scope,
            AuthRateThrottle().scope,
            ReportesRateThrottle().scope,
        }

        # Debe haber 5 scopes únicos
        self.assertEqual(len(scopes), 5)

        # Verificar nombres esperados
        expected_scopes = {"burst", "sustained", "ventas", "auth", "reportes"}
        self.assertEqual(scopes, expected_scopes)

    def test_user_rate_throttles_consistentes(self):
        """UserRateThrottles generan cache keys consistentes"""
        from rest_framework.throttling import UserRateThrottle

        user_throttles = [
            BurstRateThrottle(),
            SustainedRateThrottle(),
            VentasRateThrottle(),
            ReportesRateThrottle(),
        ]

        request = self.create_request("GET", self.user)

        for throttle in user_throttles:
            # Todas deben heredar de UserRateThrottle
            self.assertIsInstance(throttle, UserRateThrottle)

            # Todas deben generar cache key para usuarios autenticados
            cache_key = throttle.get_cache_key(request, None)
            self.assertIsNotNone(cache_key)

    def test_anon_rate_throttle_para_auth(self):
        """AuthRateThrottle usa AnonRateThrottle para seguridad"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = AuthRateThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)

        # Debe funcionar sin usuario autenticado
        request = self.create_request("POST")
        cache_key = throttle.get_cache_key(request, None)
        self.assertIsNotNone(cache_key)
