from rest_framework import serializers
from .models import StockUnico, MovimientosStock, AjustesInventario


class StockUnicoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    producto_categoria = serializers.CharField(source='id_producto.id_categoria.nombre', read_only=True)
    
    class Meta:
        model = StockUnico
        fields = '__all__'


class MovimientosStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    empleado_nombre = serializers.CharField(source='id_empleado_autoriza.nombre', read_only=True)
    
    class Meta:
        model = MovimientosStock
        fields = '__all__'


class AjustesInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AjustesInventario
        fields = '__all__'
