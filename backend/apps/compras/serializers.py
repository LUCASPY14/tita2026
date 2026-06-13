"""
Serializers para la app compras
"""

from rest_framework import serializers

from .models import (
    Proveedor,
    CuentaCorrienteProveedor,
    Compra,
    DetalleCompra,
    PagoProveedor,
    AplicacionPagoCompra,
    NotaCreditoProveedor,
    DetalleNotaCreditoProveedor,
)


class ProveedorSerializer(serializers.ModelSerializer):
    saldo_cuenta_corriente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Proveedor
        fields = "__all__"
        read_only_fields = ["fecha_registro"]


class CuentaCorrienteProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)

    class Meta:
        model = CuentaCorrienteProveedor
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]


class DetalleCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleCompra
        fields = "__all__"


class CompraSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    detalles = DetalleCompraSerializer(many=True, read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Compra
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class PagoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    medio_pago_nombre = serializers.CharField(source="medio_pago.descripcion", read_only=True)

    class Meta:
        model = PagoProveedor
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class AplicacionPagoCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = AplicacionPagoCompra
        fields = "__all__"


class DetalleNotaCreditoProveedorSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleNotaCreditoProveedor
        fields = "__all__"


class NotaCreditoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    detalles = DetalleNotaCreditoProveedorSerializer(many=True, read_only=True)

    class Meta:
        model = NotaCreditoProveedor
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]
