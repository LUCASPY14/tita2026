"""
Tests para serializers de la app core
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal
from unittest.mock import Mock

from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios

from .models import CargasSaldo, MediosPago, Tarjetas
from .serializers import CargasSaldoSerializer, MediosPagoSerializer, TarjetasSerializer


class TarjetasSerializerTest(TestCase):
    """Tests para TarjetasSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Estudiantes", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="Carlos",
            apellidos="Ramírez",
            ruc_ci="4444444444",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre="Martín",
            apellido="Ramírez",
            fecha_nacimiento="2014-06-10",
            grado="Cuarto Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

    def test_serializar_tarjeta_completa(self):
        """Test de serialización de una tarjeta con todos los campos"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001",
            saldo_actual=Decimal("50000.00"),
            estado="ACTIVA",
            fecha_vencimiento="2025-12-31",
            saldo_alerta=Decimal("10000.00"),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
        )

        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data

        self.assertEqual(data["nro_tarjeta"], "T001")
        self.assertEqual(Decimal(data["saldo_actual"]), Decimal("50000.00"))
        self.assertEqual(data["estado"], "ACTIVA")
        self.assertFalse(data["permite_saldo_negativo"])
        self.assertTrue(data["notificar_saldo_bajo"])

    def test_serializar_saldo_disponible(self):
        """Test que el serializer incluye el campo saldo_disponible calculado"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T002",
            saldo_actual=Decimal("30000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal("20000.00"),
            id_hijo=self.hijo,
        )

        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data

        # saldo_disponible = saldo_actual + limite_credito cuando permite_saldo_negativo=True
        self.assertEqual(Decimal(data["saldo_disponible"]), Decimal("50000.00"))

    def test_validar_tarjeta_valida(self):
        """Test de validación de datos válidos de tarjeta"""
        data = {
            "nro_tarjeta": "T003",
            "saldo_actual": "100000.00",
            "estado": "ACTIVA",
            "fecha_creacion": timezone.now().isoformat(),
            "permite_saldo_negativo": False,
            "limite_credito": "0.00",
            "notificar_saldo_bajo": True,
            "id_hijo": self.hijo.id_hijo,
        }

        serializer = TarjetasSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_get_hijo_foto_con_foto_y_request(self):
        """Test get_hijo_foto retorna URL absoluta cuando hay foto y request en context"""
        # Crear hijo con foto_perfil mockeada
        hijo_con_foto = Hijos.objects.create(
            nombre="Pedro",
            apellido="García",
            fecha_nacimiento="2013-03-15",
            grado="Quinto Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="TFOTO001",
            saldo_actual=Decimal("40000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=hijo_con_foto,
        )

        # Mockear foto_perfil en el hijo
        mock_foto = Mock()
        mock_foto.url = "/media/fotos/test.jpg"
        hijo_con_foto.foto_perfil = mock_foto

        # Crear request mock
        factory = RequestFactory()
        request = factory.get("/api/tarjetas/")

        # Serializar con request en context
        serializer = TarjetasSerializer(tarjeta, context={"request": request})
        data = serializer.data

        # Debe retornar URL absoluta
        self.assertIsNotNone(data["hijo_foto"])
        self.assertIn("http", data["hijo_foto"])
        self.assertIn("/media/fotos/test.jpg", data["hijo_foto"])

    def test_get_hijo_foto_con_foto_sin_request(self):
        """Test get_hijo_foto retorna URL relativa cuando hay foto pero no request"""
        hijo_con_foto = Hijos.objects.create(
            nombre="Ana",
            apellido="López",
            fecha_nacimiento="2012-08-20",
            grado="Sexto Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="TFOTO002",
            saldo_actual=Decimal("35000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=hijo_con_foto,
        )

        # Mockear foto_perfil
        mock_foto = Mock()
        mock_foto.url = "/media/fotos/ana.jpg"
        hijo_con_foto.foto_perfil = mock_foto

        # Serializar SIN request en context
        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data

        # Debe retornar URL relativa
        self.assertEqual(data["hijo_foto"], "/media/fotos/ana.jpg")

    def test_get_hijo_foto_sin_foto(self):
        """Test get_hijo_foto retorna None cuando el hijo no tiene foto"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta="TNOFOTO",
            saldo_actual=Decimal("25000.00"),
            estado="ACTIVA",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            id_hijo=self.hijo,  # self.hijo no tiene foto_perfil
        )

        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data

        # Debe retornar None
        self.assertIsNone(data["hijo_foto"])

    def test_validar_tarjeta_sin_nro_invalida(self):
        """Test que valida que una tarjeta sin número es inválida"""
        data = {
            "saldo_actual": "50000.00",
            "estado": "ACTIVA",
            "fecha_creacion": timezone.now().isoformat(),
            "id_hijo": self.hijo.id_hijo,
        }

        serializer = TarjetasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("nro_tarjeta", serializer.errors)

    def test_validar_tarjeta_sin_hijo_invalida(self):
        """Test que valida que una tarjeta sin hijo es inválida"""
        data = {
            "nro_tarjeta": "T004",
            "saldo_actual": "25000.00",
            "estado": "ACTIVA",
            "fecha_creacion": timezone.now().isoformat(),
        }

        serializer = TarjetasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("id_hijo", serializer.errors)


class MediosPagoSerializerTest(TestCase):
    """Tests para MediosPagoSerializer"""

    def test_serializar_medio_pago_completo(self):
        """Test de serialización de un medio de pago con todos los campos"""
        medio = MediosPago.objects.create(
            descripcion="Efectivo", genera_comision=False, requiere_validacion=False, estado=True
        )

        serializer = MediosPagoSerializer(medio)
        data = serializer.data

        self.assertEqual(data["descripcion"], "Efectivo")
        self.assertFalse(data["genera_comision"])
        self.assertFalse(data["requiere_validacion"])
        self.assertTrue(data["estado"])

    def test_serializar_medio_pago_con_comision(self):
        """Test de serialización de un medio de pago que genera comisión"""
        medio = MediosPago.objects.create(
            descripcion="Tarjeta de Crédito",
            genera_comision=True,
            requiere_validacion=True,
            estado=True,
        )

        serializer = MediosPagoSerializer(medio)
        data = serializer.data

        self.assertEqual(data["descripcion"], "Tarjeta de Crédito")
        self.assertTrue(data["genera_comision"])
        self.assertTrue(data["requiere_validacion"])

    def test_validar_medio_pago_valido(self):
        """Test de validación de datos válidos de medio de pago"""
        data = {
            "descripcion": "Transferencia Bancaria",
            "genera_comision": False,
            "requiere_validacion": True,
            "estado": True,
        }

        serializer = MediosPagoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_medio_pago_sin_descripcion_invalido(self):
        """Test que valida que un medio de pago sin descripción es inválido"""
        data = {"genera_comision": False, "requiere_validacion": False, "estado": True}

        serializer = MediosPagoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("descripcion", serializer.errors)

    def test_crear_medio_pago_desde_serializer(self):
        """Test de creación de medio de pago usando el serializer"""
        data = {
            "descripcion": "QR Pago Móvil",
            "genera_comision": True,
            "requiere_validacion": True,
            "estado": True,
        }

        serializer = MediosPagoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        medio = serializer.save()
        self.assertIsNotNone(medio.id_medio_pago)
        self.assertEqual(medio.descripcion, "QR Pago Móvil")
        self.assertTrue(medio.genera_comision)

    def test_actualizar_medio_pago_parcialmente(self):
        """Test de actualización parcial de medio de pago"""
        medio = MediosPago.objects.create(
            descripcion="Cheque", genera_comision=False, requiere_validacion=True, estado=True
        )

        data = {"estado": False}
        serializer = MediosPagoSerializer(medio, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        medio_actualizado = serializer.save()

        self.assertFalse(medio_actualizado.estado)


class CargasSaldoSerializerTest(TestCase):
    """Tests for CargasSaldoSerializer missing except branches (lines 41-44, 48-51, 55-58)."""

    def setUp(self):
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Serializer", moneda="PYG", estado=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Carga",
            apellidos="Test",
            ruc_ci="9999999999",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_get_hijo_nombre_returns_none_when_no_tarjeta(self):
        """get_hijo_nombre returns None when nro_tarjeta is None (lines 41-44)."""
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("10000.00"),
            estado="pendiente",
            nro_tarjeta=None,
            id_cliente_origen=self.cliente,
        )
        serializer = CargasSaldoSerializer(carga)
        # nro_tarjeta is None → accessing id_hijo raises AttributeError → returns None
        self.assertIsNone(serializer.data["hijo_nombre"])

    def test_get_cajero_nombre_returns_none_when_no_responsable(self):
        """get_cajero_nombre returns None when usuario_responsable is None (lines 48-51)."""
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("10000.00"),
            estado="pendiente",
            nro_tarjeta=None,
            id_cliente_origen=self.cliente,
            usuario_responsable=None,
        )
        serializer = CargasSaldoSerializer(carga)
        self.assertIsNone(serializer.data["cajero_nombre"])

    def test_get_supervisor_nombre_returns_none_when_no_supervisor(self):
        """get_supervisor_nombre returns None when supervisor_aprobador is None (lines 55-58)."""
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("10000.00"),
            estado="pendiente",
            nro_tarjeta=None,
            id_cliente_origen=self.cliente,
            supervisor_aprobador=None,
        )
        serializer = CargasSaldoSerializer(carga)
        self.assertIsNone(serializer.data["supervisor_nombre"])
