"""
Serializers para la app ventas
"""

from decimal import Decimal
from rest_framework import serializers

from .models import (
    Venta,
    DetalleVenta,
    PagoVenta,
    AplicacionPago,
    NotaCredito,
    DetalleNotaCredito,
    CondicionVenta,
)


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = "__all__"


class VentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    saldo_pendiente = serializers.SerializerMethodField()

    def get_saldo_pendiente(self, obj):
        total_pagado = getattr(obj, "_total_pagado", None)
        if total_pagado is None:
            total_pagado = obj.total_pagado
        return obj.monto_total - total_pagado

    class Meta:
        model = Venta
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]

    def validate(self, attrs):
        # monto_total debe ser positivo
        monto_total = attrs.get("monto_total")
        if monto_total is not None and monto_total <= Decimal("0"):
            raise serializers.ValidationError({"monto_total": "El monto total debe ser mayor a cero."})

        # No se puede crear una venta anulada directamente
        if attrs.get("estado") == "ANULADA" and self.instance is None:
            raise serializers.ValidationError({"estado": "No se puede crear una venta en estado ANULADA."})

        # El cliente debe estar activo
        cliente = attrs.get("cliente")
        if cliente and not getattr(cliente, "activo", True):
            raise serializers.ValidationError({"cliente": "El cliente está inactivo y no puede realizar compras."})

        return attrs


class PagoVentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    medio_pago_nombre = serializers.CharField(source="medio_pago.descripcion", read_only=True)
    total_cobrado = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = PagoVenta
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class AplicacionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AplicacionPago
        fields = "__all__"


class DetalleNotaCreditoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleNotaCredito
        fields = "__all__"


class NotaCreditoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    detalles = DetalleNotaCreditoSerializer(many=True, read_only=True)

    class Meta:
        model = NotaCredito
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class CondicionVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicionVenta
        fields = "__all__"