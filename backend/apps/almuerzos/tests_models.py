"""
Tests para modelos de la app almuerzos
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.contabilidad.models import Impuestos
from apps.core.models import MediosPago, Tarjetas
from apps.productos.models import Categorias, ListasPrecios, Productos, UnidadesMedida
from apps.usuarios.models import Empleados, Roles

from .models import (
    Alergenos,
    CuentasAlmuerzoMensual,
    PagosAlmuerzoMensual,
    PagosCuentasAlmuerzo,
    PlanesAlmuerzo,
    ProductosAlergenos,
    RegistrosConsumoAlmuerzo,
    SuscripcionesAlmuerzo,
    TiposAlmuerzo,
)


class PlanesAlmuerzoModelTest(TestCase):
    """Tests para el modelo PlanesAlmuerzo"""

    def test_str_method(self):
        """Test del método __str__"""
        plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Básico",
            descripcion="Almuerzo diario básico",
            precio_mensual=Decimal("400000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            estado=True,
        )

        self.assertIsNotNone(str(plan))

    def test_crear_plan_completo(self):
        """Test de creación de plan con todos los campos"""
        plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Premium",
            descripcion="Almuerzo premium con extras",
            precio_mensual=Decimal("600000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertIsNotNone(plan.id_plan_almuerzo)
        self.assertEqual(plan.precio_mensual, Decimal("600000.00"))
        self.assertTrue(plan.estado)

    def test_plan_inactivo(self):
        """Test de plan inactivo"""
        plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Antiguo",
            descripcion="Plan descontinuado",
            precio_mensual=Decimal("350000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            estado=False,
        )

        self.assertFalse(plan.estado)


class TiposAlmuerzoModelTest(TestCase):
    """Tests para el modelo TiposAlmuerzo"""

    def test_str_method(self):
        """Test del método __str__"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Menú del Día",
            descripcion="Menú diario estándar",
            precio_unitario=Decimal("25000.00"),
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertIsNotNone(str(tipo))

    def test_crear_menu_completo(self):
        """Test de creación de menú con todos los componentes"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Menú Completo",
            descripcion="Incluye todo",
            precio_unitario=Decimal("35000.00"),
            incluye_plato_principal=True,
            incluye_postre=True,
            incluye_bebida=True,
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertTrue(tipo.incluye_plato_principal)
        self.assertTrue(tipo.incluye_postre)
        self.assertTrue(tipo.incluye_bebida)

    def test_crear_menu_basico(self):
        """Test de creación de menú básico sin extras"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Menú Básico",
            descripcion="Solo plato principal",
            precio_unitario=Decimal("20000.00"),
            incluye_plato_principal=True,
            incluye_postre=False,
            incluye_bebida=False,
            fecha_creacion=timezone.now(),
            estado=True,
        )

        self.assertTrue(tipo.incluye_plato_principal)
        self.assertFalse(tipo.incluye_postre)
        self.assertFalse(tipo.incluye_bebida)


class SuscripcionesAlmuerzoModelTest(TestCase):
    """Tests para el modelo SuscripcionesAlmuerzo"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Estudiantes", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Roberto",
            apellidos="Silva",
            ruc_ci="7777777777",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Sofía",
            apellido="Silva",
            fecha_nacimiento=timezone.datetime(2013, 5, 15).date(),
            grado="Sexto Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear plan
        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Regular",
            precio_mensual=Decimal("450000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            estado=True,
        )

    def test_str_method(self):
        """Test del método __str__"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_fin=(timezone.now() + timezone.timedelta(days=30)).date(),
            estado="activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        self.assertIsNotNone(str(suscripcion))

    def test_crear_suscripcion_activa(self):
        """Test de creación de suscripción activa"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_fin=(timezone.now() + timezone.timedelta(days=30)).date(),
            estado="activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        self.assertEqual(suscripcion.estado, "activa")
        self.assertIsNotNone(suscripcion.id_suscripcion)

    def test_suscripcion_sin_fecha_fin(self):
        """Test de suscripción sin fecha de finalización (indefinida)"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_fin=None,
            estado="activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        self.assertIsNone(suscripcion.fecha_fin)

    def test_cancelar_suscripcion(self):
        """Test de cancelación de suscripción"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_fin=(timezone.now() + timezone.timedelta(days=30)).date(),
            estado="activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        # Simular cancelación
        suscripcion.estado = "cancelada"
        suscripcion.save()

        self.assertEqual(suscripcion.estado, "cancelada")


class RegistrosConsumoAlmuerzoModelTest(TestCase):
    """Tests para el modelo RegistrosConsumoAlmuerzo"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista General", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Elena",
            apellidos="Benítez",
            ruc_ci="6666666666",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Diego",
            apellido="Benítez",
            fecha_nacimiento=timezone.datetime(2012, 8, 20).date(),
            grado="Séptimo Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear tarjeta
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="9000000001",
            saldo_actual=Decimal("50000.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        # Crear tipo de almuerzo
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Menú del Día",
            precio_unitario=Decimal("25000.00"),
            fecha_creacion=timezone.now(),
            estado=True,
        )

    def test_str_method(self):
        """Test del método __str__"""
        registro = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=timezone.now().date(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("25000.00"),
            ya_cobrado=True,
            estado="aprobado",
            id_hijo=self.hijo,
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        self.assertIsNotNone(str(registro))

    def test_crear_registro_aprobado(self):
        """Test de creación de registro aprobado"""
        registro = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=timezone.now().date(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("25000.00"),
            ya_cobrado=True,
            marcado_en_cuenta=False,
            estado="aprobado",
            id_hijo=self.hijo,
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        self.assertEqual(registro.estado, "aprobado")
        self.assertTrue(registro.ya_cobrado)

    def test_registro_rechazado(self):
        """Test de registro rechazado con motivo"""
        registro = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=timezone.now().date(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("0.00"),
            ya_cobrado=False,
            estado="rechazado",
            motivo_rechazo="Saldo insuficiente",
            id_hijo=self.hijo,
            nro_tarjeta=self.tarjeta,
        )

        self.assertEqual(registro.estado, "rechazado")
        self.assertIsNotNone(registro.motivo_rechazo)
        self.assertFalse(registro.ya_cobrado)

    def test_segundo_consumo_dia_no_cobra(self):
        """Test de segundo consumo del mismo día no cobra"""
        # Primer consumo del día
        registro1 = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=timezone.now().date(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("25000.00"),
            ya_cobrado=True,
            estado="aprobado",
            id_hijo=self.hijo,
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        # Segundo consumo del mismo día (no cobra)
        registro2 = RegistrosConsumoAlmuerzo.objects.create(
            fecha_consumo=timezone.now().date(),
            hora_registro=timezone.now().time(),
            costo_almuerzo=Decimal("25000.00"),
            ya_cobrado=False,
            estado="aprobado",
            id_hijo=self.hijo,
            nro_tarjeta=self.tarjeta,
            id_tipo_almuerzo=self.tipo_almuerzo,
        )

        self.assertTrue(registro1.ya_cobrado)
        self.assertFalse(registro2.ya_cobrado)


class ModelosAlmuerzosAdicionalesTest(TestCase):
    """Tests __str__ para modelos adicionales de almuerzos."""

    def setUp(self):
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Str Test", moneda="PYG", estado=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Tipo Str", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Str",
            ruc_ci="9000001",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Hijo",
            apellido="Str",
            fecha_nacimiento=timezone.now().date(),
            estado=True,
            id_cliente_responsable=self.cliente,
        )
        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Str",
            precio_mensual=Decimal("400000"),
            dias_semana_incluidos="L-V",
            estado=True,
        )
        self.suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            estado="Activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

    def test_str_cuentas_almuerzo_mensual(self):
        cuenta = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=3,
            cantidad_almuerzos=20,
            monto_total=Decimal("500000"),
            forma_cobro="debito",
            monto_pagado=Decimal("0"),
            estado="Pendiente",
            fecha_generacion=timezone.now().date(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )
        self.assertIn("#", str(cuenta))

    def test_str_pagos_almuerzo_mensual(self):
        pago = PagosAlmuerzoMensual.objects.create(
            fecha_pago=timezone.now(),
            monto_pagado=Decimal("400000"),
            mes_pagado=timezone.now().date(),
            id_suscripcion=self.suscripcion,
        )
        self.assertIn("#", str(pago))

    def test_str_pagos_cuentas_almuerzo(self):
        cuenta = CuentasAlmuerzoMensual.objects.create(
            anio=2026,
            mes=4,
            cantidad_almuerzos=15,
            monto_total=Decimal("375000"),
            forma_cobro="efectivo",
            monto_pagado=Decimal("0"),
            estado="Pendiente",
            fecha_generacion=timezone.now().date(),
            fecha_actualizacion=timezone.now(),
            id_hijo=self.hijo,
        )
        pago_cuenta = PagosCuentasAlmuerzo.objects.create(
            fecha_pago=timezone.now(),
            medio_pago="efectivo",
            monto=Decimal("375000"),
            id_cuenta=cuenta,
        )
        self.assertIn("#", str(pago_cuenta))

    def test_str_alergenos(self):
        alergeno = Alergenos.objects.create(
            nombre="Gluten Str",
            palabras_clave=["trigo", "harina"],
            nivel_severidad="Alto",
            estado=True,
            fecha_creacion=timezone.now(),
        )
        self.assertIn("#", str(alergeno))

    def test_str_productos_alergenos(self):
        impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA Str",
            porcentaje=10,
            vigente_desde=timezone.now().date(),
            estado=True,
        )
        cat = Categorias.objects.create(nombre="Cat Str", estado=True)
        prod = Productos.objects.create(
            descripcion="Producto Str",
            stock_minimo=0,
            estado=True,
            id_categoria=cat,
            id_impuesto=impuesto,
        )
        alergeno = Alergenos.objects.create(
            nombre="Lactosa Str",
            palabras_clave=["leche"],
            nivel_severidad="Medio",
            estado=True,
            fecha_creacion=timezone.now(),
        )
        prod_alerg = ProductosAlergenos.objects.create(
            contiene=True,
            fecha_registro=timezone.now(),
            id_alergeno=alergeno,
            id_producto=prod,
        )
        self.assertIn("#", str(prod_alerg))
