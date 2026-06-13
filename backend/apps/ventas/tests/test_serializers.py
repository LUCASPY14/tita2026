"""
Tests para VentaSerializer — cubre los métodos SerializerMethodField y validate().
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from rest_framework.exceptions import ValidationError as DRFValidationError


def _serializer():
    from apps.ventas.serializers import VentaSerializer
    return VentaSerializer()


class TestVentaSerializerMethodFields:

    def test_get_hijo_nombre_sin_hijo_retorna_none(self):
        """obj.hijo = None → get_hijo_nombre retorna None (línea 39)."""
        obj = MagicMock()
        obj.hijo = None
        assert _serializer().get_hijo_nombre(obj) is None

    def test_get_hijo_nombre_con_hijo(self):
        hijo = MagicMock()
        hijo.nombre = "Ana"
        hijo.apellido = "García"
        obj = MagicMock()
        obj.hijo = hijo
        assert _serializer().get_hijo_nombre(obj) == "Ana García"

    def test_get_hijo_grado_sin_hijo_retorna_none(self):
        """obj.hijo = None → get_hijo_grado retorna None (línea 44)."""
        obj = MagicMock()
        obj.hijo = None
        assert _serializer().get_hijo_grado(obj) is None

    def test_get_hijo_grado_con_hijo_sin_grado_retorna_none(self):
        hijo = MagicMock()
        hijo.grado = None
        obj = MagicMock()
        obj.hijo = hijo
        assert _serializer().get_hijo_grado(obj) is None

    def test_get_hijo_grado_con_grado(self):
        hijo = MagicMock()
        hijo.grado = "3er Grado"
        obj = MagicMock()
        obj.hijo = hijo
        assert _serializer().get_hijo_grado(obj) == "3er Grado"


class TestVentaSerializerValidate:

    def test_monto_total_cero_falla(self):
        """monto_total <= 0 → ValidationError (línea 64)."""
        ser = _serializer()
        with pytest.raises(DRFValidationError):
            ser.validate({"monto_total": Decimal("0")})

    def test_monto_total_negativo_falla(self):
        ser = _serializer()
        with pytest.raises(DRFValidationError):
            ser.validate({"monto_total": Decimal("-100")})

    def test_monto_total_positivo_ok(self):
        ser = _serializer()
        attrs = {"monto_total": Decimal("1000")}
        result = ser.validate(attrs)
        assert result == attrs

    def test_estado_anulada_en_create_falla(self):
        """estado=ANULADA en instancia nueva → ValidationError (línea 68)."""
        ser = _serializer()
        with pytest.raises(DRFValidationError):
            ser.validate({"estado": "ANULADA"})

    def test_cliente_inactivo_falla(self):
        """cliente.activo = False → ValidationError (línea 73)."""
        ser = _serializer()
        cliente = MagicMock()
        cliente.activo = False
        with pytest.raises(DRFValidationError):
            ser.validate({"cliente": cliente})

    def test_cliente_activo_ok(self):
        ser = _serializer()
        cliente = MagicMock()
        cliente.activo = True
        attrs = {"cliente": cliente}
        result = ser.validate(attrs)
        assert result == attrs
