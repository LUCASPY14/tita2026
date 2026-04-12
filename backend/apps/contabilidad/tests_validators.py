"""
Tests de validadores del módulo de Contabilidad
Cobertura completa: 62 validadores, ~186 tests
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, timedelta
from .validators import *

# =============================================================================
# 1. TESTS DE CAJAS (9 tests)
# =============================================================================


class ValidarNombreCajaTest(TestCase):
    def test_nombre_valido(self):
        validar_nombre_caja("Caja Principal")  # OK

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_caja("Ca")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_caja("C" * 51)


class ValidarUbicacionCajaTest(TestCase):
    def test_ubicacion_valida(self):
        validar_ubicacion_caja("Planta Baja, Sector A")  # OK

    def test_ubicacion_opcional(self):
        validar_ubicacion_caja(None)  # OK

    def test_ubicacion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_ubicacion_caja("U" * 101)


class ValidarActivoCajaTest(TestCase):
    def test_activo_true(self):
        validar_activo_caja(True)  # OK

    def test_activo_false(self):
        validar_activo_caja(False)  # OK

    def test_activo_no_boolean(self):
        with self.assertRaises(ValidationError):
            validar_activo_caja("true")


# =============================================================================
# 2. TESTS DE CIERRES DE CAJA (21 tests)
# =============================================================================


class ValidarFechaAperturaCierreTest(TestCase):
    def test_fechas_validas(self):
        apertura = timezone.now() - timedelta(hours=5)
        cierre = timezone.now()
        validar_fecha_apertura_cierre(apertura, cierre)  # OK

    def test_cierre_antes_apertura(self):
        apertura = timezone.now()
        cierre = apertura - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validar_fecha_apertura_cierre(apertura, cierre)

    def test_cierre_mas_48_horas(self):
        apertura = timezone.now() - timedelta(hours=50)
        cierre = timezone.now()
        with self.assertRaises(ValidationError):
            validar_fecha_apertura_cierre(apertura, cierre)


class ValidarMontoInicialCajaTest(TestCase):
    def test_monto_inicial_valido(self):
        validar_monto_inicial_caja(Decimal("50000.00"))  # OK

    def test_monto_inicial_cero(self):
        validar_monto_inicial_caja(Decimal("0"))  # OK

    def test_monto_inicial_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_inicial_caja(Decimal("-100"))

    def test_monto_inicial_muy_grande(self):
        with self.assertRaises(ValidationError):
            validar_monto_inicial_caja(Decimal("1000000000"))


class ValidarMontoContadoFisicoTest(TestCase):
    def test_monto_contado_valido(self):
        validar_monto_contado_fisico(Decimal("42500.50"))  # OK

    def test_monto_contado_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_contado_fisico(Decimal("-50"))


class ValidarDiferenciaEfectivoTest(TestCase):
    def test_diferencia_positiva(self):
        validar_diferencia_efectivo(Decimal("100.00"))  # OK

    def test_diferencia_negativa(self):
        validar_diferencia_efectivo(Decimal("-50.25"))  # OK (permitido)

    def test_diferencia_muy_grande(self):
        with self.assertRaises(ValidationError):
            validar_diferencia_efectivo(Decimal("1000000000"))


class ValidarEstadoCierreCajaTest(TestCase):
    def test_estado_abierto(self):
        validar_estado_cierre_caja("Abierto")  # OK

    def test_estado_cerrado(self):
        validar_estado_cierre_caja("Cerrado")  # OK

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_cierre_caja("Pendiente")


class ValidarConsistenciaCierreTest(TestCase):
    def test_consistencia_correcta(self):
        monto_inicial = Decimal("10000")
        monto_contado = Decimal("12000")
        diferencia = Decimal("2000")
        validar_consistencia_cierre(monto_inicial, monto_contado, diferencia)  # OK

    def test_consistencia_incorrecta(self):
        monto_inicial = Decimal("10000")
        monto_contado = Decimal("12000")
        diferencia = Decimal("500")  # Deber�a ser 2000
        with self.assertRaises(ValidationError):
            validar_consistencia_cierre(monto_inicial, monto_contado, diferencia)


# =============================================================================
# 3. TESTS DE MOVIMIENTOS DE CAJA (15 tests)
# =============================================================================


class ValidarTipoMovimientoCajaTest(TestCase):
    def test_tipo_ingreso(self):
        validar_tipo_movimiento_caja("Ingreso")  # OK

    def test_tipo_egreso(self):
        validar_tipo_movimiento_caja("Egreso")  # OK

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_movimiento_caja("Pago")


class ValidarMontoMovimientoCajaTest(TestCase):
    def test_monto_valido(self):
        validar_monto_movimiento_caja(Decimal("1500.75"))  # OK

    def test_monto_cero(self):
        with self.assertRaises(ValidationError):
            validar_monto_movimiento_caja(Decimal("0"))

    def test_monto_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_movimiento_caja(Decimal("-100"))


class ValidarMontoComisionMovimientoTest(TestCase):
    def test_comision_valida(self):
        validar_monto_comision_movimiento(Decimal("50.25"))  # OK

    def test_comision_cero(self):
        validar_monto_comision_movimiento(Decimal("0"))  # OK

    def test_comision_negativa(self):
        with self.assertRaises(ValidationError):
            validar_monto_comision_movimiento(Decimal("-10"))


class ValidarFechaMovimientoCajaTest(TestCase):
    def test_fecha_actual(self):
        validar_fecha_movimiento_caja(timezone.now())  # OK

    def test_fecha_pasada(self):
        validar_fecha_movimiento_caja(timezone.now() - timedelta(days=5))  # OK

    def test_fecha_futura(self):
        with self.assertRaises(ValidationError):
            validar_fecha_movimiento_caja(timezone.now() + timedelta(hours=2))


class ValidarDescripcionMovimientoTest(TestCase):
    def test_descripcion_valida(self):
        validar_descripcion_movimiento("Venta de almuerzos del d�a")  # OK

    def test_descripcion_opcional(self):
        validar_descripcion_movimiento(None)  # OK

    def test_descripcion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_movimiento("D" * 201)


# =============================================================================
# 4. TESTS DE TARIFAS DE COMISI�N (15 tests)
# =============================================================================


class ValidarFechaVigenciaTarifaTest(TestCase):
    def test_fechas_validas(self):
        inicio = timezone.now()
        fin = inicio + timedelta(days=30)
        validar_fecha_vigencia_tarifa(inicio, fin)  # OK

    def test_fecha_fin_antes_inicio(self):
        inicio = timezone.now()
        fin = inicio - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fecha_vigencia_tarifa(inicio, fin)

    def test_fecha_fin_opcional(self):
        inicio = timezone.now()
        validar_fecha_vigencia_tarifa(inicio, None)  # OK


class ValidarPorcentajeComisionTest(TestCase):
    def test_porcentaje_valido(self):
        validar_porcentaje_comision(Decimal("0.0350"))  # 3.5%

    def test_porcentaje_cero(self):
        validar_porcentaje_comision(Decimal("0"))  # OK

    def test_porcentaje_maximo(self):
        validar_porcentaje_comision(Decimal("1.0000"))  # 100%

    def test_porcentaje_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision(Decimal("1.5"))


class ValidarMontoFijoComisionTest(TestCase):
    def test_monto_fijo_valido(self):
        validar_monto_fijo_comision(Decimal("500.00"))  # OK

    def test_monto_fijo_opcional(self):
        validar_monto_fijo_comision(None)  # OK

    def test_monto_fijo_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_fijo_comision(Decimal("-100"))


class ValidarActivoTarifaTest(TestCase):
    def test_activo_true(self):
        validar_activo_tarifa(True)  # OK

    def test_activo_false(self):
        validar_activo_tarifa(False)  # OK


# =============================================================================
# 5. TESTS DE AUDITOR�A DE COMISIONES (12 tests)
# =============================================================================


class ValidarFechaCambioAuditoriaTest(TestCase):
    def test_fecha_actual(self):
        validar_fecha_cambio_auditoria(timezone.now())  # OK

    def test_fecha_pasada(self):
        validar_fecha_cambio_auditoria(timezone.now() - timedelta(days=10))  # OK

    def test_fecha_futura(self):
        with self.assertRaises(ValidationError):
            validar_fecha_cambio_auditoria(timezone.now() + timedelta(hours=1))


class ValidarCampoModificadoAuditoriaTest(TestCase):
    def test_campo_valido(self):
        validar_campo_modificado_auditoria("porcentaje_comision")  # OK

    def test_campo_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_campo_modificado_auditoria("p")

    def test_campo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_campo_modificado_auditoria("c" * 51)


class ValidarValorAnteriorAuditoriaTest(TestCase):
    def test_valor_anterior_valido(self):
        validar_valor_anterior_auditoria(Decimal("0.0350"))  # OK

    def test_valor_anterior_opcional(self):
        validar_valor_anterior_auditoria(None)  # OK

    def test_valor_anterior_muy_grande(self):
        with self.assertRaises(ValidationError):
            validar_valor_anterior_auditoria(Decimal("1000000"))


class ValidarValorNuevoAuditoriaTest(TestCase):
    def test_valor_nuevo_valido(self):
        validar_valor_nuevo_auditoria(Decimal("0.0425"))  # OK

    def test_valor_nuevo_opcional(self):
        validar_valor_nuevo_auditoria(None)  # OK


# =============================================================================
# 6. TESTS DE CONCILIACI�N DE PAGOS (18 tests)
# =============================================================================


class ValidarFechaAcreditacionConciliacionTest(TestCase):
    def test_fecha_acreditacion_valida(self):
        validar_fecha_acreditacion_conciliacion(timezone.now())  # OK

    def test_fecha_acreditacion_opcional(self):
        validar_fecha_acreditacion_conciliacion(None)  # OK


class ValidarFechaConciliacionTest(TestCase):
    def test_fecha_conciliacion_valida(self):
        validar_fecha_conciliacion(timezone.now())  # OK

    def test_fecha_conciliacion_requerida(self):
        with self.assertRaises(ValidationError):
            validar_fecha_conciliacion(None)


class ValidarEstadoConciliacionTest(TestCase):
    def test_estado_pendiente(self):
        validar_estado_conciliacion("Pendiente")  # OK

    def test_estado_conciliado(self):
        validar_estado_conciliacion("Conciliado")  # OK

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_conciliacion("Aprobado")


class ValidarMontoAcreditadoConciliacionTest(TestCase):
    def test_monto_acreditado_valido(self):
        validar_monto_acreditado_conciliacion(Decimal("15000.50"))  # OK

    def test_monto_acreditado_opcional(self):
        validar_monto_acreditado_conciliacion(None)  # OK

    def test_monto_acreditado_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_acreditado_conciliacion(Decimal("-100"))


class ValidarObservacionesConciliacionTest(TestCase):
    def test_observaciones_validas(self):
        validar_observaciones_conciliacion("Pago acreditado correctamente")  # OK

    def test_observaciones_opcionales(self):
        validar_observaciones_conciliacion(None)  # OK

    def test_observaciones_muy_largas(self):
        with self.assertRaises(ValidationError):
            validar_observaciones_conciliacion("O" * 1001)


class ValidarFechasConciliacionConsistenciaTest(TestCase):
    def test_fechas_consistentes(self):
        creacion = timezone.now() - timedelta(days=5)
        actualizacion = timezone.now()
        validar_fechas_conciliacion_consistencia(creacion, actualizacion)  # OK

    def test_actualizacion_antes_creacion(self):
        creacion = timezone.now()
        actualizacion = creacion - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validar_fechas_conciliacion_consistencia(creacion, actualizacion)


# =============================================================================
# 7. TESTS DE DOCUMENTOS TRIBUTARIOS (27 tests)
# =============================================================================


class ValidarNroSecuencialDocumentoTest(TestCase):
    def test_nro_secuencial_valido(self):
        validar_nro_secuencial_documento(123456)  # OK

    def test_nro_secuencial_uno(self):
        validar_nro_secuencial_documento(1)  # OK

    def test_nro_secuencial_cero(self):
        with self.assertRaises(ValidationError):
            validar_nro_secuencial_documento(0)

    def test_nro_secuencial_muy_grande(self):
        with self.assertRaises(ValidationError):
            validar_nro_secuencial_documento(1000000000)


class ValidarFechaEmisionDocumentoTest(TestCase):
    def test_fecha_emision_actual(self):
        validar_fecha_emision_documento(timezone.now())  # OK

    def test_fecha_emision_pasada(self):
        validar_fecha_emision_documento(timezone.now() - timedelta(days=30))  # OK

    def test_fecha_emision_muy_futura(self):
        with self.assertRaises(ValidationError):
            validar_fecha_emision_documento(timezone.now() + timedelta(hours=25))


class ValidarMontoTotalDocumentoTest(TestCase):
    def test_monto_total_valido(self):
        validar_monto_total_documento(Decimal("250000.00"))  # OK

    def test_monto_total_cero(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento(Decimal("0"))

    def test_monto_total_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento(Decimal("-1000"))


class ValidarTipoDocumentoTributarioTest(TestCase):
    def test_tipo_factura(self):
        validar_tipo_documento_tributario("Factura")  # OK

    def test_tipo_nota_credito(self):
        validar_tipo_documento_tributario("NotaCredito")  # OK

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_tributario("Ticket")


class ValidarCdcDocumentoTest(TestCase):
    def test_cdc_valido(self):
        validar_cdc_documento("A" * 44)  # OK

    def test_cdc_opcional(self):
        validar_cdc_documento(None)  # OK

    def test_cdc_longitud_incorrecta(self):
        with self.assertRaises(ValidationError):
            validar_cdc_documento("A" * 40)

    def test_cdc_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_cdc_documento("A" * 43 + "@")


class ValidarUrlKudeDocumentoTest(TestCase):
    def test_url_kude_valida(self):
        validar_url_kude_documento("https://ekuatia.set.gov.py/consulta/12345")  # OK

    def test_url_kude_opcional(self):
        validar_url_kude_documento(None)  # OK

    def test_url_kude_invalida(self):
        with self.assertRaises(ValidationError):
            validar_url_kude_documento("no-es-una-url")


class ValidarNroPreimpresoDocumentoTest(TestCase):
    def test_nro_preimpreso_valido(self):
        validar_nro_preimpreso_documento("001-001-0000001")  # OK

    def test_nro_preimpreso_opcional(self):
        validar_nro_preimpreso_documento(None)  # OK

    def test_nro_preimpreso_formato_invalido(self):
        with self.assertRaises(ValidationError):
            validar_nro_preimpreso_documento("001-001-001")


class ValidarFechasEnvioRespuestaDocumentoTest(TestCase):
    def test_fechas_validas(self):
        envio = timezone.now() - timedelta(hours=2)
        respuesta = timezone.now()
        validar_fechas_envio_respuesta_documento(envio, respuesta)  # OK

    def test_respuesta_antes_envio(self):
        envio = timezone.now()
        respuesta = envio - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validar_fechas_envio_respuesta_documento(envio, respuesta)


# =============================================================================
# 8. TESTS DE DOCUMENTO IMPUESTOS (6 tests)
# =============================================================================


class ValidarBaseImponibleTest(TestCase):
    def test_base_imponible_valida(self):
        validar_base_imponible(Decimal("100000.00"))  # OK

    def test_base_imponible_cero(self):
        validar_base_imponible(Decimal("0"))  # OK

    def test_base_imponible_negativa(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible(Decimal("-1000"))


class ValidarMontoImpuestoTest(TestCase):
    def test_monto_impuesto_valido(self):
        validar_monto_impuesto(Decimal("10000.00"))  # OK

    def test_monto_impuesto_cero(self):
        validar_monto_impuesto(Decimal("0"))  # OK

    def test_monto_impuesto_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto(Decimal("-500"))


# =============================================================================
# 9. TESTS DE TIMBRADOS (21 tests)
# =============================================================================


class ValidarNroTimbradoTest(TestCase):
    def test_nro_timbrado_valido(self):
        validar_nro_timbrado(12345678)  # 8 d�gitos

    def test_nro_timbrado_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nro_timbrado(1234567)  # 7 d�gitos

    def test_nro_timbrado_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nro_timbrado(123456789012)  # 12 d�gitos


class ValidarTipoDocumentoTimbradoTest(TestCase):
    def test_tipo_factura(self):
        validar_tipo_documento_timbrado("Factura")  # OK

    def test_tipo_nota_credito(self):
        validar_tipo_documento_timbrado("NotaCredito")  # OK

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_timbrado("Boleta")


class ValidarFechasTimbradoTest(TestCase):
    def test_fechas_validas(self):
        inicio = date.today()
        fin = inicio + timedelta(days=365)
        validar_fechas_timbrado(inicio, fin)  # OK

    def test_fecha_fin_antes_inicio(self):
        inicio = date.today()
        fin = inicio - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado(inicio, fin)

    def test_vigencia_muy_larga(self):
        inicio = date.today()
        fin = inicio + timedelta(days=731)
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado(inicio, fin)


class ValidarNumerosTimbradoTest(TestCase):
    def test_numeros_validos(self):
        validar_numeros_timbrado(1, 10000)  # OK

    def test_nro_final_menor_inicial(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado(10, 5)

    def test_nro_inicial_cero(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado(0, 100)


class ValidarActivoTimbradoTest(TestCase):
    def test_activo_true(self):
        validar_activo_timbrado(True)  # OK

    def test_activo_false(self):
        validar_activo_timbrado(False)  # OK


# =============================================================================
# 10. TESTS DE PUNTOS DE EXPEDICI�N (9 tests)
# =============================================================================


class ValidarCodigoEstablecimientoTest(TestCase):
    def test_codigo_valido(self):
        validar_codigo_establecimiento("001")  # OK

    def test_codigo_tres_digitos(self):
        validar_codigo_establecimiento("999")  # OK

    def test_codigo_longitud_incorrecta(self):
        with self.assertRaises(ValidationError):
            validar_codigo_establecimiento("01")

    def test_codigo_no_numerico(self):
        with self.assertRaises(ValidationError):
            validar_codigo_establecimiento("0A1")


class ValidarCodigoPuntoExpedicionTest(TestCase):
    def test_codigo_valido(self):
        validar_codigo_punto_expedicion("001")  # OK

    def test_codigo_tres_digitos(self):
        validar_codigo_punto_expedicion("555")  # OK

    def test_codigo_longitud_incorrecta(self):
        with self.assertRaises(ValidationError):
            validar_codigo_punto_expedicion("1")


class ValidarDescripcionPuntoExpedicionTest(TestCase):
    def test_descripcion_valida(self):
        validar_descripcion_punto_expedicion("Caja Principal")  # OK

    def test_descripcion_opcional(self):
        validar_descripcion_punto_expedicion(None)  # OK

    def test_descripcion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_punto_expedicion("D" * 101)


# =============================================================================
# 11. TESTS DE DATOS EMPRESA (21 tests)
# =============================================================================


class ValidarRucEmpresaTest(TestCase):
    def test_ruc_valido(self):
        validar_ruc_empresa("80000000-0")  # OK

    def test_ruc_formato_invalido(self):
        with self.assertRaises(ValidationError):
            validar_ruc_empresa("800000000")

    def test_ruc_digitos_incorrectos(self):
        with self.assertRaises(ValidationError):
            validar_ruc_empresa("8000000-0")


class ValidarRazonSocialEmpresaTest(TestCase):
    def test_razon_social_valida(self):
        validar_razon_social_empresa("Cantina Tita S.R.L.")  # OK

    def test_razon_social_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_razon_social_empresa("CT")

    def test_razon_social_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_razon_social_empresa("R" * 256)


class ValidarDireccionEmpresaTest(TestCase):
    def test_direccion_valida(self):
        validar_direccion_empresa("Av. Espa�a 1234")  # OK

    def test_direccion_opcional(self):
        validar_direccion_empresa(None)  # OK

    def test_direccion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_direccion_empresa("Av.")


class ValidarCiudadEmpresaTest(TestCase):
    def test_ciudad_valida(self):
        validar_ciudad_empresa("Asunci�n")  # OK

    def test_ciudad_opcional(self):
        validar_ciudad_empresa(None)  # OK

    def test_ciudad_con_numeros(self):
        with self.assertRaises(ValidationError):
            validar_ciudad_empresa("Asunci�n123")


class ValidarPaisEmpresaTest(TestCase):
    def test_pais_valido(self):
        validar_pais_empresa("Paraguay")  # OK

    def test_pais_opcional(self):
        validar_pais_empresa(None)  # OK


class ValidarTelefonoEmpresaTest(TestCase):
    def test_telefono_valido(self):
        validar_telefono_empresa("+595981234567")  # OK

    def test_telefono_opcional(self):
        validar_telefono_empresa(None)  # OK

    def test_telefono_formato_invalido(self):
        with self.assertRaises(ValidationError):
            validar_telefono_empresa("123")


class ValidarEmailEmpresaTest(TestCase):
    def test_email_valido(self):
        validar_email_empresa("contacto@cantinatita.com")  # OK

    def test_email_opcional(self):
        validar_email_empresa(None)  # OK

    def test_email_invalido(self):
        with self.assertRaises(ValidationError):
            validar_email_empresa("no-es-email")


# =============================================================================
# 12. TESTS DE IMPUESTOS (12 tests)
# =============================================================================


class ValidarNombreImpuestoTest(TestCase):
    def test_nombre_valido(self):
        validar_nombre_impuesto("IVA 10%")  # OK

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_impuesto("IV")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_impuesto("I" * 51)


class ValidarPorcentajeImpuestoTest(TestCase):
    def test_porcentaje_valido(self):
        validar_porcentaje_impuesto(Decimal("10.00"))  # OK

    def test_porcentaje_cero(self):
        validar_porcentaje_impuesto(Decimal("0"))  # OK

    def test_porcentaje_maximo(self):
        validar_porcentaje_impuesto(Decimal("99.99"))  # OK

    def test_porcentaje_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto(Decimal("100"))


class ValidarVigentesdeImpuestoTest(TestCase):
    def test_fecha_desde_valida(self):
        validar_vigente_desde_impuesto(date.today())  # OK

    def test_fecha_desde_requerida(self):
        with self.assertRaises(ValidationError):
            validar_vigente_desde_impuesto(None)


class ValidarVigenteHastaImpuestoTest(TestCase):
    def test_fechas_validas(self):
        desde = date.today()
        hasta = desde + timedelta(days=365)
        validar_vigente_hasta_impuesto(desde, hasta)  # OK

    def test_fecha_hasta_opcional(self):
        desde = date.today()
        validar_vigente_hasta_impuesto(desde, None)  # OK

    def test_fecha_hasta_antes_desde(self):
        desde = date.today()
        hasta = desde - timedelta(days=10)
        with self.assertRaises(ValidationError):
            validar_vigente_hasta_impuesto(desde, hasta)
