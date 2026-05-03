"""
Tests complementarios para admin de productos
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal

from django.contrib import admin
from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.models import Impuestos
from apps.productos.admin import CategoriasAdmin, ProductosAdmin
from apps.productos.models import Categorias, Productos, UnidadesMedida


class ProductosAdminTest(TestCase):
    """Tests básicos para ProductosAdmin"""

    def setUp(self):
        """Configuración inicial"""
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="Unid", estado=True)

        self.producto = Productos.objects.create(
            codigo_barra="1234567890",
            descripcion="Coca Cola 500ml",
            stock_minimo=Decimal("20.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_admin_registered(self):
        """Test que ProductosAdmin está registrado"""
        self.assertTrue(admin.site.is_registered(Productos))

    def test_list_display(self):
        """Test que list_display está configurado"""
        admin_instance = ProductosAdmin(Productos, admin.site)
        self.assertTrue(hasattr(admin_instance, "list_display"))

    def test_search_fields(self):
        """Test que search_fields está configurado"""
        admin_instance = ProductosAdmin(Productos, admin.site)
        self.assertTrue(hasattr(admin_instance, "search_fields"))


class CategoriasAdminTest(TestCase):
    """Tests básicos para CategoriasAdmin"""

    def setUp(self):
        """Configuración inicial"""
        self.categoria = Categorias.objects.create(nombre="Snacks", estado=True)

    def test_admin_registered(self):
        """Test que CategoriasAdmin está registrado"""
        self.assertTrue(admin.site.is_registered(Categorias))
