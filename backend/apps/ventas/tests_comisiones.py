"""
Tests para comisiones POS Bancard
Validación de cálculo y registro de comisiones
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.contabilidad.models import MovimientosCaja, TarifasComision
from apps.core.models import MediosPago, Tarjetas
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import PagosVenta, Ventas


class ComisionesBancardTest(TestCase):
    """Tests para validación de comisiones POS Bancard"""

    def setUp(self):
        """Configuración inicial"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Pedro",
            apellidos="Martínez",
            ruc_ci="12345678",
            limite_credito=Decimal("1000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Juan",
            apellido="Martínez",
            grado="5to",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T500",
            saldo_actual=Decimal("50000.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras="BAR500",
        )

        # Crear rol y empleado
        self.rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        self.cajero = Empleados.objects.create(
            nombre="María",
            apellido="Gómez",
            usuario="cajero_test",
            contrasena_hash="hash789",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear medios de pago Bancard para tests
        self.debito, _ = MediosPago.objects.get_or_create(
            descripcion="Tarjeta Débito Bancard",
            defaults={"genera_comision": True, "requiere_validacion": True, "estado": True},
        )
        self.credito, _ = MediosPago.objects.get_or_create(
            descripcion="Tarjeta Crédito Bancard",
            defaults={"genera_comision": True, "requiere_validacion": True, "estado": True},
        )

        # Crear tarifas para tests
        self.tarifa_debito, _ = TarifasComision.objects.get_or_create(
            id_medio_pago=self.debito,
            estado=True,
            fecha_fin_vigencia__isnull=True,
            defaults={
                "fecha_inicio_vigencia": timezone.now(),
                "porcentaje_comision": Decimal("0.0340"),
                "monto_fijo_comision": None,
            },
        )
        self.tarifa_credito, _ = TarifasComision.objects.get_or_create(
            id_medio_pago=self.credito,
            estado=True,
            fecha_fin_vigencia__isnull=True,
            defaults={
                "fecha_inicio_vigencia": timezone.now(),
                "porcentaje_comision": Decimal("0.0530"),
                "monto_fijo_comision": None,
            },
        )

    def test_calculo_comision_debito(self):
        """Test: Cálculo correcto de comisión 3.4% para débito"""
        from apps.ventas.views import VentasViewSet

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Calcular comisión
        comision, tarifa = viewset._calcular_comision(self.debito, monto_base)

        # Verificar cálculo
        esperado = monto_base * Decimal("0.0340")
        self.assertEqual(comision, esperado)
        self.assertEqual(comision, Decimal("340.00"))
        self.assertIsNotNone(tarifa)
        self.assertEqual(tarifa.porcentaje_comision, Decimal("0.0340"))

    def test_calculo_comision_credito(self):
        """Test: Cálculo correcto de comisión 5.3% para crédito"""
        from apps.ventas.views import VentasViewSet

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Calcular comisión
        comision, tarifa = viewset._calcular_comision(self.credito, monto_base)

        # Verificar cálculo
        esperado = monto_base * Decimal("0.0530")
        self.assertEqual(comision, esperado)
        self.assertEqual(comision, Decimal("530.00"))
        self.assertIsNotNone(tarifa)
        self.assertEqual(tarifa.porcentaje_comision, Decimal("0.0530"))

    def test_sin_comision_medio_pago_efectivo(self):
        """Test: No calcular comisión para efectivo"""
        from apps.ventas.views import VentasViewSet

        # Crear medio de pago efectivo
        efectivo = MediosPago.objects.create(
            descripcion="Efectivo",
            genera_comision=False,  # No genera comisión
            requiere_validacion=False,
            estado=True,
        )

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Calcular comisión
        comision, tarifa = viewset._calcular_comision(efectivo, monto_base)

        # Verificar que no hay comisión
        self.assertEqual(comision, Decimal("0.00"))
        self.assertIsNone(tarifa)

    def test_registro_pago_con_comision_debito(self):
        """Test: Registro completo de pago con comisión débito"""
        from apps.ventas.views import VentasViewSet

        # Crear venta
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("10000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=None,  # Venta sin tarjeta
        )

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Registrar pago con comisión
        pago = viewset._registrar_pago_con_comision(venta, self.debito, monto_base)

        # Verificar PagosVenta
        self.assertEqual(pago.monto, Decimal("10000.00"))
        self.assertEqual(pago.monto_comision, Decimal("340.00"))
        self.assertEqual(pago.total_cobrado, Decimal("10340.00"))
        self.assertEqual(pago.id_medio_pago, self.debito)
        self.assertEqual(pago.estado, "confirmado")

        # MovimientosCaja ya NO los crea _registrar_pago_con_comision directamente;
        # los crea la señal post_save de Ventas (cuando hay turno abierto en la caja).
        movimientos = MovimientosCaja.objects.filter(id_venta=venta)
        self.assertEqual(movimientos.count(), 0)

    def test_registro_pago_con_comision_credito(self):
        """Test: Registro completo de pago con comisión crédito"""
        from apps.ventas.views import VentasViewSet

        # Crear venta
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("10000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Registrar pago con comisión
        pago = viewset._registrar_pago_con_comision(venta, self.credito, monto_base)

        # Verificar PagosVenta
        self.assertEqual(pago.monto, Decimal("10000.00"))
        self.assertEqual(pago.monto_comision, Decimal("530.00"))
        self.assertEqual(pago.total_cobrado, Decimal("10530.00"))
        self.assertEqual(pago.porcentaje_comision_aplicado, Decimal("5.30"))

    def test_propiedades_calculadas_pago(self):
        """Test: Propiedades calculadas de PagosVenta"""
        # Crear pago manual
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("20000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )

        pago = PagosVenta.objects.create(
            monto=Decimal("20000.00"),
            monto_comision=Decimal("680.00"),  # 3.4% de 20000
            fecha_pago=timezone.now(),
            estado="confirmado",
            id_medio_pago=self.debito,
            id_venta=venta,
        )

        # Verificar @property total_cobrado
        self.assertEqual(pago.total_cobrado, Decimal("20680.00"))

        # Verificar @property porcentaje_comision_aplicado
        self.assertEqual(pago.porcentaje_comision_aplicado, Decimal("3.40"))

    def test_multiples_valores_comision(self):
        """Test: Validar cálculos con diferentes montos"""
        from apps.ventas.views import VentasViewSet

        viewset = VentasViewSet()

        casos_prueba = [
            (Decimal("5000.00"), Decimal("170.00")),  # 5000 * 3.4% = 170
            (Decimal("15000.00"), Decimal("510.00")),  # 15000 * 3.4% = 510
            (Decimal("25000.00"), Decimal("850.00")),  # 25000 * 3.4% = 850
            (Decimal("100000.00"), Decimal("3400.00")),  # 100000 * 3.4% = 3400
        ]

        for monto, comision_esperada in casos_prueba:
            comision, _ = viewset._calcular_comision(self.debito, monto)
            self.assertEqual(
                comision,
                comision_esperada,
                f"Fallo en monto {monto}: esperado {comision_esperada}, obtenido {comision}",
            )

    def test_sin_tarifa_configurada(self):
        """Test: Comportamiento cuando no hay tarifa configurada"""
        from apps.ventas.views import VentasViewSet

        # Crear medio de pago sin tarifa
        nuevo_medio = MediosPago.objects.create(
            descripcion="Nuevo POS Sin Tarifa",
            genera_comision=True,
            requiere_validacion=True,
            estado=True,
        )

        viewset = VentasViewSet()
        monto_base = Decimal("10000.00")

        # Calcular comisión (no debería haber tarifa)
        comision, tarifa = viewset._calcular_comision(nuevo_medio, monto_base)

        # Verificar que retorna 0 sin tarifa
        self.assertEqual(comision, Decimal("0.00"))
        self.assertIsNone(tarifa)


class IntegracionComisionesTest(TestCase):
    """Tests de integración con flow completo de venta"""

    def setUp(self):
        """Configuración inicial"""
        # Reutilizar setup similar
        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Ana",
            apellidos="López",
            ruc_ci="87654321",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.rol = Roles.objects.create(nombre_rol="Gerente", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Carlos",
            apellido="Ruiz",
            usuario="gerente_test",
            contrasena_hash="hash321",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )
        self.debito, _ = MediosPago.objects.get_or_create(
            descripcion="Tarjeta Débito Bancard",
            defaults={"genera_comision": True, "requiere_validacion": True, "estado": True},
        )
        # Crear tarifa para débito
        TarifasComision.objects.get_or_create(
            id_medio_pago=self.debito,
            estado=True,
            fecha_fin_vigencia__isnull=True,
            defaults={
                "fecha_inicio_vigencia": timezone.now(),
                "porcentaje_comision": Decimal("0.0340"),
                "monto_fijo_comision": None,
            },
        )

    def test_venta_pago_directo_con_comision(self):
        """Test: Venta con pago directo y comisión Bancard"""
        from apps.ventas.views import VentasViewSet

        # Simular datos de venta
        venta_data = {
            "fecha": timezone.now(),
            "monto_total": Decimal("15000.00"),
            "saldo_pendiente": Decimal("0.00"),
            "estado_pago": "pagada",
            "estado": "activa",
            "tipo_venta": "contado",
            "genera_factura_legal": False,
            "id_cliente": self.cliente,
            "id_empleado_cajero": self.empleado,
            "id_medio_pago": self.debito,
        }

        # Crear venta
        venta = Ventas.objects.create(**venta_data)

        # Registrar pago con comisión
        viewset = VentasViewSet()
        pago = viewset._registrar_pago_con_comision(venta, self.debito, venta_data["monto_total"])

        # Verificaciones finales
        self.assertEqual(pago.monto, Decimal("15000.00"))
        self.assertEqual(pago.monto_comision, Decimal("510.00"))  # 15000 * 3.4%
        self.assertEqual(pago.total_cobrado, Decimal("15510.00"))

        # MovimientosCaja los crea la señal post_save de Ventas (cuando hay turno abierto).
        # Sin turno abierto en el test → 0 movimientos desde esta llamada directa.
        movimientos = MovimientosCaja.objects.filter(id_venta=venta)
        self.assertEqual(movimientos.count(), 0)
