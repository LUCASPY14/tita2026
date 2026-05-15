"""
Serializers para la app inventario
"""

from rest_framework import serializers

from .models import (
    Stock,
    MovimientoStock,
    AjusteInventario,
    DetalleAjuste,
    CostoHistorico,
    AlertaStock,
    LoteProducto,
    AlertaVencimiento,
)


class StockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    costo_promedio = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    valor_inventario = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    requiere_reposicion = serializers.BooleanField(read_only=True)
    dias_stock_disponible = serializers.IntegerField(read_only=True)

    class Meta:
        model = Stock
        fields = "__all__"
        read_only_fields = ["fecha_actualizacion"]


class MovimientoStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = MovimientoStock
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]


class DetalleAjusteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleAjuste
        fields = "__all__"


class AjusteInventarioSerializer(serializers.ModelSerializer):
    detalles = DetalleAjusteSerializer(many=True, read_only=True)

    class Meta:
        model = AjusteInventario
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class CostoHistoricoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    costo_total = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = CostoHistorico
        fields = "__all__"


class AlertaStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = AlertaStock
        fields = "__all__"
        read_only_fields = ["fecha_generada"]


class AlertaVencimientoSerializer(serializers.ModelSerializer):
    lote_numero = serializers.CharField(source="lote.numero_lote", read_only=True)

    class Meta:
        model = AlertaVencimiento
        fields = "__all__"
        read_only_fields = ["fecha_generada"]


class LoteProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    dias_hasta_vencimiento = serializers.IntegerField(read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)

    class Meta:
        model = LoteProducto
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]