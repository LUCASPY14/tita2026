"""
Tests finales para alcanzar 100% cobertura en productos.models
Cubre líneas: 17, 19, 53, 136, 148, 283, 319
"""

from decimal import Decimal

from django.test import TestCase

from .models import Categorias, HistoricoPrecios, ListasPrecios, PreciosPorLista, Productos


class ProductosManagerTest(TestCase):
    """Tests para ProductosManager - cubrir líneas 17, 19, 53"""

    def test_create_con_nombre_sin_descripcion(self):
        """
        Cubrir línea 17: cuando 'nombre' existe pero 'descripcion' no existe,
        se asigna nombre a descripcion con pop
        """
        # Act: crear producto con 'nombre' legacy pero sin 'descripcion'
        producto = Productos.objects.create(
            nombre="Producto Test Legacy",  # campo legacy
            codigo_barra="1234567890",
            stock_minimo=Decimal("10.000"),
            estado=True,
        )

        # Assert: descripcion debe tener el valor de nombre
        self.assertEqual(producto.descripcion, "Producto Test Legacy")

    def test_create_con_nombre_y_descripcion(self):
        """
        Cubrir línea 19: cuando ambos 'nombre' y 'descripcion' existen,
        se elimina 'nombre' (elif branch)
        """
        # Act: crear producto con ambos campos
        producto = Productos.objects.create(
            nombre="Nombre Ignorado",  # este se elimina
            descripcion="Descripcion Real",  # este prevalece
            codigo_barra="9876543210",
            stock_minimo=Decimal("5.000"),
            estado=True,
        )

        # Assert: debe usar descripcion, no nombre
        self.assertEqual(producto.descripcion, "Descripcion Real")

    def test_get_or_create_con_defaults(self):
        """
        Cubrir línea 53: get_or_create con defaults actualiza create_kwargs
        """
        # Arrange: buscar producto que no existe
        codigo = "NEW_PRODUCT_123"

        # Act: get_or_create con defaults
        producto, created = Productos.objects.get_or_create(
            codigo_barra=codigo,
            defaults={"descripcion": "Producto con Defaults", "stock_minimo": Decimal("15.000"), "estado": True},
        )

        # Assert: debe haberse creado con los defaults
        self.assertTrue(created)
        self.assertEqual(producto.descripcion, "Producto con Defaults")
        self.assertEqual(producto.stock_minimo, Decimal("15.000"))


class ProductoPrecioVentaTest(TestCase):
    """Tests para property precio_venta - cubrir línea 136"""

    def test_precio_venta_sin_precios_retorna_cero(self):
        """
        Cubrir línea 136: cuando producto no tiene precios,
        precio_venta retorna Decimal('0.00')
        """
        # Arrange: crear producto sin precios asociados
        producto = Productos.objects.create(
            codigo_barra="NO_PRICE_PROD",
            descripcion="Producto Sin Precios",
            stock_minimo=Decimal("10.000"),
            estado=True,
        )

        # Act: acceder a precio_venta property
        precio = producto.precio_venta

        # Assert: debe retornar Decimal('0.00')
        self.assertEqual(precio, Decimal("0.00"))


class CategoriasManagerTest(TestCase):
    """Tests para CategoriasManager - cubrir línea 148"""

    def test_create_con_nombre_categoria_sin_nombre(self):
        """
        Cubrir línea 148: cuando 'nombre_categoria' existe pero 'nombre' no,
        se asigna nombre_categoria a nombre con pop
        """
        # Act: crear categoría con campo legacy 'nombre_categoria'
        categoria = Categorias.objects.create(nombre_categoria="Categoria Legacy", estado=True)

        # Assert: nombre debe tener el valor de nombre_categoria
        self.assertEqual(categoria.nombre, "Categoria Legacy")


class PreciosPorListaStrTest(TestCase):
    """Tests para __str__ de PreciosPorLista - cubrir línea 283"""

    def test_str_precios_por_lista(self):
        """Cubrir línea 283: __str__ de PreciosPorLista"""
        # Arrange: crear producto, lista y precio
        producto = Productos.objects.create(
            codigo_barra="PROD_STR_TEST",
            descripcion="Producto para __str__",
            stock_minimo=Decimal("10.000"),
            estado=True,
        )

        lista = ListasPrecios.objects.create(nombre_lista="Lista Mayorista", moneda="PYG", estado=True)

        precio = PreciosPorLista.objects.create(
            id_producto=producto, id_lista=lista, precio_unitario=Decimal("5000.00")
        )

        # Act: obtener string representation
        str_repr = str(precio)

        # Assert: debe contener formato esperado
        self.assertIn("PROD_STR_TEST", str_repr)
        self.assertIn("Lista Mayorista", str_repr)
        self.assertIn("5000", str_repr)


class HistoricoPreciosStrTest(TestCase):
    """Tests para __str__ de HistoricoPrecios - cubrir línea 319"""

    def test_str_historico_precios(self):
        """Cubrir línea 319: __str__ de HistoricoPrecios"""
        # Arrange: crear producto para historico
        producto = Productos.objects.create(
            codigo_barra="HIST_PROD", descripcion="Producto Historico", stock_minimo=Decimal("5.000"), estado=True
        )

        historico = HistoricoPrecios.objects.create(
            id_producto=producto, precio_anterior=Decimal("10000.00"), precio_nuevo=Decimal("12000.00")
        )

        # Act: obtener string representation
        str_repr = str(historico)

        # Assert: debe contener precios anterior y nuevo con flecha
        self.assertIn("10000", str_repr)
        self.assertIn("12000", str_repr)
        self.assertIn("→", str_repr)
