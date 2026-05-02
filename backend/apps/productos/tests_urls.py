"""
Tests para URLs de productos
"""

from django.test import SimpleTestCase
from rest_framework.routers import DefaultRouter


class ProductosUrlsImportTest(SimpleTestCase):
    """Cubre apps/productos/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.productos import urls as productos_urls

        self.assertTrue(hasattr(productos_urls, "urlpatterns"))
        self.assertIsInstance(productos_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.productos import urls as productos_urls

        self.assertIsInstance(productos_urls.router, DefaultRouter)

    def test_viewsets_registrados(self):
        from apps.productos import urls as productos_urls
        from apps.productos.views import ProductosViewSet, CategoriasViewSet

        # Verificar que los ViewSets están registrados en el router
        registry_names = [prefix for prefix, _, _ in productos_urls.router.registry]
        self.assertIn("productos", registry_names)
        self.assertIn("categorias", registry_names)
