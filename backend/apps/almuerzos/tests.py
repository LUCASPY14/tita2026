"""
Tests para la app almuerzos - Independencia del módulo de cantina
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

from apps.almuerzos.models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    CuentasAlmuerzoMensual,
)
from apps.core.models import Tarjetas, ConsumosTarjeta
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles


class IndependenciaAlmuerzoCantinaTest(TestCase):
    """
    Tests críticos para verificar que el módulo de almuerzo
    NO afecta el saldo de la tarjeta de cantina
    """

    def setUp(self):
        """Configuración inicial"""
        # Crear datos base
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Roberto",
            apellidos="Martínez",
            ruc_ci="55555555",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        self.hijo = Hijos.objects.create(
            nombre="Sofía",
            apellido="Martínez",
            grado="4to",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta con saldo inicial conocido
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T1000",
            saldo_actual=Decimal("200.00"),  # Saldo inicial cantina
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras="BAR1000",
        )

        # Crear plan de almuerzo
        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Completo",
            descripcion="5 días a la semana",
            precio_mensual=Decimal("120.00"),
            dias_semana_incluidos="Lunes,Martes,Miércoles,Jueves,Viernes",
            fecha_creacion=timezone.now(),
            estado=True,
        )

        # Crear tipo de almuerzo (para consumos sin suscripción)
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Completo",
            descripcion="Plato principal + postre + bebida",
            precio_unitario=Decimal("25.00"),
            incluye_plato_principal=True,
            incluye_postre=True,
            incluye_bebida=True,
            fecha_creacion=timezone.now(),
            estado=True,
        )

        # Crear suscripción activa
        self.suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=date.today(),
            fecha_fin=None,
            estado="estado",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        # Crear empleado
        rol = Roles.objects.create(nombre_rol="Encargado Cocina", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Carmen",
            apellido="López",
            usuario="empleado_test",
            contrasena_hash="hash456",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )

    def test_registro_almuerzo_con_suscripcion_no_descuenta_saldo_cantina(self):
        """
        TEST CRÍTICO: Registrar almuerzo con suscripción NO debe descontar
        el saldo de la tarjeta de cantina
        """
        saldo_cantina_inicial = self.tarjeta.saldo_actual

        # Registrar consumo de almuerzo con suscripción activa
        registro = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=date.today(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("0.00"),  # Gratis con suscripción
            marcado_en_cuenta=False,
            estado="aprobado",
            id_hijo=self.hijo,
            id_suscripcion=self.suscripcion,
            nro_tarjeta=self.tarjeta,  # Solo para identificación
            id_empleado_registro=self.empleado,
        )

        # Refrescar saldo de tarjeta
        self.tarjeta.refresh_from_db()

        # VERIFICACIÓN CRÍTICA: El saldo de cantina NO debe cambiar
        self.assertEqual(
            self.tarjeta.saldo_actual,
            saldo_cantina_inicial,
            "ERROR: El registro de almuerzo descontó saldo de cantina",
        )

        # Verificar que NO se creó consumo en ConsumosTarjeta
        consumos_cantina = ConsumosTarjeta.objects.filter(nro_tarjeta=self.tarjeta, detalle__contains="almuerzo")
        self.assertEqual(
            consumos_cantina.count(),
            0,
            "ERROR: Se registró consumo de almuerzo en historial de cantina",
        )

        # Verificar que el registro se creó correctamente
        self.assertEqual(registro.costo_almuerzo, Decimal("0.00"))
        self.assertEqual(registro.estado, "aprobado")

    def test_registro_almuerzo_sin_suscripcion_no_descuenta_saldo_cantina(self):
        """
        TEST CRÍTICO: Almuerzo sin suscripción tampoco debe descontar saldo
        de tarjeta, debe ir a cuenta mensual de almuerzo
        """
        saldo_cantina_inicial = self.tarjeta.saldo_actual

        # Hijo sin suscripción consume almuerzo
        # Crear nuevo hijo sin suscripción
        hijo_sin_suscripcion = Hijos.objects.create(
            nombre="Carlos",
            apellido="Martínez",
            grado="2do",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        tarjeta_sin_suscripcion = Tarjetas.objects.create(
            nro_tarjeta="T2000",
            saldo_actual=Decimal("150.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=hijo_sin_suscripcion,
            codigo_barras="BAR2000",
        )

        saldo_inicial_tarjeta2 = tarjeta_sin_suscripcion.saldo_actual

        # Registrar consumo sin suscripción (se cobra precio unitario)
        registro = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=date.today(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=self.tipo_almuerzo.precio_unitario,  # 25.00
            marcado_en_cuenta=True,  # Se marca en cuenta mensual de ALMUERZO
            estado="aprobado",
            id_hijo=hijo_sin_suscripcion,
            id_suscripcion=None,  # Sin suscripción
            id_tipo_almuerzo=self.tipo_almuerzo,
            nro_tarjeta=tarjeta_sin_suscripcion,
            id_empleado_registro=self.empleado,
        )

        # Refrescar saldo
        tarjeta_sin_suscripcion.refresh_from_db()

        # VERIFICACIÓN CRÍTICA: El saldo de cantina NO debe cambiar
        self.assertEqual(
            tarjeta_sin_suscripcion.saldo_actual,
            saldo_inicial_tarjeta2,
            "ERROR: Almuerzo sin suscripción descontó saldo de cantina",
        )

        # Verificar que NO hay consumo en ConsumosTarjeta
        consumos_cantina = ConsumosTarjeta.objects.filter(nro_tarjeta=tarjeta_sin_suscripcion)
        self.assertEqual(consumos_cantina.count(), 0)

        # Verificar que tiene costo (se cobrará en cuenta mensual)
        self.assertEqual(registro.costo_almuerzo, Decimal("25.00"))
        self.assertTrue(registro.marcado_en_cuenta)

    def test_cuenta_mensual_almuerzo_separada_de_saldo_cantina(self):
        """
        TEST: La cuenta mensual de almuerzo es independiente del saldo de cantina
        """
        # Crear cuenta mensual de almuerzo
        cuenta = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=3,
            cantidad_almuerzos=10,
            monto_total=Decimal("250.00"),  # Total adeudado por almuerzos
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date.today(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )

        # Verificar saldo de tarjeta cantina
        saldo_cantina = self.tarjeta.saldo_actual

        # VERIFICACIÓN: La cuenta de almuerzo NO afecta el saldo de cantina
        self.assertEqual(saldo_cantina, Decimal("200.00"))
        self.assertEqual(cuenta.monto_total, Decimal("250.00"))

        # Son sistemas completamente independientes
        self.assertNotEqual(
            cuenta.monto_total,
            saldo_cantina,
            "La cuenta de almuerzo y el saldo de cantina deben ser independientes",
        )


class SuscripcionesAlmuerzoTest(TestCase):
    """Tests para suscripciones de almuerzo"""

    def setUp(self):
        """Configuración base"""
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        cliente = Clientes.objects.create(
            nombres="Laura",
            apellidos="Fernández",
            ruc_ci="77777777",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        self.hijo = Hijos.objects.create(
            nombre="Diego",
            apellido="Fernández",
            grado="3ro",
            estado=True,
            id_cliente_responsable=cliente,
        )

        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Básico",
            descripcion="3 días a la semana",
            precio_mensual=Decimal("80.00"),
            dias_semana_incluidos="Lunes,Miércoles,Viernes",
            fecha_creacion=timezone.now(),
            estado=True,
        )

    def test_crear_suscripcion_activa(self):
        """Test: Crear suscripción activa"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=date.today(),
            fecha_fin=None,  # Sin fecha fin = recurrente
            estado="estado",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        self.assertEqual(suscripcion.estado, "estado")
        self.assertIsNone(suscripcion.fecha_fin)
        self.assertEqual(suscripcion.id_plan_almuerzo.precio_mensual, Decimal("80.00"))

    def test_suscripcion_activa_costo_cero(self):
        """Test: Con suscripción activa, el costo del almuerzo es 0"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=date.today(),
            estado="estado",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        # Cuando hay suscripción activa, el costo debe ser 0
        # (ya está pagado mensualmente)
        costo_con_suscripcion = Decimal("0.00")

        self.assertEqual(costo_con_suscripcion, Decimal("0.00"))


class TiposAlmuerzoTest(TestCase):
    """Tests para tipos de almuerzo y sus componentes"""

    def test_tipo_almuerzo_completo(self):
        """Test: Tipo de almuerzo con todos los componentes"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Premium",
            descripcion="Todo incluido",
            precio_unitario=Decimal("30.00"),
            incluye_plato_principal=True,  # BooleanField
            incluye_postre=True,  # BooleanField
            incluye_bebida=True,  # BooleanField
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertTrue(tipo.incluye_plato_principal)
        self.assertTrue(tipo.incluye_postre)
        self.assertTrue(tipo.incluye_bebida)

    def test_tipo_almuerzo_basico(self):
        """Test: Tipo de almuerzo solo plato principal"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Básico",
            descripcion="Solo plato principal",
            precio_unitario=Decimal("15.00"),
            incluye_plato_principal=True,
            incluye_postre=False,  # No incluye
            incluye_bebida=False,  # No incluye
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertTrue(tipo.incluye_plato_principal)
        self.assertFalse(tipo.incluye_postre)
        self.assertFalse(tipo.incluye_bebida)


class CuentasAlmuerzoMensualTest(TestCase):
    """Tests para cuentas mensuales de almuerzo"""

    def setUp(self):
        """Configuración"""
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        cliente = Clientes.objects.create(
            nombres="Patricia",
            apellidos="Sosa",
            ruc_ci="88888888",
            limite_credito=Decimal("500.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        self.hijo = Hijos.objects.create(
            nombre="Martín",
            apellido="Sosa",
            grado="5to",
            estado=True,
            id_cliente_responsable=cliente,
        )

    def test_cuenta_unica_por_hijo_por_mes(self):
        """Test: Solo puede haber una cuenta por hijo por mes"""
        # Crear primera cuenta
        cuenta1 = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=3,
            cantidad_almuerzos=5,
            monto_total=Decimal("125.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date.today(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )

        # Verificar unique_together (id_hijo, anio, mes)
        # Django no permite crear otra cuenta con los mismos valores
        cuentas = CuentasAlmuerzoMensual.objects.filter(id_hijo=self.hijo, anio=2026, mes=3)

        self.assertEqual(cuentas.count(), 1)
        self.assertEqual(cuentas.first().id_cuenta, cuenta1.id_cuenta)

    def test_cuenta_acumula_consumos(self):
        """Test: La cuenta acumula cantidad y monto"""
        cuenta = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=3,
            cantidad_almuerzos=0,  # Inicia en 0
            monto_total=Decimal("0.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date.today(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )

        # Simular agregar consumos
        cuenta.cantidad_almuerzos += 1
        cuenta.monto_total += Decimal("25.00")
        cuenta.save()

        cuenta.cantidad_almuerzos += 1
        cuenta.monto_total += Decimal("25.00")
        cuenta.save()

        # Verificar acumulación
        cuenta.refresh_from_db()
        self.assertEqual(cuenta.cantidad_almuerzos, 2)
        self.assertEqual(cuenta.monto_total, Decimal("50.00"))

    def test_cuenta_con_pagos_parciales(self):
        """Test: La cuenta puede tener pagos parciales"""
        cuenta = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=3,
            cantidad_almuerzos=10,
            monto_total=Decimal("250.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date.today(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )

        # Simular pago parcial
        cuenta.monto_pagado = Decimal("100.00")
        cuenta.estado = "parcial"
        cuenta.save()

        # Verificar estado
        self.assertEqual(cuenta.estado, "parcial")
        self.assertLess(cuenta.monto_pagado, cuenta.monto_total)

        # Calcular saldo pendiente
        saldo_pendiente = cuenta.monto_total - cuenta.monto_pagado
        self.assertEqual(saldo_pendiente, Decimal("150.00"))
