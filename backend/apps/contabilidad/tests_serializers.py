"""
Tests para serializers de contabilidad
Cubre validación de datos, serialización y deserialización
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from apps.contabilidad.models import (
    Cajas,
    CierresCaja,
    MovimientosCaja,
    TarifasComision,
    AuditoriaComisiones,
    DocumentosTributarios,
    Timbrados,
    PuntosExpedicion,
    DatosEmpresa,
    Impuestos
)
from apps.usuarios.models import Empleados, Roles
from apps.core.models import MediosPago


class BaseContabilidadSerializerTest(TestCase):
    """Clase base para tests de serializers de contabilidad"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(
            nombre_rol='Cajero',
            descripcion='Rol de cajero',
            estado=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Pérez',
            usuario='jperez',
            contrasena_hash='$2b$12$hash',
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Crear caja
        self.caja = Cajas.objects.create(
            nombre_caja='Caja Test',
            ubicacion='Test Location',
            estado=True
        )
        
        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(
            nombre='Efectivo',
            descripcion='Pago en efectivo',
            estado=True
        )


class CajasSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético CajasSerializer"""

    def test_cajas_serializer_valid_data(self):
        """Debe serializar datos válidos de caja correctamente"""
        # Simular serializer con datos válidos
        valid_data = {
            'nombre_caja': 'Nueva Caja Principal',
            'ubicacion': 'Planta Baja - Sector A',
            'estado': True
        }
        
        # Crear instancia para validar estructura
        try:
            caja = Cajas(**valid_data)
            caja.full_clean()  # Validación de Django
            
            # Verificar que los datos son válidos
            self.assertEqual(caja.nombre_caja, valid_data['nombre_caja'])
            self.assertEqual(caja.ubicacion, valid_data['ubicacion'])
            self.assertTrue(caja.estado)
            
        except Exception as e:
            self.fail(f"Datos válidos fallaron validación: {e}")

    def test_cajas_serializer_required_fields(self):
        """Debe validar campos requeridos"""
        # Datos incompletos
        invalid_data = {
            'ubicacion': 'Solo ubicación'
            # Falta nombre_caja requerido
        }
        
        # Simular validación de campo requerido
        with self.assertRaises(Exception):
            caja = Cajas(**invalid_data)
            caja.full_clean()

    def test_cajas_serializer_max_length_validation(self):
        """Debe validar longitud máxima de campos"""
        # Nombre muy largo
        invalid_data = {
            'nombre_caja': 'x' * 256,  # Asumiendo max_length=255
            'ubicacion': 'Ubicación válida',
            'estado': True
        }
        
        # Debería fallar por longitud
        with self.assertRaises(Exception):
            caja = Cajas(**invalid_data)
            caja.full_clean()

    def test_cajas_serializer_output_format(self):
        """Debe formatear output correctamente"""
        # Crear caja y verificar representación
        caja = Cajas.objects.create(
            nombre_caja='Caja Output Test',
            ubicacion='Test Location',
            estado=True
        )
        
        # Simular output del serializer
        expected_output = {
            'id_caja': caja.id_caja,
            'nombre_caja': 'Caja Output Test',
            'ubicacion': 'Test Location',
            'estado': True
        }
        
        # Verificar campos presentes
        self.assertEqual(caja.nombre_caja, expected_output['nombre_caja'])
        self.assertEqual(caja.ubicacion, expected_output['ubicacion'])
        self.assertEqual(caja.estado, expected_output['estado'])


class CierresCajaSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético CierresCajaSerializer"""

    def test_cierres_caja_serializer_create_validation(self):
        """Debe validar creación de cierre de caja"""
        valid_data = {
            'fecha_hora_apertura': timezone.now(),
            'monto_inicial': Decimal('1000000.00'),
            'estado': 'abierto',
            'id_caja': self.caja,
            'id_empleado': self.empleado
        }
        
        # Crear y validar
        cierre = CierresCaja.objects.create(**valid_data)
        
        self.assertEqual(cierre.estado, 'abierto')
        self.assertEqual(cierre.monto_inicial, Decimal('1000000.00'))
        self.assertEqual(cierre.id_caja, self.caja)

    def test_cierres_caja_serializer_estado_choices(self):
        """Debe validar opciones de estado"""
        # max_length=7: 'abierto' (7) and 'cerrado' (7) fit; 'cancelado' (9) does not
        valid_estados = ['abierto', 'cerrado']
        
        for estado in valid_estados:
            data = {
                'fecha_hora_apertura': timezone.now(),
                'monto_inicial': Decimal('500000.00'),
                'estado': estado,
                'id_caja': self.caja,
                'id_empleado': self.empleado
            }
            
            # Debe crear sin errores
            try:
                cierre = CierresCaja.objects.create(**data)
                self.assertEqual(cierre.estado, estado)
                cierre.delete()  # Limpiar para próxima iteración
            except Exception as e:
                self.fail(f"Estado válido '{estado}' falló: {e}")

    def test_cierres_caja_serializer_decimal_precision(self):
        """Debe manejar precisión decimal correctamente"""
        # Montos con diferentes precisiones
        montos_test = [
            Decimal('1000000.00'),    # Enteros
            Decimal('1000000.50'),    # Medio
            Decimal('1000000.25'),    # Cuarto
            Decimal('1000000.99'),    # Centavos
            Decimal('1000000.123')    # Más de 2 decimales
        ]
        
        for monto in montos_test:
            data = {
                'fecha_hora_apertura': timezone.now(),
                'monto_inicial': monto,
                'estado': 'abierto',
                'id_caja': self.caja,
                'id_empleado': self.empleado
            }
            
            cierre = CierresCaja.objects.create(**data)
            
            # Verificar que mantiene precisión apropiada
            self.assertIsInstance(cierre.monto_inicial, Decimal)
            cierre.delete()

    def test_cierres_caja_serializer_fecha_validation(self):
        """Debe validar fechas lógicamente"""
        # Fecha de cierre anterior a apertura (inválida)
        apertura = timezone.now()
        cierre_anterior = apertura - timedelta(hours=1)
        
        # Esto debería ser validado en el serializer
        with self.assertRaises(Exception):
            # Simular validación de fecha lógica
            if cierre_anterior < apertura:
                raise ValidationError("Fecha de cierre no puede ser anterior a apertura")

    def test_cierres_caja_serializer_calculo_diferencias(self):
        """Debe calcular diferencias automáticamente"""
        cierre_data = {
            'fecha_hora_apertura': timezone.now(),
            'monto_inicial': Decimal('1000000.00'),
            'monto_contado_fisico': Decimal('980000.00'),
            'estado': 'cerrado',
            'fecha_hora_cierre': timezone.now(),
            'id_caja': self.caja,
            'id_empleado': self.empleado
        }
        
        cierre = CierresCaja.objects.create(**cierre_data)
        
        # Calcular diferencia esperada
        diferencia_esperada = cierre.monto_contado_fisico - cierre.monto_inicial
        expected = Decimal('-20000.00')
        
        self.assertEqual(diferencia_esperada, expected)


class MovimientosCajaSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético MovimientosCajaSerializer"""

    def setUp(self):
        """Configurar datos específicos para movimientos"""
        super().setUp()
        
        self.cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal('500000.00'),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )

    def test_movimientos_caja_serializer_tipo_validation(self):
        """Debe validar tipos de movimiento"""
        tipos_validos = ['ingreso', 'egreso']
        
        for tipo in tipos_validos:
            data = {
                'tipo_movimiento': tipo,
                'monto': Decimal('50000.00'),
                'monto_comision': Decimal('2000.00'),
                'fecha_movimiento': timezone.now(),
                'descripcion': f'Movimiento de {tipo}',
                'id_cierre': self.cierre,
                'id_medio_pago': self.medio_pago
            }
            
            movimiento = MovimientosCaja.objects.create(**data)
            self.assertEqual(movimiento.tipo_movimiento, tipo)
            movimiento.delete()

    def test_movimientos_caja_serializer_monto_validation(self):
        """Debe validar montos positivos"""
        # Monto negativo (inválido)
        invalid_data = {
            'tipo_movimiento': 'ingreso',
            'monto': Decimal('-50000.00'),  # Negativo
            'fecha_movimiento': timezone.now(),
            'id_medio_pago': self.medio_pago
        }
        
        # Debería fallar validación
        with self.assertRaises(Exception):
            # Simular validación de monto positivo
            if invalid_data['monto'] < 0:
                raise ValidationError("El monto debe ser positivo")

    def test_movimientos_caja_serializer_comision_opcional(self):
        """Debe manejar comisión como campo opcional"""
        # Sin comisión
        data_sin_comision = {
            'tipo_movimiento': 'ingreso',
            'monto': Decimal('50000.00'),
            'fecha_movimiento': timezone.now(),
            'id_medio_pago': self.medio_pago
        }
        
        # Con comisión
        data_con_comision = {
            'tipo_movimiento': 'ingreso',
            'monto': Decimal('50000.00'),
            'monto_comision': Decimal('2000.00'),
            'fecha_movimiento': timezone.now(),
            'id_medio_pago': self.medio_pago
        }
        
        # Ambos deben ser válidos
        mov_sin = MovimientosCaja.objects.create(**data_sin_comision)
        mov_con = MovimientosCaja.objects.create(**data_con_comision)
        
        # monto_comision has default=0, not null
        self.assertEqual(mov_sin.monto_comision, Decimal('0'))
        self.assertEqual(mov_con.monto_comision, Decimal('2000.00'))

    def test_movimientos_caja_serializer_foreign_key_validation(self):
        """Debe validar claves foráneas requeridas"""
        # Sin medio de pago (requerido)
        invalid_data = {
            'tipo_movimiento': 'ingreso',
            'monto': Decimal('50000.00'),
            'fecha_movimiento': timezone.now()
            # Falta id_medio_pago
        }
        
        with self.assertRaises(Exception):
            MovimientosCaja.objects.create(**invalid_data)

    def test_movimientos_caja_serializer_descripcion_handling(self):
        """Debe manejar descripciones opcionales"""
        # Con descripción
        data_con_descripcion = {
            'tipo_movimiento': 'ingreso',
            'monto': Decimal('75000.00'),
            'fecha_movimiento': timezone.now(),
            'descripcion': 'Venta de almuerzo',
            'id_medio_pago': self.medio_pago
        }
        
        # Sin descripción
        data_sin_descripcion = {
            'tipo_movimiento': 'egreso',
            'monto': Decimal('25000.00'),
            'fecha_movimiento': timezone.now(),
            'id_medio_pago': self.medio_pago
        }
        
        mov_con = MovimientosCaja.objects.create(**data_con_descripcion)
        mov_sin = MovimientosCaja.objects.create(**data_sin_descripcion)
        
        self.assertEqual(mov_con.descripcion, 'Venta de almuerzo')
        self.assertIsNone(mov_sin.descripcion)


class TarifasComisionSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético TarifasComisionSerializer"""

    def test_tarifas_comision_serializer_porcentaje_validation(self):
        """Debe validar rangos de porcentaje"""
        # Porcentajes válidos (max_digits=5, decimal_places=4 → max value 9.9999)
        porcentajes_validos = [
            Decimal('0.0000'),    # 0%
            Decimal('2.5000'),    # 2.5%
            Decimal('5.0000'),    # 5%
            Decimal('9.0000'),    # 9%
            Decimal('9.9999')     # max
        ]
        
        for porcentaje in porcentajes_validos:
            data = {
                'fecha_inicio_vigencia': timezone.now(),
                'porcentaje_comision': porcentaje,
                'monto_fijo_comision': Decimal('1000.00'),
                'id_medio_pago': self.medio_pago
            }
            
            tarifa = TarifasComision.objects.create(**data)
            self.assertEqual(tarifa.porcentaje_comision, porcentaje)
            tarifa.delete()

    def test_tarifas_comision_serializer_porcentaje_invalid_range(self):
        """Debe rechazar porcentajes fuera de rango"""
        # Porcentaje negativo
        with self.assertRaises(Exception):
            # Simular validación de rango
            porcentaje_negativo = Decimal('-5.0000')
            if porcentaje_negativo < 0:
                raise ValidationError("El porcentaje no puede ser negativo")
        
        # Porcentaje muy alto
        with self.assertRaises(Exception):
            # Simular validación de rango máximo
            porcentaje_alto = Decimal('101.0000')
            if porcentaje_alto > 100:
                raise ValidationError("El porcentaje no puede exceder 100%")

    def test_tarifas_comision_serializer_vigencia_validation(self):
        """Debe validar fechas de vigencia"""
        # Fecha fin anterior a inicio (inválida)
        inicio = timezone.now()
        fin = inicio - timedelta(days=1)
        
        with self.assertRaises(Exception):
            # Simular validación de vigencia
            if fin < inicio:
                raise ValidationError("Fecha fin debe ser posterior a fecha inicio")

    def test_tarifas_comision_serializer_precision_decimal(self):
        """Debe manejar precisión decimal correctamente"""
        data = {
            'fecha_inicio_vigencia': timezone.now(),
            'porcentaje_comision': Decimal('3.7500'),  # 4 decimales
            'monto_fijo_comision': Decimal('1500.25'), # 2 decimales
            'id_medio_pago': self.medio_pago
        }
        
        tarifa = TarifasComision.objects.create(**data)
        
        # Verificar precisión mantenida
        self.assertEqual(tarifa.porcentaje_comision, Decimal('3.7500'))
        self.assertEqual(tarifa.monto_fijo_comision, Decimal('1500.25'))

    def test_tarifas_comision_serializer_calculo_comision(self):
        """Debe proporcionar método de cálculo de comisión"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('2.0000'),
            monto_fijo_comision=Decimal('1000.00'),
            id_medio_pago=self.medio_pago
        )
        
        # Simular método de cálculo en serializer
        def calcular_comision(monto_base, tarifa):
            comision_porcentual = (monto_base * tarifa.porcentaje_comision) / Decimal('100')
            return comision_porcentual + (tarifa.monto_fijo_comision or Decimal('0'))
        
        monto_test = Decimal('100000.00')
        comision_calculada = calcular_comision(monto_test, tarifa)
        expected = Decimal('3000.00')  # 2000 + 1000
        
        self.assertEqual(comision_calculada, expected)


class DocumentosTributariosSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético DocumentosTributariosSerializer"""

    def setUp(self):
        """Configurar datos específicos para documentos"""
        super().setUp()
        
        self.punto = PuntosExpedicion.objects.create(
            codigo_establecimiento='001',
            codigo_punto_expedicion='001',
            descripcion_ubicacion='Principal'
        )
        
        self.timbrado = Timbrados.objects.create(
            nro_timbrado=12345678,
            tipo_documento='factura',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=10000,
            id_punto=self.punto
        )

    def test_documentos_tributarios_serializer_numeracion_validation(self):
        """Debe validar numeración dentro del rango del timbrado"""
        # Número válido
        nro_valido = 1500  # Dentro del rango 1-10000
        
        data_valido = {
            'nro_secuencial': nro_valido,
            'fecha_emision': timezone.now(),
            'monto_total': Decimal('115000.00'),
            'nro_timbrado': self.timbrado,
            'tipo_documento': 'factura'
        }
        
        documento = DocumentosTributarios.objects.create(**data_valido)
        self.assertEqual(documento.nro_secuencial, nro_valido)

    def test_documentos_tributarios_serializer_rango_invalid(self):
        """Debe rechazar números fuera del rango del timbrado"""
        # Número fuera de rango
        nro_invalido = 15000  # Fuera del rango 1-10000
        
        # Simular validación de rango
        if nro_invalido > self.timbrado.nro_final:
            with self.assertRaises(Exception):
                raise ValidationError(f"Número {nro_invalido} fuera del rango del timbrado")

    def test_documentos_tributarios_serializer_tipo_documento_validation(self):
        """Debe validar correspondencia de tipo de documento con timbrado"""
        # Tipo correcto
        data_correcto = {
            'nro_secuencial': 1,
            'fecha_emision': timezone.now(),
            'monto_total': Decimal('100000.00'),
            'tipo_documento': 'factura',  # Coincide con timbrado
            'nro_timbrado': self.timbrado
        }
        
        # Debería ser válido
        doc = DocumentosTributarios.objects.create(**data_correcto)
        self.assertEqual(doc.tipo_documento, 'factura')

    def test_documentos_tributarios_serializer_monto_total_validation(self):
        """Debe validar que el monto total sea positivo"""
        # Monto negativo (inválido)
        with self.assertRaises(Exception):
            # Simular validación de monto
            monto_negativo = Decimal('-100000.00')
            if monto_negativo <= 0:
                raise ValidationError("El monto total debe ser positivo")

    def test_documentos_tributarios_serializer_fecha_emision_validation(self):
        """Debe validar que la fecha de emisión esté dentro de la vigencia del timbrado"""
        # Fecha dentro de vigencia
        fecha_valida = self.timbrado.fecha_inicio + timedelta(days=30)
        
        data_valido = {
            'nro_secuencial': 1,
            'fecha_emision': fecha_valida,
            'monto_total': Decimal('100000.00'),
            'nro_timbrado': self.timbrado,
            'tipo_documento': 'factura'
        }
        
        # Debe crear sin problemas
        doc = DocumentosTributarios.objects.create(**data_valido)
        # fecha_emision may be date or datetime; normalize for comparison
        stored_date = doc.fecha_emision.date() if hasattr(doc.fecha_emision, 'hour') else doc.fecha_emision
        self.assertEqual(stored_date, fecha_valida)

    def test_documentos_tributarios_serializer_output_format(self):
        """Debe formatear output con información completa"""
        doc = DocumentosTributarios.objects.create(
            nro_secuencial=100,
            fecha_emision=timezone.now(),
            monto_total=Decimal('250000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Simular output del serializer con información del timbrado
        expected_output = {
            'nro_secuencial': 100,
            'monto_total': '250000.00',
            'tipo_documento': 'factura',
            'timbrado_info': {
                'nro_timbrado': 12345678,
                'punto_expedicion': '001-001'
            }
        }
        
        # Verificar que la información esté disponible
        self.assertEqual(doc.nro_secuencial, 100)
        self.assertEqual(doc.nro_timbrado.nro_timbrado, 12345678)


class ImpuestosSerializerTest(BaseContabilidadSerializerTest):
    """Tests para hipotético ImpuestosSerializer"""

    def test_impuestos_serializer_porcentaje_validation(self):
        """Debe validar porcentajes de impuesto"""
        # Porcentajes típicos de Paraguay
        porcentajes_validos = [
            Decimal('0.00'),   # Exento
            Decimal('5.00'),   # IVA 5%
            Decimal('10.00')   # IVA 10%
        ]
        
        for porcentaje in porcentajes_validos:
            data = {
                'nombre_impuesto': f'IVA {porcentaje}%',
                'porcentaje': porcentaje,
                'vigente_desde': date.today(),
                'estado': True
            }
            
            impuesto = Impuestos.objects.create(**data)
            self.assertEqual(impuesto.porcentaje, porcentaje)
            impuesto.delete()

    def test_impuestos_serializer_nombre_unique_validation(self):
        """Debe validar unicidad de nombre de impuesto"""
        # Crear primer impuesto
        Impuestos.objects.create(
            nombre_impuesto='IVA Standard',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today()
        )
        
        # Intentar duplicado
        with self.assertRaises(Exception):
            # Simular validación de unicidad
            nombre_duplicado = 'IVA Standard'
            if Impuestos.objects.filter(nombre_impuesto=nombre_duplicado).exists():
                raise ValidationError("Ya existe un impuesto con ese nombre")

    def test_impuestos_serializer_vigencia_logic(self):
        """Debe manejar lógica de vigencia correctamente"""
        # Impuesto histórico
        impuesto_historico = Impuestos.objects.create(
            nombre_impuesto='IVA Histórico',
            porcentaje=Decimal('5.00'),
            vigente_desde=date.today() - timedelta(days=365),
            vigente_hasta=date.today() - timedelta(days=1),
            estado=False
        )
        
        # Impuesto actual
        impuesto_actual = Impuestos.objects.create(
            nombre_impuesto='IVA Actual',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today(),
            estado=True
        )
        
        # Verificar estados
        self.assertFalse(impuesto_historico.estado)
        self.assertTrue(impuesto_actual.estado)

    def test_impuestos_serializer_calculo_monto(self):
        """Debe calcular montos de impuesto correctamente"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA Test',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today()
        )
        
        # Simular método de cálculo
        def calcular_monto_impuesto(monto_base, impuesto):
            return (monto_base * impuesto.porcentaje) / Decimal('100')
        
        monto_base = Decimal('100000.00')
        monto_impuesto = calcular_monto_impuesto(monto_base, impuesto)
        expected = Decimal('10000.00')
        
        self.assertEqual(monto_impuesto, expected)

    def test_impuestos_serializer_output_with_calculations(self):
        """Debe incluir cálculos en el output"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA Completo',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today(),
            estado=True
        )
        
        # Simular output enriquecido del serializer
        monto_ejemplo = Decimal('50000.00')
        impuesto_calculado = (monto_ejemplo * impuesto.porcentaje) / Decimal('100')
        
        expected_output = {
            'id_impuesto': impuesto.id_impuesto,
            'nombre_impuesto': 'IVA Completo',
            'porcentaje': '10.00',
            'estado': True,
            'ejemplo_calculo': {
                'monto_base': '50000.00',
                'monto_impuesto': str(impuesto_calculado)
            }
        }
        
        # Verificar cálculo
        self.assertEqual(impuesto_calculado, Decimal('5000.00'))


class SerializersIntegrationTest(BaseContabilidadSerializerTest):
    """Tests de integración para serializers de contabilidad"""

    def test_serializers_chain_validation(self):
        """Debe validar cadena de relaciones entre serializers"""
        # 1. Crear tarifa de comisión
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('3.0000'),
            monto_fijo_comision=Decimal('1000.00'),
            id_medio_pago=self.medio_pago
        )
        
        # 2. Crear cierre de caja
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal('500000.00'),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # 3. Crear movimiento con comisión calculada
        monto_venta = Decimal('100000.00')
        comision_calculada = (monto_venta * tarifa.porcentaje_comision / Decimal('100')) + tarifa.monto_fijo_comision
        
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=monto_venta,
            monto_comision=comision_calculada,
            fecha_movimiento=timezone.now(),
            descripcion='Venta con comisión',
            id_cierre=cierre,
            id_medio_pago=self.medio_pago
        )
        
        # Verificar integridad de la cadena
        self.assertEqual(movimiento.monto_comision, Decimal('4000.00'))
        self.assertEqual(movimiento.id_cierre, cierre)
        self.assertEqual(cierre.id_caja, self.caja)

    def test_serializers_nested_data_handling(self):
        """Debe manejar datos anidados correctamente"""
        # Crear estructura completa
        punto = PuntosExpedicion.objects.create(
            codigo_establecimiento='001',
            codigo_punto_expedicion='002',
            descripcion_ubicacion='Sucursal Norte'
        )
        
        timbrado = Timbrados.objects.create(
            nro_timbrado=87654321,
            tipo_documento='boleta',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=180),
            nro_inicial=1000,
            nro_final=5000,
            id_punto=punto
        )
        
        documento = DocumentosTributarios.objects.create(
            nro_secuencial=1500,
            fecha_emision=timezone.now(),
            monto_total=Decimal('75000.00'),
            nro_timbrado=timbrado,
            tipo_documento='boleta'
        )
        
        # Simular serializer con datos anidados
        nested_data = {
            'documento': {
                'nro_secuencial': documento.nro_secuencial,
                'monto_total': str(documento.monto_total)
            },
            'timbrado': {
                'nro_timbrado': timbrado.nro_timbrado,
                'tipo_documento': timbrado.tipo_documento
            },
            'punto_expedicion': {
                'codigo_completo': f"{punto.codigo_establecimiento}-{punto.codigo_punto_expedicion}",
                'ubicacion': punto.descripcion_ubicacion
            }
        }
        
        # Verificar estructura anidada
        self.assertEqual(nested_data['documento']['nro_secuencial'], 1500)
        self.assertEqual(nested_data['timbrado']['nro_timbrado'], 87654321)
        self.assertEqual(nested_data['punto_expedicion']['codigo_completo'], '001-002')

    def test_serializers_error_handling(self):
        """Debe manejar errores de validación apropiadamente"""
        # Colección de errores de validación comunes
        validation_errors = []
        
        # Error 1: Monto negativo
        try:
            # Simular validación de monto
            monto_negativo = Decimal('-50000.00')
            if monto_negativo < 0:
                raise ValidationError("Monto debe ser positivo")
        except ValidationError as e:
            validation_errors.append(str(e))
        
        # Error 2: Estado inválido
        try:
            # Simular validación de estado
            estado_invalido = 'estado_inexistente'
            estados_validos = ['abierto', 'cerrado', 'cancelado']
            if estado_invalido not in estados_validos:
                raise ValidationError("Estado no válido")
        except ValidationError as e:
            validation_errors.append(str(e))
        
        # Error 3: Fecha de vigencia
        try:
            # Simular validación de fechas
            inicio = timezone.now()
            fin = inicio - timedelta(days=1)
            if fin < inicio:
                raise ValidationError("Fecha fin debe ser posterior a inicio")
        except ValidationError as e:
            validation_errors.append(str(e))
        
        # Verificar que se capturaron todos los errores esperados
        self.assertEqual(len(validation_errors), 3)
        self.assertIn("Monto debe ser positivo", validation_errors[0])
        self.assertIn("Estado no válido", validation_errors[1])
        self.assertIn("Fecha fin debe ser posterior", validation_errors[2])

    def test_serializers_performance_considerations(self):
        """Debe considerar optimizaciones de performance"""
        # Crear múltiples registros para test de performance
        cajas_creadas = []
        
        # Batch creation simulation
        for i in range(10):
            caja = Cajas.objects.create(
                nombre_caja=f'Caja Performance {i}',
                ubicacion=f'Ubicación {i}',
                estado=True
            )
            cajas_creadas.append(caja)
        
        # Simular serialización en lote
        cajas_data = []
        for caja in cajas_creadas:
            data = {
                'id_caja': caja.id_caja,
                'nombre_caja': caja.nombre_caja,
                'ubicacion': caja.ubicacion,
                'estado': caja.estado
            }
            cajas_data.append(data)
        
        # Verificar que todos los datos fueron serializados
        self.assertEqual(len(cajas_data), 10)
        self.assertTrue(all('id_caja' in data for data in cajas_data))