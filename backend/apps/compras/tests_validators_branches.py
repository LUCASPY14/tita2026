"""
Tests de ramas faltantes en compras/validators.py
Cubre branches no alcanzados por los tests principales.
"""

from django.core.exceptions import ValidationError

import pytest

from apps.compras.validators import validar_numero_factura


class TestValidarNumeroFacturaBranches:
    """
    Branch 356->361: la condición if not (match_paraguayo or match_simple or len >= 5)
    es True → string muy corto (len < 5) y no coincide con ningún regex → raises.
    """

    def test_very_short_string_raises(self):
        """Branch 356->361: string de 2 chars → len < 5, no es dígito-formato → raises."""
        with pytest.raises(ValidationError, match="formato válido"):
            validar_numero_factura("ab")

    def test_three_char_non_matching_raises(self):
        """Branch 356->361: string de 3 chars no numérico → raises."""
        with pytest.raises(ValidationError, match="formato válido"):
            validar_numero_factura("abc")

    def test_four_char_numeric_raises(self):
        """Branch 356->361: 4 dígitos → no coincide con ningún regex, len < 5 → raises."""
        with pytest.raises(ValidationError, match="formato válido"):
            validar_numero_factura("1234")
