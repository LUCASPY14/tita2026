"""
Tests para Serializers de Ventas
Objetivo: Aumentar cobertura de serializers de 0% a 40%+
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal

from apps.ventas.models import Ventas, DetallesVenta
from apps.ventas.serializers import VentasSerializer, DetallesVentaSerializer
from apps.core.models import MediosPago
from apps.clientes.models import Clientes, TiposCliente
from apps.productos.models import ListasPrecios, Productos, Categorias, UnidadesMedida
from apps.usuarios.models import Empleados, Roles
from apps.contabilidad.models import Impuestos


class VentasSerializerTest(TestCase):
    """Tests para VentasSerializer"""

    def setUp(self):
        """Configuración inicial"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            usuario="jcajero",
            email="cajero@test.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(descripcion="Efectivo", estado=True)

        # Crear tipo de cliente y lista de precios
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        self.lista_precio = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="María",
            apellidos="González",
            ruc_ci="12345678",
            estado=True,
            id_lista=self.lista_precio,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_serializar_venta_completa(self):
        """Test: Serializar una venta con todos sus campos"""
        venta = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
            fecha=timezone.now(),
            monto_total=Decimal("10000.00"),
            estado="completada",
            estado_pago="pagada",
        )

        serializer = VentasSerializer(venta)
        data = serializer.data

        self.assertEqual(data["tipo_venta"], "contado")
        self.assertEqual(Decimal(data["monto_total"]), Decimal("10000.00"))
        self.assertEqual(data["estado"], "completada")
        self.assertEqual(data["estado_pago"], "pagada")

    def test_validar_datos_venta_validos(self):
        """Test: Validar datos válidos para crear venta"""
        data = {
            "tipo_venta": "contado",
            "id_cliente": self.cliente.id_cliente,
            "id_empleado_cajero": self.empleado.id_empleado,
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "monto_total": "5000.00",
            "estado": "completada",
            "estado_pago": "pagada",
        }

        serializer = VentasSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_validar_venta_sin_cliente_invalida(self):
        """Test: Venta sin cliente debe ser inválida"""
        data = {
            "tipo_venta": "contado",
            "id_empleado_cajero": self.empleado.id_empleado,
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "monto_total": "5000.00",
        }

        serializer = VentasSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_validar_monto_negativo_invalido(self):
        """Test: Monto negativo debe ser inválido"""
        data = {
            "tipo_venta": "contado",
            "id_cliente": self.cliente.id_cliente,
            "id_empleado_cajero": self.empleado.id_empleado,
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "monto_total": "-100.00",
            "estado": "completada",
        }

        serializer = VentasSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class DetallesVentaSerializerTest(TestCase):
    """Tests para DetallesVentaSerializer"""

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

        # Crear producto
        self.producto = Productos.objects.create(
            codigo_barra="PROD001",
            descripcion="Coca Cola 500ml",
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto,
            estado=True,
        )

        # Crear venta
        rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        empleado = Empleados.objects.create(
            nombre="Cajero",
            apellido="Test",
            usuario="cajero",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=rol,
        )

        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        lista_precio = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        cliente = Clientes.objects.create(
            nombres="Cliente",
            apellidos="Test",
            ruc_ci="123",
            estado=True,
            id_lista=lista_precio,
            id_tipo_cliente=tipo_cliente,
        )

        medio_pago = MediosPago.objects.create(descripcion="Efectivo", estado=True)

        self.venta = Ventas.objects.create(
            tipo_venta="contado",
            id_cliente=cliente,
            id_empleado_cajero=empleado,
            id_medio_pago=medio_pago,
            fecha=timezone.now(),
            monto_total=Decimal("7700.00"),
            estado="completada",
        )

    def test_serializar_detalle_venta(self):
        """Test: Serializar un detalle de venta"""
        # Crear stock para el producto primero
        from apps.inventario.models import StockUnico

        StockUnico.objects.create(id_producto=self.producto, cantidad=Decimal("100"))

        detalle = DetallesVenta.objects.create(
            id_venta=self.venta,
            id_producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal("7000.00"),
            subtotal=Decimal("14000.00"),
        )

        serializer = DetallesVentaSerializer(detalle)
        data = serializer.data

        self.assertEqual(Decimal(data["cantidad"]), Decimal("2"))
        self.assertEqual(Decimal(data["precio_unitario"]), Decimal("7000.00"))
        self.assertEqual(Decimal(data["subtotal"]), Decimal("14000.00"))

    def test_validar_detalle_sin_producto_invalido(self):
        """Test: Detalle sin producto debe ser inválido"""
        data = {
            "id_venta": self.venta.id_venta,
            "cantidad": 1,
            "precio_unitario": "7000.00",
            "subtotal": "7000.00",
        }

        serializer = DetallesVentaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
