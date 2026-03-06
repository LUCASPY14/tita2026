"""
Tests para serializers de la app almuerzos
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import PlanesAlmuerzo, TiposAlmuerzo, SuscripcionesAlmuerzo
from .serializers import (
    PlanesAlmuerzoSerializer,
    TiposAlmuerzoSerializer,
    SuscripcionesAlmuerzoSerializer,
)
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


class PlanesAlmuerzoSerializerTest(TestCase):
    """Tests para PlanesAlmuerzoSerializer"""

    def test_serializar_plan_completo(self):
        """Test de serialización de un plan de almuerzo completo"""
        plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Básico",
            descripcion="Almuerzo básico diario",
            precio_mensual=Decimal("400000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            activo=True,
        )

        serializer = PlanesAlmuerzoSerializer(plan)
        data = serializer.data

        self.assertEqual(data["nombre_plan"], "Plan Básico")
        self.assertEqual(Decimal(data["precio_mensual"]), Decimal("400000.00"))
        self.assertEqual(data["dias_semana_incluidos"], "Lunes-Viernes")
        self.assertTrue(data["activo"])

    def test_validar_plan_valido(self):
        """Test de validación de datos válidos de plan"""
        data = {
            "nombre_plan": "Plan Premium",
            "descripcion": "Almuerzo premium con postre",
            "precio_mensual": "600000.00",
            "dias_semana_incluidos": "Lunes-Viernes",
            "activo": True,
        }

        serializer = PlanesAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_plan_sin_nombre_invalido(self):
        """Test que valida que un plan sin nombre es inválido"""
        data = {
            "precio_mensual": "500000.00",
            "dias_semana_incluidos": "Lunes-Viernes",
            "activo": True,
        }

        serializer = PlanesAlmuerzoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre_plan", serializer.errors)

    def test_crear_plan_desde_serializer(self):
        """Test de creación de plan usando el serializer"""
        data = {
            "nombre_plan": "Plan Completo",
            "descripcion": "Todo incluido",
            "precio_mensual": "800000.00",
            "dias_semana_incluidos": "Lunes-Viernes",
            "activo": True,
        }

        serializer = PlanesAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        plan = serializer.save()
        self.assertIsNotNone(plan.id_plan_almuerzo)
        self.assertEqual(plan.nombre_plan, "Plan Completo")


class TiposAlmuerzoSerializerTest(TestCase):
    """Tests para TiposAlmuerzoSerializer"""

    def test_serializar_tipo_completo(self):
        """Test de serialización de un tipo de almuerzo completo"""
        tipo = TiposAlmuerzo.objects.create(
            nombre="Menú del Día",
            descripcion="Menú diario principal",
            precio_unitario=Decimal("25000.00"),
            fecha_creacion=timezone.now(),
            activo=True,
        )

        serializer = TiposAlmuerzoSerializer(tipo)
        data = serializer.data

        self.assertEqual(data["nombre"], "Menú del Día")
        self.assertEqual(Decimal(data["precio_unitario"]), Decimal("25000.00"))
        self.assertTrue(data["activo"])

    def test_validar_tipo_valido(self):
        """Test de validación de datos válidos de tipo"""
        data = {
            "nombre": "Menú Vegetariano",
            "descripcion": "Opción sin carne",
            "precio_unitario": "28000.00",
            "fecha_creacion": timezone.now().isoformat(),
            "activo": True,
        }

        serializer = TiposAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_crear_tipo_desde_serializer(self):
        """Test de creación de tipo usando el serializer"""
        data = {
            "nombre": "Menú Light",
            "descripcion": "Opción baja en calorías",
            "precio_unitario": "30000.00",
            "fecha_creacion": timezone.now().isoformat(),
            "activo": True,
        }

        serializer = TiposAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        tipo = serializer.save()
        self.assertIsNotNone(tipo.id_tipo_almuerzo)
        self.assertEqual(tipo.nombre, "Menú Light")


class SuscripcionesAlmuerzoSerializerTest(TestCase):
    """Tests para SuscripcionesAlmuerzoSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista="Lista Estudiantes", moneda="PYG", activo=True
        )

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", activo=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Ricardo",
            apellidos="Núñez",
            ruc_ci="9999999999",
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Lucía",
            apellido="Núñez",
            fecha_nacimiento=timezone.datetime(2014, 3, 10).date(),
            grado="Quinto Grado",
            activo=True,
            id_cliente_responsable=self.cliente,
        )

        # Crear plan de almuerzo
        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Estándar",
            descripcion="Almuerzo estándar",
            precio_mensual=Decimal("450000.00"),
            dias_semana_incluidos="Lunes-Viernes",
            activo=True,
        )

    def test_serializar_suscripcion_completa(self):
        """Test de serialización de una suscripción completa"""
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=timezone.now().date(),
            fecha_fin=(timezone.now() + timezone.timedelta(days=30)).date(),
            estado="activa",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )

        serializer = SuscripcionesAlmuerzoSerializer(suscripcion)
        data = serializer.data

        self.assertEqual(data["estado"], "activa")
        self.assertEqual(data["hijo_nombre"], "Lucía")
        self.assertEqual(data["plan_nombre"], "Plan Estándar")

    def test_validar_suscripcion_valida(self):
        """Test de validación de datos válidos de suscripción"""
        data = {
            "fecha_inicio": timezone.now().date().isoformat(),
            "fecha_fin": (timezone.now() + timezone.timedelta(days=30)).date().isoformat(),
            "estado": "activa",
            "id_hijo": self.hijo.id_hijo,
            "id_plan_almuerzo": self.plan.id_plan_almuerzo,
        }

        serializer = SuscripcionesAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_suscripcion_sin_hijo_invalida(self):
        """Test que valida que una suscripción sin hijo es inválida"""
        data = {
            "fecha_inicio": timezone.now().date().isoformat(),
            "estado": "activa",
            "id_plan_almuerzo": self.plan.id_plan_almuerzo,
        }

        serializer = SuscripcionesAlmuerzoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("id_hijo", serializer.errors)

    def test_validar_suscripcion_sin_plan_invalida(self):
        """Test que valida que una suscripción sin plan es inválida"""
        data = {
            "fecha_inicio": timezone.now().date().isoformat(),
            "estado": "activa",
            "id_hijo": self.hijo.id_hijo,
        }

        serializer = SuscripcionesAlmuerzoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("id_plan_almuerzo", serializer.errors)

    def test_crear_suscripcion_desde_serializer(self):
        """Test de creación de suscripción usando el serializer"""
        data = {
            "fecha_inicio": timezone.now().date().isoformat(),
            "fecha_fin": (timezone.now() + timezone.timedelta(days=60)).date().isoformat(),
            "estado": "activa",
            "id_hijo": self.hijo.id_hijo,
            "id_plan_almuerzo": self.plan.id_plan_almuerzo,
        }

        serializer = SuscripcionesAlmuerzoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        suscripcion = serializer.save()
        self.assertIsNotNone(suscripcion.id_suscripcion)
        self.assertEqual(suscripcion.estado, "activa")
