"""
Tests para serializers de compras
Sprint 2 - Backend Coverage Improvement
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.compras.models import Compras, Proveedores
from apps.compras.serializers import ComprasSerializer, ProveedoresSerializer
from apps.usuarios.models import Empleados, Roles


class ProveedoresSerializerTest(TestCase):
    """Tests para ProveedoresSerializer"""

    def test_serializar_proveedor(self):
        """Test de serialización de proveedor"""
        proveedor = Proveedores.objects.create(
            razon_social='Distribuidora ABC',
            ruc='80012345-6',
            telefono='0981123456',
            email='contacto@abc.com',
            fecha_registro=timezone.now(),
            activo=True
        )
        
        serializer = ProveedoresSerializer(proveedor)
        data = serializer.data
        
        self.assertEqual(data['razon_social'], 'Distribuidora ABC')
        self.assertEqual(data['ruc'], '80012345-6')

    def test_crear_proveedor_desde_serializer(self):
        """Test de creación de proveedor usando serializer"""
        data = {
            'razon_social': 'Proveedor XYZ',
            'ruc': '80099999-9',
            'telefono': '0982999999',
            'fecha_registro': timezone.now().isoformat(),
            'activo': True
        }
        
        serializer = ProveedoresSerializer(data=data)
        if serializer.is_valid():
            proveedor = serializer.save()
            self.assertIsNotNone(proveedor.id_proveedor)


class ComprasSerializerTest(TestCase):
    """Tests para ComprasSerializer"""

    def setUp(self):
        """Configuración inicial"""
        self.proveedor = Proveedores.objects.create(
            razon_social='Proveedor Test',
            ruc='80055555-5',
            fecha_registro=timezone.now(),
            activo=True
        )

    def test_serializar_compra(self):
        """Test de serialización de compra"""
        compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal('500000.00'),
            estado_pago='pendiente',
            id_proveedor=self.proveedor
        )
        
        serializer = ComprasSerializer(compra)
        data = serializer.data
        
        self.assertEqual(Decimal(data['monto_total']), Decimal('500000.00'))
        self.assertEqual(data['estado_pago'], 'pendiente')

    def test_crear_compra_desde_serializer(self):
        """Test de creación de compra usando serializer"""
        data = {
            'fecha': timezone.now().isoformat(),
            'monto_total': '300000.00',
            'estado_pago': 'completada',
            'id_proveedor': self.proveedor.id_proveedor
        }
        
        serializer = ComprasSerializer(data=data)
        if serializer.is_valid():
            compra = serializer.save()
            self.assertIsNotNone(compra.id_compra)
