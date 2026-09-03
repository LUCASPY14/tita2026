"""
Serializers para la app contabilidad
"""

from rest_framework import serializers

from .models import (
    Caja,
    CierreCaja,
    MovimientoCaja,
    Factura,
    DatosEmpresa,
)


class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = "__all__"


class CierreCajaSerializer(serializers.ModelSerializer):
    caja_nombre = serializers.CharField(source="caja.nombre", read_only=True)
    caja_activo = serializers.BooleanField(source="caja.activo", read_only=True)
    empleado_nombre = serializers.CharField(source="empleado.nombre_completo", read_only=True)

    class Meta:
        model = CierreCaja
        fields = "__all__"
        read_only_fields = [
            "empleado",
            "fecha_apertura",
            "fecha_creacion",
            "diferencia_efectivo",
            "monto_contado_fisico",
            "fecha_cierre",
            "estado",
        ]


class MovimientoCajaSerializer(serializers.ModelSerializer):
    medio_pago_nombre = serializers.SerializerMethodField()

    def get_medio_pago_nombre(self, obj):
        return obj.medio_pago.descripcion if obj.medio_pago_id else None

    class Meta:
        model = MovimientoCaja
        fields = "__all__"


class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)

    class Meta:
        model = Factura
        fields = "__all__"
        read_only_fields = [
            "fecha_creacion",
            "iva_10",
            "iva_5",
            "monto_exenta",
            "monto_total",
        ]


class DatosEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosEmpresa
        fields = "__all__"


class CerrarCajaSerializer(serializers.Serializer):
    monto_contado_fisico = serializers.IntegerField(min_value=0)


class EmitirFacturaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["CARGA_SALDO", "PAGO_ALMUERZO", "VENTA", "PAGO_CREDITO"])
    origen_id = serializers.IntegerField(min_value=1)
    nro_factura = serializers.CharField(max_length=20)


class EmitirLoteSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["CARGA_SALDO", "PAGO_ALMUERZO", "VENTA", "PAGO_CREDITO"])
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1)
    nro_factura = serializers.CharField(max_length=20)


class PendienteItemSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    id = serializers.IntegerField()
    cliente_id = serializers.IntegerField(allow_null=True)
    cliente_nombre = serializers.CharField()
    modalidad_facturacion = serializers.CharField()
    descripcion = serializers.CharField()
    monto = serializers.IntegerField()
    fecha = serializers.DateTimeField()
