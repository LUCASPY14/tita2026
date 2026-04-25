"""
Tests for remaining missing lines in apps/ventas/views.py to reach 100% coverage.

Target missing lines:
- 156-194: _crear_pagos_mixtos validation errors
- 245-257: cliente genérico creation when no id_cliente/id_hijo
- 345-383: stock validation with multiple products (ValidationError path)
- 513: pagos_data path (pago múltiple)
- 564: id_medio_pago path (pago simple)
- 630-631, 658: Productos.DoesNotExist in create_detalles
- 677-678: ValueError/TypeError in nro_preimpreso
- 704-707: Exception in emitir_factura
- 733, 737, 741: cuenta_corriente filter branches
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from apps.clientes.models import Clientes, TiposCliente, Hijos
from apps.core.models import MediosPago, Tarjetas
from apps.contabilidad.models import Impuestos
from apps.inventario.models import StockUnico
from apps.productos.models import (
    Productos, Categorias, UnidadesMedida, PreciosPorLista, ListasPrecios
)
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import Ventas, DetallesVenta, PagosVenta
from apps.ventas.views import VentasViewSet


class CrearPagosMixtosValidationTest(TestCase):
    """Test _crear_pagos_mixtos validation errors (lines 156-194)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Setup data
        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente = Clientes.objects.create(
            ruc_ci="123456", nombres="Test", apellidos="Cliente",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.medio_pago = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, estado=True
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%", porcentaje=Decimal("10"), vigente_desde="2026-01-01", estado=True
        )
        self.categoria = Categorias.objects.create(nombre_categoria="Test")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="Un")
        self.producto = Productos.objects.create(
            codigo_barra="PROD001", descripcion="Producto Test",
            id_categoria=self.categoria, id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto, estado=True
        )
        PreciosPorLista.objects.create(
            id_producto=self.producto, id_lista=self.lista,
            precio_unitario=Decimal("1000.00")
        )
        StockUnico.objects.create(id_producto=self.producto, cantidad=100)

    def test_pagos_mixtos_suma_no_coincide_con_total(self):
        """Lines 156-194: ValidationError when sum of pagos != monto_total."""
        # Create venta instance
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("5000.00"),
            iva_10=Decimal("500.00"),
            estado="Activa",
            estado_pago="Pendiente"
        )
        DetallesVenta.objects.create(
            id_venta=venta, id_producto=self.producto,
            cantidad=5, precio_unitario=Decimal("1000.00"),
            subtotal=Decimal("5000.00")
        )

        # Create viewset instance
        viewset = VentasViewSet()
        viewset.request = Mock()

        # Pagos that don't sum to total
        pagos_data = [
            {"id_medio_pago": self.medio_pago.id_medio_pago, "monto": "3000.00"},
            {"id_medio_pago": self.medio_pago.id_medio_pago, "monto": "1000.00"}
            # Sum = 4000, but venta.monto_total = 5000
        ]

        with self.assertRaises(ValidationError) as ctx:
            viewset._registrar_pagos_multiples(venta, pagos_data)

        error_dict = ctx.exception.detail
        self.assertIn("error", error_dict)
        self.assertIn("suma de pagos no coincide", str(error_dict["error"]))

    def test_pagos_mixtos_medio_pago_no_existe(self):
        """Lines 156-194: ValidationError when MediosPago.DoesNotExist."""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("1000.00"),
            iva_10=Decimal("100.00"),
            estado="Activa",
            estado_pago="Pendiente"
        )

        viewset = VentasViewSet()
        viewset.request = Mock()

        # Invalid medio_pago ID
        pagos_data = [
            {"id_medio_pago": 99999, "monto": "1000.00"}
        ]

        with self.assertRaises(ValidationError) as ctx:
            viewset._registrar_pagos_multiples(venta, pagos_data)

        error_dict = ctx.exception.detail
        self.assertIn("error", error_dict)
        self.assertIn("Medio de pago no encontrado", str(error_dict["error"]))


class ClienteGenericoCreationTest(TestCase):
    """Test cliente genérico creation when no id_cliente/id_hijo (lines 245-257)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=Decimal("10"), vigente_desde="2026-01-01", estado=True
        )
        self.categoria = Categorias.objects.create(nombre_categoria="Test")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="Un")
        
        # Create lista 'General' beforehand to test get_or_create
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        
        self.producto = Productos.objects.create(
            codigo_barra="PROD001", descripcion="Test",
            id_categoria=self.categoria, id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto, estado=True
        )
        PreciosPorLista.objects.create(
            id_producto=self.producto, id_lista=self.lista,
            precio_unitario=Decimal("1000.00")
        )
        StockUnico.objects.create(id_producto=self.producto, cantidad=100)

    def test_create_venta_sin_cliente_crea_cliente_generico(self):
        """Lines 245-257: Creates cliente genérico when no id_cliente provided."""
        url = reverse("ventas-list")
        data = {
            # NO id_cliente, NO id_hijo
            "detalles": [
                {"id_producto": self.producto.id_producto, "cantidad": 1, "precio_unitario": "1000.00"}
            ]
        }

        response = self.client.post(url, data, format="json")

        # Should create successfully with cliente genérico
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        venta = Ventas.objects.get(id_venta=response.data["id_venta"])
        
        # Verify cliente genérico was used
        self.assertEqual(venta.id_cliente.ruc_ci, "0000000")
        self.assertEqual(venta.id_cliente.nombres, "Cliente")
        self.assertEqual(venta.id_cliente.apellidos, "Genérico")


class StockInsuficienteMultipleProductosTest(TestCase):
    """Test stock validation with multiple products (lines 345-383)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente = Clientes.objects.create(
            ruc_ci="123", nombres="Test", apellidos="Cliente",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=Decimal("10"), vigente_desde="2026-01-01", estado=True
        )
        self.categoria = Categorias.objects.create(nombre_categoria="Test")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="Un")

        # Product with insufficient stock
        self.producto = Productos.objects.create(
            codigo_barra="PROD001", descripcion="Producto Test",
            id_categoria=self.categoria, id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto, estado=True
        )
        PreciosPorLista.objects.create(
            id_producto=self.producto, id_lista=self.lista,
            precio_unitario=Decimal("100.00")
        )
        StockUnico.objects.create(id_producto=self.producto, cantidad=5)  # Only 5 in stock

    @patch("apps.inventario.services.StockService.validar_disponibilidad_multiple")
    def test_stock_insuficiente_multiple_productos_raises_validation_error(self, mock_validar):
        """Lines 345-383: Raises ValidationError when stock insufficient for multiple products."""
        # Mock stock validation to return insufficient stock
        mock_validar.return_value = {
            "todo_disponible": False,
            "productos_faltantes": [
                {
                    "producto": {
                        "descripcion": "Producto Test",
                        "codigo_barra": "PROD001"
                    },
                    "stock_actual": 5,
                    "faltante": 5
                }
            ]
        }

        url = reverse("ventas-list")
        data = {
            "id_cliente": self.cliente.id_cliente,
            "detalles": [
                {"id_producto": self.producto.id_producto, "cantidad": 10, "precio_unitario": "100.00"}
            ]
        }

        response = self.client.post(url, data, format="json")

        # Should return 400 with validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Stock insuficiente", str(response.data["error"]))
        self.assertIn("productos_faltantes", response.data)


class PagoMultipleSimplePathTest(TestCase):
    """Test pago múltiple vs simple paths (lines 513, 564)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente = Clientes.objects.create(
            ruc_ci="123", nombres="Test", apellidos="Cliente",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.medio_efectivo = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, estado=True
        )
        self.medio_tarjeta = MediosPago.objects.create(
            descripcion="Tarjeta", genera_comision=True, estado=True
        )
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=Decimal("10"), vigente_desde="2026-01-01", estado=True
        )
        self.categoria = Categorias.objects.create(nombre_categoria="Test")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="Un")
        self.producto = Productos.objects.create(
            codigo_barra="PROD001", descripcion="Test",
            id_categoria=self.categoria, id_unidad_medida=self.unidad,
            id_impuesto=self.impuesto, estado=True
        )
        PreciosPorLista.objects.create(
            id_producto=self.producto, id_lista=self.lista,
            precio_unitario=Decimal("1000.00")
        )
        StockUnico.objects.create(id_producto=self.producto, cantidad=100)

    @patch("apps.ventas.views.VentasViewSet._registrar_pagos_multiples")
    def test_pago_multiple_path_with_pagos_data(self, mock_registrar_multiples):
        """Line 513: Uses pagos_data path for pago múltiple."""
        url = reverse("ventas-list")
        data = {
            "id_cliente": self.cliente.id_cliente,
            "detalles": [
                {"id_producto": self.producto.id_producto, "cantidad": 2, "precio_unitario": "1000.00"}
            ],
            "pagos_data": [
                {"id_medio_pago": self.medio_efectivo.id_medio_pago, "monto": "1000.00"},
                {"id_medio_pago": self.medio_tarjeta.id_medio_pago, "monto": "1000.00"}
            ]
        }

        response = self.client.post(url, data, format="json")

        # Verify it used the pagos_data path
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_registrar_multiples.assert_called_once()

    @patch("apps.ventas.views.VentasViewSet._registrar_pago_con_comision")
    def test_pago_simple_path_with_id_medio_pago(self, mock_registrar_simple):
        """Line 564: Uses id_medio_pago path for pago simple."""
        url = reverse("ventas-list")
        data = {
            "id_cliente": self.cliente.id_cliente,
            "id_medio_pago": self.medio_efectivo.id_medio_pago,
            "detalles": [
                {"id_producto": self.producto.id_producto, "cantidad": 1, "precio_unitario": "1000.00"}
            ]
        }

        response = self.client.post(url, data, format="json")

        # Verify it used the simple pago path
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_registrar_simple.assert_called_once()


class CreateDetallesProductoNotFoundTest(TestCase):
    """Test Productos.DoesNotExist in create_detalles (lines 630-631, 658)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test")
        
        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente = Clientes.objects.create(
            ruc_ci="123", nombres="Test", apellidos="Cliente",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )

    def test_create_detalles_producto_no_existe_raises_validation_error(self):
        """Lines 630-631, 658: Raises ValidationError when producto doesn't exist."""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("1000.00"),
            iva_10=Decimal("100.00"),
            estado="Activa"
        )

        viewset = VentasViewSet()
        viewset.request = Mock()

        # Detalle with non-existent producto
        detalles = [
            {"id_producto": 99999, "cantidad": 1, "precio_unitario": "1000.00"}
        ]

        with self.assertRaises(ValidationError) as ctx:
            viewset._crear_detalles_venta(venta, detalles)

        self.assertIn("error", ctx.exception.detail)
        self.assertIn("Producto 99999 no encontrado", str(ctx.exception.detail["error"]))


class EmitirFacturaErrorHandlingTest(TestCase):
    """Test emitir_factura error handling (lines 677-678, 704-707)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente = Clientes.objects.create(
            ruc_ci="123456", nombres="Test", apellidos="Cliente",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.venta = Ventas.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("1000.00"),
            iva_10=Decimal("100.00"),
            estado="Activa",
            estado_pago="Pagada",
            genera_factura_legal=True
        )

    def test_emitir_factura_nro_preimpreso_invalid_type(self):
        """Lines 677-678: Returns 400 when nro_preimpreso is invalid type."""
        url = reverse("ventas-emitir-factura", kwargs={"pk": self.venta.id_venta})
        data = {
            "nro_preimpreso": "invalid_number"  # String that can't be converted to int
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("número entero", str(response.data["error"]))

    @patch("apps.contabilidad.facturacion_service.FacturacionService.emitir")
    def test_emitir_factura_general_exception(self, mock_emitir):
        """Lines 704-707: Returns 500 on general Exception."""
        mock_emitir.side_effect = Exception("Database connection failed")

        url = reverse("ventas-emitir-factura", kwargs={"pk": self.venta.id_venta})
        data = {"nro_preimpreso": 123}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertIn("Error al emitir factura", str(response.data["error"]))


class CuentaCorrienteFiltersTest(TestCase):
    """Test cuenta_corriente action filters (lines 733, 737, 741)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.rol = Roles.objects.create(nombre_rol="Admin", estado=True)
        self.empleado = Empleados.objects.create(
            usuario="test", nombre="Test", apellido="User", id_rol=self.rol, estado=True,
            contrasena_hash="hash", fecha_ingreso="2026-01-01"
        )
        self.lista = ListasPrecios.objects.create(nombre_lista="General")
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="General")
        self.cliente1 = Clientes.objects.create(
            ruc_ci="111", nombres="Cliente", apellidos="Uno",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.cliente2 = Clientes.objects.create(
            ruc_ci="222", nombres="Cliente", apellidos="Dos",
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.medio = MediosPago.objects.create(
            descripcion="Efectivo", estado=True
        )

        # Ventas for filtering
        self.venta1 = Ventas.objects.create(
            id_cliente=self.cliente1,
            monto_total=Decimal("1000"), iva_10=Decimal("100"),
            estado="Activa", estado_pago="Pagada", id_medio_pago=self.medio,
            genera_factura_legal=True
        )
        self.venta2 = Ventas.objects.create(
            id_cliente=self.cliente2,
            monto_total=Decimal("2000"), iva_10=Decimal("200"),
            estado="Activa", estado_pago="Pagada", id_medio_pago=self.medio,
            genera_factura_legal=True
        )
        self.venta3 = Ventas.objects.create(
            id_cliente=self.cliente1,
            monto_total=Decimal("500"), iva_10=Decimal("50"),
            estado="Activa", estado_pago="Pagada", id_medio_pago=self.medio,
            genera_factura_legal=True
        )

    def test_cuenta_corriente_filter_by_id_cliente(self):
        """Line 733: Filters by id_cliente."""
        url = reverse("ventas-sin-facturar")
        response = self.client.get(url, {"id_cliente": self.cliente1.id_cliente})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return ventas for cliente1
        ventas_returned = [v["id_venta"] for v in response.data["results"]]
        self.assertIn(self.venta1.id_venta, ventas_returned)
        self.assertNotIn(self.venta2.id_venta, ventas_returned)

    def test_cuenta_corriente_filter_by_fecha_desde(self):
        """Line 737: Filters by fecha_desde."""
        url = reverse("ventas-sin-facturar")
        response = self.client.get(url, {"fecha_desde": "2026-04-15"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ventas_returned = [v["id_venta"] for v in response.data["results"]]
        # Should include venta2 and venta3, exclude venta1
        self.assertIn(self.venta2.id_venta, ventas_returned)
        self.assertIn(self.venta3.id_venta, ventas_returned)
        self.assertNotIn(self.venta1.id_venta, ventas_returned)

    def test_cuenta_corriente_filter_by_fecha_hasta(self):
        """Line 741: Filters by fecha_hasta."""
        url = reverse("ventas-sin-facturar")
        response = self.client.get(url, {"fecha_hasta": "2026-04-30"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ventas_returned = [v["id_venta"] for v in response.data["results"]]
        # Should include venta1 and venta2, exclude venta3
        self.assertIn(self.venta1.id_venta, ventas_returned)
        self.assertIn(self.venta2.id_venta, ventas_returned)
        self.assertNotIn(self.venta3.id_venta, ventas_returned)
