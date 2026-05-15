"""
Serializers para la app contabilidad
"""

from rest_framework import serializers

from .models import (
    Caja,
    CierreCaja,
    MovimientoCaja,
    ConciliacionPago,
    Factura,
    DatosEmpresa,
)


class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = "__all__"


class CierreCajaSerializer(serializers.ModelSerializer):
    caja_nombre = serializers.CharField(source="caja.nombre", read_only=True)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)

    class Meta:
        model = CierreCaja
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class MovimientoCajaSerializer(serializers.ModelSerializer):
    medio_pago_nombre = serializers.CharField(source="medio_pago.descripcion", read_only=True)

    class Meta:
        model = MovimientoCaja
        fields = "__all__"


class ConciliacionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConciliacionPago
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "fecha_actualizacion"]


class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)

    class Meta:
        model = Factura
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class DatosEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosEmpresa
        fields = "__all__"