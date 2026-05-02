"""
Tests targeting remaining missing lines in apps/core/validators.py

Missing lines covered here:
  81-84   — validar_saldo_tarjeta: except (ValueError, TypeError) for saldo_actual
  87-90   — validar_saldo_tarjeta: except (ValueError, TypeError) for limite_credito
  154     — validar_codigo_barras_tarjeta: Code-128 invalid-chars regex
  195     — validar_fecha_vencimiento_tarjeta: early return when falsy
  244-247 — validar_limite_credito: except (ValueError, TypeError)
  279     — validar_saldo_alerta: early return when saldo_alerta is None
  282-285 — validar_saldo_alerta: except (ValueError, TypeError)
  339     — validar_codigo_barra_autorizacion: invalid-chars regex
  394     — validar_fecha_vencimiento_autorizacion: non-date type raises
  435-438 — validar_monto_carga: except (ValueError, TypeError)
  632-635 — validar_monto_consumo: except (ValueError, TypeError)
  669-674 — validar_saldos_coherentes: except (ValueError, TypeError)
  715-718 — validar_monto_transaccion: except (ValueError, TypeError)
  906     — validar_valor_configuracion: except (ValueError, TypeError) for decimal tipo
  1021-1024 — validar_monto_limite: except (ValueError, TypeError)
  1054    — validar_unicidad_rol_operacion: early return when id_rol is falsy

Strategy for except (ValueError, TypeError) blocks:
  Decimal(str(x)) normally raises decimal.InvalidOperation (not ValueError/TypeError),
  so these branches are unreachable with plain strings.  We instead pass an object
  whose __str__ raises ValueError, which IS caught by the except clause.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.validators import (
    validar_codigo_barra_autorizacion,
    validar_codigo_barras_tarjeta,
    validar_fecha_vencimiento_autorizacion,
    validar_fecha_vencimiento_tarjeta,
    validar_limite_credito,
    validar_monto_carga,
    validar_monto_consumo,
    validar_monto_limite,
    validar_monto_transaccion,
    validar_saldo_alerta,
    validar_saldo_tarjeta,
    validar_saldos_coherentes,
    validar_unicidad_rol_operacion,
    validar_valor_configuracion,
)


class _RaisesValueErrorOnStr:
    """Helper whose __str__ raises ValueError.

    When passed to Decimal(str(obj)), str(obj) raises ValueError before Decimal
    is even called, so the 'except (ValueError, TypeError)' blocks are executed.
    """

    def __str__(self):
        raise ValueError("intentional ValueError from __str__")


# =============================================================================
# validar_saldo_tarjeta (lines 63-108)
# =============================================================================


class ValidarSaldoTarjetaSaldoActualConversionErrorTest(TestCase):
    """Lines 81-84: except (ValueError, TypeError) for saldo_actual conversion."""

    def test_saldo_actual_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_tarjeta(_RaisesValueErrorOnStr(), Decimal("0"), False)
        self.assertIn("numérico", str(ctx.exception))


class ValidarSaldoTarjetaLimiteCreditoConversionErrorTest(TestCase):
    """Lines 87-90: except (ValueError, TypeError) for limite_credito conversion."""

    def test_limite_credito_str_raises_valueerror(self):
        # saldo_actual IS a valid Decimal so lines 81-84 are skipped
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_tarjeta(Decimal("500"), _RaisesValueErrorOnStr(), False)
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_codigo_barras_tarjeta (line 154)
# =============================================================================


class ValidarCodigoBarrasTarjetaEarlyReturnTest(TestCase):
    """Line 154: early return when codigo_barras is falsy (optional field)."""

    def test_none_returns_early_no_raise(self):
        validar_codigo_barras_tarjeta(None)

    def test_empty_string_returns_early_no_raise(self):
        validar_codigo_barras_tarjeta("")


class ValidarCodigoBarrasTarjetaInvalidCharsTest(TestCase):
    """Code-128 path raises when barcode contains invalid characters."""

    def test_alphanumeric_with_at_sign_raises(self):
        # INVALID@CODE: 12 chars, not purely numeric → Code-128 branch
        # '@' is not in [A-Za-z0-9\-] → raises
        with self.assertRaises(ValidationError) as ctx:
            validar_codigo_barras_tarjeta("INVALID@CODE")
        self.assertIn("letras, números y guiones", str(ctx.exception))

    def test_alphanumeric_with_space_raises(self):
        with self.assertRaises(ValidationError):
            validar_codigo_barras_tarjeta("CODE WITH SP")  # space not allowed


# =============================================================================
# validar_fecha_vencimiento_tarjeta (line 195)
# =============================================================================


class ValidarFechaVencimientoTarjetaFalsyTest(TestCase):
    """Line 195: early return when fecha_vencimiento is falsy."""

    def test_none_returns_early_no_raise(self):
        # Should not raise — optional field
        validar_fecha_vencimiento_tarjeta(None)

    def test_empty_string_returns_early_no_raise(self):
        validar_fecha_vencimiento_tarjeta("")


# =============================================================================
# validar_limite_credito (lines 244-247)
# =============================================================================


class ValidarLimiteCreditoConversionErrorTest(TestCase):
    """Lines 244-247: except (ValueError, TypeError) for limite_credito conversion."""

    def test_limite_credito_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_limite_credito(_RaisesValueErrorOnStr())
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_saldo_alerta (lines 279, 282-285)
# =============================================================================


class ValidarSaldoAlertaNoneEarlyReturnTest(TestCase):
    """Line 279: early return when saldo_alerta is None."""

    def test_saldo_alerta_none_returns_early(self):
        # None is explicitly checked → returns without error
        validar_saldo_alerta(None, Decimal("1000"))


class ValidarSaldoAlertaConversionErrorTest(TestCase):
    """Lines 282-285: except (ValueError, TypeError) for saldo_alerta conversion."""

    def test_saldo_alerta_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_alerta(_RaisesValueErrorOnStr(), Decimal("1000"))
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_codigo_barra_autorizacion (line 339)
# =============================================================================


class ValidarCodigoBarraAutorizacionInvalidCharsTest(TestCase):
    """Line 339: regex raises when barcode contains characters outside [A-Za-z0-9\\-]."""

    def test_code_with_at_sign_raises(self):
        # "AUTH@CODE" is 9 chars, not empty, length OK → regex branch
        with self.assertRaises(ValidationError) as ctx:
            validar_codigo_barra_autorizacion("AUTH@CODE")
        self.assertIn("letras, números y guiones", str(ctx.exception))

    def test_code_with_space_raises(self):
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("AUTH CODE1")


# =============================================================================
# validar_fecha_vencimiento_autorizacion (line 394)
# =============================================================================


class ValidarFechaVencimientoAutorizacionNonDateTest(TestCase):
    """Line 394: raises when fecha_vencimiento is truthy but not a date instance."""

    def test_string_fecha_raises(self):
        # tipo != "Temporal" so first check ignored; "not-a-date" is truthy;
        # isinstance("not-a-date", date) is False → ValidationError
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_vencimiento_autorizacion("not-a-date", "Supervisor")
        self.assertIn("fecha válida", str(ctx.exception))

    def test_integer_fecha_raises(self):
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_autorizacion(20260101, "Gerente")


# =============================================================================
# validar_monto_carga (lines 435-438)
# =============================================================================


class ValidarMontoCargaConversionErrorTest(TestCase):
    """Lines 435-438: except (ValueError, TypeError) for monto conversion."""

    def test_monto_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_carga(_RaisesValueErrorOnStr())
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_monto_consumo (lines 632-635)
# =============================================================================


class ValidarMontoConsumoConversionErrorTest(TestCase):
    """Lines 632-635: except (ValueError, TypeError) for monto conversion."""

    def test_monto_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_consumo(_RaisesValueErrorOnStr())
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_saldos_coherentes (lines 669-674)
# =============================================================================


class ValidarSaldosCoherentesConversionErrorTest(TestCase):
    """Lines 669-674: except (ValueError, TypeError) for saldo/monto conversion."""

    def test_saldo_anterior_str_raises_valueerror(self):
        # saldo_anterior is not Decimal → all(isinstance...) is False → try block
        # str(RaisesValueError()) raises ValueError on line 670 → caught → ValidationError
        with self.assertRaises(ValidationError) as ctx:
            validar_saldos_coherentes(_RaisesValueErrorOnStr(), Decimal("100"), Decimal("50"))
        self.assertIn("numéricos", str(ctx.exception))

    def test_monto_consumido_str_raises_valueerror(self):
        # saldo_anterior="100" and saldo_posterior="50" both convert successfully
        # (lines 670-671), then monto_consumido fails on line 672 → except → ValidationError
        with self.assertRaises(ValidationError) as ctx:
            validar_saldos_coherentes("100", "50", _RaisesValueErrorOnStr())
        self.assertIn("numéricos", str(ctx.exception))


# =============================================================================
# validar_monto_transaccion (lines 715-718)
# =============================================================================


class ValidarMontoTransaccionConversionErrorTest(TestCase):
    """Lines 715-718: except (ValueError, TypeError) for monto conversion."""

    def test_monto_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_transaccion(_RaisesValueErrorOnStr())
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_valor_configuracion (line 906)
# =============================================================================


class ValidarValorConfiguracionDecimalTypeErrorTest(TestCase):
    """Line 906: except (ValueError, TypeError) in decimal branch.

    Decimal("abc") raises InvalidOperation (not ValueError/TypeError) so
    we instead pass a list — Decimal([1]) raises TypeError which IS caught.
    A non-empty list is truthy so it bypasses the 'if not valor' early raise.
    """

    def test_list_as_valor_causes_typeerror_raises_validation_error(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion([1], "decimal")
        self.assertIn("decimal", str(ctx.exception))


# =============================================================================
# validar_monto_limite (lines 1021-1024)
# =============================================================================


class ValidarMontoLimiteConversionErrorTest(TestCase):
    """Lines 1021-1024: except (ValueError, TypeError) for monto conversion."""

    def test_monto_str_raises_valueerror(self):
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_limite(_RaisesValueErrorOnStr())
        self.assertIn("numérico", str(ctx.exception))


# =============================================================================
# validar_unicidad_rol_operacion (line 1054)
# =============================================================================


class ValidarUnicidadRolOperacionEarlyReturnTest(TestCase):
    """Line 1054: early return when id_rol or tipo_operacion is falsy."""

    def test_id_rol_none_returns_early(self):
        # Should not raise — returns immediately
        validar_unicidad_rol_operacion(None, "CONSUMO")

    def test_tipo_operacion_none_returns_early(self):
        validar_unicidad_rol_operacion(1, None)

    def test_id_rol_falsy_empty_returns_early(self):
        validar_unicidad_rol_operacion("", "CONSUMO")
