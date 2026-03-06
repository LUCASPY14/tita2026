"""
Tests para el módulo productos
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.productos.models import (
    Productos,
    Categorias,
    UnidadesMedida,
    ListasPrecios,
    PreciosPorLista,
)
from apps.contabilidad.models import Impuestos


class CategoriasTest(TestCase):
    """Tests para el modelo Categorias"""

    def setUp(self):
        """Configuración inicial para tests de categorías"""
        self.categoria_padre = Categorias.objects.create(nombre="Bebidas", activo=True)

        self.categoria_hija = Categorias.objects.create(
            nombre="Gaseosas", activo=True, id_categoria_padre=self.categoria_padre
        )

    def test_crear_categoria_raiz(self):
        """Test: Crear categoría de nivel superior (sin padre)"""
        categoria = Categorias.objects.create(nombre="Snacks", activo=True)

        self.assertIsNotNone(categoria.id_categoria)
        self.assertEqual(categoria.nombre, "Snacks")
        self.assertTrue(categoria.activo)
        self.assertIsNone(categoria.id_categoria_padre)
        self.assertTrue(categoria.es_categoria_raiz)

    def test_crear_subcategoria(self):
        """Test: Crear subcategoría (con padre)"""
        self.assertIsNotNone(self.categoria_hija.id_categoria)
        self.assertEqual(self.categoria_hija.nombre, "Gaseosas")
        self.assertEqual(self.categoria_hija.id_categoria_padre, self.categoria_padre)
        self.assertFalse(self.categoria_hija.es_categoria_raiz)

    def test_str_categoria_raiz(self):
        """Test: __str__ de categoría raíz muestra solo nombre"""
        self.assertEqual(str(self.categoria_padre), "Bebidas")

    def test_str_subcategoria(self):
        """Test: __str__ de subcategoría muestra jerarquía"""
        self.assertEqual(str(self.categoria_hija), "Bebidas > Gaseosas")

    def test_relacion_subcategorias(self):
        """Test: Acceso a subcategorías desde categoría padre"""
        subcategorias = self.categoria_padre.subcategorias.all()
        self.assertEqual(subcategorias.count(), 1)
        self.assertIn(self.categoria_hija, subcategorias)


class UnidadesMedidaTest(TestCase):
    """Tests para el modelo UnidadesMedida"""

    def test_crear_unidad_medida(self):
        """Test: Crear unidad de medida correctamente"""
        unidad = UnidadesMedida.objects.create(nombre="Kilogramo", abreviatura="Kg", activo=True)

        self.assertIsNotNone(unidad.id_unidad_medida)
        self.assertEqual(unidad.nombre, "Kilogramo")
        self.assertEqual(unidad.abreviatura, "Kg")
        self.assertTrue(unidad.activo)

    def test_multiples_unidades(self):
        """Test: Crear múltiples unidades de medida"""
        unidades = [
            UnidadesMedida.objects.create(nombre="Litro", abreviatura="L", activo=True),
            UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", activo=True),
            UnidadesMedida.objects.create(nombre="Gramo", abreviatura="g", activo=True),
        ]

        self.assertEqual(UnidadesMedida.objects.count(), 3)
        self.assertEqual(len(unidades), 3)


class ProductosTest(TestCase):
    """Tests para el modelo Productos"""

    def setUp(self):
        """Configuración inicial para tests de productos"""
        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", activo=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", activo=True)

    def test_crear_producto_completo(self):
        """Test: Crear producto con todos los campos"""
        producto = Productos.objects.create(
            codigo_barra="7890123456789",
            descripcion="Coca Cola 500ml",
            stock_minimo=Decimal("10.000"),
            permite_stock_negativo=False,
            activo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.assertIsNotNone(producto.id_producto)
        self.assertEqual(producto.codigo_barra, "7890123456789")
        self.assertEqual(producto.descripcion, "Coca Cola 500ml")
        self.assertEqual(producto.stock_minimo, Decimal("10.000"))
        self.assertFalse(producto.permite_stock_negativo)
        self.assertTrue(producto.activo)
        self.assertEqual(producto.id_categoria, self.categoria)
        self.assertEqual(producto.id_impuesto, self.impuesto)
        self.assertEqual(producto.id_unidad_medida, self.unidad)

    def test_crear_producto_sin_codigo_barra(self):
        """Test: Producto sin código de barras (opcional)"""
        producto = Productos.objects.create(
            descripcion="Empanada Casera",
            stock_minimo=Decimal("5.000"),
            activo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.assertIsNone(producto.codigo_barra)
        self.assertEqual(producto.descripcion, "Empanada Casera")

    def test_str_producto_con_codigo(self):
        """Test: __str__ con código de barras"""
        producto = Productos.objects.create(
            codigo_barra="123456",
            descripcion="Test",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.assertEqual(str(producto), "123456 - Test")

    def test_str_producto_sin_codigo(self):
        """Test: __str__ sin código de barras muestra S/C"""
        producto = Productos.objects.create(
            descripcion="Test",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.assertEqual(str(producto), "S/C - Test")

    def test_producto_permite_stock_negativo(self):
        """Test: Producto con stock negativo permitido"""
        producto = Productos.objects.create(
            descripcion="Producto Premium",
            stock_minimo=Decimal("0"),
            permite_stock_negativo=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.assertTrue(producto.permite_stock_negativo)

    def test_relacion_productos_categoria(self):
        """Test: Acceso a productos desde categoría"""
        producto1 = Productos.objects.create(
            descripcion="Producto 1",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        producto2 = Productos.objects.create(
            descripcion="Producto 2",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        productos = self.categoria.productos.all()
        self.assertEqual(productos.count(), 2)
        self.assertIn(producto1, productos)
        self.assertIn(producto2, productos)


class ListasPreciosTest(TestCase):
    """Tests para el modelo ListasPrecios"""

    def test_crear_lista_precio(self):
        """Test: Crear lista de precios"""
        lista = ListasPrecios.objects.create(
            nombre_lista="Minorista",
            fecha_vigencia=timezone.now().date(),
            moneda="PYG",
            activo=True,
        )

        self.assertIsNotNone(lista.id_lista)
        self.assertEqual(lista.nombre_lista, "Minorista")
        self.assertEqual(lista.moneda, "PYG")
        self.assertTrue(lista.activo)

    def test_multiples_listas_precios(self):
        """Test: Crear múltiples listas de precios"""
        lista_minorista = ListasPrecios.objects.create(
            nombre_lista="Minorista", moneda="PYG", activo=True
        )

        lista_mayorista = ListasPrecios.objects.create(
            nombre_lista="Mayorista", moneda="PYG", activo=True
        )

        self.assertEqual(ListasPrecios.objects.count(), 2)
        self.assertNotEqual(lista_minorista.nombre_lista, lista_mayorista.nombre_lista)

    def test_str_lista_precios(self):
        """Test: __str__ muestra nombre y moneda"""
        lista = ListasPrecios.objects.create(nombre_lista="Estudiantes", moneda="USD", activo=True)

        self.assertEqual(str(lista), "Estudiantes (USD)")


class PreciosPorListaTest(TestCase):
    """Tests para el modelo PreciosPorLista"""

    def setUp(self):
        """Configuración inicial"""
        # Impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Categoría y unidad
        self.categoria = Categorias.objects.create(nombre="Bebidas", activo=True)
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", activo=True)

        # Producto
        self.producto = Productos.objects.create(
            descripcion="Coca Cola",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Listas de precios
        self.lista_minorista = ListasPrecios.objects.create(
            nombre_lista="Minorista", moneda="PYG", activo=True
        )

        self.lista_mayorista = ListasPrecios.objects.create(
            nombre_lista="Mayorista", moneda="PYG", activo=True
        )

    def test_crear_precio_producto(self):
        """Test: Asignar precio a producto en lista"""
        precio = PreciosPorLista.objects.create(
            precio_unitario=Decimal("5000.00"),
            id_lista=self.lista_minorista,
            id_producto=self.producto,
        )

        self.assertIsNotNone(precio.id_precio)
        self.assertEqual(precio.precio_unitario, Decimal("5000.00"))
        self.assertEqual(precio.id_lista, self.lista_minorista)
        self.assertEqual(precio.id_producto, self.producto)

    def test_producto_multiples_precios(self):
        """Test: Producto con diferentes precios según lista"""
        precio_minorista = PreciosPorLista.objects.create(
            precio_unitario=Decimal("5000.00"),
            id_lista=self.lista_minorista,
            id_producto=self.producto,
        )

        precio_mayorista = PreciosPorLista.objects.create(
            precio_unitario=Decimal("4500.00"),
            id_lista=self.lista_mayorista,
            id_producto=self.producto,
        )

        # Verificar precios diferentes
        self.assertGreater(precio_minorista.precio_unitario, precio_mayorista.precio_unitario)

        # Acceder desde producto
        precios = self.producto.precios.all()
        self.assertEqual(precios.count(), 2)

    def test_unique_together_producto_lista(self):
        """Test: No puede haber dos precios para misma combinación producto-lista"""
        PreciosPorLista.objects.create(
            precio_unitario=Decimal("5000.00"),
            id_lista=self.lista_minorista,
            id_producto=self.producto,
        )

        # Intentar crear duplicado
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            PreciosPorLista.objects.create(
                precio_unitario=Decimal("6000.00"),
                id_lista=self.lista_minorista,
                id_producto=self.producto,
            )

    def test_acceso_precios_desde_lista(self):
        """Test: Acceder a precios desde lista"""
        precio1 = PreciosPorLista.objects.create(
            precio_unitario=Decimal("5000.00"),
            id_lista=self.lista_minorista,
            id_producto=self.producto,
        )

        # Crear otro producto
        producto2 = Productos.objects.create(
            descripcion="Pepsi",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        precio2 = PreciosPorLista.objects.create(
            precio_unitario=Decimal("4500.00"), id_lista=self.lista_minorista, id_producto=producto2
        )

        # Acceder desde lista
        precios = self.lista_minorista.precios.all()
        self.assertEqual(precios.count(), 2)
        self.assertIn(precio1, precios)
        self.assertIn(precio2, precios)
