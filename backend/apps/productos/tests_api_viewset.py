"""
Tests para ProductosViewSet - API REST endpoints
Objetivo: Aumentar cobertura de productos views
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

from django.utils import timezone

from apps.contabilidad.models import Impuestos
from apps.productos.models import (
    Categorias,
    ListasPrecios,
    PreciosPorLista,
    Productos,
    UnidadesMedida,
)
from apps.usuarios.models import Empleados, Roles


class ProductosViewSetAPITest(TestCase):
    """
    Tests para endpoints de API de Productos

    Endpoints testeados:
    - GET /api/v1/productos/ (listar productos)
    - POST /api/v1/productos/ (crear producto)
    - GET /api/v1/productos/{id}/ (detalle producto)
    - PATCH /api/v1/productos/{id}/ (actualizar producto)
    - DELETE /api/v1/productos/{id}/ (desactivar producto)
    """

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        # Crear usuario admin Django
        self.user = User.objects.create_user(username="admin_prod_test", password="testpass123", is_staff=True)

        # Crear rol admin
        self.rol_admin = Roles.objects.create(
            nombre_rol="Administrador", descripcion="Administrador del sistema", estado=True
        )

        # Crear empleado admin
        self.admin = Empleados.objects.create(
            nombre="Admin",
            apellido="Sistema",
            usuario="admin",
            email="admin@test.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol_admin,
        )

        # Autenticar
        self.client.force_authenticate(user=self.user)

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un", estado=True)

        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear lista de precios
        self.lista_precio = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

    def test_listar_productos_sin_autenticacion(self):
        """Test: Listar productos sin autenticación debe retornar 401"""
        self.client.force_authenticate(user=None)
        url = reverse("productos-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_productos_vacio(self):
        """Test: Listar productos cuando no hay registros"""
        url = reverse("productos-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_crear_producto_exitoso(self):
        """Test: Crear producto con datos válidos"""
        url = reverse("productos-list")
        data = {
            "codigo_barra": "PROD001",
            "descripcion": "Coca Cola 500ml",
            "id_categoria": self.categoria.id_categoria,
            "id_unidad_medida": self.unidad.id_unidad_medida,
            "stock_minimo": "10",
            "id_impuesto": self.impuesto_10.id_impuesto,
            "estado": True,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Productos.objects.count(), 1)

        producto = Productos.objects.first()
        self.assertEqual(producto.descripcion, "Coca Cola 500ml")
        self.assertEqual(producto.stock_minimo, Decimal("10"))

    def test_crear_producto_sin_descripcion_falla(self):
        """Test: Crear producto sin descripción debe fallar"""
        url = reverse("productos-list")
        data = {
            "codigo_barra": "PROD002",
            "id_categoria": self.categoria.id_categoria,
            "id_unidad_medida": self.unidad.id_unidad_medida,
            "id_impuesto": self.impuesto_10.id_impuesto,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtener_detalle_producto(self):
        """Test: Obtener detalle de un producto específico"""
        producto = Productos.objects.create(
            codigo_barra="PROD003",
            descripcion="Pepsi 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            stock_minimo=Decimal("5"),
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        url = reverse("productos-detail", kwargs={"pk": producto.id_producto})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["descripcion"], "Pepsi 500ml")
        self.assertEqual(Decimal(response.data["stock_minimo"]), Decimal("5"))

    def test_actualizar_producto(self):
        """Test: Actualizar datos de un producto"""
        producto = Productos.objects.create(
            codigo_barra="PROD004",
            descripcion="Fanta 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            stock_minimo=Decimal("10"),
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        url = reverse("productos-detail", kwargs={"pk": producto.id_producto})
        data = {"descripcion": "Fanta Naranja 500ml", "stock_minimo": "15"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        producto.refresh_from_db()
        self.assertEqual(producto.descripcion, "Fanta Naranja 500ml")
        self.assertEqual(producto.stock_minimo, Decimal("15"))

    def test_desactivar_producto(self):
        """Test: Desactivar un producto (soft delete)"""
        producto = Productos.objects.create(
            codigo_barra="PROD005",
            descripcion="Sprite 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        url = reverse("productos-detail", kwargs={"pk": producto.id_producto})
        data = {"estado": False}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        producto.refresh_from_db()
        self.assertFalse(producto.estado)

    def test_filtrar_productos_por_categoria(self):
        """Test: Filtrar productos por categoría"""
        categoria_snacks = Categorias.objects.create(nombre="Snacks", estado=True)

        # Producto de bebidas
        producto1 = Productos.objects.create(
            codigo_barra="BEB001",
            descripcion="Agua Mineral",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        # Producto de snacks
        producto2 = Productos.objects.create(
            codigo_barra="SNK001",
            descripcion="Papas Fritas",
            id_categoria=categoria_snacks,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        url = reverse("productos-list")
        response = self.client.get(url, {"id_categoria": self.categoria.id_categoria})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["descripcion"], "Agua Mineral")

    def test_buscar_productos_por_descripcion(self):
        """Test: Buscar productos por descripción"""
        Productos.objects.create(
            codigo_barra="P001",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        Productos.objects.create(
            codigo_barra="P002",
            descripcion="Coca Cola 1L",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        Productos.objects.create(
            codigo_barra="P003",
            descripcion="Pepsi 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        url = reverse("productos-list")
        response = self.client.get(url, {"search": "Coca"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filtrar_productos_activos(self):
        """Test: Filtrar solo productos activos"""
        Productos.objects.create(
            codigo_barra="ACT001",
            descripcion="Producto estado",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=True,
        )

        Productos.objects.create(
            codigo_barra="INACT001",
            descripcion="Producto Inactivo",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto_10,
            estado=False,
        )

        url = reverse("productos-list")
        response = self.client.get(url, {"estado": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["descripcion"], "Producto estado")


class CategoriasViewSetAPITest(TestCase):
    """Tests para endpoints de Categorías"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        # Crear usuario admin Django
        self.user = User.objects.create_user(username="admin_cat_test", password="testpass123", is_staff=True)

        # Crear empleado admin
        self.rol_admin = Roles.objects.create(nombre_rol="Administrador", estado=True)

        self.admin = Empleados.objects.create(
            nombre="Admin",
            apellido="Test",
            usuario="admin",
            email="admin@test.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol_admin,
        )

        self.client.force_authenticate(user=self.user)

    def test_crear_categoria(self):
        """Test: Crear nueva categoría"""
        url = reverse("categorias-list")
        data = {"nombre": "Bebidas Calientes", "estado": True}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Categorias.objects.count(), 1)

        categoria = Categorias.objects.first()
        self.assertEqual(categoria.nombre, "Bebidas Calientes")
        self.assertTrue(categoria.estado)

    def test_listar_categorias(self):
        """Test: Listar todas las categorías"""
        Categorias.objects.create(nombre="Bebidas", estado=True)
        Categorias.objects.create(nombre="Snacks", estado=True)
        Categorias.objects.create(nombre="Lácteos", estado=False)

        url = reverse("categorias-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_filtrar_categorias_activas(self):
        """Test: Filtrar solo categorías activas"""
        Categorias.objects.create(nombre="Activa", estado=True)
        Categorias.objects.create(nombre="Inactiva", estado=False)

        url = reverse("categorias-list")
        response = self.client.get(url, {"estado": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["nombre"], "Activa")
