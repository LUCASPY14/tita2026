"""
Validador de RUC/CI para Paraguay
RUC: Registro Único de Contribuyentes
CI: Cédula de Identidad
"""
from django.core.exceptions import ValidationError
import re


def validate_ruc(value):
    """
    Valida el formato de RUC o CI paraguayo
    
    Formatos válidos:
    - CI: 1-9999999 (números de 1 a 7 dígitos)
    - RUC: XXXXXXX-D (7 dígitos + guión + dígito verificador)
    """
    if not value:
        raise ValidationError('El RUC/CI es requerido')
    
    value = str(value).strip()
    
    # Verificar formato RUC con dígito verificador (XXXXXXX-D)
    ruc_pattern = re.compile(r'^\d{1,8}-\d$')
    # Verificar formato CI simple (solo números)
    ci_pattern = re.compile(r'^\d{1,8}$')
    
    if not (ruc_pattern.match(value) or ci_pattern.match(value)):
        raise ValidationError(
            'Formato inválido. Use: XXXXXXX-D (RUC) o XXXXXXX (CI)'
        )
    
    return value
