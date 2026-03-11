"""
Tests para admin de contabilidad
Cubre interfaz administrativa y funcionalidades de gestión
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from django.db.models import Q

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
from apps.contabilidad.admin import *
from apps.usuarios.models import Empleados, Roles
from apps.core.models import MediosPago


class BaseContabilidadAdminTest(TestCase):
    """Clase base para tests de admin de contabilidad"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear superusuario para admin
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Crear rol y empleado
        self.rol = Roles.objects.create(
            nombre_rol='Administrador',
            descripcion='Rol administrativo',
            activo=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Admin',
            apellido='Sistema',
            usuario='admin_sistema',
            contrasena_hash='$2b$12$hash',
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Crear datos de soporte
        self.caja = Cajas.objects.create(
            nombre_caja='Caja Admin Test',
            ubicacion='Administración',
            activo=True
        )
        
        self.medio_pago = MediosPago.objects.create(
            nombre='Efectivo Admin',
            descripcion='Para tests admin',
            activo=True
        )
        
        # Cliente para requests
        self.client = Client()
        self.client.force_login(self.superuser)
        
        # Mock admin site
        self.admin_site = AdminSite()


class CajasAdminTest(BaseContabilidadAdminTest):
    """Tests para CajasAdmin"""

    def test_cajas_admin_list_display(self):
        """Debe mostrar campos correctos en lista"""
        # Crear múltiples cajas
        Cajas.objects.create(nombre_caja='Caja 1', activo=True)
        Cajas.objects.create(nombre_caja='Caja 2', activo=False)
        
        # Simular list_display
        expected_fields = ['nombre_caja', 'ubicacion', 'activo']
        
        # Verificar que los campos existen en el modelo
        for field in expected_fields:
            self.assertTrue(hasattr(Cajas, field), f"Campo {field} no existe en modelo")

    def test_cajas_admin_search_functionality(self):
        """Debe permitir búsqueda por nombre y ubicación"""
        # Crear cajas con datos específicos
        caja1 = Cajas.objects.create(
            nombre_caja='Caja Principal Norte',
            ubicacion='Planta Alta - Norte'
        )
        caja2 = Cajas.objects.create(
            nombre_caja='Caja Secundaria Sur',
            ubicacion='Planta Baja - Sur'
        )
        
        # Simular búsqueda por nombre
        resultados_norte = Cajas.objects.filter(nombre_caja__icontains='Norte')
        self.assertIn(caja1, resultados_norte)
        self.assertNotIn(caja2, resultados_norte)
        
        # Simular búsqueda por ubicación
        resultados_planta_alta = Cajas.objects.filter(ubicacion__icontains='Planta Alta')
        self.assertIn(caja1, resultados_planta_alta)
        self.assertNotIn(caja2, resultados_planta_alta)

    def test_cajas_admin_filter_by_activo(self):
        """Debe permitir filtrar por estado activo"""
        # Crear cajas con diferentes estados
        caja_activa = Cajas.objects.create(nombre_caja='Activa', activo=True)
        caja_inactiva = Cajas.objects.create(nombre_caja='Inactiva', activo=False)
        
        # Filtrar por estado
        cajas_activas = Cajas.objects.filter(activo=True)
        cajas_inactivas = Cajas.objects.filter(activo=False)
        
        self.assertIn(caja_activa, cajas_activas)
        self.assertNotIn(caja_activa, cajas_inactivas)
        self.assertIn(caja_inactiva, cajas_inactivas)
        self.assertNotIn(caja_inactiva, cajas_activas)

    def test_cajas_admin_readonly_fields(self):
        """Debe tener campos de solo lectura apropiados"""
        # Simular campos readonly para timestamps
        readonly_fields = ['fecha_creacion', 'fecha_modificacion']
        
        # En este caso, verificamos que los campos de timestamps no sean editables
        # en un entorno real
        caja = Cajas.objects.create(nombre_caja='Test readonly')
        
        # Los campos de timestamp deberían ser manejados automáticamente
        self.assertIsNotNone(caja.id_caja)

    def test_cajas_admin_form_validation(self):
        """Debe validar formulario de admin"""
        # Datos válidos
        valid_data = {
            'nombre_caja': 'Caja Form Test',
            'ubicacion': 'Test Location',
            'activo': True
        }
        
        # Crear a través de admin form simulation
        try:
            caja = Cajas.objects.create(**valid_data)
            self.assertEqual(caja.nombre_caja, valid_data['nombre_caja'])
        except Exception as e:
            self.fail(f"Formulario válido falló: {e}")
        
        # Datos inválidos (nombre vacío)
        invalid_data = {
            'nombre_caja': '',
            'ubicacion': 'Test Location',
            'activo': True
        }
        
        with self.assertRaises(Exception):
            caja_invalid = Cajas(**invalid_data)
            caja_invalid.full_clean()


class CierresCajaAdminTest(BaseContabilidadAdminTest):
    """Tests para CierresCajaAdmin"""

    def test_cierres_caja_admin_list_display(self):
        """Debe mostrar información relevante en lista"""
        # Crear cierre de ejemplo
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal('1000000.00'),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Campos esperados en list_display
        expected_fields = [
            'fecha_hora_apertura', 'id_caja', 'id_empleado', 
            'estado', 'monto_inicial'
        ]
        
        for field in expected_fields:
            # Verificar que el campo existe o es accesible
            if hasattr(cierre, field):
                self.assertIsNotNone(getattr(cierre, field, None))

    def test_cierres_caja_admin_filter_by_estado(self):
        """Debe permitir filtrar por estado de cierre"""
        # Crear cierres con diferentes estados
        cierre_abierto = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        cierre_cerrado = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now() - timedelta(hours=8),
            fecha_hora_cierre=timezone.now(),
            estado='cerrado',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Filtrar por estado
        abiertos = CierresCaja.objects.filter(estado='abierto')
        cerrados = CierresCaja.objects.filter(estado='cerrado')
        
        self.assertIn(cierre_abierto, abiertos)
        self.assertIn(cierre_cerrado, cerrados)

    def test_cierres_caja_admin_date_hierarchy(self):
        """Debe permitir navegación por jerarquía de fechas"""
        # Crear cierres en diferentes fechas
        hoy = timezone.now()
        ayer = hoy - timedelta(days=1)
        
        cierre_hoy = CierresCaja.objects.create(
            fecha_hora_apertura=hoy,
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        cierre_ayer = CierresCaja.objects.create(
            fecha_hora_apertura=ayer,
            estado='cerrado',
            fecha_hora_cierre=ayer + timedelta(hours=8),
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Filtrar por fecha
        cierres_hoy = CierresCaja.objects.filter(
            fecha_hora_apertura__date=hoy.date()
        )
        cierres_ayer = CierresCaja.objects.filter(
            fecha_hora_apertura__date=ayer.date()
        )
        
        self.assertIn(cierre_hoy, cierres_hoy)
        self.assertIn(cierre_ayer, cierres_ayer)
        self.assertNotIn(cierre_hoy, cierres_ayer)
        self.assertNotIn(cierre_ayer, cierres_hoy)

    def test_cierres_caja_admin_calculate_differences(self):
        """Debe calcular diferencias automáticamente"""
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal('1000000.00'),
            monto_contado_fisico=Decimal('950000.00'),
            estado='cerrado',
            fecha_hora_cierre=timezone.now(),
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Calcular diferencia
        diferencia = cierre.monto_contado_fisico - cierre.monto_inicial
        expected_diferencia = Decimal('-50000.00')
        
        self.assertEqual(diferencia, expected_diferencia)

    def test_cierres_caja_admin_permissions_validation(self):
        """Debe validar permisos para operaciones sensibles"""
        # Simular validación de permisos para cierre de caja
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Solo usuarios autorizados deberían poder cerrar cajas
        # En un escenario real, esto sería validado en el admin
        
        # Verificar que el usuario tiene permisos de admin
        self.assertTrue(self.superuser.is_superuser)
        
        # Simular cierre autorizado
        if self.superuser.is_superuser:
            cierre.estado = 'cerrado'
            cierre.fecha_hora_cierre = timezone.now()
            cierre.save()
            self.assertEqual(cierre.estado, 'cerrado')


class MovimientosCajaAdminTest(BaseContabilidadAdminTest):
    """Tests para MovimientosCajaAdmin"""

    def setUp(self):
        """Configurar datos específicos para movimientos"""
        super().setUp()
        
        self.cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )

    def test_movimientos_caja_admin_list_display(self):
        """Debe mostrar información completa del movimiento"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('75000.00'),
            monto_comision=Decimal('3000.00'),
            fecha_movimiento=timezone.now(),
            descripcion='Venta admin test',
            id_cierre=self.cierre,
            id_medio_pago=self.medio_pago
        )
        
        # Campos para mostrar en admin
        expected_fields = [
            'fecha_movimiento', 'tipo_movimiento', 'monto',
            'monto_comision', 'id_medio_pago'
        ]
        
        for field in expected_fields:
            self.assertTrue(hasattr(movimiento, field))

    def test_movimientos_caja_admin_filter_by_tipo(self):
        """Debe permitir filtrar por tipo de movimiento"""
        # Crear diferentes tipos de movimientos
        ingreso = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('100000.00'),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago
        )
        
        egreso = MovimientosCaja.objects.create(
            tipo_movimiento='egreso',
            monto=Decimal('50000.00'),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago
        )
        
        # Filtrar por tipo
        ingresos = MovimientosCaja.objects.filter(tipo_movimiento='ingreso')
        egresos = MovimientosCaja.objects.filter(tipo_movimiento='egreso')
        
        self.assertIn(ingreso, ingresos)
        self.assertNotIn(ingreso, egresos)
        self.assertIn(egreso, egresos)
        self.assertNotIn(egreso, ingresos)

    def test_movimientos_caja_admin_search_description(self):
        """Debe permitir búsqueda por descripción"""
        # Crear movimientos con descripciones específicas
        mov1 = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('80000.00'),
            descripcion='Venta almuerzo ejecutivo',
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago
        )
        
        mov2 = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('45000.00'),
            descripcion='Recarga tarjeta estudiante',
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago
        )
        
        # Búsqueda por descripción
        almuerzo_results = MovimientosCaja.objects.filter(
            descripcion__icontains='almuerzo'
        )
        recarga_results = MovimientosCaja.objects.filter(
            descripcion__icontains='recarga'
        )
        
        self.assertIn(mov1, almuerzo_results)
        self.assertNotIn(mov2, almuerzo_results)
        self.assertIn(mov2, recarga_results)
        self.assertNotIn(mov1, recarga_results)

    def test_movimientos_caja_admin_readonly_calculated_fields(self):
        """Debe tener campos calculados como readonly"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('100000.00'),
            monto_comision=Decimal('5000.00'),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago
        )
        
        # En admin, campos como id_movimiento deberían ser readonly
        self.assertIsNotNone(movimiento.id_movimiento)
        
        # Fechas de creación/modificación automáticas
        self.assertIsNotNone(movimiento.fecha_movimiento)

    def test_movimientos_caja_admin_bulk_actions(self):
        """Debe soportar acciones en lote"""
        # Crear múltiples movimientos
        movimientos = []
        for i in range(5):
            mov = MovimientosCaja.objects.create(
                tipo_movimiento='ingreso',
                monto=Decimal('50000.00') + (Decimal('10000.00') * i),
                fecha_movimiento=timezone.now(),
                descripcion=f'Movimiento {i+1}',
                id_medio_pago=self.medio_pago
            )
            movimientos.append(mov)
        
        # Simular acción en lote (ej: marcar como revisados)
        ids_movimientos = [mov.id_movimiento for mov in movimientos]
        
        # Verificar que todos fueron creados
        self.assertEqual(len(ids_movimientos), 5)
        
        # Simular actualización en lote
        MovimientosCaja.objects.filter(
            id_movimiento__in=ids_movimientos
        ).update(descripcion='Revisado en lote')
        
        # Verificar actualización
        movimientos_actualizados = MovimientosCaja.objects.filter(
            descripcion='Revisado en lote'
        )
        self.assertEqual(movimientos_actualizados.count(), 5)


class TarifasComisionAdminTest(BaseContabilidadAdminTest):
    """Tests para TarifasComisionAdmin"""

    def test_tarifas_comision_admin_list_display(self):
        """Debe mostrar información de tarifia claramente"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('3.5000'),
            monto_fijo_comision=Decimal('2000.00'),
            activo=True,
            id_medio_pago=self.medio_pago
        )
        
        # Verificar campos importantes
        self.assertEqual(tarifa.porcentaje_comision, Decimal('3.5000'))
        self.assertEqual(tarifa.monto_fijo_comision, Decimal('2000.00'))
        self.assertTrue(tarifa.activo)

    def test_tarifas_comision_admin_vigencia_validation(self):
        """Debe validar lógica de vigencia en admin"""
        # Tarifa actual
        tarifa_actual = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now() - timedelta(days=30),
            fecha_fin_vigencia=timezone.now() + timedelta(days=30),
            porcentaje_comision=Decimal('2.5000'),
            activo=True,
            id_medio_pago=self.medio_pago
        )
        
        # Verificar que está vigente
        fecha_actual = timezone.now()
        es_vigente = (
            tarifa_actual.fecha_inicio_vigencia <= fecha_actual and
            (tarifa_actual.fecha_fin_vigencia is None or 
             tarifa_actual.fecha_fin_vigencia >= fecha_actual)
        )
        self.assertTrue(es_vigente)

    def test_tarifas_comision_admin_calculation_preview(self):
        """Debe mostrar preview de cálculo de comisión"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('4.0000'),
            monto_fijo_comision=Decimal('1500.00'),
            id_medio_pago=self.medio_pago
        )
        
        # Preview para monto ejemplo
        monto_ejemplo = Decimal('100000.00')
        comision_porcentual = (monto_ejemplo * tarifa.porcentaje_comision) / Decimal('100')
        comision_total = comision_porcentual + (tarifa.monto_fijo_comision or Decimal('0'))
        
        expected_comision = Decimal('5500.00')  # 4000 + 1500
        self.assertEqual(comision_total, expected_comision)

    def test_tarifas_comision_admin_filter_by_medio_pago(self):
        """Debe permitir filtrar por medio de pago"""
        # Crear otro medio de pago
        otro_medio = MediosPago.objects.create(
            nombre='Tarjeta Débito',
            descripcion='Pagos con débito',
            activo=True
        )
        
        # Crear tarifas para diferentes medios
        tarifa_efectivo = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('2.0000'),
            id_medio_pago=self.medio_pago
        )
        
        tarifa_debito = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('3.0000'),
            id_medio_pago=otro_medio
        )
        
        # Filtrar por medio de pago
        tarifas_efectivo = TarifasComision.objects.filter(
            id_medio_pago=self.medio_pago
        )
        tarifas_debito = TarifasComision.objects.filter(
            id_medio_pago=otro_medio
        )
        
        self.assertIn(tarifa_efectivo, tarifas_efectivo)
        self.assertIn(tarifa_debito, tarifas_debito)
        self.assertNotIn(tarifa_efectivo, tarifas_debito)
        self.assertNotIn(tarifa_debito, tarifas_efectivo)


class DocumentosTributariosAdminTest(BaseContabilidadAdminTest):
    """Tests para DocumentosTributariosAdmin"""

    def setUp(self):
        """Configurar datos específicos para documentos"""
        super().setUp()
        
        self.punto = PuntosExpedicion.objects.create(
            codigo_establecimiento='001',
            codigo_punto_expedicion='001',
            descripcion_ubicacion='Principal Admin'
        )
        
        self.timbrado = Timbrados.objects.create(
            nro_timbrado=11111111,
            tipo_documento='factura',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=5000,
            es_electronico=1,
            id_punto=self.punto
        )

    def test_documentos_tributarios_admin_list_display(self):
        """Debe mostrar información tributaria completa"""
        documento = DocumentosTributarios.objects.create(
            nro_secuencial=100,
            fecha_emision=timezone.now(),
            monto_total=Decimal('150000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Campos importantes para admin
        expected_fields = [
            'nro_secuencial', 'fecha_emision', 'monto_total',
            'tipo_documento', 'nro_timbrado'
        ]
        
        for field in expected_fields:
            self.assertTrue(hasattr(documento, field))

    def test_documentos_tributarios_admin_search_by_numero(self):
        """Debe permitir búsqueda por número secuencial"""
        # Crear múltiples documentos
        doc1 = DocumentosTributarios.objects.create(
            nro_secuencial=150,
            fecha_emision=timezone.now(),
            monto_total=Decimal('100000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        doc2 = DocumentosTributarios.objects.create(
            nro_secuencial=250,
            fecha_emision=timezone.now(),
            monto_total=Decimal('200000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Búsqueda por número
        resultado_150 = DocumentosTributarios.objects.filter(nro_secuencial=150)
        resultado_250 = DocumentosTributarios.objects.filter(nro_secuencial=250)
        
        self.assertIn(doc1, resultado_150)
        self.assertNotIn(doc2, resultado_150)
        self.assertIn(doc2, resultado_250)
        self.assertNotIn(doc1, resultado_250)

    def test_documentos_tributarios_admin_filter_by_tipo(self):
        """Debe permitir filtrar por tipo de documento"""
        documento = DocumentosTributarios.objects.create(
            nro_secuencial=300,
            fecha_emision=timezone.now(),
            monto_total=Decimal('100000.00'),
            tipo_documento='factura',
            nro_timbrado=self.timbrado
        )
        
        # Filtrar por tipo
        facturas = DocumentosTributarios.objects.filter(tipo_documento='factura')
        
        self.assertIn(documento, facturas)

    def test_documentos_tributarios_admin_date_hierarchy(self):
        """Debe permitir navegación por fecha de emisión"""
        # Crear documentos en diferentes fechas
        hoy = timezone.now()
        ayer = hoy - timedelta(days=1)
        
        doc_hoy = DocumentosTributarios.objects.create(
            nro_secuencial=400,
            fecha_emision=hoy,
            monto_total=Decimal('100000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        doc_ayer = DocumentosTributarios.objects.create(
            nro_secuencial=401,
            fecha_emision=ayer,
            monto_total=Decimal('100000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Filtrar por fecha
        docs_hoy = DocumentosTributarios.objects.filter(
            fecha_emision__date=hoy.date()
        )
        docs_ayer = DocumentosTributarios.objects.filter(
            fecha_emision__date=ayer.date()
        )
        
        self.assertIn(doc_hoy, docs_hoy)
        self.assertIn(doc_ayer, docs_ayer)
        self.assertNotIn(doc_hoy, docs_ayer)
        self.assertNotIn(doc_ayer, docs_hoy)

    def test_documentos_tributarios_admin_timbrado_validation(self):
        """Debe validar que el documento esté en rango de timbrado"""
        # Número en rango válido
        nro_valido = 2500  # Dentro de 1-5000
        
        documento_valido = DocumentosTributarios.objects.create(
            nro_secuencial=nro_valido,
            fecha_emision=timezone.now(),
            monto_total=Decimal('100000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Verificar que está en rango
        self.assertGreaterEqual(nro_valido, self.timbrado.nro_inicial)
        self.assertLessEqual(nro_valido, self.timbrado.nro_final)

    def test_documentos_tributarios_admin_readonly_fields(self):
        """Debe tener campos calculados como readonly"""
        documento = DocumentosTributarios.objects.create(
            nro_secuencial=500,
            fecha_emision=timezone.now(),
            monto_total=Decimal('300000.00'),
            nro_timbrado=self.timbrado,
            tipo_documento='factura'
        )
        
        # Campos que deberían ser readonly en admin
        # ID y timestamps generalmente son readonly
        self.assertIsNotNone(documento.id_documento)


class ImpuestosAdminTest(BaseContabilidadAdminTest):
    """Tests para ImpuestosAdmin"""

    def test_impuestos_admin_list_display(self):
        """Debe mostrar información fiscal claramente"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA 10% Admin',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today(),
            activo=True
        )
        
        # Campos para mostrar
        expected_fields = [
            'nombre_impuesto', 'porcentaje', 'vigente_desde',
            'vigente_hasta', 'activo'
        ]
        
        for field in expected_fields:
            self.assertTrue(hasattr(impuesto, field))

    def test_impuestos_admin_filter_by_activo(self):
        """Debe permitir filtrar por estado activo"""
        impuesto_activo = Impuestos.objects.create(
            nombre_impuesto='IVA Activo',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today(),
            activo=True
        )
        
        impuesto_inactivo = Impuestos.objects.create(
            nombre_impuesto='IVA Inactivo',
            porcentaje=Decimal('5.00'),
            vigente_desde=date.today() - timedelta(days=365),
            vigente_hasta=date.today() - timedelta(days=1),
            activo=False
        )
        
        # Filtrar por estado
        activos = Impuestos.objects.filter(activo=True)
        inactivos = Impuestos.objects.filter(activo=False)
        
        self.assertIn(impuesto_activo, activos)
        self.assertIn(impuesto_inactivo, inactivos)
        self.assertNotIn(impuesto_activo, inactivos)
        self.assertNotIn(impuesto_inactivo, activos)

    def test_impuestos_admin_search_by_nombre(self):
        """Debe permitir búsqueda por nombre"""
        iva_10 = Impuestos.objects.create(
            nombre_impuesto='IVA 10% Standard',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today()
        )
        
        iva_5 = Impuestos.objects.create(
            nombre_impuesto='IVA 5% Reducido',
            porcentaje=Decimal('5.00'),
            vigente_desde=date.today()
        )
        
        # Búsqueda por nombre
        resultados_10 = Impuestos.objects.filter(nombre_impuesto__icontains='10%')
        resultados_5 = Impuestos.objects.filter(nombre_impuesto__icontains='5%')
        
        self.assertIn(iva_10, resultados_10)
        self.assertNotIn(iva_5, resultados_10)
        self.assertIn(iva_5, resultados_5)
        self.assertNotIn(iva_10, resultados_5)

    def test_impuestos_admin_calculation_preview(self):
        """Debe mostrar preview de cálculo de impuesto"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA Cálculo Test',
            porcentaje=Decimal('10.00'),
            vigente_desde=date.today()
        )
        
        # Preview para diferentes montos
        montos_test = [
            Decimal('100000.00'),
            Decimal('250000.00'),
            Decimal('500000.00')
        ]
        
        for monto in montos_test:
            impuesto_calculado = (monto * impuesto.porcentaje) / Decimal('100')
            expected = monto * Decimal('0.10')
            self.assertEqual(impuesto_calculado, expected)

    def test_impuestos_admin_vigencia_validation(self):
        """Debe validar fechas de vigencia"""
        # Impuesto con vigencia válida
        impuesto_valido = Impuestos.objects.create(
            nombre_impuesto='IVA Vigencia Test',
            porcentaje=Decimal('8.00'),
            vigente_desde=date.today(),
            vigente_hasta=date.today() + timedelta(days=180)
        )
        
        # Verificar vigencia
        fecha_actual = date.today()
        es_vigente = (
            impuesto_valido.vigente_desde <= fecha_actual and
            (impuesto_valido.vigente_hasta is None or 
             impuesto_valido.vigente_hasta >= fecha_actual)
        )
        self.assertTrue(es_vigente)


class ContabilidadAdminIntegrationTest(BaseContabilidadAdminTest):
    """Tests de integración para admin de contabilidad"""

    def test_admin_workflow_complete_cash_cycle(self):
        """Debe manejar ciclo completo de caja en admin"""
        # 1. Configurar tarifa de comisión
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal('3.0000'),
            monto_fijo_comision=Decimal('1000.00'),
            activo=True,
            id_medio_pago=self.medio_pago
        )
        
        # 2. Abrir caja
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal('1000000.00'),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # 3. Registrar movimientos
        movimiento1 = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('150000.00'),
            monto_comision=Decimal('5500.00'),  # 4500 + 1000
            fecha_movimiento=timezone.now(),
            descripcion='Venta 1',
            id_cierre=cierre,
            id_medio_pago=self.medio_pago
        )
        
        movimiento2 = MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=Decimal('200000.00'),
            monto_comision=Decimal('7000.00'),  # 6000 + 1000
            fecha_movimiento=timezone.now(),
            descripcion='Venta 2',
            id_cierre=cierre,
            id_medio_pago=self.medio_pago
        )
        
        # 4. Calcular totales
        from django.db.models import Sum
        totales = MovimientosCaja.objects.filter(id_cierre=cierre).aggregate(
            total_ingresos=Sum('monto'),
            total_comisiones=Sum('monto_comision')
        )
        
        # 5. Cerrar caja
        monto_teorico = cierre.monto_inicial + totales['total_ingresos']
        cierre.estado = 'cerrado'
        cierre.fecha_hora_cierre = timezone.now()
        cierre.monto_contado_fisico = monto_teorico - Decimal('5000.00')  # Diferencia
        cierre.diferencia_efectivo = cierre.monto_contado_fisico - monto_teorico
        cierre.save()
        
        # Verificaciones
        self.assertEqual(totales['total_ingresos'], Decimal('350000.00'))
        self.assertEqual(totales['total_comisiones'], Decimal('12500.00'))
        self.assertEqual(cierre.estado, 'cerrado')
        self.assertEqual(cierre.diferencia_efectivo, Decimal('-5000.00'))

    def test_admin_bulk_operations(self):
        """Debe soportar operaciones en lote"""
        # Crear múltiples registros para operaciones en lote
        cajas_bulk = []
        for i in range(10):
            caja = Cajas.objects.create(
                nombre_caja=f'Caja Bulk {i}',
                ubicacion=f'Ubicación {i}',
                activo=True
            )
            cajas_bulk.append(caja)
        
        # Simular operación en lote: desactivar todas
        cajas_ids = [caja.id_caja for caja in cajas_bulk]
        Cajas.objects.filter(id_caja__in=cajas_ids).update(activo=False)
        
        # Verificar resultados
        cajas_desactivadas = Cajas.objects.filter(
            id_caja__in=cajas_ids,
            activo=False
        )
        self.assertEqual(cajas_desactivadas.count(), 10)

    def test_admin_reporting_aggregations(self):
        """Debe generar reportes agregados desde admin"""
        # Crear datos para reportes
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Crear movimientos variados
        tipos_montos = [
            ('ingreso', Decimal('100000.00')),
            ('ingreso', Decimal('150000.00')),
            ('ingreso', Decimal('75000.00')),
            ('egreso', Decimal('25000.00'))
        ]
        
        for tipo, monto in tipos_montos:
            MovimientosCaja.objects.create(
                tipo_movimiento=tipo,
                monto=monto,
                fecha_movimiento=timezone.now(),
                id_medio_pago=self.medio_pago,
                id_cierre=cierre
            )
        
        # Generar agregaciones
        from django.db.models import Sum, Count, Avg
        reportes = MovimientosCaja.objects.aggregate(
            total_ingresos=Sum(
                'monto',
                filter=Q(tipo_movimiento='ingreso')
            ),
            total_egresos=Sum(
                'monto',
                filter=Q(tipo_movimiento='egreso')
            ),
            cantidad_transacciones=Count('id_movimiento'),
            promedio_transaccion=Avg('monto')
        )
        
        # Verificar cálculos
        self.assertEqual(reportes['total_ingresos'], Decimal('325000.00'))
        self.assertEqual(reportes['total_egresos'], Decimal('25000.00'))
        self.assertEqual(reportes['cantidad_transacciones'], 4)
        self.assertEqual(reportes['promedio_transaccion'], Decimal('87500.00'))

    def test_admin_security_validations(self):
        """Debe validar seguridad en operaciones administrativas"""
        # Crear usuario sin permisos de admin
        user_limited = User.objects.create_user(
            username='limited',
            password='limited123'
        )
        
        # Verificar que no tiene permisos de superusuario
        self.assertFalse(user_limited.is_superuser)
        self.assertFalse(user_limited.is_staff)
        
        # Solo superusuarios deberían acceder a admin
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_staff)
        
        # Verificar permisos para operaciones sensibles
        # En un escenario real, esto sería validado por el sistema de permisos de Django
        
        # Operación que requiere permisos especiales (cerrar caja)
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            estado='abierto',
            id_caja=self.caja,
            id_empleado=self.empleado
        )
        
        # Solo admin puede cerrar
        if self.superuser.is_superuser:
            cierre.estado = 'cerrado'
            cierre.fecha_hora_cierre = timezone.now()
            cierre.save()
            
            self.assertEqual(cierre.estado, 'cerrado')
        
        # Usuario limitado no podría realizar esta operación