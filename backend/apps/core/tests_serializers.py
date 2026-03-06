"""
Tests para serializers de la app core
Sprint 2 - Backend Coverage Improvement
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from .models import Tarjetas, MediosPago
from .serializers import TarjetasSerializer, MediosPagoSerializer
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


class TarjetasSerializerTest(TestCase):
    """Tests para TarjetasSerializer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista='Lista Estudiantes',
            moneda='PYG',
            activo=True
        )
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Padre',
            activo=True
        )
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres='Carlos',
            apellidos='Ramírez',
            ruc_ci='4444444444',
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente
        )
        
        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre='Martín',
            apellido='Ramírez',
            fecha_nacimiento='2014-06-10',
            grado='Cuarto Grado',
            activo=True,
            id_cliente_responsable=self.cliente
        )

    def test_serializar_tarjeta_completa(self):
        """Test de serialización de una tarjeta con todos los campos"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('50000.00'),
            estado='ACTIVA',
            fecha_vencimiento='2025-12-31',
            saldo_alerta=Decimal('10000.00'),
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('0.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo
        )
        
        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data
        
        self.assertEqual(data['nro_tarjeta'], 'T001')
        self.assertEqual(Decimal(data['saldo_actual']), Decimal('50000.00'))
        self.assertEqual(data['estado'], 'ACTIVA')
        self.assertFalse(data['permite_saldo_negativo'])
        self.assertTrue(data['notificar_saldo_bajo'])

    def test_serializar_saldo_disponible(self):
        """Test que el serializer incluye el campo saldo_disponible calculado"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T002',
            saldo_actual=Decimal('30000.00'),
            estado='ACTIVA',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal('20000.00'),
            id_hijo=self.hijo
        )
        
        serializer = TarjetasSerializer(tarjeta)
        data = serializer.data
        
        # saldo_disponible = saldo_actual + limite_credito cuando permite_saldo_negativo=True
        self.assertEqual(Decimal(data['saldo_disponible']), Decimal('50000.00'))

    def test_validar_tarjeta_valida(self):
        """Test de validación de datos válidos de tarjeta"""
        data = {
            'nro_tarjeta': 'T003',
            'saldo_actual': '100000.00',
            'estado': 'ACTIVA',
            'fecha_creacion': timezone.now().isoformat(),
            'permite_saldo_negativo': False,
            'limite_credito': '0.00',
            'notificar_saldo_bajo': True,
            'id_hijo': self.hijo.id_hijo
        }
        
        serializer = TarjetasSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_tarjeta_sin_nro_invalida(self):
        """Test que valida que una tarjeta sin número es inválida"""
        data = {
            'saldo_actual': '50000.00',
            'estado': 'ACTIVA',
            'fecha_creacion': timezone.now().isoformat(),
            'id_hijo': self.hijo.id_hijo
        }
        
        serializer = TarjetasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nro_tarjeta', serializer.errors)

    def test_validar_tarjeta_sin_hijo_invalida(self):
        """Test que valida que una tarjeta sin hijo es inválida"""
        data = {
            'nro_tarjeta': 'T004',
            'saldo_actual': '25000.00',
            'estado': 'ACTIVA',
            'fecha_creacion': timezone.now().isoformat()
        }
        
        serializer = TarjetasSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('id_hijo', serializer.errors)


class MediosPagoSerializerTest(TestCase):
    """Tests para MediosPagoSerializer"""

    def test_serializar_medio_pago_completo(self):
        """Test de serialización de un medio de pago con todos los campos"""
        medio = MediosPago.objects.create(
            descripcion='Efectivo',
            genera_comision=False,
            requiere_validacion=False,
            activo=True
        )
        
        serializer = MediosPagoSerializer(medio)
        data = serializer.data
        
        self.assertEqual(data['descripcion'], 'Efectivo')
        self.assertFalse(data['genera_comision'])
        self.assertFalse(data['requiere_validacion'])
        self.assertTrue(data['activo'])

    def test_serializar_medio_pago_con_comision(self):
        """Test de serialización de un medio de pago que genera comisión"""
        medio = MediosPago.objects.create(
            descripcion='Tarjeta de Crédito',
            genera_comision=True,
            requiere_validacion=True,
            activo=True
        )
        
        serializer = MediosPagoSerializer(medio)
        data = serializer.data
        
        self.assertEqual(data['descripcion'], 'Tarjeta de Crédito')
        self.assertTrue(data['genera_comision'])
        self.assertTrue(data['requiere_validacion'])

    def test_validar_medio_pago_valido(self):
        """Test de validación de datos válidos de medio de pago"""
        data = {
            'descripcion': 'Transferencia Bancaria',
            'genera_comision': False,
            'requiere_validacion': True,
            'activo': True
        }
        
        serializer = MediosPagoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validar_medio_pago_sin_descripcion_invalido(self):
        """Test que valida que un medio de pago sin descripción es inválido"""
        data = {
            'genera_comision': False,
            'requiere_validacion': False,
            'activo': True
        }
        
        serializer = MediosPagoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('descripcion', serializer.errors)

    def test_crear_medio_pago_desde_serializer(self):
        """Test de creación de medio de pago usando el serializer"""
        data = {
            'descripcion': 'QR Pago Móvil',
            'genera_comision': True,
            'requiere_validacion': True,
            'activo': True
        }
        
        serializer = MediosPagoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        medio = serializer.save()
        self.assertIsNotNone(medio.id_medio_pago)
        self.assertEqual(medio.descripcion, 'QR Pago Móvil')
        self.assertTrue(medio.genera_comision)

    def test_actualizar_medio_pago_parcialmente(self):
        """Test de actualización parcial de medio de pago"""
        medio = MediosPago.objects.create(
            descripcion='Cheque',
            genera_comision=False,
            requiere_validacion=True,
            activo=True
        )
        
        data = {'activo': False}
        serializer = MediosPagoSerializer(medio, data=data, partial=True)
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        medio_actualizado = serializer.save()
        
        self.assertFalse(medio_actualizado.activo)
        self.assertEqual(medio_actualizado.descripcion, 'Cheque')  # No cambió
