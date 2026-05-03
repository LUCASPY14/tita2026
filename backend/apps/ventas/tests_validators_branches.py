"""
Tests de ramas faltantes en ventas/validators.py
Cubre branches no alcanzados por los tests principales.
"""

from django.core.exceptions import ValidationError

import pytest

from apps.ventas.validators import (
    validar_codigo_promocion,
    validar_credito_disponible,
    validar_dias_semana,
    validar_saldo_tarjeta,
)


class TestValidarCodigoPromocionBranches:
    """Branch 129->130: isinstance check con valor no-string."""

    def test_non_string_raises(self):
        """Pasa un entero (no string, no falsy) → isinstance False → raises."""
        with pytest.raises(ValidationError, match="string"):
            validar_codigo_promocion(123)

    def test_float_raises(self):
        with pytest.raises(ValidationError, match="string"):
            validar_codigo_promocion(3.14)


class TestValidarCreditoDisponibleBranches:
    """Branch 333->334: isinstance check con objeto que no es Clientes."""

    def test_non_cliente_instance_raises(self):
        """Pasa un string (no instancia de Clientes) → raises ValidationError."""
        with pytest.raises(ValidationError, match="instancia válida de Cliente"):
            validar_credito_disponible("no_es_cliente", 100)

    def test_none_raises(self):
        with pytest.raises(ValidationError, match="instancia válida de Cliente"):
            validar_credito_disponible(None, 100)


class TestValidarSaldoTarjetaBranches:
    """Branch 367->368: isinstance check con objeto que no es Tarjetas."""

    def test_non_tarjeta_instance_raises(self):
        """Pasa un dict (no instancia de Tarjetas) → raises ValidationError."""
        with pytest.raises(ValidationError, match="instancia válida de Tarjeta"):
            validar_saldo_tarjeta({}, 100)

    def test_none_raises(self):
        with pytest.raises(ValidationError, match="instancia válida de Tarjeta"):
            validar_saldo_tarjeta(None, 50)


class TestValidarDiasSemanaBranches:
    """Branch 422->423: isinstance check en cada dia de la lista."""

    def test_string_in_list_raises(self):
        """Pasa string en lista → not isinstance(dia, int) → raises."""
        with pytest.raises(ValidationError, match="número entero"):
            validar_dias_semana(["lunes"])

    def test_float_in_list_raises(self):
        with pytest.raises(ValidationError, match="número entero"):
            validar_dias_semana([1, 2.5])
