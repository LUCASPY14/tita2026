"""
Extended tests for apps/reportes/validators.py covering previously missing lines.

Missing lines targeted:
  81, 83         - validar_parametros_reporte: non-str key, short/long key
  158-159, 162   - validar_configuracion_dashboard: invalid JSON string, non-dict
  442-443, 446   - validar_parametros_tarea: invalid JSON string, non-dict
  589            - validar_pid_ejecucion: PID > max
  647-656        - validar_configuracion_json: all branches
  661-666        - validar_frecuencia_ejecucion: invalid value
  671-680        - validar_formato_datos_json: all branches
"""

import json
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.reportes.validators import (
    validar_parametros_reporte,
    validar_configuracion_dashboard,
    validar_parametros_tarea,
    validar_pid_ejecucion,
    validar_configuracion_json,
    validar_frecuencia_ejecucion,
    validar_formato_datos_json,
)


# =============================================================================
# validar_parametros_reporte — lines 81, 83
# =============================================================================

class ValidarParametrosReporteExtendedTest(TestCase):
    """Cover lines 81 (non-str key) and 83 (key too short/long)."""

    def test_clave_no_es_string(self):
        """Line 81: dict with non-string key raises ValidationError."""
        # Passing value dict directly (not JSON) so the loop hits line 80-81
        with self.assertRaises(ValidationError) as ctx:
            validar_parametros_reporte({123: "valor"})
        self.assertIn("string", str(ctx.exception).lower())

    def test_clave_demasiado_corta(self):
        """Line 83: key with 1 char is too short (< 2)."""
        with self.assertRaises(ValidationError) as ctx:
            validar_parametros_reporte({"x": "valor"})
        self.assertIn("2", str(ctx.exception))

    def test_clave_demasiado_larga(self):
        """Line 83: key with 51 chars is too long (> 50)."""
        long_key = "a" * 51
        with self.assertRaises(ValidationError) as ctx:
            validar_parametros_reporte({long_key: "valor"})
        self.assertIn("50", str(ctx.exception))


# =============================================================================
# validar_configuracion_dashboard — lines 158-159, 162
# =============================================================================

class ValidarConfiguracionDashboardExtendedTest(TestCase):
    """Cover invalid JSON string (158-159) and non-dict value (162)."""

    def test_json_invalido_como_string(self):
        """Lines 158-159: string that is not valid JSON raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_configuracion_dashboard("{not: valid json}")
        self.assertIn("json", str(ctx.exception).lower())

    def test_valor_lista_no_dict(self):
        """Line 162: a JSON list (not dict) raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_configuracion_dashboard([{"widgets": []}])
        self.assertIn("diccionario", str(ctx.exception).lower())

    def test_configuracion_valida_con_widgets(self):
        """Valid dashboard config with 1 widget passes."""
        cfg = {"widgets": [{"type": "chart"}]}
        validar_configuracion_dashboard(cfg)  # Should not raise

    def test_configuracion_string_json_valida(self):
        """Valid JSON string with widgets passes."""
        cfg_str = json.dumps({"widgets": [{"type": "table"}]})
        validar_configuracion_dashboard(cfg_str)  # Should not raise


# =============================================================================
# validar_parametros_tarea — lines 442-443, 446
# =============================================================================

class ValidarParametrosTareaExtendedTest(TestCase):
    """Cover invalid JSON string (442-443) and non-dict value but not None (446)."""

    def test_json_invalido_como_string(self):
        """Lines 442-443: invalid JSON string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_parametros_tarea("{bad json}")
        self.assertIn("json", str(ctx.exception).lower())

    def test_valor_lista_no_dict(self):
        """Line 446: list value (not dict) raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_parametros_tarea(["a", "b"])
        self.assertIn("diccionario", str(ctx.exception).lower())

    def test_none_retorna(self):
        """None returns immediately without error."""
        result = validar_parametros_tarea(None)
        self.assertIsNone(result)

    def test_dict_valido_pasa(self):
        """Valid dict less than 20 keys passes."""
        validar_parametros_tarea({"fecha_inicio": "2026-01-01"})  # Should not raise


# =============================================================================
# validar_pid_ejecucion — line 589
# =============================================================================

class ValidarPidEjecucionExtendedTest(TestCase):
    """Cover line 589: PID > 2,147,483,647."""

    def test_pid_excede_maximo(self):
        """Line 589: PID > 2147483647 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_pid_ejecucion(2147483648)
        self.assertIn("máximo", str(ctx.exception).lower())

    def test_pid_valido(self):
        """Valid PID passes."""
        validar_pid_ejecucion(1234)  # Should not raise

    def test_pid_none_retorna(self):
        """None returns without error."""
        result = validar_pid_ejecucion(None)
        self.assertIsNone(result)

    def test_pid_menor_a_uno(self):
        """PID < 1 raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_pid_ejecucion(0)
        self.assertIn("0", str(ctx.exception))


# =============================================================================
# validar_configuracion_json — lines 647-656
# =============================================================================

class ValidarConfiguracionJsonTest(TestCase):
    """Cover all branches of validar_configuracion_json."""

    def test_none_retorna(self):
        """Line 647-648: None returns immediately."""
        result = validar_configuracion_json(None)
        self.assertIsNone(result)

    def test_string_json_valido(self):
        """Lines 649-651: valid JSON string parsed and returned."""
        result = validar_configuracion_json('{"key": "val"}')
        self.assertEqual(result, {"key": "val"})

    def test_string_json_invalido(self):
        """Lines 652-653: invalid JSON string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_configuracion_json("{bad json}")
        self.assertIn("json", str(ctx.exception).lower())

    def test_valor_lista_no_dict(self):
        """Lines 654-655: list (not dict) raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_configuracion_json(["a", "b"])
        self.assertIn("objeto json", str(ctx.exception).lower())

    def test_dict_valido_retorna(self):
        """Line 656: dict returns correctly."""
        result = validar_configuracion_json({"clave": "valor"})
        self.assertEqual(result, {"clave": "valor"})


# =============================================================================
# validar_frecuencia_ejecucion — lines 661-666
# =============================================================================

class ValidarFrecuenciaEjecucionTest(TestCase):
    """Cover invalid frequency path (lines 662-665) and return (666)."""

    def test_frecuencia_invalida(self):
        """Lines 662-665: unlisted frequency raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_frecuencia_ejecucion("bimensual")
        self.assertIn("frecuencia", str(ctx.exception).lower())

    def test_frecuencia_valida_retorna(self):
        """Line 666: valid frequency returns the value."""
        result = validar_frecuencia_ejecucion("diaria")
        self.assertEqual(result, "diaria")

    def test_frecuencia_vacia_retorna(self):
        """Empty string — falsy value skips validation and returns."""
        result = validar_frecuencia_ejecucion("")
        self.assertEqual(result, "")

    def test_frecuencia_none_retorna(self):
        """None is falsy — skips validation and returns None."""
        result = validar_frecuencia_ejecucion(None)
        self.assertIsNone(result)


# =============================================================================
# validar_formato_datos_json — lines 671-680
# =============================================================================

class ValidarFormatoDatosJsonTest(TestCase):
    """Cover all branches of validar_formato_datos_json."""

    def test_none_retorna(self):
        """Lines 671-672: None returns immediately."""
        result = validar_formato_datos_json(None)
        self.assertIsNone(result)

    def test_string_json_dict_valido(self):
        """Lines 673-675: valid JSON dict string parsed and returned."""
        result = validar_formato_datos_json('{"col": "val"}')
        self.assertEqual(result, {"col": "val"})

    def test_string_json_lista_valida(self):
        """Lines 673-675: valid JSON list string parsed and returned."""
        result = validar_formato_datos_json('[1, 2, 3]')
        self.assertEqual(result, [1, 2, 3])

    def test_string_json_invalido(self):
        """Lines 676-677: invalid JSON string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_formato_datos_json("{bad json}")
        self.assertIn("json", str(ctx.exception).lower())

    def test_valor_entero_no_valido(self):
        """Lines 678-679: integer (not dict or list) raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_formato_datos_json(42)
        self.assertIn("objeto o lista", str(ctx.exception).lower())

    def test_dict_valido_retorna(self):
        """Dict passes through and is returned."""
        result = validar_formato_datos_json({"key": "val"})
        self.assertEqual(result, {"key": "val"})

    def test_lista_valida_retorna(self):
        """List passes through and is returned."""
        result = validar_formato_datos_json([1, 2, 3])
        self.assertEqual(result, [1, 2, 3])
