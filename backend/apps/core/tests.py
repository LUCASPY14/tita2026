"""
Tests para la app core - Reglas de negocio de tarjetas prepago
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from apps.core.models import Tarjetas, CargasSaldo, ConsumosTarjeta, MediosPago
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


class TarjetasModelTest(TestCase):
    """Tests para el modelo Tarjetas y sus reglas de negocio"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(
            nombre_lista='Minorista',
            activo=True
        )
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo='Regular',
            activo=True
        )
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            ruc_ci='12345678',
            limite_credito=Decimal('500.00'),
            activo=True,
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente
        )
        
        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre='Pedro',
            apellido='Pérez',
            grado='5to',
            activo=True,
            id_cliente_responsable=self.cliente
        )
    
    def test_crear_tarjeta_exitosamente(self):
        """Test: Crear tarjeta con configuración correcta"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('100.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            saldo_alerta=Decimal('20.00'),
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        self.assertEqual(tarjeta.nro_tarjeta, 'T001')
        self.assertEqual(tarjeta.saldo_actual, Decimal('100.00'))
        self.assertFalse(tarjeta.permite_saldo_negativo)
        self.assertTrue(tarjeta.notificar_saldo_bajo)
    
    def test_tarjeta_unica_por_hijo(self):
        """Test: Un hijo solo puede tener una tarjeta"""
        # Primera tarjeta
        Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('100.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        # Intentar crear segunda tarjeta para el mismo hijo
        with self.assertRaises(ValidationError):
            tarjeta2 = Tarjetas(
                nro_tarjeta='T002',
                saldo_actual=Decimal('50.00'),
                estado='activa',
                fecha_creacion=timezone.now(),
                permite_saldo_negativo=False,
                limite_credito=Decimal('50.00'),
                notificar_saldo_bajo=True,
                id_hijo=self.hijo,  # Mismo hijo
                codigo_barras='BAR002'
            )
            tarjeta2.save()  # Debe fallar por signal validar_tarjeta_unica
    
    def test_saldo_disponible_sin_credito(self):
        """Test: Saldo disponible cuando NO permite saldo negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('100.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,  # NO permite negativo
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        # Saldo disponible = saldo actual (sin considerar crédito)
        self.assertEqual(tarjeta.saldo_disponible, Decimal('100.00'))
    
    def test_saldo_disponible_con_credito(self):
        """Test: Saldo disponible cuando permite saldo negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('100.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,  # SI permite negativo
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        # Saldo disponible = saldo actual + límite crédito
        self.assertEqual(tarjeta.saldo_disponible, Decimal('150.00'))
    
    def test_alerta_saldo_bajo_activada(self):
        """Test: Detectar cuando el saldo está bajo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('15.00'),  # Por debajo de la alerta
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            saldo_alerta=Decimal('20.00'),  # Alerta en 20
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        self.assertTrue(tarjeta.esta_en_alerta)
        self.assertTrue(tarjeta.requiere_notificacion)
    
    def test_alerta_saldo_bajo_no_activada(self):
        """Test: No alertar cuando el saldo es suficiente"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('50.00'),  # Por encima de la alerta
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True,
            saldo_alerta=Decimal('20.00'),
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        self.assertFalse(tarjeta.esta_en_alerta)
        self.assertFalse(tarjeta.requiere_notificacion)
    
    def test_notificacion_desactivada(self):
        """Test: No notificar cuando está desactivado"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001',
            saldo_actual=Decimal('15.00'),  # Bajo
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=False,  # Notificaciones desactivadas
            saldo_alerta=Decimal('20.00'),
            id_hijo=self.hijo,
            codigo_barras='BAR001'
        )
        
        self.assertTrue(tarjeta.esta_en_alerta)
        self.assertFalse(tarjeta.requiere_notificacion)  # No notifica


class CargasSaldoSignalTest(TestCase):
    """Tests para el signal de actualización de saldo en recargas"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear datos base (igual que TarjetasModelTest)
        self.lista = ListasPrecios.objects.create(nombre_lista='Minorista', activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo='Regular', activo=True)
        self.cliente = Clientes.objects.create(
            nombres='Juan', apellidos='Pérez', ruc_ci='12345678',
            limite_credito=Decimal('500.00'), activo=True,
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        self.hijo = Hijos.objects.create(
            nombre='Pedro', apellido='Pérez', grado='5to',
            activo=True, id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T001', saldo_actual=Decimal('50.00'),
            estado='activa', fecha_creacion=timezone.now(),
            permite_saldo_negativo=False, limite_credito=Decimal('50.00'),
            notificar_saldo_bajo=True, id_hijo=self.hijo, codigo_barras='BAR001'
        )
    
    def test_recarga_confirmada_actualiza_saldo(self):
        """Test: Signal actualiza saldo cuando recarga se confirma"""
        saldo_inicial = self.tarjeta.saldo_actual
        
        # Crear recarga confirmada
        recarga = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal('100.00'),
            referencia='TEST-001',
            estado='confirmado',  # Estado confirmado activa el signal
            fecha_confirmacion=timezone.now()
        )
        
        # Refrescar tarjeta desde BD
        self.tarjeta.refresh_from_db()
        
        # Verificar que el saldo aumentó
        self.assertEqual(
            self.tarjeta.saldo_actual,
            saldo_inicial + Decimal('100.00')
        )
        
        # Verificar que se registró en historial de consumos
        consumo = ConsumosTarjeta.objects.filter(
            nro_tarjeta=self.tarjeta,
            detalle__contains=f'Recarga #{recarga.id_carga}'
        ).first()
        
        self.assertIsNotNone(consumo)
        self.assertEqual(consumo.monto_consumido, -Decimal('100.00'))  # Negativo = ingreso
    
    def test_recarga_pendiente_no_actualiza_saldo(self):
        """Test: Recarga en estado pendiente NO actualiza saldo"""
        saldo_inicial = self.tarjeta.saldo_actual
        
        # Crear recarga pendiente
        CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal('100.00'),
            referencia='TEST-002',
            estado='pendiente'  # No confirmado
        )
        
        # Refrescar tarjeta
        self.tarjeta.refresh_from_db()
        
        # El saldo NO debe cambiar
        self.assertEqual(self.tarjeta.saldo_actual, saldo_inicial)


class MediosPagoTest(TestCase):
    """Tests para configuración de medios de pago"""
    
    def test_medio_pago_con_comision(self):
        """Test: Medio de pago con comisión configurada"""
        medio = MediosPago.objects.create(
            descripcion='Tarjeta Crédito',
            genera_comision=True,  # BooleanField
            requiere_validacion=True,  # BooleanField
            activo=True
        )
        
        self.assertTrue(medio.genera_comision)
        self.assertTrue(medio.requiere_validacion)
    
    def test_medio_pago_efectivo(self):
        """Test: Efectivo sin comisión"""
        medio = MediosPago.objects.create(
            descripcion='Efectivo',
            genera_comision=False,
            requiere_validacion=False,
            activo=True
        )
        
        self.assertFalse(medio.genera_comision)
        self.assertFalse(medio.requiere_validacion)
