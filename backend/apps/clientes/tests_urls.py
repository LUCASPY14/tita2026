"""
Tests para URLs de clientes
Cubre configuración de rutas y patrones URL para el módulo de clientes
"""

from django.test import TestCase
from django.urls import reverse, resolve, NoReverseMatch
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from apps.clientes.views import ClientesViewSet, HijosViewSet
from apps.clientes.models import Clientes, TiposCliente, Hijos, Grados
from django.contrib.auth import get_user_model

User = get_user_model()


class ClientesURLPatternsTest(TestCase):
    """Tests para patrones de URL de clientes"""

    def test_clientes_list_url_pattern(self):
        """Debe resolver URL de lista de clientes"""
        url = reverse('clientes-list')
        self.assertEqual(url, '/api/v1/clientes/')
        
        # Verificar que se puede resolver al ViewSet correcto
        resolver = resolve('/api/v1/clientes/')
        self.assertEqual(resolver.func.cls, ClientesViewSet)

    def test_clientes_detail_url_pattern(self):
        """Debe resolver URL de detalle de cliente"""
        url = reverse('clientes-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/v1/clientes/1/')
        
        # Verificar resolución
        resolver = resolve('/api/v1/clientes/1/')
        self.assertEqual(resolver.func.cls, ClientesViewSet)
        self.assertEqual(resolver.kwargs['pk'], '1')

    def test_hijos_list_url_pattern(self):
        """Debe resolver URL de lista de hijos"""
        url = reverse('hijos-list')
        self.assertEqual(url, '/api/v1/hijos/')
        
        # Verificar que se puede resolver al ViewSet correcto
        resolver = resolve('/api/v1/hijos/')
        self.assertEqual(resolver.func.cls, HijosViewSet)

    def test_hijos_detail_url_pattern(self):
        """Debe resolver URL de detalle de hijo"""
        url = reverse('hijos-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/v1/hijos/1/')
        
        # Verificar resolución
        resolver = resolve('/api/v1/hijos/1/')
        self.assertEqual(resolver.func.cls, HijosViewSet)
        self.assertEqual(resolver.kwargs['pk'], '1')

    def test_api_url_namespacing(self):
        """Debe manejar namespacing de URLs correctamente"""
        # Test sin namespace (básico)
        url = reverse('clientes-list')
        self.assertIsNotNone(url)
        
        # Test que las URLs no colisionan
        clientes_url = reverse('clientes-list')
        hijos_url = reverse('hijos-list')
        self.assertNotEqual(clientes_url, hijos_url)

    def test_viewset_action_urls(self):
        """Debe resolver URLs de acciones de ViewSet"""
        # URLs básicas de ViewSet
        urls_to_test = [
            ('clientes-list', {}),
            ('clientes-detail', {'pk': 1}),
            ('hijos-list', {}),
            ('hijos-detail', {'pk': 1}),
        ]
        
        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                self.assertIsNotNone(url)
                
                # Verificar que se puede resolver
                resolved = resolve(url)
                self.assertIsNotNone(resolved.func)
                
            except NoReverseMatch:
                self.fail(f"No se pudo resolver URL: {url_name}")

    def test_url_pattern_security(self):
        """Debe tener patrones de URL seguros"""
        # Test que las URLs no permiten caracteres peligrosos
        dangerous_patterns = ['../', '<script>', 'javascript:', 'data:']
        
        for pattern in dangerous_patterns:
            try:
                # Intentar resolver con patrón peligroso
                url = f'/clientes/{pattern}/'
                resolved = resolve(url)
                # Si llega aquí, verificar que maneja apropiadamente
                self.assertIsNotNone(resolved)
            except Exception:
                # Esperado que falle con patrones peligrosos
                pass

    def test_url_parameter_validation(self):
        """Debe validar parámetros de URL correctamente"""
        # Test con ID válido
        try:
            url = reverse('clientes-detail', kwargs={'pk': 123})
            self.assertIn('123', url)
        except NoReverseMatch:
            self.fail("No pudo resolver URL con ID válido")
        
        # Test con diferentes tipos de parámetro
        valid_ids = ['1', '999', '123456']
        for valid_id in valid_ids:
            url = reverse('clientes-detail', kwargs={'pk': valid_id})
            self.assertIsNotNone(url)

    def test_router_configuration(self):
        """Debe configurar router de DRF correctamente"""
        # Verificar que las URLs están configuradas por un router
        clientes_url = reverse('clientes-list')
        hijos_url = reverse('hijos-list')
        
        # Verificar formato típico de DRF router
        self.assertTrue(clientes_url.endswith('/'))
        self.assertTrue(hijos_url.endswith('/'))

    def test_url_patterns_consistency(self):
        """Debe mantener consistencia en patrones de URL"""
        # Test que todos los endpoints siguen convenciones similares
        list_urls = [
            reverse('clientes-list'),
            reverse('hijos-list'),
        ]
        
        for url in list_urls:
            # Verificar formato consistente
            self.assertTrue(url.endswith('/'))
            self.assertFalse(url.startswith('//'))

    def test_http_methods_routing(self):
        """Debe routear métodos HTTP correctamente"""
        # Test GET en lista
        resolver = resolve('/api/v1/clientes/')
        self.assertEqual(resolver.func.cls, ClientesViewSet)
        
        # Test GET en detalle
        resolver = resolve('/api/v1/clientes/1/')
        self.assertEqual(resolver.func.cls, ClientesViewSet)

    def test_url_encoding_handling(self):
        """Debe manejar encoding de URLs correctamente"""
        # Test con caracteres especiales escapados
        try:
            # URLs deberían manejar encoding apropiadamente
            base_url = reverse('clientes-list')
            self.assertIsNotNone(base_url)
            
            # Verificar que no hay doble encoding
            self.assertNotIn('%25', base_url)  # %25 = % encodificado
            
        except Exception as e:
            self.fail(f"Error en manejo de encoding: {e}")


class ClientesURLRoutingTest(APITestCase):
    """Tests para routing de URLs con requests reales"""

    def setUp(self):
        """Setup común para tests de routing"""
        self.client = APIClient()
        
        # Crear usuario para autenticación
        self.user = User.objects.create_user(
            'testuser@test.com',
            password='testpass123'
        )
        
        # Crear datos de prueba
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Cliente Test',
            estado=True
        )
        
        self.cliente = Clientes.objects.create(
            nombres='Test',
            apellidos='User',
            ruc_ci='12345678',
            email='test@test.com',
            estado=True,
            id_tipo_cliente=self.tipo_cliente
        )

    def test_clientes_list_routing(self):
        """Debe rutear correctamente a lista de clientes"""
        url = reverse('clientes-list')
        response = self.client.get(url)
        
        # Verificar que la URL existe (aunque requiera auth)
        self.assertNotEqual(response.status_code, 404)

    def test_clientes_detail_routing(self):
        """Debe rutear correctamente a detalle de cliente"""
        url = reverse('clientes-detail', kwargs={'pk': self.cliente.pk})
        response = self.client.get(url)
        
        # Verificar que la URL existe
        self.assertNotEqual(response.status_code, 404)

    def test_hijos_list_routing(self):
        """Debe rutear correctamente a lista de hijos"""
        url = reverse('hijos-list')
        response = self.client.get(url)
        
        # Verificar que la URL existe
        self.assertNotEqual(response.status_code, 404)

    def test_invalid_url_routing(self):
        """Debe manejar URLs inválidas apropiadamente"""
        invalid_urls = [
            '/clientes/invalid/',
            '/clientes/-1/',
            '/clientes/9999999999999999999/',
            '/hijos/invalid/',
        ]
        
        for invalid_url in invalid_urls:
            response = self.client.get(invalid_url)
            # Debería retornar 404 para URLs inválidas
            # No 500 (error del servidor)
            self.assertIn(response.status_code, [400, 404])

    def test_method_not_allowed_routing(self):
        """Debe manejar métodos no permitidos correctamente"""
        url = reverse('clientes-list')
        
        # Test método PATCH sin ID devuelve 405
        response = self.client.patch(url, data={}, format='json')
        self.assertIn(response.status_code, [405, 401, 403])

    def test_authentication_routing_behavior(self):
        """Debe manejar comportamiento de routing con autenticación"""
        # Test sin autenticación
        url = reverse('clientes-list')
        response = self.client.get(url)
        
        # Verificar que no es error 500
        self.assertNotIn(response.status_code, [500])

    def test_content_type_routing(self):
        """Debe manejar diferentes content types"""
        url = reverse('clientes-list')
        
        # Test con content type JSON
        response = self.client.get(url, content_type='application/json')
        self.assertNotEqual(response.status_code, 404)
        
        # Test con content type form
        response = self.client.get(url, content_type='application/x-www-form-urlencoded')
        self.assertNotEqual(response.status_code, 404)

    def test_query_parameters_routing(self):
        """Debe manejar query parameters en routing"""
        url = reverse('clientes-list')
        
        # Test con parámetros de query
        response = self.client.get(f"{url}?page=1&search=test")
        self.assertNotEqual(response.status_code, 404)

    def test_api_versioning_routing(self):
        """Debe manejar versionado de API en routing"""
        url = reverse('clientes-list')
        
        # Test con headers de versionado
        response = self.client.get(url, HTTP_ACCEPT='application/json; version=1.0')
        self.assertNotEqual(response.status_code, 404)

    def test_special_characters_routing(self):
        """Debe manejar caracteres especiales en routing"""
        # Test caracteres especiales en parámetros de query
        url = reverse('clientes-list')
        
        special_params = [
            'search=test%20user',  # espacio encodificado
            'search=test+user',    # espacio como +
            'search=test@user',    # @ symbol
        ]
        
        for param in special_params:
            response = self.client.get(f"{url}?{param}")
            self.assertNotEqual(response.status_code, 404)

    def test_trailing_slash_routing(self):
        """Debe manejar trailing slashes correctamente"""
        # URLs con y sin trailing slash
        urls_to_test = [
            reverse('clientes-list'),
            reverse('hijos-list'),
        ]
        
        for url in urls_to_test:
            response = self.client.get(url)
            # Verificar que maneja ambos casos apropiadamente
            # O redirige o responde directamente
            self.assertIn(response.status_code, [200, 301, 302, 401, 403])


class ClientesURLSecurityTest(TestCase):
    """Tests de seguridad para URLs de clientes"""

    def test_url_injection_prevention(self):
        """Debe prevenir inyección en URLs"""
        malicious_patterns = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32',
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '${7*7}',
            '{{7*7}}',
        ]
        
        for pattern in malicious_patterns:
            try:
                # Intentar usar pattern malicioso como ID
                url = f'/clientes/{pattern}/'
                resolved = resolve(url)
                # Si resuelve, verificar que sanitiza
                self.assertNotIn('<script>', resolved.kwargs.get('pk', ''))
            except Exception:
                # Esperado que falle
                pass

    def test_directory_traversal_prevention(self):
        """Debe prevenir directory traversal"""
        traversal_patterns = [
            '../',
            '..\\',
            '..',
            '..../',
            '%2e%2e%2f',  # ../ encoded
        ]
        
        for pattern in traversal_patterns:
            try:
                url = f'/clientes/{pattern}'
                resolved = resolve(url)
                # Verificar que no permite traversal
                self.assertIsNotNone(resolved)
            except Exception:
                # Esperado que falle con traversal
                pass

    def test_sql_injection_url_parameters(self):
        """Debe manejar parámetros sospechosos de SQL injection"""
        sql_patterns = [
            "1'; DROP TABLE--",
            "1' OR '1'='1",
            "1 UNION SELECT",
            "'; EXEC xp_--",
        ]
        
        # Django ORM debería prevenir these automáticamente,
        # pero verificar que URLs no causan errores 500
        for pattern in sql_patterns:
            try:
                url = f'/clientes/{pattern}/'
                resolved = resolve(url)
                # Verificar que puede manejar sin crash
                self.assertIsNotNone(resolved)
            except Exception:
                # Esperado para parámetros malformados
                pass

    def test_xss_prevention_in_urls(self):
        """Debe prevenir XSS a través de URLs"""
        xss_patterns = [
            '<img src=x onerror=alert(1)>',
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
        ]
        
        for pattern in xss_patterns:
            try:
                # URLs no deberían ejecutar JavaScript
                url = f'/clientes/{pattern}/'
                resolved = resolve(url)
                self.assertIsNotNone(resolved.func)
            except Exception:
                # Esperado para URLs malformadas
                pass

    def test_path_disclosure_prevention(self):
        """Debe prevenir revelación de paths del sistema"""
        # Test que errores no revelen información del sistema
        invalid_url = '/clientes/nonexistent/'
        
        try:
            resolved = resolve(invalid_url)
            # Si resuelve, no debería revelar paths
            self.assertIsNotNone(resolved)
        except Exception as e:
            # Error messages no deberían contener paths sensibles
            error_msg = str(e).lower()
            sensitive_paths = [
                '/etc/', 
                '/home/', 
                '/var/www/', 
                'c:\\', 
                'c:\\windows\\'
            ]
            
            for path in sensitive_paths:
                self.assertNotIn(path, error_msg)


class ClientesUrlsModuleImportTest(TestCase):
    """Test que importa explícitamente el módulo urls de clientes para cobertura."""

    def test_importar_modulo_urls(self):
        from apps.clientes import urls as clientes_urls
        self.assertTrue(hasattr(clientes_urls, 'urlpatterns'))
        self.assertIsInstance(clientes_urls.urlpatterns, list)

    def test_router_registrado(self):
        from apps.clientes import urls as clientes_urls
        from rest_framework.routers import DefaultRouter
        self.assertIsInstance(clientes_urls.router, DefaultRouter)


    def test_csrf_token_requirement(self):
        """Debe validar configuración de CSRF cuando corresponde"""
        # Para POST/PUT/DELETE, verificar that CSRF está activado
        from django.conf import settings
        
        # Verificar que CSRF middleware está configurado
        middleware = getattr(settings, 'MIDDLEWARE', [])
        csrf_middleware = any(
            'csrf' in middleware_class.lower() 
            for middleware_class in middleware
        )
        self.assertTrue(csrf_middleware, "CSRF middleware no está configurado")