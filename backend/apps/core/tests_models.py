"""
Tests para modelos de la app core
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios

from .models import CargasSaldo, Tarjetas


class TarjetasModelTest(TestCase):
    """Tests para el modelo Tarjetas y sus propiedades calculadas"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Estudiantes", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Patricia",
            apellidos="Benítez",
            ruc_ci="7777777777",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Diego",
            apellido="Benítez",
            fecha_nacimiento=timezone.datetime(2013, 8, 15).date(),
            grado="Sexto Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

    def test_saldo_disponible_sin_credito(self):
        """Test de saldo_disponible cuando no permite saldo negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T100",
            saldo_actual=Decimal("50000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        # Cuando no permite saldo negativo, saldo_disponible = saldo_actual
        self.assertEqual(tarjeta.saldo_disponible, Decimal("50000.00"))

    def test_saldo_disponible_con_credito(self):
        """Test de saldo_disponible cuando permite saldo negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T101",
            saldo_actual=Decimal("30000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal("20000.00"),
            id_hijo=self.hijo,
        )

        # Cuando permite saldo negativo, saldo_disponible = saldo_actual + limite_credito
        # 30000 + 20000 = 50000
        self.assertEqual(tarjeta.saldo_disponible, Decimal("50000.00"))

    def test_saldo_disponible_negativo(self):
        """Test de saldo_disponible con saldo actual negativo pero sin permitir crédito"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T102",
            saldo_actual=Decimal("-5000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        # Cuando no permite saldo negativo, el mínimo es 0
        self.assertEqual(tarjeta.saldo_disponible, Decimal("0.00"))

    def test_esta_en_alerta_true(self):
        """Test de esta_en_alerta cuando el saldo está por debajo del nivel de alerta"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T103",
            saldo_actual=Decimal("8000.00"),
            estado="ACTIVA",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        self.assertTrue(tarjeta.esta_en_alerta)

    def test_esta_en_alerta_false(self):
        """Test de esta_en_alerta cuando el saldo está por encima del nivel de alerta"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T104",
            saldo_actual=Decimal("15000.00"),
            estado="ACTIVA",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        self.assertFalse(tarjeta.esta_en_alerta)

    def test_esta_en_alerta_sin_saldo_alerta(self):
        """Test de esta_en_alerta cuando no hay saldo de alerta configurado"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T105",
            saldo_actual=Decimal("5000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        # Sin saldo_alerta configurado, no debe estar en alerta
        self.assertFalse(tarjeta.esta_en_alerta)

    def test_requiere_notificacion_true(self):
        """Test de requiere_notificacion cuando está en alerta y notificaciones activas"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T106",
            saldo_actual=Decimal("5000.00"),
            estado="ACTIVA",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
        )

        self.assertTrue(tarjeta.requiere_notificacion)

    def test_requiere_notificacion_false_notificaciones_desactivadas(self):
        """Test de requiere_notificacion cuando notificaciones están desactivadas"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T107",
            saldo_actual=Decimal("5000.00"),
            estado="ACTIVA",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
        )

        self.assertFalse(tarjeta.requiere_notificacion)

    def test_requiere_notificacion_false_saldo_normal(self):
        """Test de requiere_notificacion cuando el saldo está normal"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T108",
            saldo_actual=Decimal("20000.00"),
            estado="ACTIVA",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
        )

        self.assertFalse(tarjeta.requiere_notificacion)

    def test_str_method(self):
        """Test del método __str__"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T109",
            saldo_actual=Decimal("25000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,
        )

        expected = f"Tarjeta T109 - {self.hijo}"
        self.assertEqual(str(tarjeta), expected)


class CargasSaldoModelTest(TestCase):
    """Tests para propiedades alias de CargasSaldo."""

    def test_codigo_referencia_alias(self):
        """codigo_referencia es alias de custom_identifier."""
        from django.utils import timezone as tz

        carga = CargasSaldo.objects.create(
            fecha_carga=tz.now(),
            monto_cargado=Decimal("50000"),
            estado="Completado",
            custom_identifier="REF-2026-001",
        )
        self.assertEqual(carga.codigo_referencia, "REF-2026-001")
