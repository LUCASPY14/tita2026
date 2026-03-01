from rest_framework import serializers
from .models import Proveedores, Compras, DetallesCompra, PagosProveedores, NotasCreditoProveedor


class ProveedoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedores
        fields = '__all__'


class DetallesCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    
    class Meta:
        model = DetallesCompra
        fields = '__all__'


class ComprasSerializer(serializers.ModelSerializer):
    detalles = DetallesCompraSerializer(many=True, read_only=True, source='detallescompra_set')
    proveedor_nombre = serializers.CharField(source='id_proveedor.razon_social', read_only=True)
    
    class Meta:
        model = Compras
        fields = '__all__'


class PagosProveedoresSerializer(serializers.ModelSerializer):
    medio_pago_descripcion = serializers.CharField(source='id_medio_pago.descripcion', read_only=True)
    
    class Meta:
        model = PagosProveedores
        fields = '__all__'


class NotasCreditoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='id_proveedor.razon_social', read_only=True)
    
    class Meta:
        model = NotasCreditoProveedor
        fields = '__all__'
