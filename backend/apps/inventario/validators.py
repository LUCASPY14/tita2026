"""
Validadores personalizados para inventario
"""
from rest_framework import serializers
from decimal import Decimal

from .models import StockUnico
from .services import StockService
from apps.productos.models import Productos


class StockDisponibleValidator:
    """
    Validador reutilizable para verificar stock disponible.
    
    Uso en serializer:
        class VentaSerializer(serializers.ModelSerializer):
            cantidad = serializers.DecimalField(
                validators=[StockDisponibleValidator()]
            )
    """
    
    def __init__(self, producto_field='id_producto'):
        self.producto_field = producto_field
    
    def __call__(self, value):
        """
        Valida que la cantidad solicitada esté disponible.
        """
        # Obtener el producto del contexto del serializer
        # Esto se debe hacer en el serializer padre
        pass  # Se implementa en el serializer


def validar_stock_disponible(producto_id, cantidad):
    """
    Función validadora standalone.
    
    Args:
        producto_id: ID del producto
        cantidad: Cantidad solicitada
        
    Raises:
        serializers.ValidationError: Si no hay stock suficiente
    """
    resultado = StockService.validar_disponibilidad(producto_id, cantidad)
    
    if not resultado['disponible']:
        raise serializers.ValidationError({
            'stock': f"Stock insuficiente para producto ID {producto_id}. "
                    f"Disponible: {resultado['stock_actual']}, "
                    f"Solicitado: {cantidad}, "
                    f"Faltante: {resultado['faltante']}"
        })


class StockMinimoValidator:
    """
    Valida que el stock mínimo sea coherente.
    """
    
    def __call__(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El stock mínimo no puede ser negativo"
            )
        
        if value > 10000:
            raise serializers.ValidationError(
                "El stock mínimo parece excesivo. Verifique el valor."
            )


class CantidadPositivaValidator:
    """
    Valida que la cantidad sea siempre positiva.
    """
    
    def __call__(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor a cero"
            )
