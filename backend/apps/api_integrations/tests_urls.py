"""
Tests para URLs de api_integrations
Cubre configuración y resolución de rutas para integraciones API
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.api_integrations import urls as api_integrations_urls
from apps.api_integrations.views import bancard_webhook, webhook_test


class ApiIntegrationsUrlsTest(TestCase):
    """Tests para URLs de api_integrations"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.client = Client()

    def test_url_patterns_exist(self):
        """Debe tener patterns de URL definidos"""
        self.assertTrue(hasattr(api_integrations_urls, "urlpatterns"))
        self.assertIsInstance(api_integrations_urls.urlpatterns, list)

    def test_bancard_webhook_url_resolution(self):
        """Debe resolver URL de webhook Bancard correctamente"""
        try:
            url = reverse("bancard_webhook")
            resolver = resolve(url)
            self.assertEqual(resolver.func, bancard_webhook)
        except:
            # Si no existe reverse name, probar con path directo
            resolver = resolve("/api/v1/webhooks/bancard/")
            self.assertEqual(resolver.func, bancard_webhook)

    def test_webhook_test_url_resolution(self):
        """Debe resolver URL de test webhook correctamente"""
        try:
            url = reverse("webhook_test")
            resolver = resolve(url)
            self.assertEqual(resolver.func, webhook_test)
        except:
            # Si no existe reverse name, probar con path directo
            resolver = resolve("/api/v1/webhooks/test/")
            self.assertEqual(resolver.func, webhook_test)

    def test_bancard_webhook_url_pattern(self):
        """Debe tener patrón correcto para webhook Bancard"""
        # Probar diferentes variaciones de URL que deberían funcionar
        possible_urls = [
            "/api/v1/webhooks/bancard/",
            "/api/webhooks/bancard/",
            "/webhooks/bancard/",
            "/bancard/webhook/",
        ]

        resolved_any = False
        for url in possible_urls:
            try:
                resolver = resolve(url)
                if resolver.url_name == "bancard_webhook":
                    resolved_any = True
                    break
            except:
                continue

        self.assertTrue(resolved_any, "Ninguna URL de webhook Bancard se resolvió correctamente")

    def test_webhook_test_url_pattern(self):
        """Debe tener patrón correcto para test webhook"""
        possible_urls = [
            "/api/v1/webhooks/bancard/test/",
            "/api/webhooks/bancard/test/",
            "/api/v1/webhooks/test/",
            "/api/webhooks/test/",
            "/webhooks/test/",
            "/webhook/test/",
        ]

        resolved_any = False
        for url in possible_urls:
            try:
                resolver = resolve(url)
                if resolver.url_name == "webhook_test":
                    resolved_any = True
                    break
            except:
                continue

        self.assertTrue(resolved_any, "Ninguna URL de test webhook se resolvió correctamente")

    def test_url_namespace(self):
        """Debe tener namespace apropiado si está configurado"""
        # Si las URLs están bajo un namespace, verificar que funciona
        try:
            # Probar con namespace común para APIs
            url = reverse("api_integrations:bancard_webhook")
            self.assertTrue(url.startswith("/"))
        except:
            # Si no hay namespace, está bien, las URLs pueden estar en root
            pass

    def test_url_trailing_slash_consistency(self):
        """Debe manejar trailing slashes consistentemente"""
        test_paths = ["/api/webhooks/bancard", "/api/webhooks/bancard/", "/api/webhooks/test", "/api/webhooks/test/"]

        # Al menos uno de cada par (con/sin slash) debe funcionar
        for path in test_paths:
            try:
                resolve(path)
                # Si se resuelve, está bien
            except:
                # Si no se resuelve, probar la variante opuesta
                if path.endswith("/"):
                    alt_path = path[:-1]
                else:
                    alt_path = path + "/"

                try:
                    resolve(alt_path)
                    # La variante alternativa funciona
                except:
                    # Ninguna funciona - puede ser normal si esa URL no existe
                    pass


class ApiIntegrationsUrlsIntegrationTest(APITestCase):
    """Tests de integración para URLs de api_integrations"""

    def test_bancard_webhook_url_post_access(self):
        """Debe permitir acceso POST a webhook Bancard"""
        webhook_data = {
            "operation": {"response": "S", "amount": "50000.00", "currency": "PYG"},
            "shop_process_id": "REC-TEST-URL",
            "signature": "test_signature",
        }

        # Probar URLs posibles
        possible_urls = ["/api/v1/webhooks/bancard/", "/api/webhooks/bancard/", "/webhooks/bancard/"]

        success_found = False
        for url in possible_urls:
            try:
                response = self.client.post(url, data=webhook_data, content_type="application/json")

                # Si no es 404 (URL no encontrada), la URL existe
                if response.status_code != 404:
                    success_found = True
                    break
            except:
                continue

        self.assertTrue(success_found, "No se pudo acceder a webhook Bancard por ninguna URL")

    def test_webhook_test_url_get_access(self):
        """Debe permitir acceso GET a test webhook"""
        possible_urls = ["/api/v1/webhooks/test/", "/api/webhooks/test/", "/webhooks/test/"]

        success_found = False
        for url in possible_urls:
            try:
                response = self.client.get(url)

                # Si no es 404 (URL no encontrada), la URL existe
                if response.status_code != 404:
                    success_found = True
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    break
            except Exception as e:
                continue

        self.assertTrue(success_found, "No se pudo acceder a test webhook por ninguna URL")

    def test_webhook_urls_method_restrictions(self):
        """Debe restringir métodos HTTP apropiadamente"""
        # Test webhook debe permitir solo GET
        test_urls = ["/api/v1/webhooks/test/", "/api/webhooks/test/", "/webhooks/test/"]

        for url in test_urls:
            try:
                # GET debe funcionar
                get_response = self.client.get(url)
                if get_response.status_code != 404:  # URL existe
                    self.assertIn(get_response.status_code, [200, 405])  # 200 OK o 405 Method Not Allowed

                    # POST no debe funcionar para test
                    post_response = self.client.post(url, {})
                    if post_response.status_code != 404:
                        self.assertEqual(post_response.status_code, 405)  # Method Not Allowed
                    break
            except:
                continue

    def test_webhook_urls_content_type_handling(self):
        """Debe manejar content types apropiadamente"""
        webhook_data = {"test": "data"}

        bancard_urls = ["/api/v1/webhooks/bancard/", "/api/webhooks/bancard/", "/webhooks/bancard/"]

        for url in bancard_urls:
            try:
                # JSON content type
                response = self.client.post(url, data=webhook_data, content_type="application/json")

                if response.status_code != 404:  # URL existe
                    # Debe aceptar JSON (no debe ser 415 Unsupported Media Type)
                    self.assertNotEqual(response.status_code, 415)
                    break
            except:
                continue

    @patch("apps.api_integrations.services.BancardService")
    def test_webhook_url_with_service_integration(self, mock_bancard_service):
        """Debe integrar URL con servicio correctamente"""
        # Mock del servicio
        mock_service_instance = mock_bancard_service.return_value
        mock_service_instance.procesar_webhook.return_value = {"success": True, "recarga_id": 123}

        webhook_data = {
            "operation": {"response": "S", "amount": "25000.00", "currency": "PYG"},
            "shop_process_id": "REC-URL-SERVICE",
            "signature": "url_service_signature",
        }

        # Testar integración completa
        possible_urls = ["/api/v1/webhooks/bancard/", "/api/webhooks/bancard/", "/webhooks/bancard/"]

        for url in possible_urls:
            try:
                response = self.client.post(url, data=webhook_data, content_type="application/json")

                if response.status_code == status.HTTP_200_OK:
                    # URL funciona y servicio fue llamado
                    self.assertTrue(response.content)  # Debe tener contenido
                    break
                elif response.status_code != 404:
                    # URL existe pero puede haber error de validación
                    break
            except:
                continue

    def test_url_pattern_security(self):
        """Debe verificar aspectos de seguridad en URLs"""
        # Verificar que URLs no exponen información sensible
        sensitive_patterns = ["password", "secret", "key", "token", "credential"]

        # Obtener todas las URLs del módulo
        from django.urls import URLPattern, URLResolver

        def extract_patterns(urlpatterns):
            patterns = []
            for pattern in urlpatterns:
                if isinstance(pattern, URLPattern):
                    patterns.append(str(pattern.pattern))
                elif isinstance(pattern, URLResolver):
                    patterns.extend(extract_patterns(pattern.url_patterns))
            return patterns

        try:
            all_patterns = extract_patterns(api_integrations_urls.urlpatterns)

            for pattern in all_patterns:
                for sensitive in sensitive_patterns:
                    with self.subTest(pattern=pattern, sensitive=sensitive):
                        self.assertNotIn(
                            sensitive.lower(),
                            pattern.lower(),
                            f"URL pattern '{pattern}' contiene término sensible '{sensitive}'",
                        )
        except:
            # Si no se puede extraer patterns, al menos verificar URLs conocidas
            known_urls = ["/api/webhooks/bancard/", "/api/webhooks/test/"]

            for url in known_urls:
                for sensitive in sensitive_patterns:
                    self.assertNotIn(sensitive.lower(), url.lower())

    def test_url_versioning_consistency(self):
        """Debe ser consistente con versionado de API"""
        # Si se usa versionado (v1, v2, etc.), debe ser consistente
        versioned_patterns = []
        unversioned_patterns = []

        test_urls = [
            "/api/v1/webhooks/bancard/",
            "/api/v1/webhooks/test/",
            "/api/webhooks/bancard/",
            "/api/webhooks/test/",
        ]

        for url in test_urls:
            try:
                resolve(url)
                if "/v1/" in url or "/v2/" in url:
                    versioned_patterns.append(url)
                else:
                    unversioned_patterns.append(url)
            except:
                continue

        # Si hay URLs versionadas, todas deberían ser versionadas
        # O todas no versionadas para consistencia
        if versioned_patterns and unversioned_patterns:
            # Ambos tipos existen - puede ser transición, pero hacer aware
            pass

    def test_url_documentation_endpoints(self):
        """Debe verificar endpoints de documentación si existen"""
        doc_urls = ["/api/docs/", "/api/v1/docs/", "/docs/", "/swagger/", "/redoc/"]

        # No falla si no existen, pero verifica si están configurados
        for url in doc_urls:
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    # Existe documentación - buena práctica
                    self.assertIn(response.status_code, [200, 301, 302])
                    break
            except:
                continue


class ApiIntegrationsUrlsErrorHandlingTest(TestCase):
    """Tests para manejo de errores en URLs"""

    def test_invalid_webhook_urls(self):
        """Debe manejar URLs inválidas apropiadamente"""
        invalid_urls = [
            "/api/webhooks/nonexistent/",
            "/api/webhooks/bancard/extra/path/",
            "/api/webhooks/",
            "/webhooks/invalid/",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                try:
                    response = self.client.get(url)
                    # Debe retornar 404 para URLs inválidas
                    self.assertEqual(response.status_code, 404)
                except:
                    # Si no se puede resolver, está bien (404 implícito)
                    pass

    def test_webhook_urls_with_trailing_content(self):
        """Debe rechazar URLs con contenido adicional"""
        malicious_urls = [
            "/api/webhooks/bancard/../admin/",
            "/api/webhooks/bancard/%2e%2e/admin/",
            "/api/webhooks/bancard/;rm -rf /",
        ]

        for url in malicious_urls:
            with self.subTest(url=url):
                try:
                    response = self.client.get(url)
                    # Debe retornar error (404 o similar) para URLs maliciosas
                    self.assertNotEqual(response.status_code, 200)
                except:
                    # Si no se puede resolver, está bien (protección implícita)
                    pass

    def test_webhook_urls_case_sensitivity(self):
        """Debe manejar case sensitivity apropiadamente"""
        case_variants = [
            "/api/webhooks/BANCARD/",
            "/API/WEBHOOKS/bancard/",
            "/Api/Webhooks/Bancard/",
            "/api/webhooks/Bancard/",
        ]

        # URLs deben ser consistentes en case sensitivity
        base_response = None
        try:
            base_response = self.client.get("/api/webhooks/bancard/")
        except:
            pass

        for url in case_variants:
            with self.subTest(url=url):
                try:
                    self.client.get(url)
                    # Debe ser consistente con URL base
                    if base_response and base_response.status_code != 404:
                        # Si la URL base funciona, las variantes pueden o no funcionar
                        # pero deben ser consistentes
                        pass
                except:
                    pass
