"""
Tests extendidos para apps/clientes/validators.py
Cubre líneas faltantes:
98 (razon_social bad chars),
132-158 (validar_ruc_ci múltiples ramas),
202 (teléfono no dígitos),
220 (teléfono fijo longitud inválida),
244-247 (limite_credito inválido type),
512-515 (nivel nivel no int),
539-542 (orden no int),
575-578 (anio no int),
779-782 (monto no Decimal)
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clientes.validators import (
    validar_limite_credito_cliente,
    validar_razon_social,
    validar_ruc_ci,
    validar_telefono_cliente,
)

# =============================================================================
# validar_razon_social - línea 98
# =============================================================================


class ValidarRazonSocialClienteExtendedTest(TestCase):
    def test_caracteres_invalidos_raises(self):
        """Línea 98: razon social con @ → raises"""
        with self.assertRaises(ValidationError):
            validar_razon_social("Empresa@Test")

    def test_caracteres_lt_gt_raises(self):
        """Razon social con < > → raises"""
        with self.assertRaises(ValidationError):
            validar_razon_social("<Script>")

    def test_razon_social_valida_pasa(self):
        """Razon social válida → no raises"""
        validar_razon_social("Empresa S.A. & Cia")

    def test_razon_social_none_pasa(self):
        """Razon social None → no raises (opcional)"""
        validar_razon_social(None)


# =============================================================================
# validar_ruc_ci - líneas 132, 135, 138, 145, 148, 153, 158
# =============================================================================


class ValidarRucCiExtendedTest(TestCase):

    def test_ruc_con_guion_mas_de_dos_partes_raises(self):
        """Línea 132: más de una parte separada por guion → formato inválido"""
        with self.assertRaises(ValidationError) as ctx:
            validar_ruc_ci("123-456-7")
        self.assertIn("inválido", str(ctx.exception).lower())

    def test_ruc_numero_no_numerico_raises(self):
        """Línea 135: número del RUC no es dígito → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("ABCDE-1")

    def test_ruc_numero_longitud_invalida_raises(self):
        """Línea 138: número tiene longitud distinta a 5 u 8 → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("123456-1")  # 6 dígitos

    def test_ruc_digito_verificador_no_digito_raises(self):
        """Línea 145: dígito verificador no es un solo dígito → raises"""
        with self.assertRaises(ValidationError) as ctx:
            validar_ruc_ci("12345-AB")
        self.assertIn("dígito verificador", str(ctx.exception).lower())

    def test_ci_con_punto_no_numerica_raises(self):
        """Línea 148: CI con puntos no numérica → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("1.2A4.567")

    def test_ci_con_punto_longitud_invalida_raises(self):
        """Línea 153: CI con puntos pero muy corta → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("1.23")  # 3 dígitos < 6

    def test_ci_sin_puntos_no_numerica_raises(self):
        """Línea 158: CI sin puntos contiene letras → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("ABCDEF")

    def test_ci_sin_puntos_valida(self):
        """CI numérica válida → no raises"""
        validar_ruc_ci("1234567")

    def test_ruc_formato_valido_5_digitos(self):
        """RUC con 5 dígitos válido → no raises"""
        validar_ruc_ci("12345-1")

    def test_ruc_formato_valido_8_digitos(self):
        """RUC con 8 dígitos válido → no raises"""
        validar_ruc_ci("12345678-1")

    def test_ruc_ci_vacio_raises(self):
        """RUC/CI vacío → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("")

    def test_ruc_ci_demasiado_corto_raises(self):
        """Demasiado corto → raises"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("123")


# =============================================================================
# validar_telefono_cliente - líneas 202, 220
# =============================================================================


class ValidarTelefonoClienteExtendedTest(TestCase):

    def test_telefono_con_letras_raises(self):
        """Línea 202: telefono con letras → raises"""
        with self.assertRaises(ValidationError) as ctx:
            validar_telefono_cliente("09ABCDEFGH")
        self.assertIn("dígitos", str(ctx.exception).lower())

    def test_telefono_fijo_longitud_invalida_raises(self):
        """Línea 220: teléfono fijo con longitud incorrecta → raises"""
        # Empieza con 0 pero no con 09, y tiene longitud inválida
        with self.assertRaises(ValidationError):
            validar_telefono_cliente("0211234")  # 7 dígitos - debería ser 9

    def test_telefono_no_empieza_cero_raises(self):
        """Teléfono que no empieza con 0 → raises"""
        with self.assertRaises(ValidationError):
            validar_telefono_cliente("1981234567")

    def test_telefono_movil_valido(self):
        """Teléfono móvil válido → no raises"""
        validar_telefono_cliente("0981234567")

    def test_telefono_none_pasa(self):
        """Teléfono None → no raises (opcional)"""
        validar_telefono_cliente(None)


# =============================================================================
# validar_limite_credito_cliente - líneas 244-247
# =============================================================================


class ValidarLimiteCreditoClienteExtendedTest(TestCase):

    def test_limite_credito_string_invalido_raises(self):
        """Líneas 244-247: string no numérico → except → raises"""
        with self.assertRaises(ValidationError) as ctx:
            validar_limite_credito_cliente("no_es_numero")
        self.assertIn("número válido", str(ctx.exception).lower())

    def test_limite_credito_negativo_raises(self):
        """Límite negativo → raises"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("-100.00"))

    def test_limite_credito_excede_maximo_raises(self):
        """Límite > 50,000,000 → raises"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("60000000.00"))

    def test_limite_credito_demasiados_decimales_raises(self):
        """Más de 2 decimales → raises"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("1000.123"))

    def test_limite_credito_valido(self):
        """Límite válido → no raises"""
        validar_limite_credito_cliente(Decimal("1000000.00"))

    def test_limite_credito_none_pasa(self):
        """Límite None → no raises (opcional)"""
        validar_limite_credito_cliente(None)

    def test_limite_credito_cero_valido(self):
        """Límite = 0 → no raises"""
        validar_limite_credito_cliente(Decimal("0.00"))


# =============================================================================
# validar_nivel_grado, validar_orden_visualizacion, validar_anio_escolar
# líneas 512-515, 539-542, 575-578
# =============================================================================


class ValidarNivelGradoExtendedTest(TestCase):
    def setUp(self):
        from apps.clientes.validators import validar_nivel_grado

        self.func = validar_nivel_grado

    def test_nivel_string_invalido_raises(self):
        """Líneas 512-515: nivel no convertible a int → raises"""
        with self.assertRaises(ValidationError) as ctx:
            self.func("abc")
        self.assertIn("número entero", str(ctx.exception).lower())

    def test_nivel_none_raises(self):
        """Nivel None → raises oblig"""
        with self.assertRaises(ValidationError):
            self.func(None)

    def test_nivel_fuera_rango_raises(self):
        """Nivel > 12 → raises"""
        with self.assertRaises(ValidationError):
            self.func(13)

    def test_nivel_valido(self):
        """Nivel 5 → no raises"""
        self.func(5)


class ValidarOrdenVisualizacionExtendedTest(TestCase):
    def setUp(self):
        from apps.clientes.validators import validar_orden_visualizacion

        self.func = validar_orden_visualizacion

    def test_orden_string_invalido_raises(self):
        """Líneas 539-542: orden no convertible a int → raises"""
        with self.assertRaises(ValidationError) as ctx:
            self.func("xyz")
        self.assertIn("número entero", str(ctx.exception).lower())

    def test_orden_none_raises(self):
        """Orden None → raises oblig"""
        with self.assertRaises(ValidationError):
            self.func(None)

    def test_orden_menor_uno_raises(self):
        """Orden < 1 → raises"""
        with self.assertRaises(ValidationError):
            self.func(0)

    def test_orden_mayor_cien_raises(self):
        """Orden > 100 → raises"""
        with self.assertRaises(ValidationError):
            self.func(101)

    def test_orden_valido(self):
        """Orden 3 → no raises"""
        self.func(3)


class ValidarAnioEscolarExtendedTest(TestCase):
    def setUp(self):
        from apps.clientes.validators import validar_anio_escolar

        self.func = validar_anio_escolar

    def test_anio_string_invalido_raises(self):
        """Líneas 575-578: año no convertible a int → raises"""
        with self.assertRaises(ValidationError) as ctx:
            self.func("dos_mil_veinte")
        self.assertIn("número entero", str(ctx.exception).lower())

    def test_anio_none_raises(self):
        """Año None → raises oblig"""
        with self.assertRaises(ValidationError):
            self.func(None)

    def test_anio_anterior_1990_raises(self):
        """Año < 1990 → raises"""
        with self.assertRaises(ValidationError):
            self.func(1989)

    def test_anio_valido(self):
        """Año 2024 → no raises"""
        self.func(2024)


# =============================================================================
# validar_monto_autorizacion - líneas 779-782
# =============================================================================


class ValidarMontoAutorizacionExtendedTest(TestCase):
    def setUp(self):
        from apps.clientes.validators import validar_monto_autorizado

        self.func = validar_monto_autorizado

    def test_monto_string_invalido_raises(self):
        """Líneas 779-782: monto string inválido → except → raises"""
        with self.assertRaises(ValidationError) as ctx:
            self.func("no_es_numero")
        self.assertIn("número válido", str(ctx.exception).lower())

    def test_monto_none_raises(self):
        """Monto None (falsy) → raises oblig"""
        with self.assertRaises(ValidationError):
            self.func(None)

    def test_monto_negativo_raises(self):
        """Monto negativo → raises"""
        with self.assertRaises(ValidationError):
            self.func(Decimal("-100.00"))

    def test_monto_excede_maximo_raises(self):
        """Monto > 5,000,000 → raises"""
        with self.assertRaises(ValidationError):
            self.func(Decimal("6000000.00"))

    def test_monto_demasiados_decimales_raises(self):
        """Más de 2 decimales → raises"""
        with self.assertRaises(ValidationError):
            self.func(Decimal("100.123"))

    def test_monto_valido(self):
        """Monto válido → no raises"""
        self.func(Decimal("500000.00"))
