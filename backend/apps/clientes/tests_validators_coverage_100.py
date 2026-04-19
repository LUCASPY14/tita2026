"""
Tests de cobertura completa para clientes.validators
Objetivo: Alcanzar 100% de cobertura en casos edge de validaciones

Cobertura de líneas:
- L148: CI con puntos pero caracteres inválidos
- L158: RUC/CI numérico con caracteres no numéricos  
- L202: Teléfono con caracteres no permitidos
"""

import pytest
from django.core.exceptions import ValidationError
from apps.clientes.validators import validar_ruc_ci, validar_telefono_cliente


@pytest.mark.parametrize("ruc_ci_invalido,error_esperado", [
    ("123.45a", "dígitos"),  # L148: Punto con letras
    ("1.234.567-a", "dígitos"),  # L148: Puntos válidos pero letra al final
    ("123.abc.456", "dígitos"),  # L148: Letras entre puntos
])
def test_validar_ruc_ci_con_puntos_y_caracteres_invalidos(ruc_ci_invalido, error_esperado):
    """
    Test L148: Validación de CI con puntos pero caracteres inválidos
    
    Cuando el RUC/CI contiene puntos, debe validar que el resto
    sean solo dígitos. Si hay letras u otros caracteres, debe fallar.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_ruc_ci(ruc_ci_invalido)
    
    # Verificar mensaje de error apropiado
    assert error_esperado.lower() in str(exc_info.value).lower()


@pytest.mark.parametrize("ruc_ci_invalido,error_esperado", [
    ("12345abc", "numérico"),  # L158: Números con letras
    ("abc12345", "numérico"),  # L158: Letras al inicio
    ("123a456", "numérico"),  # L158: Letra en medio
    ("1234#567", "numérico"),  # L158: Caracter especial
    ("123 456", "numérico"),  # L158: Espacio en medio (sin guion ni punto)
])
def test_validar_ruc_ci_solo_numeros_con_caracteres_invalidos(ruc_ci_invalido, error_esperado):
    """
    Test L158: RUC/CI sin guion ni puntos pero con caracteres inválidos
    
    Cuando el RUC/CI no tiene guion ni puntos, debe ser completamente
    numérico. Cualquier letra o caracter especial debe ser rechazado.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_ruc_ci(ruc_ci_invalido)
    
    # Verificar mensaje de error
    assert error_esperado.lower() in str(exc_info.value).lower()


@pytest.mark.parametrize("telefono_invalido", [
    "0981#123456",  # L202: Símbolo #
    "0981*123*456",  # L202: Símbolo *
    "0981@123456",  # L202: Símbolo @
    "0981abc1234",  # L202: Letras mezcladas
    "test1234567",  # L202: Letras al inicio
    "0981-123-abc",  # L202: Letras al final con guiones
    "098!123!456",  # L202: Signos de exclamación
    "0981&123456",  # L202: Ampersand
])
def test_validar_telefono_con_caracteres_no_permitidos(telefono_invalido):
    """
    Test L202: Teléfono con caracteres no permitidos
    
    El validador permite solo dígitos, espacios, guiones y paréntesis.
    Cualquier otro caracter (letras, símbolos especiales) debe ser rechazado.
    
    Caracteres permitidos: 0-9, espacios, -, (, )
    Caracteres NO permitidos: a-z, A-Z, #, *, @, !, &, etc.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_telefono_cliente(telefono_invalido)
    
    # Verificar que el error menciona caracteres permitidos
    error_msg = str(exc_info.value).lower()
    assert "dígitos" in error_msg or "caracteres" in error_msg


class TestValidadoresClientesEdgeCases:
    """Tests adicionales para casos límite de validadores"""
    
    def test_ruc_ci_valido_con_puntos(self):
        """Test: RUC/CI válido con puntos debe pasar"""
        # Arrange: CI paraguaya válida con puntos
        ci_valido = "1.234.567"
        
        # Act & Assert - No debe lanzar excepción
        try:
            validar_ruc_ci(ci_valido)
        except ValidationError:
            pytest.fail("CI válida con puntos no debería fallar")
    
    def test_ruc_ci_valido_con_guion(self):
        """Test: RUC/CI válido con guion debe pasar"""
        # Arrange: RUC paraguayo válido
        ruc_valido = "12345678-9"
        
        # Act & Assert
        try:
            validar_ruc_ci(ruc_valido)
        except ValidationError:
            pytest.fail("RUC válido con guion no debería fallar")
    
    def test_ruc_ci_valido_solo_numeros(self):
        """Test: RUC/CI válido solo números debe pasar"""
        # Arrange
        ci_valido = "1234567"
        
        # Act & Assert
        try:
            validar_ruc_ci(ci_valido)
        except ValidationError:
            pytest.fail("CI válida numérica no debería fallar")
    
    def test_telefono_valido_con_formato_internacional(self):
        """Test: Teléfono válido con formato internacional"""
        # Arrange
        telefono_valido = "+595 981 123 456"
        
        # Act & Assert
        try:
            validar_telefono_cliente(telefono_valido)
        except ValidationError:
            pytest.fail("Teléfono válido internacional no debería fallar")
    
    def test_telefono_valido_con_guiones_y_parentesis(self):
        """Test: Teléfono válido con guiones y paréntesis"""
        # Arrange
        telefono_valido = "(0981) 123-456"
        
        # Act & Assert
        try:
            validar_telefono_cliente(telefono_valido)
        except ValidationError:
            pytest.fail("Teléfono con formato válido no debería fallar")
    
    def test_telefono_vacio_o_none_es_opcional(self):
        """Test: Teléfono vacío o None es opcional (no lanza error)"""
        # Act & Assert - No debe lanzar excepción
        try:
            validar_telefono_cliente(None)
            validar_telefono_cliente("")
            validar_telefono_cliente("   ")  # Solo espacios
        except ValidationError:
            pytest.fail("Teléfono vacío/None no debería fallar (es opcional)")


@pytest.mark.parametrize("caso_test,ruc_ci,debe_fallar", [
    ("CI muy corta", "12345", True),
    ("CI mínima válida", "123456", False),
    ("CI máxima válida", "12345678", False),
    ("CI muy larga", "123456789", True),
    ("RUC válido", "80012345-1", False),
    ("RUC con guion inválido", "800123a5-1", True),
], ids=lambda x: x if isinstance(x, str) else "")
def test_validar_ruc_ci_longitud_y_formato(caso_test, ruc_ci, debe_fallar):
    """
    Tests paramétricos para validar longitudes y formatos de RUC/CI
    
    Casos cubiertos:
    - Longitud mínima/máxima para CI (6-8 dígitos)
    - Formato RUC con guion
    - Caracteres inválidos en diferentes posiciones
    """
    if debe_fallar:
        with pytest.raises(ValidationError):
            validar_ruc_ci(ruc_ci)
    else:
        # No debe lanzar excepción
        try:
            validar_ruc_ci(ruc_ci)
        except ValidationError:
            pytest.fail(f"RUC/CI válido '{ruc_ci}' no debería fallar")
