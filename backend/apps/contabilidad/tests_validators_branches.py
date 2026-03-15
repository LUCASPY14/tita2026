"""
Tests de cobertura de ramas para contabilidad/validators.py.
Cubre exactamente los branches reportados como faltantes en el informe de cobertura.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.contabilidad.validators import (
    validar_estado_cierre_caja,
    validar_consistencia_cierre,
    validar_tipo_movimiento_caja,
    validar_monto_movimiento_caja,
    validar_monto_comision_movimiento,
    validar_activo_tarifa,
    validar_activo_timbrado,
    validar_estado_conciliacion,
    validar_fechas_conciliacion_consistencia,
    validar_cdc_documento,
    validar_url_kude_documento,
    validar_estado_sifen_documento,
    validar_nro_preimpreso_documento,
    validar_fechas_envio_respuesta_documento,
    validar_numeros_timbrado,
    validar_es_electronico_timbrado,
    validar_codigo_establecimiento,
    validar_codigo_punto_expedicion,
    validar_descripcion_punto_expedicion,
    validar_ruc_empresa,
    validar_razon_social_empresa,
    validar_direccion_empresa,
    validar_ciudad_empresa,
    validar_fecha_vigencia_tarifa,
    validar_fechas_timbrado,
)


# ──────────────────────────────────────────────────────────────────────────────
# validar_estado_cierre_caja
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarEstadoCierreCaja:
    def test_none_returns_without_error(self):
        """Line 130: early return when value is None/falsy"""
        validar_estado_cierre_caja(None)  # must not raise

    def test_empty_string_returns_without_error(self):
        """Line 130: early return when value is empty string"""
        validar_estado_cierre_caja("")  # must not raise

    def test_valid_abierto(self):
        validar_estado_cierre_caja("Abierto")

    def test_valid_cerrado(self):
        validar_estado_cierre_caja("Cerrado")

    def test_invalid_state_raises(self):
        with pytest.raises(ValidationError):
            validar_estado_cierre_caja("Invalido")


# ──────────────────────────────────────────────────────────────────────────────
# validar_consistencia_cierre
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarConsistenciaCierre:
    def test_none_inicial_returns(self):
        """Line 140: early return when monto_inicial is None"""
        validar_consistencia_cierre(None, 100, 10)  # must not raise

    def test_none_contado_returns(self):
        """Line 140: early return when monto_contado is None"""
        validar_consistencia_cierre(100, None, 10)  # must not raise

    def test_none_diferencia_exits_normally(self):
        """Line 144->exit: diferencia=None skips the if block, exits normally"""
        validar_consistencia_cierre(100, 100, None)  # must not raise

    def test_valid_diferencia_no_error(self):
        """Diferencia correcta: no raise"""
        validar_consistencia_cierre(50, 100, 50)  # must not raise

    def test_wrong_diferencia_raises(self):
        with pytest.raises(ValidationError):
            validar_consistencia_cierre(50, 100, 99)  # dif real=50, provided=99


# ──────────────────────────────────────────────────────────────────────────────
# validar_tipo_movimiento_caja
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarTipoMovimientoCaja:
    def test_too_long_raises(self):
        """Line 161: len > 20 raises"""
        with pytest.raises(ValidationError):
            validar_tipo_movimiento_caja("X" * 21)

    def test_invalid_type_raises(self):
        """Line 164: not in tipos_validos raises"""
        with pytest.raises(ValidationError):
            validar_tipo_movimiento_caja("InvalidoTipo")

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validar_tipo_movimiento_caja("")

    def test_valid_ingreso(self):
        validar_tipo_movimiento_caja("Ingreso")

    def test_valid_egreso(self):
        validar_tipo_movimiento_caja("Egreso")


# ──────────────────────────────────────────────────────────────────────────────
# validar_monto_movimiento_caja
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarMontoMovimientoCaja:
    def test_none_raises(self):
        """Line 174: None raises 'El monto es requerido'"""
        with pytest.raises(ValidationError):
            validar_monto_movimiento_caja(None)

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_movimiento_caja(Decimal("1000000000000.00"))

    def test_too_many_decimals_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_movimiento_caja(Decimal("100.001"))

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_movimiento_caja(Decimal("0"))

    def test_valid_monto(self):
        validar_monto_movimiento_caja(Decimal("500.50"))


# ──────────────────────────────────────────────────────────────────────────────
# validar_monto_comision_movimiento
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarMontoComisionMovimiento:
    def test_none_raises(self):
        """Line 193: None raises 'El monto de comision es requerido'"""
        with pytest.raises(ValidationError):
            validar_monto_comision_movimiento(None)

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_comision_movimiento(Decimal("1000000000000.00"))

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_comision_movimiento(Decimal("-1"))

    def test_zero_is_valid(self):
        validar_monto_comision_movimiento(Decimal("0"))

    def test_valid_comision(self):
        validar_monto_comision_movimiento(Decimal("10.50"))


# ──────────────────────────────────────────────────────────────────────────────
# validar_activo_tarifa and validar_activo_timbrado
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarActivoTarifa:
    def test_integer_raises(self):
        """Line 301: not isinstance(value, bool) raises"""
        with pytest.raises(ValidationError):
            validar_activo_tarifa(1)

    def test_string_raises(self):
        with pytest.raises(ValidationError):
            validar_activo_tarifa("true")

    def test_true_valid(self):
        validar_activo_tarifa(True)

    def test_false_valid(self):
        validar_activo_tarifa(False)


class TestValidarActivoTimbrado:
    def test_integer_raises(self):
        """Line 728: not isinstance(value, bool) raises"""
        with pytest.raises(ValidationError):
            validar_activo_timbrado(0)

    def test_string_raises(self):
        with pytest.raises(ValidationError):
            validar_activo_timbrado("True")

    def test_true_valid(self):
        validar_activo_timbrado(True)

    def test_false_valid(self):
        validar_activo_timbrado(False)


# ──────────────────────────────────────────────────────────────────────────────
# validar_estado_conciliacion
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarEstadoConciliacion:
    def test_too_long_raises(self):
        """Line 390: len > 20 raises"""
        with pytest.raises(ValidationError):
            validar_estado_conciliacion("X" * 21)

    def test_invalid_state_raises(self):
        with pytest.raises(ValidationError):
            validar_estado_conciliacion("EstadoInvalido")

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validar_estado_conciliacion("")

    def test_valid_pendiente(self):
        validar_estado_conciliacion("Pendiente")

    def test_valid_conciliado(self):
        validar_estado_conciliacion("Conciliado")


# ──────────────────────────────────────────────────────────────────────────────
# validar_fechas_conciliacion_consistencia
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarFechasConciliacionConsistencia:
    def test_none_creacion_returns(self):
        """Line 431: early return when either date is None"""
        validar_fechas_conciliacion_consistencia(None, datetime.now())  # must not raise

    def test_none_actualizacion_returns(self):
        validar_fechas_conciliacion_consistencia(datetime.now(), None)  # must not raise

    def test_actualizacion_before_creacion_raises(self):
        ahora = datetime.now()
        with pytest.raises(ValidationError):
            validar_fechas_conciliacion_consistencia(ahora, ahora - timedelta(days=1))

    def test_valid_dates_no_raise(self):
        ahora = datetime.now()
        validar_fechas_conciliacion_consistencia(ahora, ahora + timedelta(days=1))


# ──────────────────────────────────────────────────────────────────────────────
# validar_cdc_documento
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarCdcDocumento:
    def test_wrong_length_raises(self):
        with pytest.raises(ValidationError):
            validar_cdc_documento("ABC")

    def test_non_alphanumeric_raises(self):
        """Line 527: non-alphanumeric CDC raises"""
        with pytest.raises(ValidationError):
            validar_cdc_documento("!@#$" * 11)  # 44 non-alphanumeric chars

    def test_none_returns(self):
        validar_cdc_documento(None)  # must not raise

    def test_empty_returns(self):
        validar_cdc_documento("")  # must not raise

    def test_valid_44_alphanumeric(self):
        validar_cdc_documento("A" * 44)


# ──────────────────────────────────────────────────────────────────────────────
# validar_estado_sifen_documento
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarEstadoSifenDocumento:
    def test_too_long_raises(self):
        """Line 547: len > 9 raises"""
        with pytest.raises(ValidationError):
            validar_estado_sifen_documento("X" * 10)

    def test_invalid_estado_raises(self):
        """Line 556: not in estados_validos raises"""
        with pytest.raises(ValidationError):
            validar_estado_sifen_documento("Invalido")

    def test_none_returns(self):
        validar_estado_sifen_documento(None)

    def test_empty_returns(self):
        validar_estado_sifen_documento("")

    def test_valid_aprobado(self):
        validar_estado_sifen_documento("Aprobado")

    def test_valid_rechazado(self):
        validar_estado_sifen_documento("Rechazado")


# ──────────────────────────────────────────────────────────────────────────────
# validar_nro_preimpreso_documento
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarNroPreimpresoDocumento:
    def test_too_long_raises(self):
        """Line 556: len > 20 raises"""
        with pytest.raises(ValidationError):
            validar_nro_preimpreso_documento("x" * 21)

    def test_wrong_format_raises(self):
        with pytest.raises(ValidationError):
            validar_nro_preimpreso_documento("001-001-000000A")

    def test_none_returns(self):
        validar_nro_preimpreso_documento(None)

    def test_empty_returns(self):
        validar_nro_preimpreso_documento("")

    def test_valid_format(self):
        validar_nro_preimpreso_documento("001-001-0000001")


# ──────────────────────────────────────────────────────────────────────────────
# validar_fechas_envio_respuesta_documento
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarFechasEnvioRespuestaDocumento:
    def test_none_envio_returns(self):
        validar_fechas_envio_respuesta_documento(None, datetime.now())

    def test_none_respuesta_returns(self):
        validar_fechas_envio_respuesta_documento(datetime.now(), None)

    def test_respuesta_before_envio_raises(self):
        """Line 569: respuesta < envio raises"""
        ahora = datetime.now()
        with pytest.raises(ValidationError):
            validar_fechas_envio_respuesta_documento(ahora, ahora - timedelta(hours=1))

    def test_valid_dates_no_raise(self):
        ahora = datetime.now()
        validar_fechas_envio_respuesta_documento(ahora, ahora + timedelta(hours=1))


# ──────────────────────────────────────────────────────────────────────────────
# validar_numeros_timbrado
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarNumerosTimbrado:
    def test_final_less_than_inicial_raises(self):
        """Line 699: nro_final <= nro_inicial raises"""
        with pytest.raises(ValidationError):
            validar_numeros_timbrado(1000, 500)

    def test_final_equal_inicial_raises(self):
        with pytest.raises(ValidationError):
            validar_numeros_timbrado(1000, 1000)

    def test_initial_zero_raises(self):
        with pytest.raises(ValidationError):
            validar_numeros_timbrado(0, 1000)

    def test_valid_range(self):
        validar_numeros_timbrado(1, 1000000)

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_numeros_timbrado(1, 1000000001)


# ──────────────────────────────────────────────────────────────────────────────
# validar_es_electronico_timbrado
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarEsElectronicoTimbrado:
    def test_string_raises(self):
        """Line 717: not isinstance(value, int) raises"""
        with pytest.raises(ValidationError):
            validar_es_electronico_timbrado("1")

    def test_bool_raises(self):
        """bool is subclass of int BUT Python's isinstance(True, int) is True,
        so True/False pass the int check — test with float instead"""
        with pytest.raises(ValidationError):
            validar_es_electronico_timbrado(2)  # not 0 or 1

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validar_es_electronico_timbrado(None)

    def test_zero_valid(self):
        validar_es_electronico_timbrado(0)

    def test_one_valid(self):
        validar_es_electronico_timbrado(1)


# ──────────────────────────────────────────────────────────────────────────────
# validar_codigo_establecimiento & validar_codigo_punto_expedicion
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarCodigoEstablecimiento:
    def test_empty_raises(self):
        """Line 728: empty value raises 'es requerido'"""
        with pytest.raises(ValidationError):
            validar_codigo_establecimiento("")

    def test_non_digit_raises(self):
        with pytest.raises(ValidationError):
            validar_codigo_establecimiento("aaa")

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validar_codigo_establecimiento("000")

    def test_wrong_length_raises(self):
        with pytest.raises(ValidationError):
            validar_codigo_establecimiento("1")

    def test_valid_001(self):
        validar_codigo_establecimiento("001")

    def test_valid_999(self):
        validar_codigo_establecimiento("999")


class TestValidarCodigoPuntoExpedicion:
    def test_empty_raises(self):
        """Line 745: empty value raises 'es requerido'"""
        with pytest.raises(ValidationError):
            validar_codigo_punto_expedicion("")

    def test_non_digit_raises(self):
        with pytest.raises(ValidationError):
            validar_codigo_punto_expedicion("abc")

    def test_valid_001(self):
        validar_codigo_punto_expedicion("001")


# ──────────────────────────────────────────────────────────────────────────────
# validar_ruc_empresa
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarUrlKudeDocumento:
    def test_too_long_raises(self):
        """Line 527: len > 255 raises"""
        with pytest.raises(ValidationError):
            validar_url_kude_documento("x" * 256)

    def test_none_returns(self):
        validar_url_kude_documento(None)

    def test_empty_returns(self):
        validar_url_kude_documento("")


class TestValidarRucEmpresa:
    def test_empty_raises(self):
        """Line 780: empty value raises"""
        with pytest.raises(ValidationError):
            validar_ruc_empresa("")

    def test_none_raises(self):
        """Line 780: None raises"""
        with pytest.raises(ValidationError):
            validar_ruc_empresa(None)

    def test_too_long_raises(self):
        """Line 783: len > 20 raises"""
        with pytest.raises(ValidationError):
            validar_ruc_empresa("X" * 21)

    def test_wrong_format_raises(self):
        with pytest.raises(ValidationError):
            validar_ruc_empresa("12345678")

    def test_valid_ruc(self):
        validar_ruc_empresa("80000000-0")


# ──────────────────────────────────────────────────────────────────────────────
# validar_descripcion_punto_expedicion
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarDescripcionPuntoExpedicion:
    def test_none_returns(self):
        validar_descripcion_punto_expedicion(None)

    def test_empty_returns(self):
        validar_descripcion_punto_expedicion("")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            validar_descripcion_punto_expedicion("AB")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            validar_descripcion_punto_expedicion("A" * 101)

    def test_valid(self):
        validar_descripcion_punto_expedicion("Sucursal Central")


# ──────────────────────────────────────────────────────────────────────────────
# validar_razon_social_empresa / validar_direccion_empresa / validar_ciudad_empresa
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarRazonSocialEmpresa:
    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validar_razon_social_empresa("")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            validar_razon_social_empresa("AB")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            validar_razon_social_empresa("A" * 256)

    def test_valid(self):
        validar_razon_social_empresa("Cantina Tita S.R.L.")


class TestValidarDireccionEmpresa:
    def test_none_returns(self):
        validar_direccion_empresa(None)

    def test_empty_returns(self):
        validar_direccion_empresa("")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            validar_direccion_empresa("AB")

    def test_valid(self):
        validar_direccion_empresa("Av. Principal 123")


class TestValidarCiudadEmpresa:
    def test_none_returns(self):
        validar_ciudad_empresa(None)

    def test_empty_returns(self):
        validar_ciudad_empresa("")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            validar_ciudad_empresa("AB")

    def test_valid(self):
        validar_ciudad_empresa("Asuncion")


# ──────────────────────────────────────────────────────────────────────────────
# validar_fecha_vigencia_tarifa (line to cover: None fecha_fin)
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarFechaVigenciaTarifa:
    def test_none_fecha_fin_returns(self):
        """Vigencia indefinida: no raise"""
        ahora = datetime.now()
        validar_fecha_vigencia_tarifa(ahora, None)

    def test_fin_before_inicio_raises(self):
        ahora = datetime.now()
        with pytest.raises(ValidationError):
            validar_fecha_vigencia_tarifa(ahora, ahora - timedelta(days=1))


# ──────────────────────────────────────────────────────────────────────────────
# validar_fechas_timbrado (line to cover: > 730 days)
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarFechasTimbrado:
    def test_vigencia_exceeds_730_days_raises(self):
        inicio = date(2020, 1, 1)
        fin = date(2022, 2, 5)  # > 730 days
        with pytest.raises(ValidationError):
            validar_fechas_timbrado(inicio, fin)

    def test_fin_before_inicio_raises(self):
        inicio = date(2023, 1, 1)
        fin = date(2022, 1, 1)
        with pytest.raises(ValidationError):
            validar_fechas_timbrado(inicio, fin)

    def test_valid(self):
        inicio = date(2023, 1, 1)
        fin = date(2024, 1, 1)
        validar_fechas_timbrado(inicio, fin)
