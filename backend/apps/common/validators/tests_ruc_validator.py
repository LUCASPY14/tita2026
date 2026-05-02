"""
Tests para validador de RUC/CI paraguayo
"""

import pytest
from django.core.exceptions import ValidationError
from apps.common.validators.ruc_validator import validate_ruc


class TestValidateRuc:
    """Tests para validación de RUC/CI paraguayo"""

    # === Tests de formatos válidos ===

    def test_ruc_valido_con_guion_7_digitos(self):
        """RUC válido: 1234567-8 (7 dígitos + guión + dígito)"""
        result = validate_ruc("1234567-8")
        assert result == "1234567-8"

    def test_ruc_valido_con_guion_8_digitos(self):
        """RUC válido: 12345678-9 (8 dígitos + guión + dígito)"""
        result = validate_ruc("12345678-9")
        assert result == "12345678-9"

    def test_ruc_valido_con_guion_1_digito(self):
        """RUC válido mínimo: 1-2 (1 dígito + guión + dígito)"""
        result = validate_ruc("1-2")
        assert result == "1-2"

    def test_ci_valido_7_digitos(self):
        """CI válido: 1234567 (sin guión)"""
        result = validate_ruc("1234567")
        assert result == "1234567"

    def test_ci_valido_1_digito(self):
        """CI válido mínimo: 1"""
        result = validate_ruc("1")
        assert result == "1"

    def test_ci_valido_8_digitos(self):
        """CI válido máximo: 12345678"""
        result = validate_ruc("12345678")
        assert result == "12345678"

    def test_valor_con_espacios_se_limpia(self):
        """Valor con espacios debe limpiarse y validarse"""
        result = validate_ruc("  1234567-8  ")
        assert result == "1234567-8"

    def test_valor_numerico_se_convierte_string(self):
        """Valor numérico debe convertirse a string"""
        result = validate_ruc(1234567)
        assert result == "1234567"

    # === Tests de formatos inválidos ===

    def test_valor_none_levanta_error(self):
        """None debe levantar ValidationError"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc(None)
        assert "El RUC/CI es requerido" in str(excinfo.value)

    def test_valor_vacio_levanta_error(self):
        """String vacío debe levantar ValidationError"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("")
        assert "El RUC/CI es requerido" in str(excinfo.value)

    def test_valor_solo_espacios_levanta_error(self):
        """String solo con espacios debe levantar ValidationError (formato inválido)"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("   ")
        assert "Formato inválido" in str(excinfo.value)

    def test_formato_con_letras_levanta_error(self):
        """Formato con letras debe levantar ValidationError"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("ABC1234-5")
        assert "Formato inválido" in str(excinfo.value)

    def test_formato_sin_guion_con_letra_levanta_error(self):
        """CI con letra debe levantar ValidationError"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("123456A")
        assert "Formato inválido" in str(excinfo.value)

    def test_ruc_con_guion_pero_sin_digito_verificador(self):
        """RUC con guión pero sin dígito verificador debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("1234567-")
        assert "Formato inválido" in str(excinfo.value)

    def test_ruc_con_multiples_guiones(self):
        """RUC con múltiples guiones debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("123-456-7")
        assert "Formato inválido" in str(excinfo.value)

    def test_ruc_con_mas_de_un_digito_verificador(self):
        """RUC con más de 1 dígito verificador debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("1234567-89")
        assert "Formato inválido" in str(excinfo.value)

    def test_ruc_con_9_digitos_base(self):
        """RUC con 9 dígitos base (más de 8) debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("123456789-0")
        assert "Formato inválido" in str(excinfo.value)

    def test_ci_con_9_digitos(self):
        """CI con 9 dígitos (más de 8) debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("123456789")
        assert "Formato inválido" in str(excinfo.value)

    def test_formato_con_caracteres_especiales(self):
        """Formato con caracteres especiales debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("1234@567-8")
        assert "Formato inválido" in str(excinfo.value)

    def test_guion_al_inicio(self):
        """Guión al inicio debe fallar"""
        with pytest.raises(ValidationError) as excinfo:
            validate_ruc("-1234567")
        assert "Formato inválido" in str(excinfo.value)
