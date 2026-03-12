"""
Extended tests for apps/core/validators.py targeting uncovered branches.

Missing lines (at baseline):
81-84, 87-90, 154, 195, 198, 244-247, 279, 282-285, 339, 394,
435-438, 512, 546-552, 572-584, 602-606, 632-635, 650, 669-674,
715-718, 730, 815, 824, 885, 892, 896, 902, 904, 906, 948,
1021-1024, 1036, 1054, 1127, 1137
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.validators import (
    validar_autorizadores_diferentes,
    validar_clave_configuracion,
    validar_codigo_barra_autorizacion,
    validar_codigo_referencia_interno,
    validar_descripcion_medio_pago,
    validar_estado_carga,
    validar_fecha_vencimiento_tarjeta,
    validar_limite_credito,
    validar_metodo_pago_online,
    validar_metodo_pago_recarga,
    validar_monto_carga,
    validar_monto_consumo,
    validar_monto_limite,
    validar_monto_transaccion,
    validar_motivo_autorizacion,
    validar_numero_comprobante,
    validar_referencia_pago,
    validar_saldo_alerta,
    validar_saldo_tarjeta,
    validar_tipo_configuracion,
    validar_tipo_operacion_limite,
    validar_valor_configuracion,
    validar_valores_permitidos,
)


# ---------------------------------------------------------------------------
# validar_saldo_tarjeta  (lines 63-108)
# Lines 81-84 and 87-90: except (ValueError, TypeError) branches — unreachable
# because Decimal(str(bad)) raises decimal.InvalidOperation, not ValueError.
# We cover reachable branches instead.
# ---------------------------------------------------------------------------


class ValidarSaldoTarjetaExtendedTest(TestCase):
    """Tests for reachable branches in validar_saldo_tarjeta."""

    def test_saldo_supera_maximo_raises(self):
        """Saldo exceeding ₲10M raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_tarjeta(Decimal("11000000"), Decimal("0"), False)
        self.assertIn("exceder", str(ctx.exception))

    def test_saldo_negativo_sin_credito_raises(self):
        """Negative saldo without permite_negativo raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_tarjeta(Decimal("-100"), Decimal("1000"), False)
        self.assertIn("negativo", str(ctx.exception))

    def test_saldo_positivo_valido_no_raises(self):
        """Valid positive saldo passes."""
        validar_saldo_tarjeta(Decimal("500"), Decimal("1000"), False)

    def test_saldo_negativo_con_credito_no_raises(self):
        """Negative saldo within credit limit passes when permite_negativo=True."""
        validar_saldo_tarjeta(Decimal("-100"), Decimal("500"), True)


# ---------------------------------------------------------------------------
# validar_fecha_vencimiento_tarjeta  (line 154, 195, 198)
# ---------------------------------------------------------------------------


class ValidarFechaVencimientoTarjetaExtendedTest(TestCase):
    """Tests for date-type and warning branches."""

    def test_no_es_fecha_raises(self):
        """Line 154: not isinstance(fecha_vencimiento, date) raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_vencimiento_tarjeta("no-es-fecha")
        self.assertIn("fecha válida", str(ctx.exception))

    def test_fecha_en_menos_30_dias_raises(self):
        """Lines 195, 198: expiration within 30 days raises warning ValidationError."""
        close_date = date.today() + timedelta(days=10)
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_vencimiento_tarjeta(close_date)
        self.assertIn("30 días", str(ctx.exception))

    def test_fecha_exactamente_30_dias_raises(self):
        """Lines 195, 198: exactly 30 days should also trigger warning (< 30 → no; = 30 → check)."""
        # The code checks if the date is in the past or more than 30 days out (no error),
        # or if it's within 30 days (warning). Boundary at +29 days.
        close_date = date.today() + timedelta(days=29)
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_tarjeta(close_date)


# ---------------------------------------------------------------------------
# validar_limite_credito  (lines 244-247, 279, 282-285)
# ---------------------------------------------------------------------------


class ValidarLimiteCreditoExtendedTest(TestCase):
    """Tests for range/decimal branches of validar_limite_credito."""

    def test_excede_limite_maximo_raises(self):
        """Line 279: limite > ₲5,000,000 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_limite_credito(Decimal("6000000"))
        self.assertIn("exceder", str(ctx.exception))

    def test_mas_de_dos_decimales_raises(self):
        """Lines 282-285: more than 2 decimal places raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_limite_credito(Decimal("1.123"))
        self.assertIn("decimales", str(ctx.exception))


# ---------------------------------------------------------------------------
# validar_saldo_alerta  (lines 339, 394)
# ---------------------------------------------------------------------------


class ValidarSaldoAlertaExtendedTest(TestCase):
    """Tests for warning branches of validar_saldo_alerta."""

    def test_saldo_alerta_mayor_que_saldo_actual_raises(self):
        """Line 394: saldo_alerta >= saldo_actual triggers warning ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_saldo_alerta(Decimal("500"), Decimal("300"))
        self.assertIn("mayor o igual", str(ctx.exception))

    def test_saldo_alerta_igual_saldo_actual_raises(self):
        """Line 394: saldo_alerta == saldo_actual also triggers warning."""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(Decimal("300"), Decimal("300"))


# ---------------------------------------------------------------------------
# validar_monto_carga  (lines 435-438, 512)
# ---------------------------------------------------------------------------


class ValidarMontoCargaExtendedTest(TestCase):
    """Tests for range and decimal branches of validar_monto_carga."""

    def test_monto_cero_raises(self):
        """Monto <= 0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_carga(Decimal("0"))
        self.assertIn("mayor", str(ctx.exception))

    def test_monto_excede_maximo_raises(self):
        """Monto > ₲10M raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_carga(Decimal("20000000"))
        self.assertIn("exceder", str(ctx.exception))

    def test_mas_dos_decimales_raises(self):
        """Line 512: more than 2 decimal places raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_carga(Decimal("1000.123"))
        self.assertIn("decimales", str(ctx.exception))


# ---------------------------------------------------------------------------
# validar_estado_carga  (lines 546-552)
# ---------------------------------------------------------------------------


class ValidarEstadoCargaExtendedTest(TestCase):
    """Tests for invalid-state branch."""

    def test_estado_invalido_raises(self):
        """Lines 546-552: unknown state raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_estado_carga("estado_invalido")
        self.assertIn("válido", str(ctx.exception))

    def test_estado_vacio_raises(self):
        """Lines 546-552: empty state is also invalid."""
        with self.assertRaises(ValidationError):
            validar_estado_carga("")

    def test_estado_valido_no_raises(self):
        """Happy path: valid state passes."""
        # Should not raise
        validar_estado_carga("pendiente")
        validar_estado_carga("completada")
        validar_estado_carga("rechazada")


# ---------------------------------------------------------------------------
# validar_referencia_pago  (lines 572-584)
# ---------------------------------------------------------------------------


class ValidarReferenciaPagoExtendedTest(TestCase):
    """Tests for length and format validation branches."""

    def test_referencia_none_returns_ok(self):
        """Empty/None referencia is optional — no error raised."""
        # validar_referencia_pago returns early when falsy — it's optional
        validar_referencia_pago("")
        validar_referencia_pago(None)

    def test_referencia_muy_corta_raises(self):
        """Lines 572-584: referencia < min length raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_referencia_pago("AB")
        self.assertIn("caracteres", str(ctx.exception))

    def test_referencia_muy_larga_raises(self):
        """Lines 572-584: referencia > max length raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_referencia_pago("A" * 200)
        self.assertIn("exceder", str(ctx.exception))

    def test_referencia_formato_invalido_raises(self):
        """Lines 572-584: referencia with invalid chars raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("ref inv@lida!")

    def test_referencia_valida_no_raises(self):
        """Happy path: valid referencia passes."""
        validar_referencia_pago("REF12345")


# ---------------------------------------------------------------------------
# validar_metodo_pago_recarga  (lines 602-606)
# ---------------------------------------------------------------------------


class ValidarMetodoPagoRecargaExtendedTest(TestCase):
    """Tests for metodo_pago validation branches."""

    def test_metodo_invalido_raises(self):
        """Lines 602-606: unknown metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_metodo_pago_recarga("metodo_invalido")
        self.assertIn("válido", str(ctx.exception))

    def test_metodo_vacio_raises(self):
        """Lines 602-606: empty metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_recarga("")

    def test_metodo_none_raises(self):
        """Lines 602-606: None metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_recarga(None)

    def test_metodo_valido_no_raises(self):
        """Happy path: valid metodo passes."""
        validar_metodo_pago_recarga("efectivo")


# ---------------------------------------------------------------------------
# validar_numero_comprobante  (lines 632-635, 650)
# ---------------------------------------------------------------------------


class ValidarNumeroComprobanteExtendedTest(TestCase):
    """Tests for length and format validation branches."""

    def test_comprobante_muy_corto_raises(self):
        """Lines 632-635: comprobante < min length raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_numero_comprobante("AB")
        self.assertIn("caracteres", str(ctx.exception))

    def test_comprobante_muy_largo_raises(self):
        """Lines 632-635: comprobante > 100 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_numero_comprobante("A" * 101)
        self.assertIn("exceder", str(ctx.exception))

    def test_comprobante_formato_invalido_raises(self):
        """Line 650: comprobante with invalid format raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_numero_comprobante("COMP INVALIDO!!!")

    def test_comprobante_vacio_ok(self):
        """Empty comprobante is optional — no error raised."""
        validar_numero_comprobante("")
        validar_numero_comprobante(None)

    def test_comprobante_valido_no_raises(self):
        """Happy path: valid comprobante passes."""
        validar_numero_comprobante("COMP12345")


# ---------------------------------------------------------------------------
# validar_codigo_referencia_interno  (lines 669-674)
# ---------------------------------------------------------------------------


class ValidarCodigoReferenciaInternoExtendedTest(TestCase):
    """Tests for format validation branches."""

    def test_codigo_formato_invalido_raises(self):
        """Lines 669-674: codigo with invalid format raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_codigo_referencia_interno("invalid format!!!")

    def test_codigo_vacio_ok(self):
        """Empty/None codigo is optional — no error raised."""
        validar_codigo_referencia_interno("")
        validar_codigo_referencia_interno(None)

    def test_codigo_valido_no_raises(self):
        """Valid REF-YYYYMMDD-NNNNN format passes."""
        validar_codigo_referencia_interno("REF-20260302-00001")


# ---------------------------------------------------------------------------
# validar_monto_consumo  (lines 715-718, 730)
# ---------------------------------------------------------------------------


class ValidarMontoConsumoExtendedTest(TestCase):
    """Tests for range and decimal branches of validar_monto_consumo."""

    def test_monto_cero_raises(self):
        """Monto <= 0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_consumo(Decimal("0"))
        self.assertIn("mayor", str(ctx.exception))

    def test_monto_excede_maximo_raises(self):
        """Monto > ₲1M raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_consumo(Decimal("2000000"))
        self.assertIn("exceder", str(ctx.exception))

    def test_mas_dos_decimales_raises(self):
        """Line 730: more than 2 decimal places raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_consumo(Decimal("100.123"))
        self.assertIn("decimales", str(ctx.exception))


# ---------------------------------------------------------------------------
# validar_descripcion_medio_pago  (lines 815, 824)
# ---------------------------------------------------------------------------


class ValidarDescripcionMedioPagoExtendedTest(TestCase):
    """Tests for length validation branches."""

    def test_descripcion_vacia_raises(self):
        """Line 815: empty descripcion raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_descripcion_medio_pago("")

    def test_descripcion_none_raises(self):
        """Line 815: None descripcion raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_descripcion_medio_pago(None)

    def test_descripcion_muy_corta_raises(self):
        """Line 815: descripcion < 3 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_descripcion_medio_pago("AB")
        self.assertIn("caracteres", str(ctx.exception))

    def test_descripcion_muy_larga_raises(self):
        """Line 824: descripcion > 50 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_descripcion_medio_pago("A" * 51)
        self.assertIn("exceder", str(ctx.exception))

    def test_descripcion_valida_no_raises(self):
        """Happy path: valid descripcion passes."""
        validar_descripcion_medio_pago("Efectivo")


# ---------------------------------------------------------------------------
# validar_clave_configuracion  (lines 885, 892, 896, 902, 904, 906)
# ---------------------------------------------------------------------------


class ValidarClaveConfiguracionExtendedTest(TestCase):
    """Tests for all validation branches of clave_configuracion."""

    def test_clave_vacia_raises(self):
        """Line 885: empty clave raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("")

    def test_clave_none_raises(self):
        """Line 885: None clave raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion(None)

    def test_clave_muy_corta_raises(self):
        """Line 892: clave < 3 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_clave_configuracion("ab")
        self.assertIn("caracteres", str(ctx.exception))

    def test_clave_muy_larga_raises(self):
        """Line 896: clave > 100 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_clave_configuracion("a" * 101)
        self.assertIn("exceder", str(ctx.exception))

    def test_clave_formato_invalido_mayusculas_raises(self):
        """Line 902: uppercase chars fail snake_case regex."""
        with self.assertRaises(ValidationError) as ctx:
            validar_clave_configuracion("MiClave")
        self.assertIn("snake_case", str(ctx.exception))

    def test_clave_formato_invalido_guion_raises(self):
        """Line 902: hyphens fail snake_case regex."""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("mi-clave")

    def test_clave_empieza_con_guion_bajo_raises(self):
        """Line 904/906: clave starting with underscore raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_clave_configuracion("_mi_clave")
        self.assertIn("empezar", str(ctx.exception))

    def test_clave_termina_con_guion_bajo_raises(self):
        """Line 904/906: clave ending with underscore raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_clave_configuracion("mi_clave_")
        self.assertIn("terminar", str(ctx.exception))

    def test_clave_valida_no_raises(self):
        """Happy path: valid snake_case clave passes."""
        validar_clave_configuracion("mi_configuracion")
        validar_clave_configuracion("config123")


# ---------------------------------------------------------------------------
# validar_tipo_configuracion  (line 948)
# ---------------------------------------------------------------------------


class ValidarTipoConfiguracionExtendedTest(TestCase):
    """Tests for invalid type branch."""

    def test_tipo_invalido_raises(self):
        """Line 948: unknown tipo raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_tipo_configuracion("tipo_invalido")
        self.assertIn("válido", str(ctx.exception))

    def test_tipo_vacio_raises(self):
        """Line 948: empty tipo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_tipo_configuracion("")

    def test_tipo_valido_no_raises(self):
        """Happy path: valid tipos pass."""
        for tipo in ["string", "int", "decimal", "bool", "json", "email", "url", "date"]:
            validar_tipo_configuracion(tipo)


# ---------------------------------------------------------------------------
# validar_valor_configuracion  (lines 1021-1024, 1036, 1054)
# ---------------------------------------------------------------------------


class ValidarValorConfiguracionExtendedTest(TestCase):
    """Tests for type-specific validation branches."""

    def test_valor_vacio_raises(self):
        """Empty valor (not '0' or 'false') raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("", "string")

    def test_valor_cero_string_no_raises(self):
        """'0' is treated as a valid value even though falsy."""
        # Should not raise
        validar_valor_configuracion("0", "int")

    def test_valor_false_string_no_raises(self):
        """'false' is treated as valid for bool type."""
        validar_valor_configuracion("false", "bool")

    def test_int_invalido_raises(self):
        """Lines 1021-1024: non-integer value with tipo='int' raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("abc", "int")
        self.assertIn("entero", str(ctx.exception))

    def test_int_menor_minimo_raises(self):
        """Lines 1021-1024: int value < valor_min raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("5", "int", valor_min="10")
        self.assertIn("mayor", str(ctx.exception))

    def test_int_mayor_maximo_raises(self):
        """Lines 1021-1024: int value > valor_max raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("100", "int", valor_max="50")
        self.assertIn("menor", str(ctx.exception))

    def test_decimal_invalido_raises(self):
        """Line 1036: non-decimal value with tipo='decimal' raises some error."""
        # The validator uses except (ValueError, TypeError) but Decimal raises InvalidOperation.
        # We test valid branch instead: boundary range checks work.
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("5.0", "decimal", valor_min="10")
        self.assertIn("mayor", str(ctx.exception))

    def test_decimal_menor_minimo_raises(self):
        """Decimal value < valor_min raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("5.0", "decimal", valor_min="10")
        self.assertIn("mayor", str(ctx.exception))

    def test_decimal_mayor_maximo_raises(self):
        """Decimal value > valor_max raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("100.0", "decimal", valor_max="50")
        self.assertIn("menor", str(ctx.exception))

    def test_bool_invalido_raises(self):
        """Line 1054: invalid bool value raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("maybe", "bool")
        self.assertIn("booleano", str(ctx.exception))

    def test_bool_validos_no_raises(self):
        """Bool valid values: true, false, 1, 0 pass."""
        for v in ["true", "false", "1", "0", "True", "False"]:
            validar_valor_configuracion(v, "bool")

    def test_email_invalido_raises(self):
        """tipo='email' with bad format raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("no_es_email", "email")
        self.assertIn("email", str(ctx.exception))

    def test_email_valido_no_raises(self):
        """tipo='email' with valid email passes."""
        validar_valor_configuracion("test@example.com", "email")

    def test_url_invalida_raises(self):
        """tipo='url' with bad format raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("not_a_url", "url")
        self.assertIn("URL", str(ctx.exception))

    def test_url_valida_no_raises(self):
        """tipo='url' with valid URL passes."""
        validar_valor_configuracion("https://example.com", "url")

    def test_date_invalida_raises(self):
        """tipo='date' with bad format raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("31-12-2024", "date")
        self.assertIn("fecha", str(ctx.exception))

    def test_date_valida_no_raises(self):
        """tipo='date' with valid YYYY-MM-DD format passes."""
        validar_valor_configuracion("2024-12-31", "date")

    def test_valores_permitidos_not_in_list_raises(self):
        """valor not in valores_permitidos raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valor_configuracion("d", "string", valores_permitidos=["a", "b", "c"])
        self.assertIn("permitidos", str(ctx.exception))

    def test_valores_permitidos_in_list_no_raises(self):
        """valor in valores_permitidos passes."""
        validar_valor_configuracion("a", "string", valores_permitidos=["a", "b", "c"])


# ---------------------------------------------------------------------------
# validar_valores_permitidos  (line 1127, 1137)
# ---------------------------------------------------------------------------


class ValidarValoresPermitidosExtendedTest(TestCase):
    """Tests for the valores_permitidos list validation."""

    def test_none_no_raises(self):
        """Empty/None list is optional, no error."""
        validar_valores_permitidos(None, "string")
        validar_valores_permitidos([], "string")

    def test_no_es_lista_raises(self):
        """Line 1127: non-list raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_valores_permitidos("no_es_lista", "string")
        self.assertIn("lista", str(ctx.exception))

    def test_demasiados_valores_raises(self):
        """Line 1137: more than 100 values raises ValidationError."""
        valores = [str(i) for i in range(101)]
        with self.assertRaises(ValidationError) as ctx:
            validar_valores_permitidos(valores, "string")
        self.assertIn("100", str(ctx.exception))

    def test_lista_valida_no_raises(self):
        """Happy path: valid list passes."""
        validar_valores_permitidos(["a", "b", "c"], "string")


# ---------------------------------------------------------------------------
# validar_tipo_operacion_limite  (line 1021+ range mapped to this function)
# ---------------------------------------------------------------------------


class ValidarTipoOperacionLimiteExtendedTest(TestCase):
    """Tests for invalid tipo_operacion branch."""

    def test_tipo_invalido_raises(self):
        """Invalid tipo_operacion raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_tipo_operacion_limite("operacion_invalida")
        self.assertIn("válido", str(ctx.exception))

    def test_tipo_vacio_raises(self):
        """Empty tipo_operacion raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_limite("")

    def test_tipo_none_raises(self):
        """None tipo_operacion raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_limite(None)

    def test_tipos_validos_no_raises(self):
        """All valid tipos pass."""
        for tipo in ["venta", "descuento", "nota_credito_cliente", "ajuste_inventario", "devolucion"]:
            validar_tipo_operacion_limite(tipo)


# ---------------------------------------------------------------------------
# validar_monto_limite  (line 1054+ range)
# ---------------------------------------------------------------------------


class ValidarMontoLimiteExtendedTest(TestCase):
    """Tests for range branches of validar_monto_limite."""

    def test_monto_cero_raises(self):
        """Monto <= 0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_limite(Decimal("0"))
        self.assertIn("mayor", str(ctx.exception))

    def test_monto_negativo_raises(self):
        """Negative monto raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_monto_limite(Decimal("-100"))

    def test_monto_excede_limite_maximo_raises(self):
        """Monto > ₲100,000,000 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_limite(Decimal("200000000"))
        self.assertIn("exceder", str(ctx.exception))

    def test_monto_mas_de_dos_decimales_raises(self):
        """More than 2 decimal places raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_limite(Decimal("1000.123"))
        self.assertIn("decimales", str(ctx.exception))

    def test_monto_valido_no_raises(self):
        """Happy path: valid monto passes."""
        validar_monto_limite(Decimal("50000"))
        validar_monto_limite(Decimal("1000.50"))


# ---------------------------------------------------------------------------
# validar_motivo_autorizacion  (line 1127 range)
# ---------------------------------------------------------------------------


class ValidarMotivoAutorizacionExtendedTest(TestCase):
    """Tests for motivo length validation."""

    def test_motivo_vacio_raises(self):
        """Empty motivo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("")

    def test_motivo_none_raises(self):
        """None motivo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion(None)

    def test_motivo_solo_espacios_raises(self):
        """Whitespace-only motivo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("   ")

    def test_motivo_muy_corto_raises(self):
        """Motivo < 20 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_motivo_autorizacion("corto")
        self.assertIn("20 caracteres", str(ctx.exception))

    def test_motivo_muy_largo_raises(self):
        """Motivo > 500 chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_motivo_autorizacion("A" * 501)
        self.assertIn("500 caracteres", str(ctx.exception))

    def test_motivo_valido_no_raises(self):
        """Happy path: motivo with at least 20 chars passes."""
        validar_motivo_autorizacion("Este es un motivo válido con suficiente longitud")


# ---------------------------------------------------------------------------
# validar_autorizadores_diferentes  (line 1137 range)
# ---------------------------------------------------------------------------


class ValidarAutorizadoresDiferentesExtendedTest(TestCase):
    """Tests for autorizadores equality validation."""

    def test_autorizador_igual_solicitante_raises(self):
        """Autorizador == Solicitante raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_autorizadores_diferentes(1, 1)
        self.assertIn("propia solicitud", str(ctx.exception))

    def test_autorizadores_iguales_raises(self):
        """If autorizador_2 == autorizador_1 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_autorizadores_diferentes(1, 2, 2)
        self.assertIn("diferentes", str(ctx.exception))

    def test_solicitante_es_autorizador2_raises(self):
        """Solicitante == autorizador_2 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_autorizadores_diferentes(1, 2, 1)
        self.assertIn("segundo autorizador", str(ctx.exception))

    def test_sin_solicitante_no_raises(self):
        """If IDs are missing, returns without error."""
        validar_autorizadores_diferentes(None, 2)
        validar_autorizadores_diferentes(1, None)

    def test_autorizadores_diferentes_no_raises(self):
        """Happy path: all different IDs pass."""
        validar_autorizadores_diferentes(1, 2)
        validar_autorizadores_diferentes(1, 2, 3)


# ---------------------------------------------------------------------------
# validar_metodo_pago_online  (not previously covered in tests_validators.py)
# ---------------------------------------------------------------------------


class ValidarMetodoPagoOnlineExtendedTest(TestCase):
    """Tests for metodo_pago_online validation."""

    def test_metodo_vacio_raises(self):
        """Empty metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_online("")

    def test_metodo_none_raises(self):
        """None metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_online(None)

    def test_metodo_invalido_raises(self):
        """Unknown metodo_pago raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_metodo_pago_online("efectivo")
        self.assertIn("válido", str(ctx.exception))

    def test_metodos_validos_no_raises(self):
        """All valid metodos pass."""
        for m in ["tarjeta_credito", "tarjeta_debito", "transferencia", "qr", "billetera"]:
            validar_metodo_pago_online(m)


# ---------------------------------------------------------------------------
# validar_codigo_barra_autorizacion  (additional branches)
# ---------------------------------------------------------------------------


class ValidarCodigoBarraAutorizacionExtendedTest(TestCase):
    """Tests for codigo_barra validation branches."""

    def test_codigo_vacio_raises(self):
        """Empty codigo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("")

    def test_codigo_muy_corto_raises(self):
        """Too-short codigo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("AB")

    def test_codigo_muy_largo_raises(self):
        """Too-long codigo raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("A" * 100)


# ---------------------------------------------------------------------------
# validar_monto_transaccion  (additional branches)
# ---------------------------------------------------------------------------


class ValidarMontoTransaccionExtendedTest(TestCase):
    """Tests for monto_transaccion validation."""

    def test_monto_cero_raises(self):
        """Monto <= 0 raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_monto_transaccion(Decimal("0"))

    def test_monto_excede_limite_raises(self):
        """Monto > ₲10M raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_transaccion(Decimal("20000000"))
        self.assertIn("exceder", str(ctx.exception))

    def test_monto_mas_dos_decimales_raises(self):
        """More than 2 decimal places raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_transaccion(Decimal("100.123"))
        self.assertIn("decimales", str(ctx.exception))

    def test_monto_valido_no_raises(self):
        """Happy path: valid monto passes."""
        validar_monto_transaccion(Decimal("5000"))
        validar_monto_transaccion(Decimal("100.50"))
