"""
Tests específicos para la lógica de doble registro de almuerzo
Validación de regla: Máximo 2 registros por día, cobro solo del primero
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time
from decimal import Decimal
from apps.almuerzos.validators import validar_limite_registros_diarios, determinar_si_cobra
from apps.almuerzos.models import (
    RegistrosConsumoAlmuerzo,
    TiposAlmuerzo,
    PlanesAlmuerzo,
    SuscripcionesAlmuerzo,
)
from apps.clientes.models import Hijos, Clientes, TiposCliente
from apps.productos.models import ListasPrecios
from apps.core.models import Tarjetas


class ValidarLimiteRegistrosDiariosTest(TestCase):
    """Tests para validación de máximo 2 registros por día"""

    def setUp(self):
        """Crear datos de prueba"""
        # Crear lista de precios y tipo de cliente
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        # Crear cliente
        cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="1234567890",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Juan",
            apellido="Pérez",
            grado="1ro",
            estado=True,
            id_cliente_responsable=cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="1234567890",
            saldo_actual=Decimal("100000"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0"),
            id_hijo=self.hijo,
        )

        # Crear tipo de almuerzo
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Completo",
            precio_unitario=Decimal("15000"),
            incluye_plato_principal=True,
            fecha_creacion=date.today(),
            estado=True,
        )

        self.fecha_hoy = date.today()

    def test_primer_registro_dia_permitido(self):
        """Primer registro del día debe ser permitido"""
        # No debe lanzar excepción
        try:
            validar_limite_registros_diarios(self.hijo, self.fecha_hoy)
        except ValidationError:
            self.fail("El primer registro del día no debería lanzar ValidationError")

    def test_segundo_registro_dia_permitido(self):
        """Segundo registro del día debe ser permitido"""
        # Crear primer registro
        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha_hoy,
            hora_registro=time(11, 30),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # Segundo registro NO debe lanzar excepción
        try:
            validar_limite_registros_diarios(self.hijo, self.fecha_hoy)
        except ValidationError:
            self.fail("El segundo registro del día no debería lanzar ValidationError")

    def test_tercer_registro_dia_bloqueado(self):
        """Tercer registro del día debe ser bloqueado"""
        # Crear primer registro
        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha_hoy,
            hora_registro=time(11, 30),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # Crear segundo registro
        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha_hoy,
            hora_registro=time(12, 0),
            costo_almuerzo=Decimal("0"),
            ya_cobrado=False,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # Tercer registro DEBE lanzar excepción
        with self.assertRaises(ValidationError) as context:
            validar_limite_registros_diarios(self.hijo, self.fecha_hoy)

        self.assertIn("Límite alcanzado", str(context.exception))
        self.assertIn("2 registros", str(context.exception))

    def test_registros_rechazados_no_cuentan(self):
        """Registros con estado Rechazado no deben contar para el límite"""
        # Crear dos registros rechazados
        for i in range(2):
            RegistrosConsumoAlmuerzo.objects.create(
                id_hijo=self.hijo,
                fecha_consumo=self.fecha_hoy,
                hora_registro=time(11 + i, 0),
                costo_almuerzo=Decimal("0"),
                ya_cobrado=False,
                estado="Rechazado",
                motivo_rechazo="Tarjeta bloqueada",
                nro_tarjeta=self.tarjeta,
                id_tipo_almuerzo=self.tipo_almuerzo,
            )

        # Nuevo registro válido NO debe lanzar excepción
        try:
            validar_limite_registros_diarios(self.hijo, self.fecha_hoy)
        except ValidationError:
            self.fail("Los registros rechazados no deberían contar para el límite")

    def test_registros_diferentes_dias_no_interfieren(self):
        """Registros de días diferentes no deben interferir"""
        from datetime import timedelta

        # Crear 2 registros ayer
        ayer = self.fecha_hoy - timedelta(days=1)
        for i in range(2):
            RegistrosConsumoAlmuerzo.objects.create(
                id_hijo=self.hijo,
                fecha_consumo=ayer,
                hora_registro=time(11 + i, 0),
                costo_almuerzo=Decimal("15000") if i == 0 else Decimal("0"),
                ya_cobrado=(i == 0),
                estado="Confirmado",
                nro_tarjeta=self.tarjeta,
                id_tipo_almuerzo=self.tipo_almuerzo,
            )

        # Hoy debe permitir nuevos registros
        try:
            validar_limite_registros_diarios(self.hijo, self.fecha_hoy)
        except ValidationError:
            self.fail("Los registros de ayer no deberían afectar los de hoy")


class DeterminarSiCobraTest(TestCase):
    """Tests para determinar si un registro debe generar cobro"""

    def setUp(self):
        """Crear datos de prueba"""
        # Crear lista de precios y tipo de cliente
        lista = ListasPrecios.objects.create(nombre_lista="Mayorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="VIP", estado=True)

        # Crear cliente
        cliente = Clientes.objects.create(
            nombres="Test2",
            apellidos="Cliente2",
            ruc_ci="0987654321",
            limite_credito=Decimal("1000.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="María",
            apellido="López",
            grado="2do",
            estado=True,
            id_cliente_responsable=cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="9876543210",
            saldo_actual=Decimal("200000"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0"),
            id_hijo=self.hijo,
        )

        # Crear tipo de almuerzo
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Simple",
            precio_unitario=Decimal("12000"),
            incluye_plato_principal=True,
            fecha_creacion=date.today(),
            estado=True,
        )

        self.fecha_hoy = date.today()

    def test_primer_registro_debe_cobrar(self):
        """Primer registro del día debe retornar ya_cobrado=True"""
        debe_cobrar = determinar_si_cobra(self.hijo, self.fecha_hoy)
        self.assertTrue(debe_cobrar, "El primer registro del día debe cobrar")

    def test_segundo_registro_no_debe_cobrar(self):
        """Segundo registro del día debe retornar ya_cobrado=False"""
        # Crear primer registro
        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha_hoy,
            hora_registro=time(11, 15),
            costo_almuerzo=Decimal("12000"),
            ya_cobrado=True,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # Verificar que el segundo no debe cobrar
        debe_cobrar = determinar_si_cobra(self.hijo, self.fecha_hoy)
        self.assertFalse(debe_cobrar, "El segundo registro del día NO debe cobrar")

    def test_registros_rechazados_no_afectan(self):
        """Registros rechazados no deben afectar el cobro"""
        # Crear registro rechazado
        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha_hoy,
            hora_registro=time(11, 0),
            costo_almuerzo=Decimal("0"),
            ya_cobrado=False,
            estado="Rechazado",
            motivo_rechazo="Saldo insuficiente",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # El siguiente registro debe cobrar (es el primero válido)
        debe_cobrar = determinar_si_cobra(self.hijo, self.fecha_hoy)
        self.assertTrue(debe_cobrar, "El primer registro válido debe cobrar")


class IntegracionRegistrosConsumoTest(TestCase):
    """Tests de integración para el flujo completo de registros"""

    def setUp(self):
        """Crear ambiente completo"""
        # Crear lista de precios y tipo de cliente
        lista = ListasPrecios.objects.create(nombre_lista="Escolar", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Estudiante", estado=True)

        # Crear cliente
        cliente = Clientes.objects.create(
            nombres="Carlos",
            apellidos="Mendez",
            ruc_ci="1122334455",
            limite_credito=Decimal("800.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Pedro",
            apellido="Mendez",
            grado="3ro",
            estado=True,
            id_cliente_responsable=cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="1111222233",
            saldo_actual=Decimal("50000"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0"),
            id_hijo=self.hijo,
        )

        # Crear tipo de almuerzo
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Premium",
            precio_unitario=Decimal("18000"),
            incluye_plato_principal=True,
            incluye_postre=True,
            incluye_bebida=True,
            fecha_creacion=date.today(),
            estado=True,
        )

        self.fecha = date.today()

    def test_escenario_completo_dos_registros(self):
        """Test del escenario completo: 2 registros en un día"""
        # Registro 1: 11:30 → Debe cobrar
        registro1 = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha,
            hora_registro=time(11, 30),
            costo_almuerzo=Decimal("18000"),
            ya_cobrado=True,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        self.assertEqual(registro1.ya_cobrado, True)
        self.assertEqual(registro1.costo_almuerzo, Decimal("18000"))

        # Registro 2: 12:00 → NO debe cobrar
        registro2 = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=self.hijo,
            fecha_consumo=self.fecha,
            hora_registro=time(12, 0),
            costo_almuerzo=Decimal("0"),
            ya_cobrado=False,
            estado="Confirmado",
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        self.assertEqual(registro2.ya_cobrado, False)
        self.assertEqual(registro2.costo_almuerzo, Decimal("0"))

        # Verificar que hay exactamente 2 registros
        registros_dia = RegistrosConsumoAlmuerzo.objects.filter(id_hijo=self.hijo, fecha_consumo=self.fecha).count()
        self.assertEqual(registros_dia, 2)

        # Verificar que solo 1 tiene ya_cobrado=True
        cobrados = RegistrosConsumoAlmuerzo.objects.filter(
            id_hijo=self.hijo, fecha_consumo=self.fecha, ya_cobrado=True
        ).count()
        self.assertEqual(cobrados, 1)
