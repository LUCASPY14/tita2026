from rest_framework import serializers
from django.utils import timezone
from .models import (
    Impuestos, DatosEmpresa, Timbrados, PuntosExpedicion, DocumentosTributarios,
    Cajas, CierresCaja, MovimientosCaja,
)


class ImpuestosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impuestos
        fields = "__all__"


class DatosEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosEmpresa
        fields = "__all__"


class PuntosExpedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntosExpedicion
        fields = "__all__"


class TimbradoSerializer(serializers.ModelSerializer):
    punto_detalle = PuntosExpedicionSerializer(source="id_punto", read_only=True)
    nro_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Timbrados
        fields = "__all__"

    def get_nro_disponibles(self, obj):
        from .models import DocumentosTributarios
        usados = DocumentosTributarios.objects.filter(nro_timbrado=obj).count()
        return max(0, obj.nro_final - obj.nro_inicial + 1 - usados)


class DocumentosTributariosSerializer(serializers.ModelSerializer):
    timbrado_detalle = TimbradoSerializer(source="nro_timbrado", read_only=True)
    cliente_nombre = serializers.SerializerMethodField()
    cliente_ruc = serializers.SerializerMethodField()
    condicion_venta_display = serializers.CharField(
        source='get_condicion_venta_display', read_only=True
    )

    class Meta:
        model = DocumentosTributarios
        fields = "__all__"

    def get_cliente_nombre(self, obj):
        if not obj.id_cliente:
            return None
        c = obj.id_cliente
        return c.razon_social or f"{c.nombres} {c.apellidos}"

    def get_cliente_ruc(self, obj):
        return obj.id_cliente.ruc_ci if obj.id_cliente else None


# ─── Facturación física ───────────────────────────────────────────────────────

class EmitirFacturaSerializer(serializers.Serializer):
    id_cliente = serializers.IntegerField()
    nro_preimpreso = serializers.IntegerField(min_value=1)
    ventas_ids = serializers.ListField(
        child=serializers.IntegerField(), default=list, allow_empty=True
    )
    almuerzos_ids = serializers.ListField(
        child=serializers.IntegerField(), default=list, allow_empty=True
    )
    condicion_venta = serializers.ChoiceField(
        choices=['CONTADO', 'CREDITO'],
        default='CONTADO',
    )
    plazo_dias = serializers.IntegerField(
        min_value=1,
        max_value=3650,
        required=False,
        allow_null=True,
        default=None,
    )

    def validate(self, data):
        if not data.get("ventas_ids") and not data.get("almuerzos_ids"):
            raise serializers.ValidationError(
                "Debe seleccionar al menos una venta o cuenta de almuerzo."
            )
        if data.get('condicion_venta') == 'CREDITO' and not data.get('plazo_dias'):
            raise serializers.ValidationError(
                "Para condición Crédito debe indicar el plazo en días."
            )
        if data.get('condicion_venta') == 'CONTADO':
            data['plazo_dias'] = None
        return data


# ─── Cajas ────────────────────────────────────────────────────────────────────

class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cajas
        fields = "__all__"


class MovimientosCajaSerializer(serializers.ModelSerializer):
    medio_pago_descripcion = serializers.CharField(
        source="id_medio_pago.descripcion", read_only=True
    )
    venta_nro = serializers.CharField(
        source="id_venta.nro_factura_venta", read_only=True, default=None
    )

    class Meta:
        model = MovimientosCaja
        fields = "__all__"


class CierresCajaSerializer(serializers.ModelSerializer):
    caja_nombre = serializers.CharField(source="id_caja.nombre_caja", read_only=True)
    empleado_nombre = serializers.CharField(source="id_empleado.nombre", read_only=True)
    movimientos = MovimientosCajaSerializer(many=True, read_only=True, source="movimientoscaja_set")
    total_ingresos = serializers.SerializerMethodField()
    total_egresos = serializers.SerializerMethodField()
    total_ventas = serializers.SerializerMethodField()

    class Meta:
        model = CierresCaja
        fields = "__all__"

    def get_total_ingresos(self, obj):
        from django.db.models import Sum
        total = obj.movimientoscaja_set.filter(
            tipo_movimiento__in=["Ingreso", "VentaEfectivo"]
        ).aggregate(t=Sum("monto"))["t"]
        return total or 0

    def get_total_egresos(self, obj):
        from django.db.models import Sum
        total = obj.movimientoscaja_set.filter(
            tipo_movimiento="Egreso"
        ).aggregate(t=Sum("monto"))["t"]
        return total or 0

    def get_total_ventas(self, obj):
        from django.db.models import Sum
        total = obj.movimientoscaja_set.filter(
            tipo_movimiento="Venta"
        ).aggregate(t=Sum("monto"))["t"]
        return total or 0


class AbrirCajaSerializer(serializers.Serializer):
    id_caja = serializers.IntegerField()
    id_empleado = serializers.IntegerField()
    monto_inicial = serializers.DecimalField(max_digits=10, decimal_places=2)


class CerrarCajaSerializer(serializers.Serializer):
    monto_contado_fisico = serializers.DecimalField(max_digits=10, decimal_places=2)
    observaciones = serializers.CharField(required=False, allow_blank=True)
