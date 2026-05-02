"""
Tests para módulo de inventario
Valida reglas de negocio, concurrencia y consistencia ACID
"""

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from threading import Thread
import time

from apps.inventario.models import StockUnico, MovimientosStock, AlertasStock, CostosHistoricos
from apps.inventario.services import StockService
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.compras.models import Proveedores, Compras, DetallesCompra
from apps.ventas.models import Ventas, DetallesVenta
from apps.core.models import MediosPago
from apps.contabilidad.models import Impuestos
from apps.usuarios.models import Empleados, Roles
from apps.clientes.models import Clientes, TiposCliente
from apps.productos.models import ListasPrecios


class StockUnicoTest(TestCase):
    """Tests para modelo StockUnico"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", estado=True)

        # Impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Producto
        self.producto = Productos.objects.create(
            descripcion="Coca Cola 2L",
            stock_minimo=Decimal("50.000"),
            permite_stock_negativo=False,
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

    def test_crear_stock_inicial(self):
        """Crear stock con cantidad inicial"""
        stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

        self.assertEqual(stock.cantidad, Decimal("100.000"))
        self.assertEqual(stock.id_producto, self.producto)

    def test_stock_negativo_no_permitido(self):
        """No permitir stock negativo si producto no lo permite"""
        stock = StockUnico(cantidad=Decimal("-10.000"), id_producto=self.producto)

        with self.assertRaises(ValidationError):
            stock.clean()

    def test_stock_negativo_permitido(self):
        """Permitir stock negativo si producto lo permite"""
        self.producto.permite_stock_negativo = True
        self.producto.save()

        stock = StockUnico.objects.create(cantidad=Decimal("-5.000"), id_producto=self.producto)

        self.assertEqual(stock.cantidad, Decimal("-5.000"))

    def test_requiere_reposicion(self):
        """Verificar si producto requiere reposición"""
        stock = StockUnico.objects.create(
            cantidad=Decimal("30.000"), id_producto=self.producto  # Menor que stock_minimo (50)
        )

        self.assertTrue(stock.requiere_reposicion)

        stock.cantidad = Decimal("60.000")
        stock.save()

        self.assertFalse(stock.requiere_reposicion)

    def test_costo_promedio_ponderado(self):
        """Calcular costo promedio ponderado"""
        stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

        # Crear costos históricos
        CostosHistoricos.objects.create(
            costo_unitario=Decimal("5000.00"),
            cantidad_comprada=Decimal("50.000"),
            fecha_compra=timezone.now(),
            id_producto=self.producto,
        )

        CostosHistoricos.objects.create(
            costo_unitario=Decimal("5500.00"),
            cantidad_comprada=Decimal("50.000"),
            fecha_compra=timezone.now(),
            id_producto=self.producto,
        )

        # Costo promedio = (5000*50 + 5500*50) / (50+50) = 5250
        costo_promedio = stock.costo_promedio_ponderado
        self.assertEqual(costo_promedio, Decimal("5250.00"))


class MovimientosStockTest(TestCase):
    """Tests para MovimientosStock"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.categoria = Categorias.objects.create(nombre="Bebidas")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN")
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=10, vigente_desde=timezone.now().date()
        )

        self.producto = Productos.objects.create(
            descripcion="Producto Test",
            stock_minimo=10,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.rol = Roles.objects.create(nombre_rol="Admin")
        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Pérez",
            usuario="jperez",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

    def test_crear_movimiento_ingreso(self):
        """Crear movimiento de tipo Ingreso"""
        movimiento = MovimientosStock.objects.create(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("100.000"),
            stock_resultante=Decimal("100.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )

        self.assertEqual(movimiento.tipo_movimiento, "Ingreso")
        self.assertEqual(movimiento.motivo, "compra")

    def test_cantidad_negativa_no_permitida(self):
        """No permitir cantidad negativa en movimientos"""
        movimiento = MovimientosStock(
            tipo_movimiento="Ingreso",
            motivo="compra",
            cantidad=Decimal("-10.000"),
            stock_resultante=Decimal("90.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )

        with self.assertRaises(ValidationError):
            movimiento.clean()

    def test_motivo_coherente_con_tipo(self):
        """Validar coherencia entre tipo_movimiento y motivo"""
        # Motivo 'compra' es para Ingreso, no para Egreso
        movimiento = MovimientosStock(
            tipo_movimiento="Egreso",
            motivo="compra",  # ❌ Incoherente
            cantidad=Decimal("10.000"),
            stock_resultante=Decimal("90.000"),
            id_empleado_autoriza=self.empleado,
            id_producto=self.producto,
        )

        with self.assertRaises(ValidationError):
            movimiento.clean()


class StockServiceTest(TestCase):
    """Tests para StockService"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.categoria = Categorias.objects.create(nombre="Bebidas")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN")
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=10, vigente_desde=timezone.now().date()
        )

        self.producto = Productos.objects.create(
            descripcion="Coca Cola",
            stock_minimo=50,
            permite_stock_negativo=False,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

    def test_validar_disponibilidad_suficiente(self):
        """Validar que hay stock disponible"""
        resultado = StockService.validar_disponibilidad(self.producto.id_producto, Decimal("50.000"))

        self.assertTrue(resultado["disponible"])
        self.assertEqual(resultado["stock_actual"], Decimal("100.000"))
        self.assertEqual(resultado["faltante"], Decimal("0.000"))

    def test_validar_disponibilidad_insuficiente(self):
        """Validar que no hay stock suficiente"""
        resultado = StockService.validar_disponibilidad(self.producto.id_producto, Decimal("150.000"))

        self.assertFalse(resultado["disponible"])
        self.assertEqual(resultado["faltante"], Decimal("50.000"))

    def test_validar_disponibilidad_permite_negativo(self):
        """Producto con permite_stock_negativo siempre disponible"""
        self.producto.permite_stock_negativo = True
        self.producto.save()

        resultado = StockService.validar_disponibilidad(
            self.producto.id_producto, Decimal("200.000")  # Más que el stock actual
        )

        self.assertTrue(resultado["disponible"])
        self.assertTrue(resultado["permite_negativo"])

    def test_validar_multiple_productos(self):
        """Validar disponibilidad de múltiples productos"""
        # Crear segundo producto
        producto2 = Productos.objects.create(
            descripcion="Pepsi",
            stock_minimo=50,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        StockUnico.objects.create(cantidad=Decimal("20.000"), id_producto=producto2)

        items = [
            {"id_producto": self.producto.id_producto, "cantidad": Decimal("50.000")},
            {
                "id_producto": producto2.id_producto,
                "cantidad": Decimal("30.000"),
            },  # No hay suficiente
        ]

        resultado = StockService.validar_disponibilidad_multiple(items)

        self.assertFalse(resultado["todo_disponible"])
        self.assertEqual(len(resultado["productos_faltantes"]), 1)

    def test_productos_bajo_stock(self):
        """Obtener productos que requieren reposición"""
        # Stock actual (100) > stock_minimo (50) → No requiere
        productos_bajos = StockService.obtener_productos_bajo_stock()
        self.assertEqual(len(productos_bajos), 0)

        # Reducir stock por debajo del mínimo
        self.stock.cantidad = Decimal("30.000")
        self.stock.save()

        productos_bajos = StockService.obtener_productos_bajo_stock()
        self.assertEqual(len(productos_bajos), 1)
        self.assertTrue(productos_bajos[0]["faltante"] > 0)


class ConcurrenciaStockTest(TransactionTestCase):
    """
    Tests de concurrencia para validar select_for_update().

    IMPORTANTE: Usa TransactionTestCase para soportar threading
    """

    def setUp(self):
        """Configurar datos de prueba"""
        self.categoria = Categorias.objects.create(nombre="Bebidas")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN")
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=10, vigente_desde=timezone.now().date()
        )

        self.producto = Productos.objects.create(
            descripcion="Último Jugo",
            stock_minimo=10,
            permite_stock_negativo=False,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Stock inicial: solo 1 unidad
        self.stock = StockUnico.objects.create(cantidad=Decimal("1.000"), id_producto=self.producto)

        self.rol = Roles.objects.create(nombre_rol="Cajero")
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="test",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

    def test_concurrencia_reserva_stock(self):
        """
        Simular 5 cajeros intentando vender el último producto simultáneamente.

        Solo UNO debe tener éxito, los otros 4 deben fallar.
        """
        resultados = {"exitos": 0, "fallos": 0}

        def intentar_venta():
            try:
                StockService.reservar_stock(self.producto.id_producto, Decimal("1.000"), self.empleado, "venta")
                resultados["exitos"] += 1
            except ValidationError:
                resultados["fallos"] += 1

        # Crear 5 threads (5 cajeros)
        threads = []
        for i in range(5):
            t = Thread(target=intentar_venta)
            threads.append(t)
            t.start()

        # Esperar a que terminen
        for t in threads:
            t.join()

        # Solo 1 debe tener éxito
        self.assertEqual(resultados["exitos"], 1)
        self.assertEqual(resultados["fallos"], 4)

        # Stock final debe ser 0
        stock_final = StockUnico.objects.get(id_producto=self.producto)
        self.assertEqual(stock_final.cantidad, Decimal("0.000"))


class AlertasStockTest(TestCase):
    """Tests para sistema de alertas"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.categoria = Categorias.objects.create(nombre="Bebidas")
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN")
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=10, vigente_desde=timezone.now().date()
        )

        self.producto = Productos.objects.create(
            descripcion="Producto Test",
            stock_minimo=Decimal("50.000"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.stock = StockUnico.objects.create(cantidad=Decimal("100.000"), id_producto=self.producto)

    def test_generar_alerta_stock_minimo(self):
        """Generar alerta cuando stock pasa por debajo del mínimo"""
        from apps.inventario.signals import _generar_alerta_stock_bajo

        # Stock por debajo del mínimo
        _generar_alerta_stock_bajo(self.producto, Decimal("30.000"))

        alerta = AlertasStock.objects.filter(id_producto=self.producto, activa=True).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.tipo_alerta, "stock_minimo")

    def test_no_duplicar_alertas(self):
        """No crear alertas duplicadas mientras una esté activa"""
        from apps.inventario.signals import _generar_alerta_stock_bajo

        # Primera alerta
        _generar_alerta_stock_bajo(self.producto, Decimal("30.000"))

        # Intentar crear otra
        _generar_alerta_stock_bajo(self.producto, Decimal("25.000"))

        # Debe haber solo 1 activa
        alertas_activas = AlertasStock.objects.filter(id_producto=self.producto, activa=True).count()

        self.assertEqual(alertas_activas, 1)

    def test_resolver_alerta(self):
        """Resolver alerta cuando stock vuelve arriba del mínimo"""
        from apps.inventario.signals import _generar_alerta_stock_bajo, _resolver_alertas_stock

        # Generar alerta
        _generar_alerta_stock_bajo(self.producto, Decimal("30.000"))

        # Resolver (stock vuelve arriba del mínimo)
        _resolver_alertas_stock(self.producto, Decimal("60.000"))

        alertas_activas = AlertasStock.objects.filter(id_producto=self.producto, activa=True).count()

        self.assertEqual(alertas_activas, 0)
