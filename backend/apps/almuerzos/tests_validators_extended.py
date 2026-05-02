"""
Extended tests for apps/almuerzos/validators.py covering previously missing lines.

Missing lines targeted: 90-91, 205, 209-210, 281-284, 309, 332, 362-365, 404-405,
435-436, 530, 534-539, 549, 584, 588-593, 601, 633-634, 663-664, 689-690, 714,
718-719, 732, 781, 785-786, 792, 799, 817, 840, 845-846, 877, 881, 883-886, 911,
915-916, 929, 947, 1039, 1066-1067, 1070, 1080
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.almuerzos.validators import (
    validar_precio_mensual_plan,
    validar_precio_unitario_tipo,
    validar_fecha_fin_suscripcion,
    validar_estado_suscripcion,
    validar_rango_fechas_suscripcion,
    validar_fecha_consumo,
    validar_hora_registro,
    validar_costo_almuerzo,
    validar_anio_cuenta,
    validar_mes_cuenta,
    validar_cantidad_almuerzos,
    validar_monto_total_cuenta,
    validar_monto_pagado_cuenta,
    validar_estado_cuenta,
    validar_fecha_pago,
    validar_monto_pago,
    validar_medio_pago,
    validar_nombre_alergeno,
    validar_palabras_clave_alergeno,
)

# ==============================================================================
# Plan validators
# ==============================================================================


class ValidarPrecioMensualExtendedTest(TestCase):
    """Lines 90-91: precio_mensual non-numeric."""

    def test_precio_mensual_no_numerico(self):
        """Lines 90-91: non-numeric string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_mensual_plan("no-es-numero")
        self.assertIn("número", str(ctx.exception).lower())

    def test_precio_mensual_valido(self):
        """Valid precio_mensual passes."""
        validar_precio_mensual_plan(Decimal("50000"))  # Should not raise


class ValidarPrecioUnitarioExtendedTest(TestCase):
    """Lines 205, 209-210: precio_unitario None and non-numeric."""

    def test_precio_unitario_none(self):
        """Line 205: None precio_unitario raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_unitario_tipo(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_precio_unitario_no_numerico(self):
        """Lines 209-210: non-numeric string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_unitario_tipo("abc")
        self.assertIn("número", str(ctx.exception).lower())


# ==============================================================================
# Suscripcion validators
# ==============================================================================


class ValidarFechaFinSuscripcionExtendedTest(TestCase):
    """Lines 281-284, 309: string parsing and optional."""

    def test_fecha_fin_none_returns(self):
        """Line 277/278: None returns without error (optional)."""
        validar_fecha_fin_suscripcion(None)  # Should not raise

    def test_fecha_fin_empty_string_returns(self):
        """Line 309: empty string returns without error."""
        validar_fecha_fin_suscripcion("")  # Should not raise

    def test_fecha_fin_string_valida(self):
        """Lines 281-282: valid date string is parsed and accepted."""
        future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        validar_fecha_fin_suscripcion(future_date)  # Should not raise

    def test_fecha_fin_string_invalida(self):
        """Lines 283-284: invalid date string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_fin_suscripcion("not-a-date")
        self.assertIn("fecha", str(ctx.exception).lower())


class ValidarEstadoSuscripcionExtendedTest(TestCase):
    """Line 309: None/empty returns without error."""

    def test_estado_none_returns(self):
        """None estado returns without error."""
        validar_estado_suscripcion(None)  # Should not raise

    def test_estado_vacio_returns(self):
        """Empty estado returns without error."""
        validar_estado_suscripcion("")  # Should not raise


class ValidarRangoFechasExtendedTest(TestCase):
    """Line 332: fecha_inicio None returns early."""

    def test_fecha_inicio_none_returns(self):
        """Line 332: None fecha_inicio returns without error."""
        validar_rango_fechas_suscripcion(None, date.today())  # Should not raise


# ==============================================================================
# RegistroConsumo validators
# ==============================================================================


class ValidarFechaConsumoExtendedTest(TestCase):
    """Lines 362-365: string date parsing."""

    def test_fecha_consumo_string_valida(self):
        """Lines 362-363: valid date string is parsed and accepted."""
        fecha_str = date.today().strftime("%Y-%m-%d")
        validar_fecha_consumo(fecha_str)  # Should not raise

    def test_fecha_consumo_string_invalida(self):
        """Lines 364-365: invalid date string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_consumo("not-a-date")
        self.assertIn("fecha", str(ctx.exception).lower())


class ValidarHoraRegistroExtendedTest(TestCase):
    """Lines 404-405: invalid time format."""

    def test_hora_invalida(self):
        """Lines 404-405: completely invalid time string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_hora_registro("not-a-time")
        self.assertIn("hora", str(ctx.exception).lower())

    def test_hora_formato_hhmm(self):
        """Valid HH:MM string is parsed."""
        validar_hora_registro("10:30")  # Should not raise

    def test_hora_formato_hhmmss(self):
        """Valid HH:MM:SS string is parsed."""
        validar_hora_registro("10:30:00")  # Should not raise


class ValidarCostoAlmuerzoExtendedTest(TestCase):
    """Lines 435-436: costo non-numeric."""

    def test_costo_none_returns(self):
        """None costo returns without error (optional)."""
        validar_costo_almuerzo(None)  # Should not raise

    def test_costo_vacio_returns(self):
        """Empty costo returns without error."""
        validar_costo_almuerzo("")  # Should not raise

    def test_costo_no_numerico(self):
        """Lines 435-436: non-numeric string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_costo_almuerzo("abc")
        self.assertIn("número", str(ctx.exception).lower())

    def test_costo_valido(self):
        """Valid decimal costo passes."""
        validar_costo_almuerzo(Decimal("15000"))  # Should not raise


# ==============================================================================
# Cuenta Mensual validators
# ==============================================================================


class ValidarAnioExtendedTest(TestCase):
    """Lines 633-634: año non-integer."""

    def test_anio_no_entero(self):
        """Lines 633-634: non-integer string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_anio_cuenta("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_anio_valido(self):
        """Valid integer year passes."""
        validar_anio_cuenta(2024)  # Should not raise


class ValidarMesExtendedTest(TestCase):
    """Lines 663-664: mes non-integer."""

    def test_mes_no_entero(self):
        """Lines 663-664: non-integer string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_mes_cuenta("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_mes_valido(self):
        """Valid month passes."""
        validar_mes_cuenta(6)  # Should not raise


class ValidarCantidadAlmuerzosExtendedTest(TestCase):
    """Lines 689-690: cantidad non-integer."""

    def test_cantidad_no_entera(self):
        """Lines 689-690: non-integer string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cantidad_almuerzos("abc")
        self.assertIn("entero", str(ctx.exception).lower())

    def test_cantidad_valida(self):
        """Valid integer quantity passes."""
        validar_cantidad_almuerzos(20)  # Should not raise


class ValidarMontoTotalCuentaExtendedTest(TestCase):
    """Lines 714, 718-719, 732."""

    def test_monto_total_none(self):
        """Line 714: None monto_total raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_total_cuenta(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_monto_total_no_numerico(self):
        """Lines 718-719: non-numeric raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_total_cuenta("abc")
        self.assertIn("número", str(ctx.exception).lower())

    def test_monto_total_demasiados_decimales(self):
        """Line 732: monto with > 2 decimals raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_total_cuenta(Decimal("1000.123"))
        self.assertIn("2 decimales", str(ctx.exception).lower())

    def test_monto_total_valido(self):
        """Valid monto_total passes."""
        validar_monto_total_cuenta(Decimal("500000.00"))  # Should not raise


class ValidarMontoPagadoCuentaExtendedTest(TestCase):
    """Lines 781, 785-786, 792, 799."""

    def test_monto_pagado_none(self):
        """Line 781: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pagado_cuenta(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_monto_pagado_no_numerico(self):
        """Lines 785-786: non-numeric raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pagado_cuenta("abc")
        self.assertIn("número", str(ctx.exception).lower())

    def test_monto_pagado_excede_maximo(self):
        """Line 792: monto > 10M raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pagado_cuenta(Decimal("11000000"))
        self.assertIn("10,000,000", str(ctx.exception))

    def test_monto_pagado_demasiados_decimales(self):
        """Line 799: monto with > 2 decimals raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pagado_cuenta(Decimal("100.999"))
        self.assertIn("2 decimales", str(ctx.exception).lower())

    def test_monto_pagado_valido(self):
        """Valid monto_pagado passes."""
        validar_monto_pagado_cuenta(Decimal("250000.50"))  # Should not raise


class ValidarEstadoCuentaExtendedTest(TestCase):
    """Line 817."""

    def test_estado_none(self):
        """Line 817: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_estado_cuenta(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_estado_vacio(self):
        """Line 817: empty string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_estado_cuenta("")
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_estado_valido(self):
        """Valid estados pass."""
        for estado in ["Pendiente", "Pagada", "Vencida", "Cancelada"]:
            validar_estado_cuenta(estado)  # Should not raise


# ==============================================================================
# Pago validators
# ==============================================================================


class ValidarFechaPagoExtendedTest(TestCase):
    """Lines 877, 881, 883-886."""

    def test_fecha_pago_none(self):
        """Line 877: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_pago(None)
        self.assertIn("obligatori", str(ctx.exception).lower())

    def test_fecha_pago_datetime_object(self):
        """Line 881: datetime object is converted to date."""
        from datetime import datetime as dt

        dt_object = dt.now()
        validar_fecha_pago(dt_object)  # Should not raise (today's datetime)

    def test_fecha_pago_string_valida(self):
        """Lines 883-884: valid date string (no time part)."""
        fecha_str = date.today().strftime("%Y-%m-%d")
        validar_fecha_pago(fecha_str)  # Should not raise

    def test_fecha_pago_string_invalida(self):
        """Lines 885-886: invalid date string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_fecha_pago("not-a-date")
        self.assertIn("fecha", str(ctx.exception).lower())


class ValidarMontoPagoExtendedTest(TestCase):
    """Lines 911, 915-916, 929."""

    def test_monto_pago_none(self):
        """Line 911: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pago(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_monto_pago_no_numerico(self):
        """Lines 915-916: non-numeric raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pago("abc")
        self.assertIn("número", str(ctx.exception).lower())

    def test_monto_pago_demasiados_decimales(self):
        """Line 929: monto with > 2 decimals raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_monto_pago(Decimal("1000.999"))
        self.assertIn("2 decimales", str(ctx.exception).lower())

    def test_monto_pago_valido(self):
        """Valid monto passes."""
        validar_monto_pago(Decimal("50000"))  # Should not raise


class ValidarMedioPagoExtendedTest(TestCase):
    """Line 947."""

    def test_medio_pago_none(self):
        """Line 947: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_medio_pago(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_medio_pago_vacio(self):
        """Line 947: empty string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_medio_pago("")
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_medios_validos(self):
        """All valid medios pass."""
        for medio in ["Efectivo", "Transferencia", "Tarjeta Débito", "Tarjeta Crédito", "Cheque"]:
            validar_medio_pago(medio)  # Should not raise


# ==============================================================================
# Alergeno validators
# ==============================================================================


class ValidarNombreAlergeno(TestCase):
    """Line 1039: nombre with invalid characters."""

    def test_nombre_caracteres_invalidos(self):
        """Line 1039: nombre with @ raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nombre_alergeno("Maní@Especial")
        self.assertIn("caracteres", str(ctx.exception).lower())

    def test_nombre_valido(self):
        """Valid alergeno nombre passes."""
        validar_nombre_alergeno("Maní")  # Should not raise


class ValidarPalabrasClave(TestCase):
    """Lines 1066-1067, 1070."""

    def test_json_invalido(self):
        """Lines 1066-1067: invalid JSON string raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_palabras_clave_alergeno("{not valid json}")
        self.assertIn("json", str(ctx.exception).lower())

    def test_no_es_lista(self):
        """Line 1070: JSON that is not a list raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_palabras_clave_alergeno('{"key": "value"}')
        self.assertIn("lista", str(ctx.exception).lower())

    def test_lista_valida(self):
        """Valid list of palabras_clave passes."""
        validar_palabras_clave_alergeno(["gluten", "lactosa"])  # Should not raise

    def test_lista_json_valida(self):
        """Valid JSON array string passes."""
        validar_palabras_clave_alergeno('["gluten", "lactosa"]')  # Should not raise
