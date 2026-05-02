"""
Tests de cobertura de ramas para almuerzos/validators.py.
Cubre exactamente los branches reportados como faltantes en el informe de cobertura.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError

from apps.almuerzos.validators import (
    validar_precio_unitario_tipo,
    validar_motivo_rechazo,
    validar_coherencia_montos_cuenta,
    validar_monto_total_cuenta,
    validar_monto_pagado_cuenta,
    validar_estado_pago_mensual,
    validar_referencia_pago,
    validar_palabras_clave_alergeno,
    validar_nivel_severidad_alergeno,
    determinar_si_cobra,
    validar_limite_registros_diarios,
)

# ──────────────────────────────────────────────────────────────────────────────
# validar_precio_unitario_tipo
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarPrecioUnitarioTipo:
    def test_valid_price_exits_normally(self):
        """Line 220->exit: integer value (no dot) takes False branch at '.' check"""
        validar_precio_unitario_tipo(Decimal("100"))  # str = '100', no dot → 220->exit

    def test_valid_decimal_price(self):
        validar_precio_unitario_tipo(Decimal("100.00"))  # must not raise

    def test_valid_max_boundary(self):
        validar_precio_unitario_tipo(Decimal("500000.00"))

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validar_precio_unitario_tipo(Decimal("0"))

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validar_precio_unitario_tipo(Decimal("-1"))

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_precio_unitario_tipo(Decimal("500001"))

    def test_too_many_decimals_raises(self):
        with pytest.raises(ValidationError):
            validar_precio_unitario_tipo(Decimal("100.001"))


# ──────────────────────────────────────────────────────────────────────────────
# validar_motivo_rechazo
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarMotivoRechazo:
    def test_estado_aprobado_motivo_none_exits_normally(self):
        """Line 503->exit: estado != Rechazado AND valor=None → exits normally"""
        validar_motivo_rechazo(None, "Aprobado")  # must not raise

    def test_estado_aprobado_motivo_empty_exits_normally(self):
        """Line 503->exit: estado != Rechazado AND valor="" → exits normally"""
        validar_motivo_rechazo("", "Aprobado")  # must not raise

    def test_estado_rechazado_motivo_valido(self):
        """Valid rejection with proper motivo"""
        validar_motivo_rechazo("Motivo suficientemente largo para pasar", "Rechazado")

    def test_estado_rechazado_motivo_none_raises(self):
        with pytest.raises(ValidationError):
            validar_motivo_rechazo(None, "Rechazado")

    def test_estado_rechazado_motivo_corto_raises(self):
        with pytest.raises(ValidationError):
            validar_motivo_rechazo("Corto", "Rechazado")

    def test_estado_no_rechazado_con_motivo_raises(self):
        """El motivo solo aplica a Rechazado; si hay motivo con otro estado, error"""
        with pytest.raises(ValidationError):
            validar_motivo_rechazo("Motivo invalido en estado no rechazado", "Aprobado")


# ──────────────────────────────────────────────────────────────────────────────
# validar_monto_total_cuenta
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarMontoTotalCuenta:
    def test_valid_integer_monto_exits_normally(self):
        """Line 729->exit: integer value (no dot) takes False branch at '.' check"""
        validar_monto_total_cuenta(Decimal("1000"))  # str = '1000', no dot → 729->exit

    def test_valid_monto_exits_normally(self):
        validar_monto_total_cuenta(Decimal("1000.00"))  # must not raise

    def test_valid_small_monto(self):
        validar_monto_total_cuenta(Decimal("0.01"))

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_total_cuenta(Decimal("-1"))

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_total_cuenta(Decimal("10000001"))

    def test_too_many_decimals_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_total_cuenta(Decimal("100.001"))


# ──────────────────────────────────────────────────────────────────────────────
# validar_monto_pagado_cuenta
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarMontoPagadoCuenta:
    def test_valid_monto_exits_normally(self):
        """Line 796->exit: valid monto exits without raising"""
        validar_monto_pagado_cuenta(Decimal("500.00"))  # must not raise

    def test_valid_zero(self):
        validar_monto_pagado_cuenta(Decimal("0"))

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_pagado_cuenta(Decimal("-0.01"))

    def test_exceeds_max_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_pagado_cuenta(Decimal("10000001"))

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validar_monto_pagado_cuenta(None)


# ──────────────────────────────────────────────────────────────────────────────
# validar_coherencia_montos_cuenta
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarCoherenciaMontosCuenta:
    def test_monto_total_none_returns(self):
        """Early return when monto_total is None"""
        validar_coherencia_montos_cuenta(None, 100)  # must not raise

    def test_monto_pagado_none_returns(self):
        """Early return when monto_pagado is None"""
        validar_coherencia_montos_cuenta(100, None)  # must not raise

    def test_invalid_decimal_values_returns(self):
        """Line 840: except block when values can't be converted to Decimal"""
        validar_coherencia_montos_cuenta("not-a-number", "also-not")  # must not raise

    def test_pagado_exceeds_tolerancia_raises(self):
        """Lines 845-846: monto_pagado > monto_total * 1.10 raises"""
        with pytest.raises(ValidationError):
            validar_coherencia_montos_cuenta(100, 200)  # 200 > 100 * 1.10 = 110

    def test_pagado_within_tolerancia_ok(self):
        """No raise when pagado <= total * 1.10"""
        validar_coherencia_montos_cuenta(100, 110)  # exactly at tolerance


# ──────────────────────────────────────────────────────────────────────────────
# validar_estado_pago_mensual
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarEstadoPagoMensual:
    def test_none_returns(self):
        """None is optional - returns without error"""
        validar_estado_pago_mensual(None)  # must not raise

    def test_empty_returns(self):
        """Empty string is optional - returns without error"""
        validar_estado_pago_mensual("")  # must not raise

    def test_invalid_estado_raises(self):
        with pytest.raises(ValidationError):
            validar_estado_pago_mensual("Invalido")

    def test_valid_pendiente(self):
        validar_estado_pago_mensual("Pendiente")

    def test_valid_confirmado(self):
        validar_estado_pago_mensual("Confirmado")


# ──────────────────────────────────────────────────────────────────────────────
# validar_referencia_pago
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarReferenciaPago:
    def test_none_returns(self):
        """Line 840: None is optional - returns without error"""
        validar_referencia_pago(None)  # must not raise

    def test_empty_returns(self):
        validar_referencia_pago("")  # must not raise

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            validar_referencia_pago("X" * 51)

    def test_invalid_chars_raises(self):
        with pytest.raises(ValidationError):
            validar_referencia_pago("REF!@#$")

    def test_valid_reference(self):
        validar_referencia_pago("TRX-2024-001")


# ──────────────────────────────────────────────────────────────────────────────
# validar_palabras_clave_alergeno
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarPalabrasClave:
    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno(None)

    def test_invalid_json_string_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno("{not-valid-json}")

    def test_not_a_list_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno({"key": "value"})

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno([])

    def test_too_many_keywords_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno(["kw"] * 21)

    def test_non_string_element_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno([123])

    def test_too_short_element_raises(self):
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno(["x"])

    def test_too_long_element_raises(self):
        """Line 1080: element > 50 chars raises"""
        with pytest.raises(ValidationError):
            validar_palabras_clave_alergeno(["x" * 51])

    def test_valid_list(self):
        validar_palabras_clave_alergeno(["gluten", "lactosa", "nueces"])

    def test_valid_json_string(self):
        import json

        validar_palabras_clave_alergeno(json.dumps(["gluten", "lactosa"]))


# ──────────────────────────────────────────────────────────────────────────────
# validar_nivel_severidad_alergeno
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarNivelSeveridadAlergeno:
    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validar_nivel_severidad_alergeno(None)

    def test_invalid_nivel_raises(self):
        with pytest.raises(ValidationError):
            validar_nivel_severidad_alergeno("Extrema")

    def test_valid_baja(self):
        validar_nivel_severidad_alergeno("Baja")

    def test_valid_critica(self):
        validar_nivel_severidad_alergeno("Crítica")

    def test_valid_alta(self):
        validar_nivel_severidad_alergeno("Alta")


# ──────────────────────────────────────────────────────────────────────────────
# validar_limite_registros_diarios — branches not requiring real DB
# ──────────────────────────────────────────────────────────────────────────────


class TestValidarLimiteRegistrosDiarios:
    def test_none_id_hijo_returns(self):
        """Line 503->exit: early return when id_hijo is None"""
        validar_limite_registros_diarios(None, date.today())  # must not raise

    def test_none_fecha_consumo_returns(self):
        """Line 503->exit: early return when fecha_consumo is None"""
        validar_limite_registros_diarios(1, None)  # must not raise

    def test_invalid_date_string_returns(self):
        """Line 530: invalid date string triggers except → return"""
        validar_limite_registros_diarios(1, "not-a-date")  # must not raise

    @pytest.mark.django_db
    def test_con_registro_actual_id_executes_exclude(self):
        """Line 549: query.exclude called when registro_actual_id is not None"""
        # No matching records in DB → returns True (0 existing == 0)
        result = validar_limite_registros_diarios(99999, date.today(), registro_actual_id=88888)
        assert result is True


# ──────────────────────────────────────────────────────────────────────────────
# determinar_si_cobra — branches not requiring real DB
# ──────────────────────────────────────────────────────────────────────────────


class TestDeterminarSiCobra:
    def test_none_id_hijo_returns_true(self):
        """Line 584->exit: early return True when id_hijo is None"""
        result = determinar_si_cobra(None, date.today())
        assert result is True

    def test_none_fecha_returns_true(self):
        """Line 584->exit: early return True when fecha is None"""
        result = determinar_si_cobra(1, None)
        assert result is True

    def test_invalid_date_string_returns_true(self):
        """Line 588-593: invalid date string triggers except → return True"""
        result = determinar_si_cobra(1, "not-a-date")
        assert result is True

    @pytest.mark.django_db
    def test_con_registro_actual_id_executes_exclude(self):
        """Line 601: reaches if registro_actual_id branch when id_hijo and fecha are valid"""
        # No matching records → returns True (0 existing == 0)
        result = determinar_si_cobra(99999, date.today(), registro_actual_id=88888)
        assert result is True
