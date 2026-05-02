"""
Tests para serializers de la app clientes
Sprint 2 - Backend Coverage Improvement
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import Clientes, Hijos, TiposCliente
from .serializers import ClientesSerializer, HijosSerializer
from apps.productos.models import ListasPrecios


class ClientesSerializerTest(TestCase):
    """Tests para ClientesSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Minorista", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

    def test_serializar_cliente_completo(self):
        """Test de serialización de un cliente con todos los campos"""
        cliente = Clientes.objects.create(
            nombres="Juan Carlos",
            apellidos="Pérez González",
            ruc_ci="1234567890",
            direccion="Av. Principal 123",
            ciudad="Asunción",
            telefono="0981234567",
            email="juan.perez@example.com",
            limite_credito=Decimal("5000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        serializer = ClientesSerializer(cliente)
        data = serializer.data

        self.assertEqual(data["nombres"], "Juan Carlos")
        self.assertEqual(data["apellidos"], "Pérez González")
        self.assertEqual(data["ruc_ci"], "1234567890")
        self.assertEqual(data["direccion"], "Av. Principal 123")
        self.assertEqual(data["email"], "juan.perez@example.com")
        self.assertEqual(Decimal(data["limite_credito"]), Decimal("5000.00"))
        self.assertTrue(data["estado"])

    def test_validar_cliente_valido(self):
        """Test de validación de datos válidos de cliente"""
        data = {
            "nombres": "María",
            "apellidos": "López",
            "ruc_ci": "9876543210",
            "direccion": "Calle Secundaria 456",
            "ciudad": "San Lorenzo",
            "telefono": "0987654321",
            "email": "maria.lopez@example.com",
            "limite_credito": "3000.00",
            "estado": True,
            "id_lista": self.lista.id_lista,
            "id_tipo_cliente": self.tipo_cliente.id_tipo_cliente,
        }

        serializer = ClientesSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_cliente_sin_nombres_invalido(self):
        """Test que valida que un cliente sin nombres es inválido"""
        data = {
            "apellidos": "González",
            "ruc_ci": "5555555555",
            "id_lista": self.lista.id_lista,
            "id_tipo_cliente": self.tipo_cliente.id_tipo_cliente,
        }

        serializer = ClientesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("nombres", serializer.errors)

    def test_validar_cliente_sin_ruc_ci_invalido(self):
        """Test que valida que un cliente sin RUC/CI es inválido"""
        data = {
            "nombres": "Pedro",
            "apellidos": "Ramírez",
            "id_lista": self.lista.id_lista,
            "id_tipo_cliente": self.tipo_cliente.id_tipo_cliente,
        }

        serializer = ClientesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ruc_ci", serializer.errors)

    def test_actualizar_cliente_parcialmente(self):
        """Test de actualización parcial de cliente"""
        cliente = Clientes.objects.create(
            nombres="Roberto",
            apellidos="Sánchez",
            ruc_ci="1111111111",
            limite_credito=Decimal("1000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

        data = {"limite_credito": "2000.00"}
        serializer = ClientesSerializer(cliente, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        cliente_actualizado = serializer.save()

        self.assertEqual(cliente_actualizado.limite_credito, Decimal("2000.00"))
        self.assertEqual(cliente_actualizado.nombres, "Roberto")  # No cambió

    def test_crear_cliente_desde_serializer(self):
        """Test de creación de cliente usando el serializer"""
        data = {
            "nombres": "Ana",
            "apellidos": "Martínez",
            "ruc_ci": "2222222222",
            "direccion": "Calle Nueva 789",
            "telefono": "0976543210",
            "limite_credito": "4000.00",
            "estado": True,
            "id_lista": self.lista.id_lista,
            "id_tipo_cliente": self.tipo_cliente.id_tipo_cliente,
        }

        serializer = ClientesSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        cliente = serializer.save()
        self.assertIsNotNone(cliente.id_cliente)
        self.assertEqual(cliente.nombres, "Ana")
        self.assertEqual(cliente.limite_credito, Decimal("4000.00"))

    def test_crear_cliente_sin_lista_asigna_general(self):
        """Test: Crear cliente sin id_lista asigna lista 'General' por defecto"""
        data = {
            "nombres": "Pedro",
            "apellidos": "González",
            "ruc_ci": "3333333333",
            "direccion": "Avenida Principal 456",
            "telefono": "0987654321",
            "limite_credito": "5000.00",
            "estado": True,
            "id_tipo_cliente": self.tipo_cliente.id_tipo_cliente,
            # NO incluye id_lista → debe asignar 'General' automáticamente
        }

        serializer = ClientesSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        cliente = serializer.save()
        self.assertIsNotNone(cliente.id_cliente)
        self.assertIsNotNone(cliente.id_lista)
        self.assertEqual(cliente.id_lista.nombre_lista, "General")
        self.assertEqual(cliente.id_lista.moneda, "PYG")
        self.assertTrue(cliente.id_lista.estado)


class HijosSerializerTest(TestCase):
    """Tests para HijosSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista Minorista", moneda="PYG", estado=True)

        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)

        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres="José",
            apellidos="Díaz",
            ruc_ci="3333333333",
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_serializar_hijo_completo(self):
        """Test de serialización de un hijo con todos los campos"""
        hijo = Hijos.objects.create(
            nombre="Sofía",
            apellido="Díaz",
            fecha_nacimiento="2015-03-15",
            grado="Primer Grado",
            estado=True,
            id_cliente_responsable=self.cliente,
        )

        serializer = HijosSerializer(hijo)
        data = serializer.data

        self.assertEqual(data["nombre"], "Sofía")
        self.assertEqual(data["apellido"], "Díaz")
        self.assertEqual(data["grado"], "Primer Grado")
        self.assertTrue(data["estado"])

    def test_validar_hijo_valido(self):
        """Test de validación de datos válidos de hijo"""
        data = {
            "nombre": "Lucas",
            "apellido": "Díaz",
            "fecha_nacimiento": "2016-07-20",
            "grado": "Segundo Grado",
            "estado": True,
            "id_cliente_responsable": self.cliente.id_cliente,
        }

        serializer = HijosSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_hijo_sin_nombre_invalido(self):
        """Test que valida que un hijo sin nombre es inválido"""
        data = {
            "apellido": "Díaz",
            "fecha_nacimiento": "2016-01-01",
            "grado": "Primer Grado",
            "id_cliente_responsable": self.cliente.id_cliente,
        }

        serializer = HijosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_validar_hijo_sin_cliente_invalido(self):
        """Test que valida que un hijo sin cliente es inválido"""
        data = {
            "nombre": "Miguel",
            "apellido": "García",
            "fecha_nacimiento": "2015-05-10",
            "grado": "Tercer Grado",
        }

        serializer = HijosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("id_cliente_responsable", serializer.errors)

    def test_crear_hijo_desde_serializer(self):
        """Test de creación de hijo usando el serializer"""
        data = {
            "nombre": "Isabella",
            "apellido": "Díaz",
            "fecha_nacimiento": "2017-11-25",
            "grado": "Kinder",
            "estado": True,
            "id_cliente_responsable": self.cliente.id_cliente,
        }

        serializer = HijosSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        hijo = serializer.save()
        self.assertIsNotNone(hijo.id_hijo)
        self.assertEqual(hijo.nombre, "Isabella")
        self.assertEqual(hijo.grado, "Kinder")
