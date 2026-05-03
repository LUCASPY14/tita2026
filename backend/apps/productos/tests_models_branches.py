"""
Tests de ramas faltantes en productos/models.py
Cubre branches en ProductosManager._prepare_kwargs, precio_venta property,
CategoriasManager, HistoricoPrecios.variacion_porcentual, y get_or_create.
"""

from decimal import Decimal

from django.test import TestCase

import pytest


@pytest.mark.django_db
class ProductosManagerBranchesTest(TestCase):
    """
    Branch 18->19: elif 'nombre' in kwargs (nombre + descripcion both provided).
    Branch 52->54: get_or_create WITHOUT defaults.
    """

    def test_create_with_nombre_and_descripcion_both(self):
        """Branch 18->19: 'nombre' in kwargs AND 'descripcion' also in kwargs → pop nombre."""
        from apps.productos.models import Productos

        # When both 'nombre' and 'descripcion' provided → elif branch removes 'nombre'
        p = Productos.objects.create(
            nombre="ignored_name",
            descripcion="real_description_branch_test",
        )
        self.assertEqual(p.descripcion, "real_description_branch_test")
        p.delete()

    def test_get_or_create_without_defaults(self):
        """Branch 52->54: get_or_create called WITHOUT defaults → False arm taken."""
        from apps.productos.models import Productos

        # Call without defaults → defaults=None → False arm at 'if defaults:'
        p, created = Productos.objects.get_or_create(descripcion="TestProduct_NoDefaults_Branch_XYZ")
        self.assertIsNotNone(p)
        p.delete()

    def test_precio_venta_property_with_precio(self):
        """Branch 129->130: precio_venta True arm — producto HAS a precio → returns it."""
        from django.utils import timezone as tz

        from apps.productos.models import ListasPrecios, PreciosPorLista, Productos

        p = Productos.objects.create(
            descripcion="Test_PrecioVenta_Branch",
        )
        lista, _ = ListasPrecios.objects.get_or_create(
            nombre_lista="General_precio_branch",
            defaults={"fecha_vigencia": tz.now().date(), "moneda": "PYG", "estado": True},
        )
        PreciosPorLista.objects.create(
            id_producto=p,
            id_lista=lista,
            precio_unitario=Decimal("100"),
        )

        precio = p.precio_venta
        self.assertEqual(precio, Decimal("100"))
        # Cleanup: PreciosPorLista first (FK), then Producto - handled by TestCase rollback


@pytest.mark.django_db
class CategoriasManagerBranchesTest(TestCase):
    """Branch 144->145: elif 'nombre_categoria' in kwargs (when nombre also provided)."""

    def test_create_with_nombre_categoria_and_nombre(self):
        """Branch 144->145: both nombre_categoria AND nombre → pop nombre_categoria."""
        from apps.productos.models import Categorias

        # Both provided → elif branch pops nombre_categoria, keeps nombre
        cat = Categorias.objects.create(
            nombre_categoria="ignored_cat",
            nombre="real_categoria_branch_test",
        )
        self.assertEqual(cat.nombre, "real_categoria_branch_test")
        cat.delete()


@pytest.mark.django_db
class HistoricoPreciosBranchesTest(TestCase):
    """
    Branches 319->320 and 319->321: HistoricoPrecios.variacion_porcentual.
    Branch 319->320: precio_anterior exists and > 0 → calculate percentage.
    Branch 319->321: precio_anterior is None or 0 → return Decimal('0.00').
    """

    def _make_historico(self, precio_anterior, precio_nuevo):
        """Create an unsaved HistoricoPrecios with given prices (property test only)."""
        from apps.productos.models import HistoricoPrecios, Productos

        p = Productos.objects.create(
            descripcion=f"TestHist_branch",
        )
        # Use Django init (not __new__) so _state is set properly
        hist = HistoricoPrecios(
            id_producto=p,
            precio_anterior=precio_anterior,
            precio_nuevo=precio_nuevo,
        )
        return hist, p

    def test_variacion_porcentual_with_positive_anterior(self):
        """Branch 319->320: precio_anterior > 0 → calculates percentage."""
        hist, p = self._make_historico(Decimal("100"), Decimal("120"))
        result = hist.variacion_porcentual
        self.assertEqual(result, Decimal("20"))

    def test_variacion_porcentual_with_zero_anterior(self):
        """Branch 319->321: precio_anterior == 0 → returns Decimal('0.00')."""
        hist, p = self._make_historico(Decimal("0"), Decimal("100"))
        result = hist.variacion_porcentual
        self.assertEqual(result, Decimal("0.00"))

    def test_variacion_porcentual_with_none_anterior(self):
        """Branch 319->321: precio_anterior is None → returns Decimal('0.00')."""
        hist, p = self._make_historico(None, Decimal("100"))
        result = hist.variacion_porcentual
        self.assertEqual(result, Decimal("0.00"))
