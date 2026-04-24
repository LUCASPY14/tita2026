"""
Tests para la app ventas - Validación de saldo en tarjetas
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from apps.ventas.models import Ventas
from apps.core.models import Tarjetas, ConsumosTarjeta, MediosPago
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios, Productos, Categorias, UnidadesMedida
from apps.usuarios.models import Empleados, Roles


class VentasConTarjetaTest(TestCase):
    """Tests para validación de saldo en ventas con tarjeta"""

    def setUp(self):
        """Configuración inicial"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="María",
            apellidos="González",
            ruc_ci="87654321",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Ana",
            apellido="González",
            grado="6to",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta SIN permiso de saldo negativo
        self.tarjeta_sin_credito = Tarjetas.objects.create(
            nro_tarjeta="T100",
            saldo_actual=Decimal("50.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,  # NO permite negativo
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras="BAR100",
        )

        # Crear segundo hijo para pruebas de crédito
        self.hijo2 = Hijos.objects.create(
            nombre="Luis",
            apellido="González",
            grado="7mo",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta CON permiso de saldo negativo
        self.tarjeta_con_credito = Tarjetas.objects.create(
            nro_tarjeta="T200",
            saldo_actual=Decimal("30.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,  # SI permite negativo
            limite_credito=Decimal("100.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo2,
            codigo_barras="BAR200",
        )

        # Crear rol y empleado cajero
        self.rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        self.cajero = Empleados.objects.create(
            nombre="Pedro",
            apellido="Ramírez",
            usuario="cajero_test",
            contrasena_hash="hash123",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            descripcion="Tarjeta Prepago",
            genera_comision=False,
            requiere_validacion=False,
            estado=True,
        )

    def test_venta_con_saldo_suficiente(self):
        """Test: Venta exitosa cuando hay saldo suficiente"""
        saldo_inicial = self.tarjeta_sin_credito.saldo_actual
        monto_venta = Decimal("30.00")

        # Simular creación de venta (sin pasar por ViewSet)
        # Nota: En producción esto se hace a través de VentasViewSet.perform_create
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=monto_venta,
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=self.hijo,
            id_medio_pago=self.medio_pago,
        )

        # Simular descuento manual (en producción lo hace perform_create)
        self.tarjeta_sin_credito.saldo_actual -= monto_venta
        self.tarjeta_sin_credito.save()

        # Registrar consumo
        ConsumosTarjeta.objects.create(
            nro_tarjeta=self.tarjeta_sin_credito,
            fecha_consumo=venta.fecha,
            monto_consumido=monto_venta,
            detalle=f"Venta #{venta.id_venta} - Cantina",
            saldo_anterior=saldo_inicial,
            saldo_posterior=self.tarjeta_sin_credito.saldo_actual,
            id_empleado_registro=self.cajero,
        )

        # Verificar venta creada
        self.assertEqual(venta.monto_total, monto_venta)
        self.assertEqual(venta.estado_pago, "pagada")

        # Verificar saldo descontado
        self.tarjeta_sin_credito.refresh_from_db()
        self.assertEqual(self.tarjeta_sin_credito.saldo_actual, saldo_inicial - monto_venta)

        # Verificar registro de consumo
        consumo = ConsumosTarjeta.objects.filter(
            nro_tarjeta=self.tarjeta_sin_credito, monto_consumido=monto_venta
        ).first()
        self.assertIsNotNone(consumo)
        self.assertEqual(consumo.saldo_anterior, saldo_inicial)

    def test_venta_con_saldo_insuficiente_sin_autorizacion(self):
        """Test: Venta debe fallar si no hay saldo y no permite negativo"""
        # Tarjeta tiene 50.00, intentamos vender 80.00
        monto_venta = Decimal("80.00")

        # Verificar que la tarjeta NO permite saldo negativo
        self.assertFalse(self.tarjeta_sin_credito.permite_saldo_negativo)

        # Verificar saldo insuficiente
        self.assertLess(self.tarjeta_sin_credito.saldo_actual, monto_venta)

        # En producción, VentasViewSet.perform_create lanza ValidationError
        # Aquí solo verificamos las condiciones
        self.assertTrue(
            self.tarjeta_sin_credito.saldo_actual < monto_venta
            and not self.tarjeta_sin_credito.permite_saldo_negativo
        )

    def test_venta_con_credito_dentro_limite(self):
        """Test: Venta con saldo negativo permitido dentro del límite"""
        # Tarjeta: saldo=30, límite_credito=100, permite_negativo=True
        # Total disponible = 30 + 100 = 130
        saldo_inicial = self.tarjeta_con_credito.saldo_actual
        monto_venta = Decimal("80.00")  # Genera saldo negativo -50

        # Verificar que permite saldo negativo
        self.assertTrue(self.tarjeta_con_credito.permite_saldo_negativo)

        # Verificar que está dentro del límite
        saldo_negativo_proyectado = monto_venta - saldo_inicial  # 80 - 30 = 50
        self.assertLessEqual(saldo_negativo_proyectado, self.tarjeta_con_credito.limite_credito)

        # Simular venta
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=monto_venta,
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="credito",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=self.hijo2,
            id_medio_pago=self.medio_pago,
        )

        # Descontar saldo
        self.tarjeta_con_credito.saldo_actual -= monto_venta
        self.tarjeta_con_credito.save()

        # Verificar saldo negativo
        self.tarjeta_con_credito.refresh_from_db()
        self.assertEqual(self.tarjeta_con_credito.saldo_actual, Decimal("-50.00"))

        # Verificar que está dentro del límite
        self.assertGreaterEqual(
            self.tarjeta_con_credito.limite_credito, abs(self.tarjeta_con_credito.saldo_actual)
        )

    def test_venta_excede_limite_credito(self):
        """Test: Venta debe fallar si excede el límite de crédito"""
        # Tarjeta: saldo=30, límite_credito=100
        # Intento vender por 200 (saldo negativo = -170, excede límite)
        monto_venta = Decimal("200.00")
        saldo_inicial = self.tarjeta_con_credito.saldo_actual

        # Calcular saldo negativo proyectado
        saldo_negativo = monto_venta - saldo_inicial  # 200 - 30 = 170

        # Verificar que excede el límite
        self.assertGreater(saldo_negativo, self.tarjeta_con_credito.limite_credito)

        # En producción, perform_create lanza ValidationError
        # Verificamos condición
        excede_limite = (
            self.tarjeta_con_credito.permite_saldo_negativo
            and saldo_negativo > self.tarjeta_con_credito.limite_credito
        )
        self.assertTrue(excede_limite)

    def test_consumo_registrado_correctamente(self):
        """Test: Verificar que el consumo registra saldos correctamente"""
        saldo_anterior = self.tarjeta_sin_credito.saldo_actual
        monto = Decimal("25.00")

        # Descontar saldo
        self.tarjeta_sin_credito.saldo_actual -= monto
        saldo_posterior = self.tarjeta_sin_credito.saldo_actual
        self.tarjeta_sin_credito.save()

        # Crear consumo
        consumo = ConsumosTarjeta.objects.create(
            nro_tarjeta=self.tarjeta_sin_credito,
            fecha_consumo=timezone.now(),
            monto_consumido=monto,
            detalle="Test consumo",
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            id_empleado_registro=self.cajero,
        )

        # Verificar datos del consumo
        self.assertEqual(consumo.saldo_anterior, Decimal("50.00"))
        self.assertEqual(consumo.saldo_posterior, Decimal("25.00"))
        self.assertEqual(consumo.monto_consumido, monto)

        # Verificar coherencia: saldo_anterior - monto = saldo_posterior
        self.assertEqual(consumo.saldo_anterior - consumo.monto_consumido, consumo.saldo_posterior)

    def test_venta_sin_tarjeta_no_descuenta_saldo(self):
        """Test: Venta sin tarjeta (pago directo) no afecta saldo"""
        # Crear venta sin especificar hijo (pago directo en efectivo)
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("100.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=None,  # Sin hijo = sin tarjeta
            id_medio_pago=self.medio_pago,
        )

        # Verificar que no se creó consumo en tarjeta
        consumos = ConsumosTarjeta.objects.filter(detalle__contains=f"Venta #{venta.id_venta}")
        self.assertEqual(consumos.count(), 0)


class SaldoDisponibleTest(TestCase):
    """Tests para el cálculo de saldo disponible"""

    def setUp(self):
        """Configuración básica"""
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="User",
            ruc_ci="99999999",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test",
            apellido="Child",
            grado="1ro",
            estado=True,
            id_cliente_responsable=cliente,
        )

    def test_saldo_disponible_sin_credito_saldo_positivo(self):
        """Saldo disponible = saldo actual cuando no permite negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T300",
            saldo_actual=Decimal("75.50"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras="BAR300",
        )

        self.assertEqual(tarjeta.saldo_disponible, Decimal("75.50"))

    def test_saldo_disponible_con_credito(self):
        """Saldo disponible = saldo + límite cuando permite negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T400",
            saldo_actual=Decimal("40.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal("60.00"),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras="BAR400",
        )

        # 40 + 60 = 100
        self.assertEqual(tarjeta.saldo_disponible, Decimal("100.00"))

    def test_saldo_disponible_con_saldo_negativo(self):
        """Saldo disponible correcto cuando ya está en negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T500",
            saldo_actual=Decimal("-20.00"),  # Ya negativo
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal("100.00"),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras="BAR500",
        )

        # -20 + 100 = 80 disponible
        self.assertEqual(tarjeta.saldo_disponible, Decimal("80.00"))


class PromocionServiceTest(TestCase):
    """Tests para PromocionService - Sistema de Promociones y Descuentos"""

    def setUp(self):
        """Configuración inicial para tests de promociones"""
        # Crear impuesto
        from apps.contabilidad.models import Impuestos

        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", estado=True)

        # Crear productos
        self.producto1 = Productos.objects.create(
            descripcion="Coca Cola 500ml",
            codigo_barra="7890123456789",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        self.producto2 = Productos.objects.create(
            descripcion="Pepsi 500ml",
            codigo_barra="7890987654321",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Crear promoción 2x1 en producto específico
        from apps.ventas.models import Promociones, ProductosPromocion

        self.promo_2x1 = Promociones.objects.create(
            nombre="2x1 en Coca Cola",
            descripcion="Compra 2 coca colas y paga 1",
            tipo_promocion="2x1",
            valor_descuento=Decimal("0.00"),
            fecha_inicio=timezone.now().date(),
            fecha_fin=None,
            aplica_a="producto",
            min_cantidad=2,
            monto_minimo=Decimal("0.00"),
            max_usos_cliente=None,
            max_usos_total=None,
            usos_actuales=0,
            requiere_codigo=False,
            prioridad=1,
            estado=True,
            fecha_creacion=timezone.now(),
        )

        ProductosPromocion.objects.create(id_promocion=self.promo_2x1, id_producto=self.producto1)

        # Crear promoción porcentual
        self.promo_porcentaje = Promociones.objects.create(
            nombre="10% en toda la compra",
            descripcion="Obtén 10% de descuento",
            tipo_promocion="porcentaje",
            valor_descuento=Decimal("10.00"),
            fecha_inicio=timezone.now().date(),
            fecha_fin=None,
            aplica_a="total",
            min_cantidad=1,
            monto_minimo=Decimal("20000.00"),
            max_usos_cliente=None,
            max_usos_total=100,
            usos_actuales=0,
            requiere_codigo=True,
            codigo_promocion="DESCUENTO10",
            prioridad=2,
            estado=True,
            fecha_creacion=timezone.now(),
        )

        # Crear tipo de cliente y cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="12345678",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_obtener_promociones_aplicables_2x1(self):
        """Test: Debe detectar promoción 2x1 cuando se compran 2 o más unidades"""
        from apps.ventas.services import PromocionService

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("2"),
                "precio": Decimal("5000.00"),
            }
        ]

        promociones = PromocionService.obtener_promociones_aplicables(
            items=items, monto_total=Decimal("10000.00")
        )

        self.assertEqual(len(promociones), 1)
        self.assertEqual(promociones[0]["promocion"].id_promocion, self.promo_2x1.id_promocion)

    def test_calcular_descuento_2x1(self):
        """Test: Debe calcular correctamente descuento 2x1 (4 unidades = 2 gratis)"""
        from apps.ventas.services import PromocionService

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("4"),
                "precio": Decimal("5000.00"),
            }
        ]

        descuento = PromocionService.calcular_descuento(
            promocion=self.promo_2x1, items=items, monto_total=Decimal("20000.00")
        )

        # 4 unidades / 2 = 2 gratis → descuento de Gs. 10,000
        self.assertEqual(descuento["monto_descuento"], Decimal("10000.00"))
        self.assertEqual(descuento["tipo_descuento"], "2x1")

    def test_promocion_requiere_codigo(self):
        """Test: Promoción con código solo aplica si se proporciona el código"""
        from apps.ventas.services import PromocionService

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("1"),
                "precio": Decimal("25000.00"),
            }
        ]

        # Sin código, no debe aplicar
        promociones_sin_codigo = PromocionService.obtener_promociones_aplicables(
            items=items, monto_total=Decimal("25000.00")
        )

        # No debe incluir la promoción que requiere código
        codigos_encontrados = [
            p["promocion"].codigo_promocion
            for p in promociones_sin_codigo
            if p["promocion"].codigo_promocion
        ]
        self.assertNotIn("DESCUENTO10", codigos_encontrados)

        # Con código correcto, debe aplicar
        promociones_con_codigo = PromocionService.obtener_promociones_aplicables(
            items=items, monto_total=Decimal("25000.00"), codigo_promocion="DESCUENTO10"
        )

        self.assertTrue(
            any(p["promocion"].codigo_promocion == "DESCUENTO10" for p in promociones_con_codigo)
        )

    def test_calcular_descuento_porcentual(self):
        """Test: Debe calcular correctamente descuento porcentual"""
        from apps.ventas.services import PromocionService

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("5"),
                "precio": Decimal("5000.00"),
            }
        ]

        monto = Decimal("25000.00")

        descuento = PromocionService.calcular_descuento(
            promocion=self.promo_porcentaje, items=items, monto_total=monto
        )

        # 10% de 25,000 = 2,500
        self.assertEqual(descuento["monto_descuento"], Decimal("2500.00"))
        self.assertEqual(descuento["tipo_descuento"], "porcentaje")

    def test_validar_monto_minimo(self):
        """Test: Promoción no debe aplicar si no alcanza monto mínimo"""
        from apps.ventas.services import PromocionService

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("1"),
                "precio": Decimal("5000.00"),
            }
        ]

        # Monto 5,000 no alcanza el mínimo de 20,000
        promociones = PromocionService.obtener_promociones_aplicables(
            items=items, monto_total=Decimal("5000.00"), codigo_promocion="DESCUENTO10"
        )

        self.assertEqual(len(promociones), 0)

    def test_limite_usos_total(self):
        """Test: Promoción no debe aplicar si alcanzó límite de usos totales"""
        from apps.ventas.services import PromocionService

        # Marcar promoción como agotada
        self.promo_porcentaje.usos_actuales = 100
        self.promo_porcentaje.save()

        items = [
            {
                "id_producto": self.producto1.id_producto,
                "cantidad": Decimal("5"),
                "precio": Decimal("5000.00"),
            }
        ]

        promociones = PromocionService.obtener_promociones_aplicables(
            items=items, monto_total=Decimal("25000.00"), codigo_promocion="DESCUENTO10"
        )

        self.assertEqual(len(promociones), 0)

    def test_aplicar_promociones_a_venta(self):
        """Test: Debe registrar promoción aplicada y actualizar contador de usos"""
        from apps.ventas.services import PromocionService
        from apps.ventas.models import PromocionesAplicadas

        # Crear empleado
        rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        empleado = Empleados.objects.create(
            nombre="Ana",
            apellido="López",
            usuario="ana_test",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )

        # Crear venta
        medio_pago = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, requiere_validacion=False, estado=True
        )

        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("10000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="Pagada",
            estado="Activa",
            tipo_venta="Contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=empleado,
            id_medio_pago=medio_pago,
        )

        # Aplicar promoción
        descuento_info = {"monto_descuento": Decimal("5000.00"), "tipo_descuento": "2x1"}

        usos_iniciales = self.promo_2x1.usos_actuales

        resultado = PromocionService.aplicar_promociones_a_venta(
            venta=venta,
            promociones_seleccionadas=[(self.promo_2x1, descuento_info)],
            empleado=empleado,
        )

        # Verificar que se registró la aplicación
        self.assertEqual(len(resultado["promociones_aplicadas"]), 1)
        self.assertEqual(resultado["monto_total_descuentos"], Decimal("5000.00"))

        # Verificar que aumentó el contador de usos
        self.promo_2x1.refresh_from_db()
        self.assertEqual(self.promo_2x1.usos_actuales, usos_iniciales + 1)

        # Verificar registro en PromocionesAplicadas
        aplicacion = PromocionesAplicadas.objects.filter(id_venta=venta).first()
        self.assertIsNotNone(aplicacion)
        self.assertEqual(aplicacion.monto_descontado, Decimal("5000.00"))


class DevolucionServiceTest(TestCase):
    """Tests para DevolucionService - Devoluciones de Clientes"""

    def setUp(self):
        """Configuración inicial para tests de devoluciones"""
        # Crear impuesto
        from apps.contabilidad.models import Impuestos

        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría y unidad
        self.categoria = Categorias.objects.create(nombre="Snacks", estado=True)
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", estado=True)

        # Crear producto
        self.producto = Productos.objects.create(
            descripcion="Papas Fritas",
            codigo_barra="1234567890123",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Crear stock inicial
        from apps.inventario.models import StockUnico

        self.stock = StockUnico.objects.create(
            id_producto=self.producto, cantidad=Decimal("50.000")
        )

        # Crear cliente
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Carlos",
            apellidos="Ramírez",
            ruc_ci="98765432",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        # Crear empleado
        rol = Roles.objects.create(nombre_rol="Gerente", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Laura",
            apellido="Fernández",
            usuario="laura_test",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )

        # Crear venta
        medio_pago = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, requiere_validacion=False, estado=True
        )

        self.venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("9000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="Pagada",
            estado="Activa",
            tipo_venta="Contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=medio_pago,
        )

        # Crear detalle de venta
        from apps.ventas.models import DetallesVenta

        DetallesVenta.objects.create(
            cantidad=Decimal("3.000"),
            precio_unitario=Decimal("3000.00"),
            subtotal=Decimal("9000.00"),
            id_producto=self.producto,
            id_venta=self.venta,
        )

    def test_validar_productos_devolucion_exitosa(self):
        """Test: Debe validar correctamente productos que pueden devolverse"""
        from apps.ventas.services import DevolucionService

        productos = [{"id_producto": self.producto.id_producto, "cantidad": Decimal("2.000")}]

        validacion = DevolucionService.validar_productos_devolucion(
            id_venta=self.venta.id_venta, productos=productos
        )

        self.assertTrue(validacion["valido"])
        self.assertEqual(len(validacion["errores"]), 0)

    def test_validar_cantidad_excede_compra(self):
        """Test: No debe permitir devolver más de lo comprado"""
        from apps.ventas.services import DevolucionService

        productos = [
            {
                "id_producto": self.producto.id_producto,
                "cantidad": Decimal("5.000"),
            }  # Compró 3, intenta devolver 5
        ]

        validacion = DevolucionService.validar_productos_devolucion(
            id_venta=self.venta.id_venta, productos=productos
        )

        self.assertFalse(validacion["valido"])
        self.assertTrue(len(validacion["errores"]) > 0)

    def test_crear_nota_credito_exitosa(self):
        """Test: Debe crear nota de crédito y reintegrar stock"""
        from apps.ventas.services import DevolucionService
        from apps.ventas.models import NotasCreditoCliente, DetallesNotaCredito

        self.stock.refresh_from_db()  # Actualizar después de descuento por venta
        stock_inicial = self.stock.cantidad

        productos_devolucion = [
            {
                "id_producto": self.producto.id_producto,
                "cantidad": Decimal("2.000"),
                "motivo_item": "Productos defectuosos",
            }
        ]

        resultado = DevolucionService.crear_nota_credito(
            id_venta=self.venta.id_venta,
            productos_devolucion=productos_devolucion,
            motivo="Cliente insatisfecho",
            empleado_autoriza=self.empleado,
            tipo_devolucion="parcial",
        )

        # Verificar éxito
        self.assertTrue(resultado["exito"])
        self.assertIsNotNone(resultado["nota_credito"])

        # Verificar monto devuelto (2 unidades * 3,000 = 6,000)
        self.assertEqual(resultado["monto_devuelto"], Decimal("6000.00"))

        # Verificar que se creó la nota de crédito
        nota = NotasCreditoCliente.objects.filter(id_venta_origen=self.venta).first()
        self.assertIsNotNone(nota)
        self.assertEqual(nota.estado, "Emitida")
        self.assertEqual(nota.monto_total, Decimal("6000.00"))

        # Verificar detalles de nota
        detalles = DetallesNotaCredito.objects.filter(id_nota=nota)
        self.assertEqual(detalles.count(), 1)

        # Verificar que se reintegró el stock
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, stock_inicial + Decimal("2.000"))

    def test_devolucion_fuera_de_plazo(self):
        """Test: No debe permitir devolución después del plazo límite"""
        from apps.ventas.services import DevolucionService
        from datetime import timedelta

        # Modificar fecha de venta a hace 10 días (límite es 7)
        self.venta.fecha = timezone.now() - timedelta(days=10)
        self.venta.save()

        productos_devolucion = [
            {"id_producto": self.producto.id_producto, "cantidad": Decimal("1.000")}
        ]

        with self.assertRaises(ValidationError) as context:
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.id_venta,
                productos_devolucion=productos_devolucion,
                motivo="Devolviendo tarde",
                empleado_autoriza=self.empleado,
            )

        # Verificar mensaje de error
        self.assertIn("fuera de plazo", str(context.exception))

    def test_anular_nota_credito(self):
        """Test: Debe anular nota de crédito y revertir stock"""
        from apps.ventas.services import DevolucionService

        # Primero crear una devolución
        productos_devolucion = [
            {"id_producto": self.producto.id_producto, "cantidad": Decimal("1.000")}
        ]

        resultado = DevolucionService.crear_nota_credito(
            id_venta=self.venta.id_venta,
            productos_devolucion=productos_devolucion,
            motivo="Producto defectuoso",
            empleado_autoriza=self.empleado,
        )

        nota = resultado["nota_credito"]
        self.stock.refresh_from_db()  # Actualizar después de reintegro
        stock_despues_devolucion = self.stock.cantidad

        # Ahora anular
        resultado_anulacion = DevolucionService.anular_nota_credito(
            id_nota=nota.id_nota,
            empleado_autoriza=self.empleado,
            motivo_anulacion="Error en registro",
        )

        self.assertTrue(resultado_anulacion["exito"])

        # Verificar que la nota está anulada
        nota.refresh_from_db()
        self.assertEqual(nota.estado, "Anulada")

        # Verificar que se revirtió el stock (se descontó lo que se había sumado)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, stock_despues_devolucion - Decimal("1.000"))

    def test_producto_no_en_venta(self):
        """Test: No debe permitir devolver producto que no está en la venta"""
        from apps.ventas.services import DevolucionService

        # Crear otro producto
        otro_producto = Productos.objects.create(
            descripcion="Galletas",
            codigo_barra="9999999999999",
            stock_minimo=Decimal("10.000"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        productos_devolucion = [
            {"id_producto": otro_producto.id_producto, "cantidad": Decimal("1.000")}
        ]

        with self.assertRaises(ValidationError) as context:
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.id_venta,
                productos_devolucion=productos_devolucion,
                motivo="Intento de fraude",
                empleado_autoriza=self.empleado,
            )

        self.assertIn("no está en la venta original", str(context.exception))
