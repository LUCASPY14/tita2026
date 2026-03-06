"""
Tests para la app compras - Validaciones y servicios de compras
"""

from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

from apps.compras.models import Compras, DetallesCompra, Proveedores
from apps.compras.services import CompraService
from apps.productos.models import Productos, UnidadesMedida, Categorias
from apps.usuarios.models import Empleados, Roles
from apps.contabilidad.models import Impuestos


class CompraServiceValidacionTest(TestCase):
    """Tests para validaciones de CompraService"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuestos
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )
        self.impuesto_5 = Impuestos.objects.create(
            nombre_impuesto="IVA 5%",
            porcentaje=Decimal("5.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )
        self.impuesto_exenta = Impuestos.objects.create(
            nombre_impuesto="EXENTA",
            porcentaje=Decimal("0.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas")

        # Crear productos
        self.producto1 = Productos.objects.create(
            descripcion="Coca Cola 2L",
            codigo_barra="7891234567890",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

        self.producto2 = Productos.objects.create(
            descripcion="Pepsi 2L",
            codigo_barra="7891234567891",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_5,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

        self.producto3 = Productos.objects.create(
            descripcion="Sprite 2L",
            codigo_barra="7891234567892",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_exenta,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

    def test_validar_compra_correcta(self):
        """Test: Validar compra con datos correctos"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("10000.00"),
            },
            {
                "id_producto": self.producto2.id_producto,
                "cantidad": Decimal("20.000"),
                "precio_unitario": Decimal("9000.00"),
            },
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertTrue(validacion["valido"])
        self.assertEqual(len(validacion["errores"]), 0)

    def test_validar_compra_cantidad_cero(self):
        """Test: Debe detectar cantidad = 0"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("0.000"),  # ERROR
                "precio_unitario": Decimal("10000.00"),
            }
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)
        # Verificar que el error menciona cantidad
        error_msg = str(validacion["errores"][0])
        self.assertTrue("cantidad" in error_msg.lower() or "0" in error_msg)

    def test_validar_compra_cantidad_negativa(self):
        """Test: Debe detectar cantidad negativa"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("-5.000"),  # ERROR
                "precio_unitario": Decimal("10000.00"),
            }
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)

    def test_validar_compra_precio_cero(self):
        """Test: Debe detectar precio = 0"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("0.00"),  # ERROR
            }
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)

    def test_validar_compra_precio_negativo(self):
        """Test: Debe detectar precio negativo"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("-5000.00"),  # ERROR
            }
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)

    def test_validar_compra_producto_duplicado(self):
        """Test: Debe detectar productos duplicados"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("10000.00"),
            },
            {
                "id_producto": self.producto1.id_producto,  # DUPLICADO
                "cantidad": Decimal("5.000"),
                "precio_unitario": Decimal("10000.00"),
            },
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)
        # Verificar que el error menciona duplicado
        error_msg = str(validacion["errores"][0])
        self.assertTrue("duplicado" in error_msg.lower())

    def test_validar_compra_producto_inexistente(self):
        """Test: Debe detectar producto que no existe"""
        detalles = [
            {
                "id_producto": 99999,  # No existe
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("10000.00"),
            }
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        self.assertGreater(len(validacion["errores"]), 0)

    def test_validar_compra_multiple_errores(self):
        """Test: Debe detectar múltiples errores"""
        detalles = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("0.000"),  # ERROR: cantidad 0
                "precio_unitario": Decimal("10000.00"),
            },
            {
                "id_producto": self.producto2.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("-5000.00"),  # ERROR: precio negativo
            },
            {
                "id_producto": self.producto1.id_producto,  # ERROR: duplicado
                "cantidad": Decimal("5.000"),
                "precio_unitario": Decimal("10000.00"),
            },
        ]

        validacion = CompraService.validar_compra(detalles)

        self.assertFalse(validacion["valido"])
        # Debe haber al menos 3 errores
        self.assertGreaterEqual(len(validacion["errores"]), 3)


class CompraServiceCalculoTotalesTest(TestCase):
    """Tests para cálculo de totales con IVA"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuestos
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )
        self.impuesto_5 = Impuestos.objects.create(
            nombre_impuesto="IVA 5%",
            porcentaje=Decimal("5.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )
        self.impuesto_exenta = Impuestos.objects.create(
            nombre_impuesto="EXENTA",
            porcentaje=Decimal("0.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas")

        # Crear productos con diferentes IVAs
        self.producto_iva10 = Productos.objects.create(
            descripcion="Producto IVA 10%",
            codigo_barra="7891111111111",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

        self.producto_iva5 = Productos.objects.create(
            descripcion="Producto IVA 5%",
            codigo_barra="7892222222222",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_5,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

        self.producto_exenta = Productos.objects.create(
            descripcion="Producto Exenta",
            codigo_barra="7893333333333",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_exenta,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

    def test_calcular_totales_iva_10(self):
        """Test: Calcular totales con IVA 10%"""
        detalles = [
            {
                "id_producto": self.producto_iva10.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("10000.00"),
            }
        ]

        totales = CompraService.calcular_totales_compra(detalles)

        # Subtotal: 10 × 10,000 = 100,000
        self.assertEqual(totales["subtotal"], Decimal("100000.00"))

        # IVA 10%: 100,000 × 0.10 = 10,000
        self.assertEqual(totales["iva_10"], Decimal("10000.00"))
        self.assertEqual(totales["iva_5"], Decimal("0.00"))

        # Total: 100,000 + 10,000 = 110,000
        self.assertEqual(totales["total"], Decimal("110000.00"))

    def test_calcular_totales_iva_5(self):
        """Test: Calcular totales con IVA 5%"""
        detalles = [
            {
                "id_producto": self.producto_iva5.id_producto,
                "cantidad": Decimal("20.000"),
                "precio_unitario": Decimal("5000.00"),
            }
        ]

        totales = CompraService.calcular_totales_compra(detalles)

        # Subtotal: 20 × 5,000 = 100,000
        self.assertEqual(totales["subtotal"], Decimal("100000.00"))

        # IVA 5%: 100,000 × 0.05 = 5,000
        self.assertEqual(totales["iva_5"], Decimal("5000.00"))
        self.assertEqual(totales["iva_10"], Decimal("0.00"))

        # Total: 100,000 + 5,000 = 105,000
        self.assertEqual(totales["total"], Decimal("105000.00"))

    def test_calcular_totales_exenta(self):
        """Test: Calcular totales exenta (sin IVA)"""
        detalles = [
            {
                "id_producto": self.producto_exenta.id_producto,
                "cantidad": Decimal("15.000"),
                "precio_unitario": Decimal("8000.00"),
            }
        ]

        totales = CompraService.calcular_totales_compra(detalles)

        # Subtotal: 15 × 8,000 = 120,000
        self.assertEqual(totales["subtotal"], Decimal("120000.00"))

        # Sin IVA
        self.assertEqual(totales["iva_10"], Decimal("0.00"))
        self.assertEqual(totales["iva_5"], Decimal("0.00"))

        # Total = Subtotal
        self.assertEqual(totales["total"], Decimal("120000.00"))

    def test_calcular_totales_mixto(self):
        """Test: Calcular totales con productos de diferentes IVAs"""
        detalles = [
            {
                "id_producto": self.producto_iva10.id_producto,
                "cantidad": Decimal("10.000"),
                "precio_unitario": Decimal("5000.00"),
            },
            {
                "id_producto": self.producto_iva5.id_producto,
                "cantidad": Decimal("20.000"),
                "precio_unitario": Decimal("4000.00"),
            },
            {
                "id_producto": self.producto_exenta.id_producto,
                "cantidad": Decimal("5.000"),
                "precio_unitario": Decimal("3000.00"),
            },
        ]

        totales = CompraService.calcular_totales_compra(detalles)

        # Subtotales:
        # IVA 10%: 10 × 5,000 = 50,000
        # IVA 5%: 20 × 4,000 = 80,000
        # Exenta: 5 × 3,000 = 15,000
        # Total: 145,000
        self.assertEqual(totales["subtotal"], Decimal("145000.00"))

        # IVAs:
        # IVA 10%: 50,000 × 0.10 = 5,000
        # IVA 5%: 80,000 × 0.05 = 4,000
        self.assertEqual(totales["iva_10"], Decimal("5000.00"))
        self.assertEqual(totales["iva_5"], Decimal("4000.00"))

        # Total: 145,000 + 5,000 + 4,000 = 154,000
        self.assertEqual(totales["total"], Decimal("154000.00"))

    def test_calcular_totales_decimales(self):
        """Test: Calcular totales con decimales"""
        detalles = [
            {
                "id_producto": self.producto_iva10.id_producto,
                "cantidad": Decimal("12.500"),
                "precio_unitario": Decimal("3333.33"),
            }
        ]

        totales = CompraService.calcular_totales_compra(detalles)

        # Subtotal: 12.500 × 3333.33 = 41,666.625 → 41,666.62 o 41,666.63
        self.assertAlmostEqual(float(totales["subtotal"]), 41666.62, places=1)

        # IVA 10%: 41,666.63 × 0.10 = 4,166.66
        self.assertAlmostEqual(float(totales["iva_10"]), 4166.66, places=2)


class CompraServiceConfirmarCompraTest(TransactionTestCase):
    """
    Tests para confirmar compra (cambio de estado).

    Usa TransactionTestCase para probar transacciones.
    """

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear rol
        self.rol = Roles.objects.create(
            nombre_rol="Encargado Compras", descripcion="Encargado de compras"
        )

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="María",
            apellido="González",
            usuario="maria_gonzalez",
            contrasena_hash="hash789",
            fecha_ingreso=timezone.now(),
            email="maria@test.com",
            activo=True,
            id_rol=self.rol,
        )

        # Crear proveedor
        self.proveedor = Proveedores.objects.create(
            razon_social="Distribuidora ABC S.A.",
            ruc="80012345-7",
            telefono="021-555-1234",
            email="ventas@abc.com.py",
            fecha_registro=timezone.now(),
            activo=True,
        )

        # Crear unidad y categoría
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="un")

        self.categoria = Categorias.objects.create(nombre="Bebidas")

        # Crear impuesto
        self.impuesto_10 = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            activo=True,
        )

        # Crear producto
        self.producto = Productos.objects.create(
            descripcion="Coca Cola 2L",
            codigo_barra="7891234567890",
            stock_minimo=Decimal("10.000"),
            activo=True,
            id_impuesto=self.impuesto_10,
            id_unidad_medida=self.unidad,
            id_categoria=self.categoria,
        )

        # Crear compra pendiente
        self.compra = Compras.objects.create(
            id_proveedor=self.proveedor,
            fecha=timezone.now(),
            nro_factura="001-001-0001234",
            estado_pago="Pendiente",
            monto_total=Decimal("110000.00"),
            saldo_pendiente=Decimal("110000.00"),
        )

        # Crear detalle
        self.detalle = DetallesCompra.objects.create(
            id_compra=self.compra,
            id_producto=self.producto,
            cantidad=Decimal("10.000"),
            costo_unitario=Decimal("10000.00"),
            subtotal=Decimal("100000.00"),
            monto_iva=Decimal("10000.00"),
        )

    def test_confirmar_compra_exitosa(self):
        """Test: Confirmar compra cambia estado a Confirmado"""
        # Estado inicial
        self.assertEqual(self.compra.estado_pago, "Pendiente")

        # Confirmar compra
        resultado = CompraService.confirmar_compra(
            id_compra=self.compra.id_compra, empleado=self.empleado
        )

        self.assertTrue(resultado["exito"])

        # Verificar estado
        self.compra.refresh_from_db()
        self.assertEqual(self.compra.estado_pago, "Confirmado")

    def test_confirmar_compra_ya_confirmada(self):
        """Test: No puede confirmar compra ya confirmada"""
        # Confirmar compra
        self.compra.estado_pago = "Confirmado"
        self.compra.save()

        # Intentar confirmar de nuevo
        resultado = CompraService.confirmar_compra(
            id_compra=self.compra.id_compra, empleado=self.empleado
        )

        self.assertFalse(resultado["exito"])
        self.assertIn("error", resultado)

    def test_confirmar_compra_cancelada(self):
        """Test: No puede confirmar compra cancelada"""
        # Cancelar compra
        self.compra.estado_pago = "Cancelado"
        self.compra.save()

        # Intentar confirmar
        resultado = CompraService.confirmar_compra(
            id_compra=self.compra.id_compra, empleado=self.empleado
        )

        self.assertFalse(resultado["exito"])
        self.assertIn("error", resultado)
