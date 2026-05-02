"""Extended tests for apps/contabilidad/validators.py - targeting missing branches."""

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.validators import (
    validar_nombre_caja,
    validar_ubicacion_caja,
    validar_activo_caja,
    validar_fecha_apertura_cierre,
    validar_monto_inicial_caja,
    validar_monto_contado_fisico,
    validar_diferencia_efectivo,
    validar_estado_cierre_caja,
    validar_consistencia_cierre,
    validar_tipo_movimiento_caja,
    validar_monto_movimiento_caja,
    validar_monto_comision_movimiento,
    validar_fecha_movimiento_caja,
    validar_descripcion_movimiento,
    validar_fecha_vigencia_tarifa,
    validar_porcentaje_comision,
    validar_monto_fijo_comision,
    validar_activo_tarifa,
    validar_fecha_cambio_auditoria,
    validar_campo_modificado_auditoria,
    validar_valor_anterior_auditoria,
    validar_valor_nuevo_auditoria,
    validar_fecha_acreditacion_conciliacion,
    validar_fecha_conciliacion,
    validar_estado_conciliacion,
    validar_monto_acreditado_conciliacion,
    validar_observaciones_conciliacion,
    validar_fechas_conciliacion_consistencia,
    validar_nro_secuencial_documento,
    validar_fecha_emision_documento,
    validar_monto_total_documento,
    validar_tipo_documento_tributario,
    validar_cdc_documento,
    validar_url_kude_documento,
    validar_nro_preimpreso_documento,
    validar_fechas_envio_respuesta_documento,
    validar_base_imponible,
    validar_monto_impuesto,
    validar_nro_timbrado,
    validar_tipo_documento_timbrado,
    validar_fechas_timbrado,
    validar_numeros_timbrado,
    validar_activo_timbrado,
    validar_codigo_establecimiento,
    validar_codigo_punto_expedicion,
    validar_descripcion_punto_expedicion,
    validar_ruc_empresa,
    validar_razon_social_empresa,
    validar_direccion_empresa,
    validar_ciudad_empresa,
    validar_pais_empresa,
    validar_telefono_empresa,
    validar_email_empresa,
    validar_nombre_impuesto,
    validar_porcentaje_impuesto,
    validar_vigente_desde_impuesto,
    validar_vigente_hasta_impuesto,
)


class NombreCajaExtendedTest(TestCase):
    """Cover line 26 - invalid chars in nombre_caja"""

    def test_nombre_con_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_nombre_caja("Caja@#$!")

    def test_nombre_con_punto_invalido(self):
        with self.assertRaises(ValidationError):
            validar_nombre_caja("Caja.")


class UbicacionCajaExtendedTest(TestCase):
    """Cover line 36 - too short ubicacion"""

    def test_ubicacion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_ubicacion_caja("AB")


class FechaAperturaCierreExtendedTest(TestCase):
    """Cover lines 55, 58, 60 - datetime type checks and cierre_none"""

    def test_apertura_no_es_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_apertura_cierre("2024-01-01", timezone.now())

    def test_cierre_no_es_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_apertura_cierre(timezone.now(), "2024-01-01")

    def test_cierre_es_none(self):
        # Should not raise - cierre can be null
        validar_fecha_apertura_cierre(timezone.now(), None)


class MontoInicialCajaExtendedTest(TestCase):
    """Cover lines 74, 78-79, 88 - ValueError, max, decimals"""

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_inicial_caja("abc")

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_inicial_caja(Decimal("9999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_inicial_caja(Decimal("100.001"))

    def test_monto_none(self):
        # Should not raise - None is allowed
        validar_monto_inicial_caja(None)


class MontoContadoFisicoExtendedTest(TestCase):
    """Cover lines 94, 98-99 - ValueError, max, decimals"""

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_contado_fisico("xyz")

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_contado_fisico(Decimal("9999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_contado_fisico(Decimal("100.001"))

    def test_monto_none(self):
        validar_monto_contado_fisico(None)


class DiferenciaEfectivoExtendedTest(TestCase):
    """Cover lines 104, 107, 113 - ValueError, max, decimals"""

    def test_diferencia_invalida_texto(self):
        with self.assertRaises(ValidationError):
            validar_diferencia_efectivo("no_valido")

    def test_diferencia_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_diferencia_efectivo(Decimal("9999999999.99"))

    def test_diferencia_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_diferencia_efectivo(Decimal("100.001"))

    def test_diferencia_none(self):
        validar_diferencia_efectivo(None)


class MontoMovimientoCajaExtendedTest(TestCase):
    """Cover lines 174, 178-179, 184, 187 - ValueError, max, decimals, zero"""

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_movimiento_caja("abc")

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_movimiento_caja(Decimal("9999999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_movimiento_caja(Decimal("100.001"))


class MontoComisionMovimientoExtendedTest(TestCase):
    """Cover lines 193, 197-198, 203, 206 - ValueError, max, decimals"""

    def test_comision_invalida_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_comision_movimiento("abc")

    def test_comision_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_comision_movimiento(Decimal("9999999999999.99"))

    def test_comision_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_comision_movimiento(Decimal("100.001"))


class FechaMovimientoCajaExtendedTest(TestCase):
    """Cover lines 212, 215, 219 - None, not datetime/date, date type handling"""

    def test_fecha_none(self):
        with self.assertRaises(ValidationError):
            validar_fecha_movimiento_caja(None)

    def test_fecha_no_es_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_movimiento_caja("2024-01-01")

    def test_fecha_es_date_simple(self):
        # date (not datetime) should work - convert to datetime
        validar_fecha_movimiento_caja(date.today())


class FechaVigenciaTarifaExtendedTest(TestCase):
    """Cover lines 251, 253 - datetime type checks"""

    def test_inicio_no_es_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_vigencia_tarifa("2024-01-01", timezone.now())

    def test_fin_no_es_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_vigencia_tarifa(timezone.now(), "2024-01-01")


class PorcentajeComisionExtendedTest(TestCase):
    """Cover lines 262, 266-267, 270, 276 - None, ValueError, max, decimals"""

    def test_porcentaje_none(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision(None)

    def test_porcentaje_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision("abc")

    def test_porcentaje_negativo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision(Decimal("-0.1"))

    def test_porcentaje_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision(Decimal("1.0001"))

    def test_porcentaje_cinco_decimales(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_comision(Decimal("0.00001"))


class MontoFijoComisionExtendedTest(TestCase):
    """Cover lines 286-287, 292, 295, 301 - ValueError, max, decimals"""

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_fijo_comision("abc")

    def test_monto_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_fijo_comision(Decimal("-1"))

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_fijo_comision(Decimal("99999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_fijo_comision(Decimal("100.001"))


class FechaCambioAuditoriaExtendedTest(TestCase):
    """Cover lines 312, 315 - None, not datetime"""

    def test_fecha_none(self):
        with self.assertRaises(ValidationError):
            validar_fecha_cambio_auditoria(None)

    def test_fecha_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_cambio_auditoria("2024-01-01")


class ValorAnteriorAuditoriaExtendedTest(TestCase):
    """Cover lines 337-338, 344 - ValueError, max, decimals"""

    def test_valor_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_valor_anterior_auditoria("abc")

    def test_valor_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_valor_anterior_auditoria(Decimal("9999999.9999"))

    def test_valor_cinco_decimales(self):
        with self.assertRaises(ValidationError):
            validar_valor_anterior_auditoria(Decimal("100.00001"))


class ValorNuevoAuditoriaExtendedTest(TestCase):
    """Cover lines 354-355, 358, 361 - ValueError, max, decimals"""

    def test_valor_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_valor_nuevo_auditoria("abc")

    def test_valor_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_valor_nuevo_auditoria(Decimal("9999999.9999"))

    def test_valor_cinco_decimales(self):
        with self.assertRaises(ValidationError):
            validar_valor_nuevo_auditoria(Decimal("100.00001"))


class FechaAcreditacionConciliacionExtendedTest(TestCase):
    """Cover line 375 - not datetime type"""

    def test_fecha_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_acreditacion_conciliacion("2024-01-01")


class FechaConciliacionExtendedTest(TestCase):
    """Cover line 384, 390 - None, not datetime"""

    def test_fecha_none(self):
        with self.assertRaises(ValidationError):
            validar_fecha_conciliacion(None)

    def test_fecha_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_conciliacion("2024-01-01")


class EstadoConciliacionExtendedTest(TestCase):
    """Cover line 393 - estado too long"""

    def test_estado_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_estado_conciliacion("A" * 25)


class MontoAcreditadoConciliacionExtendedTest(TestCase):
    """Cover lines 407-408, 413, 416 - ValueError, max, decimals"""

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_acreditado_conciliacion("abc")

    def test_monto_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_acreditado_conciliacion(Decimal("-1"))

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_acreditado_conciliacion(Decimal("9999999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_acreditado_conciliacion(Decimal("100.001"))


class FechasConciliacionConsistenciaExtendedTest(TestCase):
    """Cover lines 431, 434, 436 - not datetime type checks"""

    def test_creacion_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fechas_conciliacion_consistencia("2024-01-01", timezone.now())

    def test_actualizacion_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fechas_conciliacion_consistencia(timezone.now(), "2024-01-01")


class NroSecuencialDocumentoExtendedTest(TestCase):
    """Cover lines 450, 453 - None, not int"""

    def test_nro_none(self):
        with self.assertRaises(ValidationError):
            validar_nro_secuencial_documento(None)

    def test_nro_no_es_int(self):
        with self.assertRaises(ValidationError):
            validar_nro_secuencial_documento("123")


class FechaEmisionDocumentoExtendedTest(TestCase):
    """Cover lines 464, 467 - None, not datetime"""

    def test_fecha_none(self):
        with self.assertRaises(ValidationError):
            validar_fecha_emision_documento(None)

    def test_fecha_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fecha_emision_documento("2024-01-01")


class MontoTotalDocumentoExtendedTest(TestCase):
    """Cover lines 479, 483-484, 489, 492 - None, ValueError, max, decimals"""

    def test_monto_none(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento(None)

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento("abc")

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento(Decimal("9999999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_total_documento(Decimal("100.001"))


class TipoDocumentoTributarioExtendedTest(TestCase):
    """Cover line 498, 501 - empty, too long"""

    def test_tipo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_tributario("")

    def test_tipo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_tributario("A" * 15)


class FechasEnvioRespuestaDocumentoExtendedTest(TestCase):
    """Cover lines 569, 572, 574 - not datetime type checks"""

    def test_envio_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fechas_envio_respuesta_documento("2024-01-01", timezone.now())

    def test_respuesta_no_datetime(self):
        with self.assertRaises(ValidationError):
            validar_fechas_envio_respuesta_documento(timezone.now(), "2024-01-01")


class BaseImponibleExtendedTest(TestCase):
    """Cover lines 588, 592-593, 598, 601 - None, ValueError, max, decimals"""

    def test_base_none(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible(None)

    def test_base_invalida_texto(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible("abc")

    def test_base_negativa(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible(Decimal("-1"))

    def test_base_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible(Decimal("9999999999999.99"))

    def test_base_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_base_imponible(Decimal("100.001"))


class MontoImpuestoExtendedTest(TestCase):
    """Cover lines 607, 611-612, 617, 620 - None, ValueError, max, decimals"""

    def test_monto_none(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto(None)

    def test_monto_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto("abc")

    def test_monto_negativo(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto(Decimal("-1"))

    def test_monto_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto(Decimal("99999999999.99"))

    def test_monto_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_monto_impuesto(Decimal("100.001"))


class NroTimbradoExtendedTest(TestCase):
    """Cover lines 631, 634 - None, not int"""

    def test_nro_none(self):
        with self.assertRaises(ValidationError):
            validar_nro_timbrado(None)

    def test_nro_no_es_int(self):
        with self.assertRaises(ValidationError):
            validar_nro_timbrado("12345678")


class TipoDocumentoTimbradoExtendedTest(TestCase):
    """Cover lines 646, 649 - empty, too long"""

    def test_tipo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_timbrado("")

    def test_tipo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_tipo_documento_timbrado("A" * 15)


class FechasTimbradoExtendedTest(TestCase):
    """Cover lines 659, 661, 664, 666 - None dates, not date type"""

    def test_inicio_none(self):
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado(None, date.today())

    def test_fin_none(self):
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado(date.today(), None)

    def test_inicio_no_date(self):
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado("2024-01-01", date.today() + timedelta(days=30))

    def test_fin_no_date(self):
        with self.assertRaises(ValidationError):
            validar_fechas_timbrado(date.today(), "2024-12-31")


class NumerosTimbradoExtendedTest(TestCase):
    """Cover lines 682, 684, 687, 689 - None values, not int"""

    def test_inicial_none(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado(None, 100)

    def test_final_none(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado(1, None)

    def test_inicial_no_es_int(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado("1", 100)

    def test_final_no_es_int(self):
        with self.assertRaises(ValidationError):
            validar_numeros_timbrado(1, "100")


class CodigoEstablecimientoExtendedTest(TestCase):
    """Cover lines 705, 708 - non-digit, out of range"""

    def test_codigo_no_numerico(self):
        with self.assertRaises(ValidationError):
            validar_codigo_establecimiento("abc")

    def test_codigo_fuera_de_rango(self):
        with self.assertRaises(ValidationError):
            validar_codigo_establecimiento("000")


class CodigoPuntoExpedicionExtendedTest(TestCase):
    """Cover line 717 - non-digit"""

    def test_codigo_no_numerico(self):
        with self.assertRaises(ValidationError):
            validar_codigo_punto_expedicion("abc")

    def test_codigo_fuera_de_rango(self):
        with self.assertRaises(ValidationError):
            validar_codigo_punto_expedicion("000")


class DescripcionPuntoExpedicionExtendedTest(TestCase):
    """Cover line 728 - too short description"""

    def test_descripcion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_descripcion_punto_expedicion("AB")


class DireccionEmpresaExtendedTest(TestCase):
    """Cover line 780, 783 - too short, too long"""

    def test_direccion_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_direccion_empresa("Abc")

    def test_direccion_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_direccion_empresa("A" * 260)


class CiudadEmpresaExtendedTest(TestCase):
    """Cover lines 807, 816, 818 - too short, too long, invalid chars"""

    def test_ciudad_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_ciudad_empresa("AB")

    def test_ciudad_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_ciudad_empresa("A" * 105)

    def test_ciudad_con_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_ciudad_empresa("Ciudad123!")


class PaisEmpresaExtendedTest(TestCase):
    """Cover lines 831, 833, 837 - too short, too long, invalid chars"""

    def test_pais_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_pais_empresa("AB")

    def test_pais_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_pais_empresa("A" * 105)

    def test_pais_con_numeros(self):
        with self.assertRaises(ValidationError):
            validar_pais_empresa("Paraguay123")


class TelefonoEmpresaExtendedTest(TestCase):
    """Cover line 846 - too long"""

    def test_telefono_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_telefono_empresa("+595" + "9" * 20)


class EmailEmpresaExtendedTest(TestCase):
    """Cover line 863 - too long"""

    def test_email_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_email_empresa("a" * 95 + "@example.com")


class PorcentajeImpuestoExtendedTest(TestCase):
    """Cover lines 889, 893-894, 897, 903 - None, ValueError, negative, max, decimals"""

    def test_porcentaje_none(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto(None)

    def test_porcentaje_invalido_texto(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto("abc")

    def test_porcentaje_negativo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto(Decimal("-1"))

    def test_porcentaje_excede_maximo(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto(Decimal("100.00"))

    def test_porcentaje_tres_decimales(self):
        with self.assertRaises(ValidationError):
            validar_porcentaje_impuesto(Decimal("10.001"))


class VigentesdeImpuestoExtendedTest(TestCase):
    """Cover line 912 - not date type"""

    def test_fecha_no_date(self):
        with self.assertRaises(ValidationError):
            validar_vigente_desde_impuesto("2024-01-01")


class VigenteHastaImpuestoExtendedTest(TestCase):
    """Cover lines 921, 924, 926 - desde is None, not date types"""

    def test_desde_none_cuando_hasta_existe(self):
        with self.assertRaises(ValidationError):
            validar_vigente_hasta_impuesto(None, date.today())

    def test_desde_no_date(self):
        with self.assertRaises(ValidationError):
            validar_vigente_hasta_impuesto("2024-01-01", date.today())

    def test_hasta_no_date(self):
        with self.assertRaises(ValidationError):
            validar_vigente_hasta_impuesto(date.today(), "2024-12-31")
