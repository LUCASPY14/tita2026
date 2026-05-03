"""
Tests para modelos de contabilidad
Cubre validaciones, relaciones y funcionalidad de modelos contables
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.models import (
    AuditoriaComisiones,
    Cajas,
    CierresCaja,
    ConciliacionPagos,
    DatosEmpresa,
    DocumentoImpuestos,
    DocumentosTributarios,
    Impuestos,
    MovimientosCaja,
    PuntosExpedicion,
    TarifasComision,
    Timbrados,
)
from apps.core.models import MediosPago
from apps.usuarios.models import Empleados, Roles


class CajasModelTest(TestCase):
    """Tests para modelo Cajas"""

    def test_crear_caja_valida(self):
        """Debe crear caja con datos válidos"""
        caja = Cajas.objects.create(nombre_caja="Caja Principal", ubicacion="Planta Baja - Sector A", estado=True)

        self.assertEqual(caja.nombre_caja, "Caja Principal")
        self.assertEqual(caja.ubicacion, "Planta Baja - Sector A")
        self.assertTrue(caja.estado)

    def test_caja_nombre_obligatorio(self):
        """Debe requerir nombre_caja"""
        with self.assertRaises(ValidationError):
            caja = Cajas(ubicacion="Test", estado=True)
            caja.full_clean()

    def test_caja_ubicacion_opcional(self):
        """Debe permitir ubicacion como None"""
        caja = Cajas.objects.create(nombre_caja="Caja Sin Ubicación", estado=True)

        self.assertIsNone(caja.ubicacion)

    def test_caja_activo_default_true(self):
        """Debe tener estado=True por defecto"""
        caja = Cajas.objects.create(nombre_caja="Caja Default")
        self.assertTrue(caja.estado)

    def test_caja_string_representation(self):
        """Debe retornar representación string correcta"""
        caja = Cajas.objects.create(nombre_caja="Test Caja")
        expected = f"Cajas #{caja.pk}"
        self.assertEqual(str(caja), expected)

    def test_caja_nombre_max_length(self):
        """Debe validar longitud máxima de nombre_caja"""
        long_name = "x" * 51  # Excede max_length=50

        with self.assertRaises(ValidationError):
            caja = Cajas(nombre_caja=long_name, estado=True)
            caja.full_clean()


class CierresCajaModelTest(TestCase):
    """Tests para modelo CierresCaja"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear caja
        self.caja = Cajas.objects.create(nombre_caja="Caja Test", estado=True)

        # Crear empleado
        self.rol = Roles.objects.create(nombre_rol="Cajero", descripcion="Rol de cajero", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            usuario="jcajero",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

    def test_crear_cierre_caja_valido(self):
        """Debe crear cierre de caja con datos válidos"""
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal("1000000.00"),
            estado="abierto",
            id_caja=self.caja,
            id_empleado=self.empleado,
        )

        self.assertEqual(cierre.estado, "abierto")
        self.assertEqual(cierre.monto_inicial, Decimal("1000000.00"))
        self.assertEqual(cierre.id_caja, self.caja)
        self.assertEqual(cierre.id_empleado, self.empleado)

    def test_cierre_caja_fechas_logicas(self):
        """Debe validar lógica de fechas de apertura y cierre"""
        apertura = timezone.now()
        cierre = timezone.now() + timedelta(hours=8)

        cierre_caja = CierresCaja.objects.create(
            fecha_hora_apertura=apertura,
            fecha_hora_cierre=cierre,
            monto_inicial=Decimal("500000.00"),
            estado="cerrado",
            id_caja=self.caja,
            id_empleado=self.empleado,
        )

        self.assertLess(cierre_caja.fecha_hora_apertura, cierre_caja.fecha_hora_cierre)

    def test_cierre_caja_calculo_diferencia_efectivo(self):
        """Debe manejar cálculo de diferencia de efectivo"""
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(),
            monto_inicial=Decimal("1000000.00"),
            monto_contado_fisico=Decimal("950000.00"),
            diferencia_efectivo=Decimal("-50000.00"),
            estado="cerrado",
            id_caja=self.caja,
            id_empleado=self.empleado,
        )

        # Verificar diferencia calculada
        diferencia_esperada = cierre.monto_contado_fisico - cierre.monto_inicial
        self.assertEqual(cierre.diferencia_efectivo, diferencia_esperada)

    def test_cierre_caja_estados_validos(self):
        """Debe manejar estados válidos de cierre"""
        estados_validos = ["abierto", "cerrado"]

        for estado in estados_validos:
            with self.subTest(estado=estado):
                cierre = CierresCaja.objects.create(
                    fecha_hora_apertura=timezone.now(), estado=estado, id_caja=self.caja, id_empleado=self.empleado
                )
                self.assertEqual(cierre.estado, estado)

    def test_cierre_caja_relacion_empleado(self):
        """Debe mantener relación correcta con empleado"""
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(), estado="abierto", id_caja=self.caja, id_empleado=self.empleado
        )

        self.assertEqual(cierre.id_empleado.usuario, "jcajero")
        self.assertEqual(cierre.id_empleado.nombre, "Juan")

    def test_cierre_caja_string_representation(self):
        """Debe retornar representación string correcta"""
        cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(), estado="abierto", id_caja=self.caja, id_empleado=self.empleado
        )

        expected = f"CierresCaja #{cierre.pk}"
        self.assertEqual(str(cierre), expected)


class MovimientosCajaModelTest(TestCase):
    """Tests para modelo MovimientosCaja"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear caja y cierre
        self.caja = Cajas.objects.create(nombre_caja="Caja Movimientos")

        self.rol = Roles.objects.create(nombre_rol="Cajero", descripcion="Rol cajero", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Ana",
            apellido="Movimientos",
            usuario="amovimientos",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        self.cierre = CierresCaja.objects.create(
            fecha_hora_apertura=timezone.now(), estado="abierto", id_caja=self.caja, id_empleado=self.empleado
        )

        # Crear medio de pago
        self.medio_pago = MediosPago.objects.create(nombre="Efectivo", descripcion="Pago en efectivo", estado=True)

    def test_crear_movimiento_caja_valido(self):
        """Debe crear movimiento de caja con datos válidos"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento="ingreso",
            monto=Decimal("150000.00"),
            monto_comision=Decimal("5000.00"),
            fecha_movimiento=timezone.now(),
            descripcion="Venta de almuerzo",
            id_cierre=self.cierre,
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(movimiento.tipo_movimiento, "ingreso")
        self.assertEqual(movimiento.monto, Decimal("150000.00"))
        self.assertEqual(movimiento.monto_comision, Decimal("5000.00"))

    def test_movimiento_tipos_validos(self):
        """Debe manejar tipos de movimiento válidos"""
        tipos_validos = ["ingreso", "egreso", "transferencia"]

        for tipo in tipos_validos:
            with self.subTest(tipo=tipo):
                movimiento = MovimientosCaja.objects.create(
                    tipo_movimiento=tipo,
                    monto=Decimal("100000.00"),
                    monto_comision=Decimal("0.00"),
                    fecha_movimiento=timezone.now(),
                    id_medio_pago=self.medio_pago,
                )
                self.assertEqual(movimiento.tipo_movimiento, tipo)

    def test_movimiento_monto_precision(self):
        """Debe manejar precisión decimal correctamente"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento="ingreso",
            monto=Decimal("123456.78"),
            monto_comision=Decimal("98765.43"),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(movimiento.monto, Decimal("123456.78"))
        self.assertEqual(movimiento.monto_comision, Decimal("98765.43"))

    def test_movimiento_descripcion_opcional(self):
        """Debe permitir descripción opcional"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento="egreso",
            monto=Decimal("50000.00"),
            monto_comision=Decimal("0.00"),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago,
        )

        self.assertIsNone(movimiento.descripcion)

    def test_movimiento_relacion_cierre_opcional(self):
        """Debe permitir relación opcional con cierre"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento="transferencia",
            monto=Decimal("75000.00"),
            monto_comision=Decimal("0.00"),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago,
        )

        self.assertIsNone(movimiento.id_cierre)

    def test_movimiento_string_representation(self):
        """Debe retornar representación string correcta"""
        movimiento = MovimientosCaja.objects.create(
            tipo_movimiento="ingreso",
            monto=Decimal("100000.00"),
            monto_comision=Decimal("0.00"),
            fecha_movimiento=timezone.now(),
            id_medio_pago=self.medio_pago,
        )

        expected = f"MovimientosCaja #{movimiento.pk}"
        self.assertEqual(str(movimiento), expected)


class TarifasComisionModelTest(TestCase):
    """Tests para modelo TarifasComision"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.medio_pago = MediosPago.objects.create(
            nombre="Tarjeta Crédito", descripcion="Pago con tarjeta de crédito", estado=True
        )

    def test_crear_tarifa_comision_valida(self):
        """Debe crear tarifa de comisión con datos válidos"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal("3.5000"),
            monto_fijo_comision=Decimal("1000.00"),
            estado=True,
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(tarifa.porcentaje_comision, Decimal("3.5000"))
        self.assertEqual(tarifa.monto_fijo_comision, Decimal("1000.00"))
        self.assertTrue(tarifa.estado)

    def test_tarifa_comision_vigencia_fechas(self):
        """Debe manejar fechas de vigencia correctamente"""
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=365)

        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=fecha_inicio,
            fecha_fin_vigencia=fecha_fin,
            porcentaje_comision=Decimal("2.5000"),
            id_medio_pago=self.medio_pago,
        )

        self.assertLess(tarifa.fecha_inicio_vigencia, tarifa.fecha_fin_vigencia)

    def test_tarifa_comision_sin_fecha_fin(self):
        """Debe permitir fecha_fin_vigencia como None (vigencia indefinida)"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(), porcentaje_comision=Decimal("4.0000"), id_medio_pago=self.medio_pago
        )

        self.assertIsNone(tarifa.fecha_fin_vigencia)

    def test_tarifa_comision_porcentaje_precision(self):
        """Debe manejar precisión de porcentaje correctamente"""
        # max_digits=5, decimal_places=4 means max value is 9.9999
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(),
            porcentaje_comision=Decimal("4.5678"),  # 1 entero + 4 decimales = 5 total
            id_medio_pago=self.medio_pago,
        )

        self.assertEqual(tarifa.porcentaje_comision, Decimal("4.5678"))

    def test_tarifa_comision_monto_fijo_opcional(self):
        """Debe permitir monto_fijo_comision como None"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(), porcentaje_comision=Decimal("2.0000"), id_medio_pago=self.medio_pago
        )

        self.assertIsNone(tarifa.monto_fijo_comision)

    def test_tarifa_comision_activo_default(self):
        """Debe tener estado=True por defecto"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(), porcentaje_comision=Decimal("1.5000"), id_medio_pago=self.medio_pago
        )

        self.assertTrue(tarifa.estado)

    def test_tarifa_comision_string_representation(self):
        """Debe retornar representación string correcta"""
        tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(), porcentaje_comision=Decimal("3.0000"), id_medio_pago=self.medio_pago
        )

        expected = f"TarifasComision #{tarifa.pk}"
        self.assertEqual(str(tarifa), expected)


class AuditoriaComisionesModelTest(TestCase):
    """Tests para modelo AuditoriaComisiones"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.medio_pago = MediosPago.objects.create(nombre="Débito", descripcion="Tarjeta débito", estado=True)

        self.tarifa = TarifasComision.objects.create(
            fecha_inicio_vigencia=timezone.now(), porcentaje_comision=Decimal("2.0000"), id_medio_pago=self.medio_pago
        )

        self.rol = Roles.objects.create(nombre_rol="Admin", descripcion="Administrador", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Carlos",
            apellido="Admin",
            usuario="cadmin",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

    def test_crear_auditoria_comision_valida(self):
        """Debe crear auditoría de comisión con datos válidos"""
        auditoria = AuditoriaComisiones.objects.create(
            fecha_cambio=timezone.now(),
            campo_modificado="porcentaje_comision",
            valor_anterior=Decimal("2.0000"),
            valor_nuevo=Decimal("2.5000"),
            id_empleado_modifico=self.empleado,
            id_tarifa=self.tarifa,
        )

        self.assertEqual(auditoria.campo_modificado, "porcentaje_comision")
        self.assertEqual(auditoria.valor_anterior, Decimal("2.0000"))
        self.assertEqual(auditoria.valor_nuevo, Decimal("2.5000"))

    def test_auditoria_comision_campos_opcionales(self):
        """Debe permitir campos opcionales como None"""
        auditoria = AuditoriaComisiones.objects.create(
            fecha_cambio=timezone.now(), campo_modificado="estado", valor_anterior=None, valor_nuevo=None
        )

        self.assertIsNone(auditoria.valor_anterior)
        self.assertIsNone(auditoria.valor_nuevo)
        self.assertIsNone(auditoria.id_empleado_modifico)
        self.assertIsNone(auditoria.id_tarifa)

    def test_auditoria_comision_precision_valores(self):
        """Debe manejar precisión de valores correctamente"""
        auditoria = AuditoriaComisiones.objects.create(
            fecha_cambio=timezone.now(),
            campo_modificado="monto_comision",
            valor_anterior=Decimal("123456.7890"),  # 10 dígitos, 4 decimales
            valor_nuevo=Decimal("654321.0987"),
        )

        self.assertEqual(auditoria.valor_anterior, Decimal("123456.7890"))
        self.assertEqual(auditoria.valor_nuevo, Decimal("654321.0987"))

    def test_auditoria_comision_string_representation(self):
        """Debe retornar representación string correcta"""
        auditoria = AuditoriaComisiones.objects.create(
            fecha_cambio=timezone.now(), campo_modificado="test_campo", id_empleado_modifico=self.empleado
        )

        expected = f"AuditoriaComisiones #{auditoria.pk}"
        self.assertEqual(str(auditoria), expected)


class ImpuestosModelTest(TestCase):
    """Tests para modelo Impuestos"""

    def test_crear_impuesto_valido(self):
        """Debe crear impuesto con datos válidos"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA", porcentaje=Decimal("10.00"), vigente_desde=date.today(), estado=True
        )

        self.assertEqual(impuesto.nombre_impuesto, "IVA")
        self.assertEqual(impuesto.porcentaje, Decimal("10.00"))
        self.assertTrue(impuesto.estado)

    def test_impuesto_nombre_unico(self):
        """Debe validar unicidad de nombre_impuesto"""
        Impuestos.objects.create(nombre_impuesto="IVA_único", porcentaje=Decimal("10.00"), vigente_desde=date.today())

        with self.assertRaises(IntegrityError):
            Impuestos.objects.create(
                nombre_impuesto="IVA_único", porcentaje=Decimal("5.00"), vigente_desde=date.today()  # Nombre duplicado
            )

    def test_impuesto_porcentaje_precision(self):
        """Debe manejar precisión de porcentaje correctamente"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto="ISC",
            porcentaje=Decimal("99.99"),  # Máximo: 4 dígitos, 2 decimales
            vigente_desde=date.today(),
        )

        self.assertEqual(impuesto.porcentaje, Decimal("99.99"))

    def test_impuesto_vigencia_fechas(self):
        """Debe manejar fechas de vigencia correctamente"""
        fecha_inicio = date.today()
        fecha_fin = date.today() + timedelta(days=365)

        impuesto = Impuestos.objects.create(
            nombre_impuesto="Temporal", porcentaje=Decimal("5.00"), vigente_desde=fecha_inicio, vigente_hasta=fecha_fin
        )

        self.assertEqual(impuesto.vigente_desde, fecha_inicio)
        self.assertEqual(impuesto.vigente_hasta, fecha_fin)
        self.assertLess(impuesto.vigente_desde, impuesto.vigente_hasta)

    def test_impuesto_vigente_hasta_opcional(self):
        """Debe permitir vigente_hasta como None (vigencia indefinida)"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto="Permanente", porcentaje=Decimal("15.00"), vigente_desde=date.today()
        )

        self.assertIsNone(impuesto.vigente_hasta)

    def test_impuesto_activo_default(self):
        """Debe tener estado=True por defecto"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto="Default", porcentaje=Decimal("8.00"), vigente_desde=date.today()
        )

        self.assertTrue(impuesto.estado)

    def test_impuesto_string_representation(self):
        """Debe retornar representación string correcta"""
        impuesto = Impuestos.objects.create(
            nombre_impuesto="Test Representation", porcentaje=Decimal("12.00"), vigente_desde=date.today()
        )

        expected = f"Impuestos #{impuesto.pk}"
        self.assertEqual(str(impuesto), expected)

    def test_impuesto_verbose_names(self):
        """Debe tener nombres verbose correctos"""
        meta = Impuestos._meta
        self.assertEqual(meta.verbose_name, "Impuesto")
        self.assertEqual(meta.verbose_name_plural, "Impuestos")


class PuntosExpedicionModelTest(TestCase):
    """Tests para modelo PuntosExpedicion"""

    def test_crear_punto_expedicion_valido(self):
        """Debe crear punto de expedición con datos válidos"""
        punto = PuntosExpedicion.objects.create(
            codigo_establecimiento="001",
            codigo_punto_expedicion="001",
            descripcion_ubicacion="Local Principal - Av. Central",
            estado=True,
        )

        self.assertEqual(punto.codigo_establecimiento, "001")
        self.assertEqual(punto.codigo_punto_expedicion, "001")
        self.assertEqual(punto.descripcion_ubicacion, "Local Principal - Av. Central")

    def test_punto_expedicion_unique_together(self):
        """Debe validar unique_together (codigo_establecimiento, codigo_punto_expedicion)"""
        PuntosExpedicion.objects.create(codigo_establecimiento="001", codigo_punto_expedicion="002")

        with self.assertRaises(IntegrityError):
            PuntosExpedicion.objects.create(
                codigo_establecimiento="001", codigo_punto_expedicion="002"  # Combinación duplicada
            )

    def test_punto_expedicion_codigos_diferentes_establecimientos(self):
        """Debe permitir mismo código punto en diferentes establecimientos"""
        punto1 = PuntosExpedicion.objects.create(codigo_establecimiento="001", codigo_punto_expedicion="001")

        punto2 = PuntosExpedicion.objects.create(
            codigo_establecimiento="002", codigo_punto_expedicion="001"  # Mismo código punto, diferente establecimiento
        )

        self.assertEqual(punto1.codigo_punto_expedicion, punto2.codigo_punto_expedicion)
        self.assertNotEqual(punto1.codigo_establecimiento, punto2.codigo_establecimiento)

    def test_punto_expedicion_descripcion_opcional(self):
        """Debe permitir descripcion_ubicacion como None"""
        punto = PuntosExpedicion.objects.create(codigo_establecimiento="003", codigo_punto_expedicion="001")

        self.assertIsNone(punto.descripcion_ubicacion)

    def test_punto_expedicion_activo_default(self):
        """Debe tener estado=True por defecto"""
        punto = PuntosExpedicion.objects.create(codigo_establecimiento="004", codigo_punto_expedicion="001")

        self.assertTrue(punto.estado)

    def test_punto_expedicion_string_representation(self):
        """Debe retornar representación string correcta"""
        punto = PuntosExpedicion.objects.create(codigo_establecimiento="005", codigo_punto_expedicion="001")

        expected = f"PuntosExpedicion #{punto.pk}"
        self.assertEqual(str(punto), expected)


class DatosEmpresaModelTest(TestCase):
    """Tests para modelo DatosEmpresa"""

    def test_crear_datos_empresa_validos(self):
        """Debe crear datos de empresa con información válida"""
        empresa = DatosEmpresa.objects.create(
            ruc="80001234-5",
            razon_social="Cantina Tita S.A.",
            direccion="Av. Principal 123",
            ciudad="Asunción",
            pais="Paraguay",
            telefono="+595 21 123456",
            email="info@cantinatita.com",
            estado=True,
        )

        self.assertEqual(empresa.ruc, "80001234-5")
        self.assertEqual(empresa.razon_social, "Cantina Tita S.A.")
        self.assertEqual(empresa.email, "info@cantinatita.com")

    def test_datos_empresa_campos_obligatorios(self):
        """Debe validar campos obligatorios"""
        # Solo ruc y razon_social son obligatorios
        empresa = DatosEmpresa.objects.create(ruc="12345678-9", razon_social="Empresa Mínima")

        self.assertEqual(empresa.ruc, "12345678-9")
        self.assertEqual(empresa.razon_social, "Empresa Mínima")

    def test_datos_empresa_campos_opcionales(self):
        """Debe permitir campos opcionales como None"""
        empresa = DatosEmpresa.objects.create(ruc="98765432-1", razon_social="Solo Básico")

        self.assertIsNone(empresa.direccion)
        self.assertIsNone(empresa.ciudad)
        self.assertIsNone(empresa.pais)
        self.assertIsNone(empresa.telefono)
        self.assertIsNone(empresa.email)

    def test_datos_empresa_activo_default(self):
        """Debe tener estado=True por defecto"""
        empresa = DatosEmpresa.objects.create(ruc="11111111-1", razon_social="Default estado")

        self.assertTrue(empresa.estado)

    def test_datos_empresa_string_representation(self):
        """Debe retornar representación string correcta"""
        empresa = DatosEmpresa.objects.create(ruc="22222222-2", razon_social="Test Representation")

        expected = f"DatosEmpresa #{empresa.pk}"
        self.assertEqual(str(empresa), expected)


class ContabilidadModelsIntegrationTest(TestCase):
    """Tests de integración entre modelos de contabilidad"""

    def setUp(self):
        """Configurar datos completos para integración"""
        # Crear estructuras base
        self.punto_expedicion = PuntosExpedicion.objects.create(
            codigo_establecimiento="001", codigo_punto_expedicion="001", descripcion_ubicacion="Principal"
        )

        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%", porcentaje=Decimal("10.00"), vigente_desde=date.today()
        )

    def test_timbrados_con_punto_expedicion(self):
        """Debe crear timbrado asociado a punto de expedición"""
        timbrado = Timbrados.objects.create(
            nro_timbrado=12345678,
            tipo_documento="factura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=10000,
            estado=True,
            id_punto=self.punto_expedicion,
        )

        self.assertEqual(timbrado.id_punto, self.punto_expedicion)
        self.assertEqual(timbrado.id_punto.codigo_establecimiento, "001")

    def test_documento_tributario_con_timbrado(self):
        """Debe crear documento tributario asociado a timbrado"""
        # Crear timbrado primero
        timbrado = Timbrados.objects.create(
            nro_timbrado=87654321,
            tipo_documento="factura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=5000,
            id_punto=self.punto_expedicion,
        )

        # Crear documento
        documento = DocumentosTributarios.objects.create(
            nro_secuencial=1,
            fecha_emision=timezone.now(),
            monto_total=Decimal("115000.00"),
            nro_timbrado=timbrado,
            tipo_documento="factura",
        )

        self.assertEqual(documento.nro_timbrado, timbrado)
        self.assertEqual(documento.nro_secuencial, 1)

    def test_documento_tributario_unique_together(self):
        """Debe validar unique_together (nro_timbrado, nro_secuencial)"""
        timbrado = Timbrados.objects.create(
            nro_timbrado=11111111,
            tipo_documento="factura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=1000,
            id_punto=self.punto_expedicion,
        )

        # Primer documento
        DocumentosTributarios.objects.create(
            nro_secuencial=1,
            fecha_emision=timezone.now(),
            monto_total=Decimal("50000.00"),
            nro_timbrado=timbrado,
            tipo_documento="factura",
        )

        # Segundo documento con mismo timbrado y secuencial debe fallar
        with self.assertRaises(IntegrityError):
            DocumentosTributarios.objects.create(
                nro_secuencial=1,  # Mismo secuencial
                fecha_emision=timezone.now(),
                monto_total=Decimal("75000.00"),
                nro_timbrado=timbrado,  # Mismo timbrado
                tipo_documento="factura",
            )

    def test_relaciones_cascada_y_integridad(self):
        """Debe mantener integridad referencial correctamente"""
        # Crear estructura completa
        timbrado = Timbrados.objects.create(
            nro_timbrado=99999999,
            tipo_documento="factura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=100,
            id_punto=self.punto_expedicion,
        )

        documento = DocumentosTributarios.objects.create(
            nro_secuencial=1,
            fecha_emision=timezone.now(),
            monto_total=Decimal("110000.00"),
            nro_timbrado=timbrado,
            tipo_documento="factura",
        )

        # Verificar relaciones
        self.assertEqual(documento.nro_timbrado.id_punto.codigo_establecimiento, "001")

        # Contar documentos asociados al timbrado
        documentos_count = DocumentosTributarios.objects.filter(nro_timbrado=timbrado).count()
        self.assertEqual(documentos_count, 1)


class ContabilidadModelsStrTest(TestCase):
    """Tests __str__ para modelos de contabilidad sin str coverage."""

    def setUp(self):
        self.punto_expedicion = PuntosExpedicion.objects.create(
            codigo_establecimiento="001",
            codigo_punto_expedicion="001",
        )
        self.timbrado = Timbrados.objects.create(
            nro_timbrado=55555555,
            tipo_documento="factura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            nro_inicial=1,
            nro_final=9999,
            estado=True,
            id_punto=self.punto_expedicion,
        )

    def test_str_timbrado(self):
        self.assertIn("#", str(self.timbrado))

    def test_str_documentos_tributarios(self):
        doc = DocumentosTributarios.objects.create(
            nro_secuencial=999,
            fecha_emision=timezone.now(),
            monto_total=Decimal("50000.00"),
            nro_timbrado=self.timbrado,
            tipo_documento="factura",
        )
        self.assertIn("#", str(doc))
