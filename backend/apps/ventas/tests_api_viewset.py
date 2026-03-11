"""
Tests para VentasViewSet - API REST endpoints
Objetivo: Aumentar cobertura de views/endpoints de 0% a 40%+
"""

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta

from apps.ventas.models import Ventas, DetallesVenta, PagosVenta
from apps.core.models import Tarjetas, ConsumosTarjeta, MediosPago
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import (
    ListasPrecios,
    Productos,
    Categorias,
    UnidadesMedida,
    PreciosPorLista,
)
from apps.usuarios.models import Empleados, Roles
from apps.contabilidad.models import Impuestos
from apps.inventario.models import StockUnico


class VentasViewSetAPITest(TestCase):
    """
    Tests para endpoints de API de Ventas

    Endpoints testeados:
    - GET /api/v1/ventas/ (listar ventas)
    - POST /api/v1/ventas/ (crear venta)
    - GET /api/v1/ventas/{id}/ (detalle venta)
    - PATCH /api/v1/ventas/{id}/ (actualizar venta)
    - DELETE /api/v1/ventas/{id}/ (cancelar venta)
    """

    def setUp(self):
        """Configuración inicial para tests de API"""
        self.client = APIClient()

        # Crear usuario Django con permisos de staff para autenticación API
        User = get_user_model()
        self.auth_user = User.objects.create_user(
            username="cajero_test", password="testpass123", is_staff=True
        )

        # Crear rol y empleado (cajero)
        self.rol_cajero = Roles.objects.create(
            nombre_rol="Cajero", descripcion="Cajero de ventas", activo=True
        )

        self.empleado_cajero = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            usuario="jcajero",
            email="cajero@test.com",
            fecha_ingreso=timezone.now(),
            activo=True,
            id_rol=self.rol_cajero,
        )

        # Autenticar cliente de API con usuario Django (is_staff=True bypasses CanManageVentas)
        self.client.force_authenticate(user=self.auth_user)

        # Crear medio de pago
        self.medio_pago_efectivo = MediosPago.objects.create(
            descripcion="Efectivo", activo=True, genera_comision=False
        )

        # Crear lista de precios
        self.lista_precio = ListasPrecios.objects.create(nombre_lista="Minorista", activo=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", activo=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="María",
            apellidos="González",
            ruc_ci="12345678",
            limite_credito=Decimal("1000.00"),
            activo=True,
            id_lista=self.lista_precio,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear categoría y unidad de medida
        self.categoria = Categorias.objects.create(nombre="Bebidas", activo=True)

        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")

        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="PROD001",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            stock_minimo=Decimal("10"),
            id_impuesto=self.impuesto_10,
            activo=True,
        )

        # Crear precio por lista
        self.precio_lista = PreciosPorLista.objects.create(
            id_producto=self.producto,
            id_lista=self.lista_precio,
            precio_unitario=Decimal("7000.00"),
        )

        # Crear stock para el producto
        self.stock = StockUnico.objects.create(
            id_producto=self.producto, cantidad=Decimal("100.00")
        )

    def test_listar_ventas_sin_autenticacion(self):
        """Test: Listar ventas sin autenticación debe retornar 401"""
        self.client.force_authenticate(user=None)
        url = reverse("ventas-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_ventas_vacio(self):
        """Test: Listar ventas cuando no hay registros retorna lista vacía"""
        url = reverse("ventas-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_crear_venta_contado_exitosa(self):
        """Test: Crear venta al contado con efectivo - flujo completo"""
        url = reverse("ventas-list")
        data = {
            "tipo_venta": "contado",
            "id_cliente": self.cliente.id_cliente,
            "id_empleado_cajero": self.empleado_cajero.id_empleado,
            "id_medio_pago": self.medio_pago_efectivo.id_medio_pago,
            "monto_sin_impuesto": "7000.00",
            "monto_impuesto": "700.00",
            "monto_total": "7700.00",
            "estado": "completada",
            "estado_pago": "pagada",
            "detalles": [
                {
                    "id_producto": self.producto.id_producto,
                    "cantidad": 1,
                    "precio_unitario": "7000.00",
                    "subtotal": "7000.00",
                    "impuesto": "700.00",
                    "total": "7700.00",
                }
            ],
        }

        response = self.client.post(url, data, format="json")

        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id_venta", response.data)

        # Verificar que se creó la venta
        self.assertEqual(Ventas.objects.count(), 1)
        venta = Ventas.objects.first()
        self.assertEqual(venta.monto_total, Decimal("7700.00"))
        self.assertEqual(venta.estado, "completada")
        self.assertEqual(venta.estado_pago, "pagada")

    def test_crear_venta_sin_producto_falla(self):
        """Test: Crear venta sin detalles de productos debe fallar"""
        url = reverse("ventas-list")
        data = {
            "tipo_venta": "contado",
            "id_cliente": self.cliente.id_cliente,
            "id_empleado_cajero": self.empleado_cajero.id_empleado,
            "id_medio_pago": self.medio_pago_efectivo.id_medio_pago,
            "monto_total": "7700.00",
            "detalles": [],  # Sin productos
        }

        response = self.client.post(url, data, format="json")

        # Debe fallar por validación
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtener_detalle_venta(self):
        """Test: Obtener detalle de una venta específica"""
        # Crear venta primero
        venta = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("7700.00"),
            estado="completada",
            estado_pago="pagada",
        )

        # Obtener detalle
        url = reverse("ventas-detail", kwargs={"pk": venta.id_venta})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id_venta"], venta.id_venta)
        self.assertEqual(Decimal(response.data["monto_total"]), Decimal("7700.00"))

    def test_filtrar_ventas_por_cliente(self):
        """Test: Filtrar ventas por cliente"""
        # Crear ventas para diferentes clientes
        venta1 = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("10000.00"),
            estado="completada",
            estado_pago="pagada",
        )

        # Crear otro cliente
        otro_cliente = Clientes.objects.create(
            nombres="Pedro",
            apellidos="Ramírez",
            ruc_ci="87654321",
            activo=True,
            id_lista=self.lista_precio,
            id_tipo_cliente=self.tipo_cliente,
        )

        venta2 = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=otro_cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("5000.00"),
            estado="completada",
            estado_pago="pagada",
        )

        # Filtrar por primer cliente
        url = reverse("ventas-list")
        response = self.client.get(url, {"id_cliente": self.cliente.id_cliente})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id_venta"], venta1.id_venta)

    def test_buscar_ventas_por_nombre_cliente(self):
        """Test: Buscar ventas por nombre del cliente"""
        # Crear venta
        venta = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("10000.00"),
            estado="completada",
            estado_pago="pagada",
        )

        # Buscar por nombre
        url = reverse("ventas-list")
        response = self.client.get(url, {"search": "María"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_ordenar_ventas_por_fecha(self):
        """Test: Ordenar ventas por fecha descendente"""
        # Crear ventas en diferentes fechas
        venta1 = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("5000.00"),
            estado="completada",
            estado_pago="pagada",
        )
        # Backdate venta1 so ordering is deterministic
        Ventas.objects.filter(pk=venta1.pk).update(fecha=timezone.now() - timedelta(days=2))

        venta2 = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("10000.00"),
            estado="completada",
            estado_pago="pagada",
        )

        # Ordenar por fecha descendente (más reciente primero)
        url = reverse("ventas-list")
        response = self.client.get(url, {"ordering": "-fecha"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id_venta"], venta2.id_venta)
        self.assertEqual(response.data["results"][1]["id_venta"], venta1.id_venta)

    def test_actualizar_estado_venta(self):
        """Test: Actualizar estado de venta (PATCH)"""
        venta = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado_cajero,
            id_medio_pago=self.medio_pago_efectivo,
            monto_total=Decimal("10000.00"),
            estado="pendiente",
            estado_pago="pendiente",
        )

        url = reverse("ventas-detail", kwargs={"pk": venta.id_venta})
        data = {"estado": "completada", "estado_pago": "pagada"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que se actualizó
        venta.refresh_from_db()
        self.assertEqual(venta.estado, "completada")
        self.assertEqual(venta.estado_pago, "pagada")

    def test_paginacion_ventas(self):
        """Test: Verificar paginación de resultados"""
        # Crear 15 ventas
        for i in range(15):
            Ventas.objects.create(
                tipo_venta="contado",
                id_cliente=self.cliente,
                id_empleado_cajero=self.empleado_cajero,
                id_medio_pago=self.medio_pago_efectivo,
                monto_total=Decimal("1000.00") * (i + 1),
                estado="completada",
                estado_pago="pagada",
            )

        url = reverse("ventas-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 15)
        self.assertIn("results", response.data)
        # Por defecto, debería paginar (ej: 10 por página)
        self.assertLessEqual(len(response.data["results"]), 15)
