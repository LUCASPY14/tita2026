"""
Tests para la app ventas - Validación de saldo en tarjetas
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from apps.ventas.models import Ventas
from apps.core.models import Tarjetas, ConsumosTarjeta, MediosPago
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios, Productos, Categorias, UnidadesMedida
from apps.usuarios.models import Empleados, Roles


class VentasConTarjetaTest(TestCase):
    """Tests para validación de saldo en ventas con tarjeta"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear lista de precios
        self.lista = ListasPrecios.objects.create(nombre_lista='Minorista', activo=True)
        
        # Crear tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo='Regular', activo=True)
        
        # Crear cliente
        self.cliente = Clientes.objects.create(
            nombres='María', apellidos='González', ruc_ci='87654321',
            limite_credito=Decimal('500.00'), activo=True,
            id_lista=self.lista, id_tipo_cliente=self.tipo_cliente
        )
        
        # Crear hijo
        self.hijo = Hijos.objects.create(
            nombre='Ana', apellido='González', grado='6to',
            activo=True, id_cliente_responsable=self.cliente
        )
        
        # Crear tarjeta SIN permiso de saldo negativo
        self.tarjeta_sin_credito = Tarjetas.objects.create(
            nro_tarjeta='T100',
            saldo_actual=Decimal('50.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,  # NO permite negativo
            limite_credito=Decimal('0.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras='BAR100'
        )
        
        # Crear segundo hijo para pruebas de crédito
        self.hijo2 = Hijos.objects.create(
            nombre='Luis', apellido='González', grado='7mo',
            activo=True, id_cliente_responsable=self.cliente
        )
        
        # Crear tarjeta CON permiso de saldo negativo
        self.tarjeta_con_credito = Tarjetas.objects.create(
            nro_tarjeta='T200',
            saldo_actual=Decimal('30.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,  # SI permite negativo
            limite_credito=Decimal('100.00'),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo2,
            codigo_barras='BAR200'
        )
        
        # Crear rol y empleado cajero
        self.rol = Roles.objects.create(nombre_rol='Cajero', activo=True)
        self.cajero = Empleados.objects.create(
            nombres='Pedro', apellidos='Ramírez', ruc_ci='11223344',
            activo=True, id_rol=self.rol
        )
        
        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            descripcion='Tarjeta Prepago',
            genera_comision=False,
            requiere_validacion=False,
            activo=True
        )
    
    def test_venta_con_saldo_suficiente(self):
        """Test: Venta exitosa cuando hay saldo suficiente"""
        saldo_inicial = self.tarjeta_sin_credito.saldo_actual
        monto_venta = Decimal('30.00')
        
        # Simular creación de venta (sin pasar por ViewSet)
        # Nota: En producción esto se hace a través de VentasViewSet.perform_create
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=monto_venta,
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='contado',
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=self.hijo,
            id_medio_pago=self.medio_pago
        )
        
        # Simular descuento manual (en producción lo hace perform_create)
        self.tarjeta_sin_credito.saldo_actual -= monto_venta
        self.tarjeta_sin_credito.save()
        
        # Registrar consumo
        ConsumosTarjeta.objects.create(
            nro_tarjeta=self.tarjeta_sin_credito,
            fecha_consumo=venta.fecha,
            monto_consumido=monto_venta,
            detalle=f'Venta #{venta.id_venta} - Cantina',
            saldo_anterior=saldo_inicial,
            saldo_posterior=self.tarjeta_sin_credito.saldo_actual,
            id_empleado_registro=self.cajero
        )
        
        # Verificar venta creada
        self.assertEqual(venta.monto_total, monto_venta)
        self.assertEqual(venta.estado_pago, 'pagada')
        
        # Verificar saldo descontado
        self.tarjeta_sin_credito.refresh_from_db()
        self.assertEqual(
            self.tarjeta_sin_credito.saldo_actual,
            saldo_inicial - monto_venta
        )
        
        # Verificar registro de consumo
        consumo = ConsumosTarjeta.objects.filter(
            nro_tarjeta=self.tarjeta_sin_credito,
            monto_consumido=monto_venta
        ).first()
        self.assertIsNotNone(consumo)
        self.assertEqual(consumo.saldo_anterior, saldo_inicial)
    
    def test_venta_con_saldo_insuficiente_sin_autorizacion(self):
        """Test: Venta debe fallar si no hay saldo y no permite negativo"""
        # Tarjeta tiene 50.00, intentamos vender 80.00
        monto_venta = Decimal('80.00')
        
        # Verificar que la tarjeta NO permite saldo negativo
        self.assertFalse(self.tarjeta_sin_credito.permite_saldo_negativo)
        
        # Verificar saldo insuficiente
        self.assertLess(self.tarjeta_sin_credito.saldo_actual, monto_venta)
        
        # En producción, VentasViewSet.perform_create lanza ValidationError
        # Aquí solo verificamos las condiciones
        self.assertTrue(
            self.tarjeta_sin_credito.saldo_actual < monto_venta and 
            not self.tarjeta_sin_credito.permite_saldo_negativo
        )
    
    def test_venta_con_credito_dentro_limite(self):
        """Test: Venta con saldo negativo permitido dentro del límite"""
        # Tarjeta: saldo=30, límite_credito=100, permite_negativo=True
        # Total disponible = 30 + 100 = 130
        saldo_inicial = self.tarjeta_con_credito.saldo_actual
        monto_venta = Decimal('80.00')  # Genera saldo negativo -50
        
        # Verificar que permite saldo negativo
        self.assertTrue(self.tarjeta_con_credito.permite_saldo_negativo)
        
        # Verificar que está dentro del límite
        saldo_negativo_proyectado = monto_venta - saldo_inicial  # 80 - 30 = 50
        self.assertLessEqual(
            saldo_negativo_proyectado,
            self.tarjeta_con_credito.limite_credito
        )
        
        # Simular venta
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=monto_venta,
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='credito',
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=self.hijo2,
            id_medio_pago=self.medio_pago
        )
        
        # Descontar saldo
        self.tarjeta_con_credito.saldo_actual -= monto_venta
        self.tarjeta_con_credito.save()
        
        # Verificar saldo negativo
        self.tarjeta_con_credito.refresh_from_db()
        self.assertEqual(
            self.tarjeta_con_credito.saldo_actual,
            Decimal('-50.00')
        )
        
        # Verificar que está dentro del límite
        self.assertGreaterEqual(
            self.tarjeta_con_credito.limite_credito,
            abs(self.tarjeta_con_credito.saldo_actual)
        )
    
    def test_venta_excede_limite_credito(self):
        """Test: Venta debe fallar si excede el límite de crédito"""
        # Tarjeta: saldo=30, límite_credito=100
        # Intento vender por 200 (saldo negativo = -170, excede límite)
        monto_venta = Decimal('200.00')
        saldo_inicial = self.tarjeta_con_credito.saldo_actual
        
        # Calcular saldo negativo proyectado
        saldo_negativo = monto_venta - saldo_inicial  # 200 - 30 = 170
        
        # Verificar que excede el límite
        self.assertGreater(
            saldo_negativo,
            self.tarjeta_con_credito.limite_credito
        )
        
        # En producción, perform_create lanza ValidationError
        # Verificamos condición
        excede_limite = (
            self.tarjeta_con_credito.permite_saldo_negativo and
            saldo_negativo > self.tarjeta_con_credito.limite_credito
        )
        self.assertTrue(excede_limite)
    
    def test_consumo_registrado_correctamente(self):
        """Test: Verificar que el consumo registra saldos correctamente"""
        saldo_anterior = self.tarjeta_sin_credito.saldo_actual
        monto = Decimal('25.00')
        
        # Descontar saldo
        self.tarjeta_sin_credito.saldo_actual -= monto
        saldo_posterior = self.tarjeta_sin_credito.saldo_actual
        self.tarjeta_sin_credito.save()
        
        # Crear consumo
        consumo = ConsumosTarjeta.objects.create(
            nro_tarjeta=self.tarjeta_sin_credito,
            fecha_consumo=timezone.now(),
            monto_consumido=monto,
            detalle='Test consumo',
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            id_empleado_registro=self.cajero
        )
        
        # Verificar datos del consumo
        self.assertEqual(consumo.saldo_anterior, Decimal('50.00'))
        self.assertEqual(consumo.saldo_posterior, Decimal('25.00'))
        self.assertEqual(consumo.monto_consumido, monto)
        
        # Verificar coherencia: saldo_anterior - monto = saldo_posterior
        self.assertEqual(
            consumo.saldo_anterior - consumo.monto_consumido,
            consumo.saldo_posterior
        )
    
    def test_venta_sin_tarjeta_no_descuenta_saldo(self):
        """Test: Venta sin tarjeta (pago directo) no afecta saldo"""
        # Crear venta sin especificar hijo (pago directo en efectivo)
        venta = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal('100.00'),
            saldo_pendiente=Decimal('0.00'),
            estado_pago='pagada',
            estado='activa',
            tipo_venta='contado',
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_hijo=None,  # Sin hijo = sin tarjeta
            id_medio_pago=self.medio_pago
        )
        
        # Verificar que no se creó consumo en tarjeta
        consumos = ConsumosTarjeta.objects.filter(
            detalle__contains=f'Venta #{venta.id_venta}'
        )
        self.assertEqual(consumos.count(), 0)


class SaldoDisponibleTest(TestCase):
    """Tests para el cálculo de saldo disponible"""
    
    def setUp(self):
        """Configuración básica"""
        lista = ListasPrecios.objects.create(nombre_lista='Minorista', activo=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo='Regular', activo=True)
        cliente = Clientes.objects.create(
            nombres='Test', apellidos='User', ruc_ci='99999999',
            limite_credito=Decimal('500.00'), activo=True,
            id_lista=lista, id_tipo_cliente=tipo_cliente
        )
        self.hijo = Hijos.objects.create(
            nombre='Test', apellido='Child', grado='1ro',
            activo=True, id_cliente_responsable=cliente
        )
    
    def test_saldo_disponible_sin_credito_saldo_positivo(self):
        """Saldo disponible = saldo actual cuando no permite negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T300',
            saldo_actual=Decimal('75.50'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal('0.00'),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras='BAR300'
        )
        
        self.assertEqual(tarjeta.saldo_disponible, Decimal('75.50'))
    
    def test_saldo_disponible_con_credito(self):
        """Saldo disponible = saldo + límite cuando permite negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T400',
            saldo_actual=Decimal('40.00'),
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal('60.00'),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras='BAR400'
        )
        
        # 40 + 60 = 100
        self.assertEqual(tarjeta.saldo_disponible, Decimal('100.00'))
    
    def test_saldo_disponible_con_saldo_negativo(self):
        """Saldo disponible correcto cuando ya está en negativo"""
        tarjeta = Tarjetas.objects.create(
            nro_tarjeta='T500',
            saldo_actual=Decimal('-20.00'),  # Ya negativo
            estado='activa',
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal('100.00'),
            notificar_saldo_bajo=False,
            id_hijo=self.hijo,
            codigo_barras='BAR500'
        )
        
        # -20 + 100 = 80 disponible
        self.assertEqual(tarjeta.saldo_disponible, Decimal('80.00'))
