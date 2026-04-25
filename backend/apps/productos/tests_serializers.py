"""
Tests para Serializers de Productos
Objetivo: Aumentar cobertura de serializers
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch

from apps.productos.models import (
    Productos,
    Categorias,
    UnidadesMedida,
    ListasPrecios,
    PreciosPorLista,
)
from apps.productos.serializers import (
    ProductosSerializer,
    CategoriasSerializer,
    PreciosPorListaSerializer,
)
from apps.contabilidad.models import Impuestos


class ProductosSerializerTest(TestCase):
    """Tests para ProductosSerializer"""

    def setUp(self):
        """Configuración inicial"""
        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Crear unidad
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un", estado=True)

        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

    def test_serializar_producto_completo(self):
        """Test: Serializar un producto con todos sus campos"""
        producto = Productos.objects.create(
            codigo_barra="77890123",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("10"),
            estado=True,
        )

        serializer = ProductosSerializer(producto)
        data = serializer.data

        self.assertEqual(data["codigo_barra"], "77890123")
        self.assertEqual(data["descripcion"], "Coca Cola 500ml")
        self.assertEqual(Decimal(data["stock_minimo"]), Decimal("10"))
        self.assertTrue(data["estado"])

    def test_validar_producto_valido(self):
        """Test: Validar datos válidos para crear producto"""
        data = {
            "codigo_barra": "123456789",
            "descripcion": "Pepsi 500ml",
            "id_categoria": self.categoria.id_categoria,
            "id_unidad_medida": self.unidad.id_unidad_medida,
            "id_impuesto": self.impuesto.id_impuesto,
            "stock_minimo": "5",
            "estado": True,
        }

        serializer = ProductosSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_producto_sin_descripcion_invalido(self):
        """Test: Producto sin descripción debe ser inválido"""
        data = {
            "codigo_barra": "987654321",
            "id_categoria": self.categoria.id_categoria,
            "id_unidad_medida": self.unidad.id_unidad_medida,
            "id_impuesto": self.impuesto.id_impuesto,
            "estado": True,
        }

        serializer = ProductosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("descripcion", serializer.errors)

    def test_actualizar_producto_parcialmente(self):
        """Test: Actualización parcial de producto"""
        producto = Productos.objects.create(
            codigo_barra="PART001",
            descripcion="Producto Original",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("5"),
            estado=True,
        )

        # Actualizar solo la descripción
        data = {"descripcion": "Producto Modificado"}
        serializer = ProductosSerializer(producto, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        producto.refresh_from_db()
        self.assertEqual(producto.descripcion, "Producto Modificado")
        self.assertEqual(producto.codigo_barra, "PART001")  # No cambió

    def test_crear_producto_sin_impuesto_asigna_default(self):
        """Test: Crear producto sin impuesto asigna IVA 10% por defecto"""
        data = {
            "codigo_barra": "NOIMP001",
            "descripcion": "Producto sin impuesto",
            "id_categoria": self.categoria.id_categoria,
            "id_unidad_medida": self.unidad.id_unidad_medida,
            "stock_minimo": "5",
            "estado": True,
        }

        serializer = ProductosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        producto = serializer.save()
        self.assertIsNotNone(producto.id_impuesto)
        self.assertEqual(producto.id_impuesto.nombre_impuesto, "IVA 10%")
        self.assertEqual(producto.id_impuesto.porcentaje, Decimal("10.00"))

    def test_get_categoria_nombre_con_excepcion(self):
        """Test: get_categoria_nombre maneja excepciones retornando None"""
        producto = Productos.objects.create(
            codigo_barra="EXC001",
            descripcion="Producto test",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("5"),
            estado=True,
        )
        
        serializer = ProductosSerializer(producto)
        
        # Patchear acceso a nombre para provocar excepción
        with patch.object(type(producto.id_categoria), 'nombre', property(lambda self: (_ for _ in ()).throw(Exception("Error")))):
            result = serializer.get_categoria_nombre(producto)
            self.assertIsNone(result)

    def test_get_impuesto_nombre_con_excepcion(self):
        """Test: get_impuesto_nombre maneja excepciones retornando None"""
        producto = Productos.objects.create(
            codigo_barra="EXCIMP001",
            descripcion="Producto test impuesto",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("5"),
            estado=True,
        )
        
        serializer = ProductosSerializer(producto)
        
        # Patchear acceso a nombre_impuesto para provocar excepción
        with patch.object(type(producto.id_impuesto), 'nombre_impuesto', property(lambda self: (_ for _ in ()).throw(Exception("Error")))):
            result = serializer.get_impuesto_nombre(producto)
            self.assertIsNone(result)

    def test_get_precio_con_excepcion(self):
        """Test: get_precio maneja excepciones retornando None"""
        producto = Productos.objects.create(
            codigo_barra="EXCPRE001",
            descripcion="Producto test precio",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            stock_minimo=Decimal("5"),
            estado=True,
        )
        
        serializer = ProductosSerializer(producto)
        
        # Patchear el manager precios para provocar excepción
        with patch.object(type(producto), 'precios', property(lambda self: (_ for _ in ()).throw(Exception("Error")))):
            result = serializer.get_precio(producto)
            self.assertIsNone(result)


class CategoriasSerializerTest(TestCase):
    """Tests para CategoriasSerializer"""

    def test_serializar_categoria_raiz(self):
        """Test: Serializar categoría sin padre"""
        categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        serializer = CategoriasSerializer(categoria)
        data = serializer.data

        self.assertEqual(data["nombre"], "Bebidas")
        self.assertTrue(data["estado"])
        self.assertIsNone(data.get("id_categoria_padre"))

    def test_serializar_subcategoria(self):
        """Test: Serializar categoría con padre"""
        padre = Categorias.objects.create(nombre="Bebidas", estado=True)
        hija = Categorias.objects.create(nombre="Gaseosas", id_categoria_padre=padre, estado=True)

        serializer = CategoriasSerializer(hija)
        data = serializer.data

        self.assertEqual(data["nombre"], "Gaseosas")
        self.assertIsNotNone(data.get("id_categoria_padre"))

    def test_crear_categoria_desde_serializer(self):
        """Test: Crear nueva categoría usando serializer"""
        data = {"nombre": "Snacks", "estado": True}

        serializer = CategoriasSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        categoria = serializer.save()
        self.assertEqual(categoria.nombre, "Snacks")
        self.assertTrue(categoria.estado)
        self.assertEqual(Categorias.objects.count(), 1)


class PreciosPorListaSerializerTest(TestCase):
    """Tests para PreciosPorListaSerializer"""

    def setUp(self):
        """Configuración inicial"""
        # Crear categoría, unidad, impuesto
        categoria = Categorias.objects.create(nombre="Bebidas", estado=True)
        unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un", estado=True)
        impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="PROD001",
            descripcion="Coca Cola 500ml",
            id_categoria=categoria,
            id_unidad_medida=unidad,
            id_impuesto=impuesto,
            estado=True,
        )

        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

    def test_serializar_precio_producto(self):
        """Test: Serializar precio de producto en lista"""
        precio = PreciosPorLista.objects.create(
            id_producto=self.producto, id_lista=self.lista, precio_unitario=Decimal("7000.00")
        )

        serializer = PreciosPorListaSerializer(precio)
        data = serializer.data

        self.assertEqual(Decimal(data["precio_unitario"]), Decimal("7000.00"))
        self.assertIsNotNone(data.get("id_producto"))
        self.assertIsNotNone(data.get("id_lista"))

    def test_crear_precio_producto(self):
        """Test: Crear precio desde serializer"""
        data = {
            "id_producto": self.producto.id_producto,
            "id_lista": self.lista.id_lista,
            "precio_unitario": "8500.00",
        }

        serializer = PreciosPorListaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        precio = serializer.save()
        self.assertEqual(precio.precio_unitario, Decimal("8500.00"))
        self.assertEqual(precio.id_producto, self.producto)
        self.assertEqual(precio.id_lista, self.lista)
