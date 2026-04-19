"""
Tests de cobertura completa para api_integrations.validators
Objetivo: Alcanzar 100% de cobertura en casos edge (excluyendo pragma: no cover)

Cobertura de líneas:
- L438: URL vacía después de strip
- L786: Payload webhook vacío después de strip
- L1031: Valor no es datetime en created_at_webhook
- L1034: Fecha webhook más de 1 hora en el futuro
"""

import pytest
from datetime import datetime, timezone, timedelta
from django.core.exceptions import ValidationError
from apps.api_integrations.validators import (
    validar_url_log,
    validar_payload_webhook,
    validar_created_at_webhook
)


@pytest.mark.parametrize("url_invalida", [
    "   ",  # L438: Solo espacios
    "     ",  # L438: Múltiples espacios
    "\t\t",  # L438: Solo tabs
    "  \n  ",  # L438: Espacios y newline
])
def test_validar_url_log_vacia_despues_strip(url_invalida):
    """
    Test L438: URL que queda vacía después de strip
    
    El validador hace strip() de la URL antes de validar.
    Si la URL solo contiene espacios/tabs, queda vacía y debe fallar.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_url_log(url_invalida)
    
    # Verificar mensaje de error apropiado
    assert "vacía" in str(exc_info.value).lower() or "requerida" in str(exc_info.value).lower()


@pytest.mark.parametrize("payload_invalido", [
    "   ",  # L786: Solo espacios
    "     ",  # L786: Múltiples espacios
    "\t",  # L786: Solo tab
    "  \n  ",  # L786: Espacios con newline
    "\r\n",  # L786: Return + newline
])
def test_validar_payload_webhook_vacio_despues_strip(payload_invalido):
    """
    Test L786: Payload que queda vacío después de strip
    
    Similar a la URL, el payload hace strip() antes de validar.
    Si solo contiene whitespace, debe ser rechazado.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_payload_webhook(payload_invalido)
    
    # Verificar mensaje de error
    assert "vacío" in str(exc_info.value).lower() or "requerido" in str(exc_info.value).lower()


@pytest.mark.parametrize("valor_invalido", [
    "2026-04-19",  # L1031: String en lugar de datetime
    "19/04/2026",  # L1031: String con formato diferente
    123456789,  # L1031: Timestamp integer
    123.456,  # L1031: Float
    None,  # L1031: None (caso especial)
    {"fecha": "2026-04-19"},  # L1031: Dict
    ["2026-04-19"],  # L1031: List
])
def test_validar_created_at_webhook_no_es_datetime(valor_invalido):
    """
    Test L1031: Valor no es objeto datetime
    
    El validador requiere específicamente un objeto datetime de Python.
    Cualquier otro tipo (string, int, dict, etc.) debe ser rechazado.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_created_at_webhook(valor_invalido)
    
    # Verificar mensaje de error
    error_msg = str(exc_info.value).lower()
    assert "datetime" in error_msg or "requerida" in error_msg or "fecha" in error_msg


@pytest.mark.parametrize("horas_futuro", [
    1.5,  # L1034: 1.5 horas futuro
    2,  # L1034: 2 horas futuro
    5,  # L1034: 5 horas futuro
    24,  # L1034: 1 día futuro
])
def test_validar_created_at_webhook_fecha_futura_excesiva(horas_futuro):
    """
    Test L1034: Fecha webhook más de 1 hora en el futuro
    
    El sistema permite hasta 1 hora de tolerancia para desfase de relojes.
    Cualquier fecha más de 1 hora en el futuro debe ser rechazada.
    """
    # Arrange: Crear fecha futura
    fecha_futura = datetime.now(timezone.utc) + timedelta(hours=horas_futuro)
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_created_at_webhook(fecha_futura)
    
    # Verificar mensaje de error
    assert "futuro" in str(exc_info.value).lower()


class TestValidadoresApiIntegrationsEdgeCases:
    """Tests adicionales para validadores de API integrations"""
    
    def test_url_log_valida_pasa(self):
        """Test: URL válida debe pasar sin errores"""
        # Arrange
        url_valida = "https://api.example.com/endpoint"
        
        # Act & Assert
        try:
            validar_url_log(url_valida)
        except ValidationError:
            pytest.fail("URL válida no debería fallar")
    
    def test_url_log_con_espacios_laterales(self):
        """Test: URL con espacios laterales se acepta (se hace strip)"""
        # Arrange
        url_con_espacios = "  https://api.example.com/test  "
        
        # Act & Assert
        try:
            validar_url_log(url_con_espacios)
        except ValidationError:
            pytest.fail("URL con espacios laterales debería pasar (se hace strip)")
    
    def test_payload_webhook_valido_json(self):
        """Test: Payload válido debe pasar"""
        # Arrange
        payload_valido = '{"event": "payment.completed", "data": {"id": 123}}'
        
        # Act & Assert
        try:
            validar_payload_webhook(payload_valido)
        except ValidationError:
            pytest.fail("Payload válido no debería fallar")
    
    def test_payload_webhook_texto_plano(self):
        """Test: Payload de texto plano también es válido"""
        # Arrange
        payload_texto = "Este es un payload de texto plano"
        
        # Act & Assert
        try:
            validar_payload_webhook(payload_texto)
        except ValidationError:
            pytest.fail("Payload de texto plano debería ser válido")
    
    def test_created_at_webhook_fecha_actual(self):
        """Test: Fecha actual debe pasar"""
        # Arrange
        ahora = datetime.now(timezone.utc)
        
        # Act & Assert
        try:
            validar_created_at_webhook(ahora)
        except ValidationError:
            pytest.fail("Fecha actual no debería fallar")
    
    def test_created_at_webhook_fecha_pasada(self):
        """Test: Fecha pasada debe pasar"""
        # Arrange
        fecha_pasada = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Act & Assert
        try:
            validar_created_at_webhook(fecha_pasada)
        except ValidationError:
            pytest.fail("Fecha pasada no debería fallar")
    
    def test_created_at_webhook_exactamente_1_hora_futuro(self):
        """Test: Exactamente 1 hora en el futuro debe pasar (tolerancia)"""
        # Arrange: Justo 1 hora (dentro de tolerancia)
        fecha_limite = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Act & Assert
        try:
            validar_created_at_webhook(fecha_limite)
        except ValidationError:
            pytest.fail("1 hora exacta debería pasar (tolerancia)")
    
    def test_created_at_webhook_59_minutos_futuro(self):
        """Test: 59 minutos en el futuro debe pasar"""
        # Arrange
        fecha_dentro_tolerancia = datetime.now(timezone.utc) + timedelta(minutes=59)
        
        # Act & Assert
        try:
            validar_created_at_webhook(fecha_dentro_tolerancia)
        except ValidationError:
            pytest.fail("Menos de 1 hora futuro debería pasar")


@pytest.mark.parametrize("caso,valor,debe_pasar", [
    ("URL válida", "https://example.com", True),
    ("URL con query", "https://api.com/v1?param=value", True),
    ("URL solo espacios", "   ", False),
    ("Payload JSON", '{"key": "value"}', True),
    ("Payload vacío tras strip", "   ", False),
    ("DateTime ahora", datetime.now(timezone.utc), True),
    ("DateTime string", "2026-04-19", False),
    ("DateTime 2h futuro", datetime.now(timezone.utc) + timedelta(hours=2), False),
], ids=lambda x: x if isinstance(x, str) else "")
def test_validadores_casos_parametricos(caso, valor, debe_pasar):
    """
    Tests paramétricos para múltiples casos de validadores
    
    Cubre casos válidos e inválidos en una sola batería de tests.
    """
    # Determinar qué validador usar según el caso
    if "URL" in caso:
        validador = validar_url_log
    elif "Payload" in caso:
        validador = validar_payload_webhook
    elif "DateTime" in caso:
        validador = validar_created_at_webhook
    else:
        return  # Skip caso desconocido
    
    # Act & Assert
    if debe_pasar:
        try:
            validador(valor)
        except ValidationError:
            pytest.fail(f"Caso '{caso}' debería pasar")
    else:
        with pytest.raises(ValidationError):
            validador(valor)
