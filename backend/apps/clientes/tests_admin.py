"""
Tests complementarios para admin de clientes
Sprint 2 - Backend Coverage Improvement
"""

from decimal import Decimal

from django.contrib import admin
from django.test import TestCase
from django.utils import timezone

from apps.clientes.admin import ClientesAdmin
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


class ClientesAdminTest(TestCase):
    """Tests básicos para ClientesAdmin"""

    def setUp(self):
        """Configuración inicial"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Lista General", moneda="PYG", estado=True)

        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="1234567890",
            limite_credito=Decimal("500000.00"),
            estado=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_admin_registered(self):
        """Test que ClientesAdmin está registrado"""
        self.assertTrue(admin.site.is_registered(Clientes))

    def test_list_display(self):
        """Test que list_display está configurado"""
        admin_instance = ClientesAdmin(Clientes, admin.site)
        self.assertTrue(hasattr(admin_instance, "list_display"))


class HijosAdminTest(TestCase):
    """Tests básicos para HijosAdmin"""

    def setUp(self):
        """Configuración inicial"""
        lista = ListasPrecios.objects.create(nombre_lista="Lista", moneda="PYG", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Roberto",
            apellidos="Silva",
            ruc_ci="5555555555",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        self.hijo = Hijos.objects.create(
            nombre="Carlos",
            apellido="Silva",
            fecha_nacimiento=timezone.datetime(2010, 5, 15).date(),
            grado="Octavo",
            estado=True,
            id_cliente_responsable=cliente,
        )

    def test_admin_registered(self):
        """Test que HijosAdmin está registrado"""
        self.assertTrue(admin.site.is_registered(Hijos))
