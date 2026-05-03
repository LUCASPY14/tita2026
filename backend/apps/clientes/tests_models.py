"""
Tests para modelos de la app clientes
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.models import MediosPago
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import Ventas

from .models import Clientes, Hijos, RestriccionesHijos, TiposCliente


class ClientesModelTest(TestCase):
    """Tests para el modelo Clientes y sus propiedades calculadas"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol
        self.rol = Roles.objects.create(nombre_rol="Vendedor", estado=True)

        # Crear empleado
        self.empleado = Empleados.objects.create(
            nombre="Ana",
            apellido="García",
            usuario="ana.garcia",
            email="ana@example.com",
            fecha_ingreso=timezone.now().date(),
            estado=True,
            id_rol=self.rol,
        )

        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Minorista", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Mayorista", estado=True)

        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, requiere_validacion=False, estado=True
        )

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Fernando",
            apellidos="Mendoza",
            ruc_ci="5555555555",
            limite_credito=Decimal("1000000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_nombre_completo_property(self):
        """Test del property nombre_completo"""
        self.assertEqual(self.cliente.nombre_completo, "Fernando Mendoza")

    def test_credito_utilizado_sin_ventas(self):
        """Test de credito_utilizado cuando no hay ventas pendientes"""
        self.assertEqual(self.cliente.credito_utilizado, Decimal("0.00"))

    def test_credito_utilizado_con_ventas_pendientes(self):
        """Test de credito_utilizado con ventas que tienen saldo pendiente"""
        # Crear venta con saldo pendiente
        Ventas.objects.create(
            monto_total=Decimal("500000.00"),
            saldo_pendiente=Decimal("300000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        # Crear otra venta con saldo pendiente
        Ventas.objects.create(
            monto_total=Decimal("200000.00"),
            saldo_pendiente=Decimal("150000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        # El crédito utilizado debe ser la suma de saldos pendientes
        self.assertEqual(self.cliente.credito_utilizado, Decimal("450000.00"))

    def test_credito_disponible_sin_ventas(self):
        """Test de credito_disponible cuando no hay ventas"""
        self.assertEqual(self.cliente.credito_disponible, Decimal("1000000.00"))

    def test_credito_disponible_con_ventas_pendientes(self):
        """Test de credito_disponible con ventas pendientes"""
        Ventas.objects.create(
            monto_total=Decimal("400000.00"),
            saldo_pendiente=Decimal("400000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        # credito_disponible = limite_credito - credito_utilizado
        # 1000000 - 400000 = 600000
        self.assertEqual(self.cliente.credito_disponible, Decimal("600000.00"))

    def test_tiene_credito_disponible_true(self):
        """Test que verifica cuando el cliente tiene crédito disponible"""
        self.assertTrue(self.cliente.tiene_credito_disponible)

    def test_tiene_credito_disponible_false(self):
        """Test que verifica cuando el cliente NO tiene crédito disponible"""
        # Crear venta que agota el crédito
        Ventas.objects.create(
            monto_total=Decimal("1000000.00"),
            saldo_pendiente=Decimal("1000000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        self.assertFalse(self.cliente.tiene_credito_disponible)

    def test_porcentaje_credito_usado_cero(self):
        """Test de porcentaje_credito_usado cuando no hay ventas"""
        self.assertEqual(self.cliente.porcentaje_credito_usado, Decimal("0.00"))

    def test_porcentaje_credito_usado_con_ventas(self):
        """Test de porcentaje_credito_usado con ventas pendientes"""
        # Crear venta con 50% del límite de crédito
        Ventas.objects.create(
            monto_total=Decimal("500000.00"),
            saldo_pendiente=Decimal("500000.00"),
            estado_pago="pendiente",
            estado="activa",
            tipo_venta="credito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

        # Debe ser 50%
        self.assertEqual(self.cliente.porcentaje_credito_usado, Decimal("50.00"))

    def test_str_method(self):
        """Test del método __str__"""
        self.assertEqual(str(self.cliente), "Mendoza, Fernando")


class HijosModelTest(TestCase):
    """Tests para el modelo Hijos y sus propiedades"""

    def setUp(self):
        """Configuración inicial"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Estudiantes", moneda="PYG", estado=True)

        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Luis",
            apellidos="Torres",
            ruc_ci="6666666666",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        self.hijo = Hijos.objects.create(
            nombre="Valentina",
            apellido="Torres",
            fecha_nacimiento=timezone.datetime(2012, 4, 20).date(),
            grado="Séptimo Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

    def test_nombre_completo_property(self):
        """Test del property nombre_completo"""
        self.assertEqual(self.hijo.nombre_completo, "Valentina Torres")

    def test_edad_property(self):
        """Test del property edad"""
        # Para una fecha de nacimiento en 2012, la edad debe ser aproximadamente 13-14 años
        edad = self.hijo.edad
        self.assertIsNotNone(edad)
        self.assertTrue(13 <= edad <= 14)

    def test_edad_property_sin_fecha_nacimiento(self):
        """Test del property edad cuando no hay fecha de nacimiento"""
        hijo_sin_fecha = Hijos.objects.create(
            nombre="Santiago",
            apellido="Torres",
            grado="Primer Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        self.assertIsNone(hijo_sin_fecha.edad)

    def test_str_method(self):
        """Test del método __str__"""
        self.assertEqual(str(self.hijo), "Torres, Valentina (Séptimo Grado)")

    def test_str_method_sin_grado(self):
        """Test del método __str__ cuando no tiene grado"""
        hijo_sin_grado = Hijos.objects.create(
            nombre="Mateo", apellido="Torres", estado=True, id_cliente_responsable=self.cliente
        )

        self.assertEqual(str(hijo_sin_grado), "Torres, Mateo (Sin grado)")


class ClientesEdgeCasesTest(TestCase):
    """Tests para casos borde de las propiedades de Clientes."""

    def setUp(self):
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Edge", moneda="PYG", estado=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Tipo Edge", estado=True)

    def test_credito_disponible_sin_limite(self):
        """credito_disponible retorna 0 cuando limite_credito es None."""
        cliente = Clientes.objects.create(
            nombres="Sin",
            apellidos="Limite",
            ruc_ci="9000001",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.assertEqual(cliente.credito_disponible, Decimal("0.00"))
        # porcentaje_credito_usado también retorna 0.00 cuando no hay limite
        self.assertEqual(cliente.porcentaje_credito_usado, Decimal("0.00"))

    def test_tiene_credito_disponible_false(self):
        """tiene_credito_disponible es False si no hay limite_credito."""
        cliente = Clientes.objects.create(
            nombres="Sin",
            apellidos="Credito",
            ruc_ci="9000002",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.assertFalse(cliente.tiene_credito_disponible)

    def test_esta_activo_property(self):
        """esta_activo retorna True cuando estado=True."""
        cliente = Clientes.objects.create(
            nombres="Act",
            apellidos="Ivo",
            ruc_ci="9000003",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.assertTrue(cliente.esta_activo)


class RestriccionesHijosTest(TestCase):
    """Tests para la propiedad es_critica de RestriccionesHijos."""

    def setUp(self):
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista RH", moneda="PYG", estado=True)
        self.tipo = TiposCliente.objects.create(nombre_tipo="Tipo RH", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Rest",
            apellidos="HijosTest",
            ruc_ci="9100001",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo,
        )
        self.hijo = Hijos.objects.create(
            nombre="Hijo",
            apellido="RH",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

    def test_es_critica_true(self):
        """es_critica retorna True cuando severidad es critica."""
        r = RestriccionesHijos.objects.create(
            tipo_restriccion="Alergia",
            severidad="critica",
            estado=True,
            id_hijo=self.hijo,
        )
        self.assertTrue(r.es_critica)

    def test_es_critica_false(self):
        """es_critica retorna False cuando severidad es Baja."""
        r = RestriccionesHijos.objects.create(
            tipo_restriccion="Intolerancia",
            severidad="Baja",
            estado=True,
            id_hijo=self.hijo,
        )
        self.assertFalse(r.es_critica)
