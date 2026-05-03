"""
Extended tests for apps/inventario/validators.py targeting uncovered branches.

Missing lines (at baseline 84.62%):
61-62, 88-89, 125-126, 166, 187, 290, 312, 336, 340-341, 385-386,
419, 469-470, 503-504, 528, 532-533, 555, 559-560, 582, 586-587,
612, 616-617, 643-644, 700-701
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

import pytest

from apps.inventario.validators import (
    validar_cantidad_ajuste,
    validar_cantidad_lote,
    validar_cantidad_no_negativa,
    validar_costo_unitario,
    validar_dias_cobertura,
    validar_dias_historico,
    validar_estado_ajuste,
    validar_fecha_vencimiento,
    validar_lead_time,
    validar_merma_aceptable,
    validar_nivel_alerta,
    validar_numero_lote,
    validar_punto_reorden,
    validar_stock_minimo_maximo,
    validar_tipo_ajuste,
    validar_umbral_alerta,
    validar_umbral_confianza,
    validar_variacion_costo,
)

# ---------------------------------------------------------------------------
# validar_cantidad_no_negativa  (lines 61-62)
# ---------------------------------------------------------------------------


class ValidarCantidadNoNegativaExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Lines 61-62: non-numeric string triggers invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_no_negativa("no-es-numero")
        self.assertIn("número válido", str(ctx.exception))

    def test_lista_invalida_raises(self):
        """Lines 61-62: list type triggers invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_no_negativa([1, 2])
        self.assertIn("número válido", str(ctx.exception))


# ---------------------------------------------------------------------------
# validar_stock_minimo_maximo  (lines 88-89, 125-126)
# ---------------------------------------------------------------------------


class ValidarStockMinimoMaximoExtendedTest(TestCase):

    def test_minimo_texto_invalido_raises(self):
        """Lines 88-89, 125-126: non-numeric raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_stock_minimo_maximo("abc", 100)
        self.assertIn("números válidos", str(ctx.exception))

    def test_maximo_texto_invalido_raises(self):
        """Lines 88-89: non-numeric max raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_stock_minimo_maximo(10, "xyz")
        self.assertIn("números válidos", str(ctx.exception))


# ---------------------------------------------------------------------------
# validar_punto_reorden  (lines 166, 187)
# ---------------------------------------------------------------------------


class ValidarPuntoReordenExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 166: non-numeric punto_reorden triggers invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_punto_reorden("abc", 10, 100)
        self.assertIn("números válidos", str(ctx.exception))

    def test_reorden_mayor_maximo_raises(self):
        """Line 187: punto_reorden > maximo triggers ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_punto_reorden(150, 10, 100)
        self.assertIn("no puede ser mayor", str(ctx.exception))

    def test_reorden_valido_no_raises(self):
        """Happy path: reorden between min and max passes."""
        validar_punto_reorden(50, 10, 100)

    def test_reorden_none_returns(self):
        """None punto_reorden returns without error."""
        validar_punto_reorden(None, 10, 100)


# ---------------------------------------------------------------------------
# validar_tipo_ajuste  (line 290)
# ---------------------------------------------------------------------------


class ValidarTipoAjusteExtendedTest(TestCase):

    def test_tipo_invalido_raises(self):
        """Line 290: unknown tipo_ajuste raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_tipo_ajuste("TipoInvalido")
        self.assertIn("inválido", str(ctx.exception))

    def test_tipo_vacio_raises(self):
        """Empty tipo_ajuste raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_tipo_ajuste("")

    def test_tipos_validos_no_raises(self):
        """All valid tipos pass."""
        for tipo in ["Merma", "Sobrante", "Correccion", "Vencimiento", "Deterioro"]:
            validar_tipo_ajuste(tipo)


# ---------------------------------------------------------------------------
# validar_estado_ajuste  (line 312)
# ---------------------------------------------------------------------------


class ValidarEstadoAjusteExtendedTest(TestCase):

    def test_estado_invalido_raises(self):
        """Line 312: unknown estado raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_estado_ajuste("EstadoInvalido")
        self.assertIn("inválido", str(ctx.exception))

    def test_estado_vacio_raises(self):
        """Empty estado raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_estado_ajuste("")

    def test_estados_validos_no_raises(self):
        """All valid estados pass."""
        for estado in ["Pendiente", "Aprobado", "Rechazado", "Aplicado"]:
            validar_estado_ajuste(estado)


# ---------------------------------------------------------------------------
# validar_cantidad_ajuste  (lines 336, 340-341)
# ---------------------------------------------------------------------------


class ValidarCantidadAjusteExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 336: non-numeric cantidad raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_ajuste("abc", "Merma")
        self.assertIn("número válido", str(ctx.exception))

    def test_merma_positiva_raises(self):
        """Lines 340-341: Merma with positive cantidad raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_ajuste(Decimal("10"), "Merma")
        self.assertIn("negativa", str(ctx.exception))

    def test_vencimiento_positivo_raises(self):
        """Lines 340-341: Vencimiento with positive cantidad raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_ajuste(Decimal("5"), "Vencimiento")
        self.assertIn("negativa", str(ctx.exception))

    def test_deterioro_positivo_raises(self):
        """Lines 340-341: Deterioro with positive cantidad raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_ajuste(Decimal("3"), "Deterioro")
        self.assertIn("negativa", str(ctx.exception))

    def test_sobrante_negativo_raises(self):
        """Sobrante with negative cantidad raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_ajuste(Decimal("-5"), "Sobrante")
        self.assertIn("positiva", str(ctx.exception))

    def test_merma_negativa_valida(self):
        """Happy path: Merma with negative cantidad passes."""
        validar_cantidad_ajuste(Decimal("-5"), "Merma")

    def test_sobrante_positivo_valido(self):
        """Happy path: Sobrante with positive cantidad passes."""
        validar_cantidad_ajuste(Decimal("10"), "Sobrante")

    def test_correccion_positivo_valido(self):
        """Happy path: Correccion with any non-zero cantidad passes."""
        validar_cantidad_ajuste(Decimal("10"), "Correccion")
        validar_cantidad_ajuste(Decimal("-5"), "Correccion")


# ---------------------------------------------------------------------------
# validar_merma_aceptable  (lines 385-386, 419)
# ---------------------------------------------------------------------------


class ValidarMermaAceptableExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Lines 385-386: non-numeric cantidad_merma raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_merma_aceptable("abc", 100)
        self.assertIn("números válidos", str(ctx.exception))

    def test_cantidad_total_texto_invalido_raises(self):
        """Lines 385-386: non-numeric cantidad_total raises some exception (TypeError before try block)."""
        with self.assertRaises(Exception):
            validar_merma_aceptable(5, "xyz")

    def test_merma_supera_porcentaje_maximo_raises(self):
        """Line 419: merma > porcentaje_max raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            # 10 / 100 * 100 = 10% > 5%
            validar_merma_aceptable(10, 100, porcentaje_max=5)
        self.assertIn("supera", str(ctx.exception))

    def test_merma_dentro_de_limite_no_raises(self):
        """Happy path: merma within limit passes."""
        # 3 / 100 * 100 = 3% <= 5%
        validar_merma_aceptable(3, 100, porcentaje_max=5)

    def test_cantidad_total_cero_raises(self):
        """cantidad_total <= 0 raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_merma_aceptable(5, 0)


# ---------------------------------------------------------------------------
# validar_fecha_vencimiento  (lines 469-470)
# ---------------------------------------------------------------------------


class ValidarFechaVencimientoExtendedTest(TestCase):

    def test_fecha_pasada_raises(self):
        """Lines 469-470: date in the past raises ValidationError."""
        fecha_pasada = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_vencimiento(fecha_pasada)
        self.assertIn("pasado", str(ctx.exception))

    def test_fecha_datetime_pasada_raises(self):
        """Lines 469-470: datetime in the past raises ValidationError (with date conversion)."""
        dt_pasado = datetime.now() - timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_vencimiento(dt_pasado)
        self.assertIn("pasado", str(ctx.exception))

    def test_fecha_futura_no_raises(self):
        """Happy path: future date passes."""
        fecha_futura = date.today() + timedelta(days=10)
        validar_fecha_vencimiento(fecha_futura)

    def test_fecha_none_no_raises(self):
        """None/empty fecha is optional — no error raised."""
        validar_fecha_vencimiento(None)
        validar_fecha_vencimiento("")

    def test_datetime_futura_no_raises(self):
        """datetime in the future also passes."""
        dt_futuro = timezone.now() + timedelta(days=10)
        validar_fecha_vencimiento(dt_futuro)


# ---------------------------------------------------------------------------
# validar_numero_lote  (lines 503-504)
# ---------------------------------------------------------------------------


class ValidarNumeroLoteExtendedTest(TestCase):

    def test_formato_invalido_raises(self):
        """Lines 503-504: lote with invalid chars raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_numero_lote("LOTE 001!!!")
        self.assertIn("letras, números y guiones", str(ctx.exception))

    def test_formato_con_espacios_raises(self):
        """Spaces in lote raise ValidationError."""
        with self.assertRaises(ValidationError):
            validar_numero_lote("LOTE 001")

    def test_lote_muy_corto_raises(self):
        """Short lote raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_numero_lote("AB")
        self.assertIn("3 caracteres", str(ctx.exception))

    def test_lote_valido_no_raises(self):
        """Happy path: valid lote passes."""
        validar_numero_lote("LOTE-001")
        validar_numero_lote("ABC123")

    def test_lote_none_raises(self):
        """None lote raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_numero_lote(None)


# ---------------------------------------------------------------------------
# validar_cantidad_lote  (lines 528, 532-533)
# ---------------------------------------------------------------------------


class ValidarCantidadLoteExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 528: non-numeric cantidad_lote raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_lote("abc", 10)
        self.assertIn("números válidos", str(ctx.exception))

    def test_cantidad_no_coincide_raises(self):
        """Lines 532-533: lote != movimiento raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_lote(Decimal("10"), Decimal("15"))
        self.assertIn("no coincide", str(ctx.exception))

    def test_cantidad_cero_raises(self):
        """cantidad_lote == 0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_lote(Decimal("0"), Decimal("0"))
        self.assertIn("positiva", str(ctx.exception))

    def test_cantidad_coincide_no_raises(self):
        """Happy path: equal amounts pass."""
        validar_cantidad_lote(Decimal("10"), Decimal("10"))


# ---------------------------------------------------------------------------
# validar_dias_historico  (lines 555, 559-560)
# ---------------------------------------------------------------------------


class ValidarDiasHistoricoExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 555: non-numeric dias raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_historico("abc")
        self.assertIn("número entero", str(ctx.exception))

    def test_dias_mayor_365_raises(self):
        """Lines 559-560: dias > 365 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_historico(400)
        self.assertIn("365", str(ctx.exception))

    def test_dias_menor_7_raises(self):
        """days < 7 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_historico(3)
        self.assertIn("7", str(ctx.exception))

    def test_dias_validos_no_raises(self):
        """Happy path: valid dias passes."""
        validar_dias_historico(7)
        validar_dias_historico(30)
        validar_dias_historico(365)


# ---------------------------------------------------------------------------
# validar_umbral_confianza  (lines 582, 586-587)
# ---------------------------------------------------------------------------


class ValidarUmbralConfianzaExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 582: non-numeric umbral raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_confianza("abc")
        self.assertIn("número decimal", str(ctx.exception))

    def test_umbral_mayor_igual_1_raises(self):
        """Lines 586-587: umbral >= 1.0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_confianza(1.0)
        self.assertIn("1.0", str(ctx.exception))

    def test_umbral_mayor_1_raises(self):
        """umbral > 1.0 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_confianza(1.5)
        self.assertIn("1.0", str(ctx.exception))

    def test_umbral_menor_05_raises(self):
        """umbral < 0.50 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_confianza(0.3)
        self.assertIn("0.50", str(ctx.exception))

    def test_umbral_valido_no_raises(self):
        """Happy path: valid umbral passes."""
        validar_umbral_confianza(0.75)
        validar_umbral_confianza(0.50)
        validar_umbral_confianza(0.99)


# ---------------------------------------------------------------------------
# validar_lead_time  (lines 612, 616-617)
# ---------------------------------------------------------------------------


class ValidarLeadTimeExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 612: non-numeric lead_time raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_lead_time("abc")
        self.assertIn("número entero", str(ctx.exception))

    def test_lead_time_mayor_90_raises(self):
        """Lines 616-617: lead_time > 90 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_lead_time(100)
        self.assertIn("90", str(ctx.exception))

    def test_lead_time_cero_raises(self):
        """lead_time < 1 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_lead_time(0)
        self.assertIn("1 día", str(ctx.exception))

    def test_lead_time_valido_no_raises(self):
        """Happy path: valid lead_time passes."""
        validar_lead_time(1)
        validar_lead_time(30)
        validar_lead_time(90)


# ---------------------------------------------------------------------------
# validar_dias_cobertura  (lines 643-644)
# ---------------------------------------------------------------------------


class ValidarDiasCoberturaExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Line 643: non-numeric dias_cobertura raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_cobertura("abc")
        self.assertIn("número entero", str(ctx.exception))

    def test_dias_mayor_60_raises(self):
        """Line 644: dias_cobertura > 60 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_cobertura(90)
        self.assertIn("60", str(ctx.exception))

    def test_dias_menor_7_raises(self):
        """dias_cobertura < 7 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_dias_cobertura(3)
        self.assertIn("7", str(ctx.exception))

    def test_dias_validos_no_raises(self):
        """Happy path: valid dias passes."""
        validar_dias_cobertura(7)
        validar_dias_cobertura(30)
        validar_dias_cobertura(60)


# ---------------------------------------------------------------------------
# validar_variacion_costo  (lines 700-701)
# ---------------------------------------------------------------------------


class ValidarVariacionCostoExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Lines 700-701: non-numeric costo_nuevo raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_variacion_costo("abc", Decimal("100"))
        self.assertIn("números válidos", str(ctx.exception))

    def test_costo_anterior_texto_invalido_raises(self):
        """Lines 700-701: non-numeric costo_anterior raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_variacion_costo(Decimal("100"), "xyz")
        self.assertIn("números válidos", str(ctx.exception))

    def test_variacion_dentro_de_limite_no_raises(self):
        """Happy path: variation within 30% passes."""
        validar_variacion_costo(Decimal("120"), Decimal("100"))  # 20% increase

    def test_variacion_supera_limite_raises(self):
        """Variation > 30% raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_variacion_costo(Decimal("200"), Decimal("100"))  # 100% increase
        self.assertIn("supera", str(ctx.exception))

    def test_costo_anterior_none_no_raises(self):
        """costo_anterior=None returns without error."""
        validar_variacion_costo(Decimal("200"), None)

    def test_costo_anterior_cero_no_raises(self):
        """costo_anterior=0 returns without error (no comparison possible)."""
        validar_variacion_costo(Decimal("200"), 0)


# ---------------------------------------------------------------------------
# Additional coverage: validar_nivel_alerta, validar_umbral_alerta
# ---------------------------------------------------------------------------


class ValidarNivelAlertaExtendedTest(TestCase):

    def test_nivel_invalido_raises(self):
        """Unknown nivel raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nivel_alerta("Extremo")
        self.assertIn("inválido", str(ctx.exception))

    def test_nivel_vacio_raises(self):
        """Empty nivel raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_nivel_alerta("")

    def test_niveles_validos_no_raises(self):
        """All valid niveles pass."""
        for nivel in ["Bajo", "Medio", "Alto", "Critico"]:
            validar_nivel_alerta(nivel)


class ValidarUmbralAlertaExtendedTest(TestCase):

    def test_texto_invalido_raises(self):
        """Non-numeric umbral raises invalid number error."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_alerta("abc", 10, 100)
        self.assertIn("números válidos", str(ctx.exception))

    def test_umbral_negativo_raises(self):
        """Negative umbral raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_alerta(-5, 10, 100)
        self.assertIn("negativo", str(ctx.exception))

    def test_umbral_mayor_maximo_raises(self):
        """umbral > maximo raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_umbral_alerta(200, 10, 100)
        self.assertIn("mayor que el stock máximo", str(ctx.exception))

    def test_umbral_valido_no_raises(self):
        """Happy path: valid umbral passes."""
        validar_umbral_alerta(50, 10, 100)
