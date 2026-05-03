"""
Tests de importación de URLs para módulos sin cobertura.
Cada app tiene su urls.py que no es incluido directamente en el router
de api/v1/urls.py, pero sí debe estar cubierto por tests.
"""

from django.test import SimpleTestCase

from rest_framework.routers import DefaultRouter


class AlmuerzosUrlsImportTest(SimpleTestCase):
    """Cubre apps/almuerzos/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.almuerzos import urls as almuerzos_urls

        self.assertTrue(hasattr(almuerzos_urls, "urlpatterns"))
        self.assertIsInstance(almuerzos_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.almuerzos import urls as almuerzos_urls

        self.assertIsInstance(almuerzos_urls.router, DefaultRouter)


class ComprasUrlsImportTest(SimpleTestCase):
    """Cubre apps/compras/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.compras import urls as compras_urls

        self.assertTrue(hasattr(compras_urls, "urlpatterns"))
        self.assertIsInstance(compras_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.compras import urls as compras_urls

        self.assertIsInstance(compras_urls.router, DefaultRouter)


class NotificacionesUrlsImportTest(SimpleTestCase):
    """Cubre apps/notificaciones/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.notificaciones import urls as notificaciones_urls

        self.assertTrue(hasattr(notificaciones_urls, "urlpatterns"))
        self.assertIsInstance(notificaciones_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.notificaciones import urls as notificaciones_urls

        self.assertIsInstance(notificaciones_urls.router, DefaultRouter)


class VentasUrlsImportTest(SimpleTestCase):
    """Cubre apps/ventas/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.ventas import urls as ventas_urls

        self.assertTrue(hasattr(ventas_urls, "urlpatterns"))
        self.assertIsInstance(ventas_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.ventas import urls as ventas_urls

        self.assertIsInstance(ventas_urls.router, DefaultRouter)


class ReportesUrlsImportTest(SimpleTestCase):
    """Cubre apps/reportes/urls.py"""

    def test_import_y_urlpatterns(self):
        from apps.reportes import urls as reportes_urls

        self.assertTrue(hasattr(reportes_urls, "urlpatterns"))
        self.assertIsInstance(reportes_urls.urlpatterns, list)

    def test_router_instancia(self):
        from apps.reportes import urls as reportes_urls

        self.assertIsInstance(reportes_urls.router, DefaultRouter)
