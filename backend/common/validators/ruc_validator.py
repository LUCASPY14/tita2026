"""
Validador de RUC para Paraguay
"""
from django.core.exceptions import ValidationError
import re


def validate_ruc(value):
    """
    Valida que el RUC tenga el formato correcto
    Formato: 12345678-9 (8 dígitos, guión, 1 dígito verificador)
    """
    if not value:
        raise ValidationError('El RUC no puede estar vacío')
    
    # Remover espacios
    ruc = value.strip()
    
    # Verificar formato
    pattern = r'^\d{6,8}-\d{1}$'
    if not re.match(pattern, ruc):
        raise ValidationError(
            'El RUC debe tener el formato: 12345678-9'
        )
    
    return value


def validate_ci(value):
    """
    Valida que la CI tenga el formato correcto
    """
    if not value:
        raise ValidationError('La CI no puede estar vacía')
    
    # Remover espacios y puntos
    ci = value.strip().replace('.', '')
    
    # Verificar que sea numérico
    if not ci.isdigit():
        raise ValidationError('La CI debe contener solo números')
    
    # Verificar longitud (generalmente entre 6 y 8 dígitos)
    if len(ci) < 6 or len(ci) > 8:
        raise ValidationError('La CI debe tener entre 6 y 8 dígitos')
    
    return value
