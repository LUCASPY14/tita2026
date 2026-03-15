"""
Tests de ramas faltantes en clientes/validators.py
Cubre branches no alcanzados por los tests principales.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.clientes.validators import (
    validar_ruc_ci,
    validar_telefono_cliente,
)


class TestValidarRucCiBranches:
    """
    Branch 147->148: CI con puntos pero dígitos limpios fuera de rango 6-8.
    Branch 157->158: CI sin separadores con longitud fuera de rango 6-8.
    """

    def test_dots_format_too_short_raises(self):
        """Contiene puntos pero string total muy corto → raises por la guardia de longitud."""
        # "1.2.3" total len=5 < 6 → early guard raises
        with pytest.raises(ValidationError):
            validar_ruc_ci("1.2.3")

    def test_dots_format_too_long_raises(self):
        """Branch 147->148: contiene puntos, dígitos limpios > 8 → raises."""
        # "1.2.3.4.5.6.7.8.9" → 9 dígitos limpios > 8 → raises
        with pytest.raises(ValidationError, match="entre 6 y 8 dígitos"):
            validar_ruc_ci("1.234.5678.9")

    def test_numeric_only_too_short_raises(self):
        """Solo dígitos, len < 6 → raises por la guardia de longitud."""
        # "12345" total len=5 < 6 → early guard raises
        with pytest.raises(ValidationError):
            validar_ruc_ci("12345")

    def test_numeric_only_too_long_raises(self):
        """Branch 157->158: solo dígitos, len > 8 → raises."""
        # "123456789" = 9 dígitos, > 8 → raises
        with pytest.raises(ValidationError, match="entre 6 y 8 dígitos"):
            validar_ruc_ci("123456789")


class TestValidarTelefonoClienteBranches:
    """Branch 201->202: teléfono con longitud fuera de rango 7-20 → raises."""

    def test_too_short_raises(self):
        """Branch 201->202: len < 7 → raises."""
        with pytest.raises(ValidationError, match="entre 7 y 20"):
            validar_telefono_cliente("123456")  # 6 caracteres

    def test_too_long_raises(self):
        """Branch 201->202: len > 20 → raises."""
        with pytest.raises(ValidationError, match="entre 7 y 20"):
            validar_telefono_cliente("0" * 21)  # 21 caracteres
