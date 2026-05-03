from rest_framework import serializers

from .models import CondicionVenta, DetallesVenta, NotasCreditoCliente, PagosVenta, Promociones, Ventas


class DetallesVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="id_producto.descripcion", read_only=True)

    class Meta:
        model = DetallesVenta
        fields = "__all__"


class PagosVentaSerializer(serializers.ModelSerializer):
    medio_pago_descripcion = serializers.CharField(source="id_medio_pago.descripcion", read_only=True)

    class Meta:
        model = PagosVenta
        fields = "__all__"


class PagoDataSerializer(serializers.Serializer):
    """
    Serializer para datos de pago en el POST de venta (pago mixto).
    No crea el modelo directamente, solo valida los datos de entrada.
    """

    id_medio_pago = serializers.IntegerField(required=True)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    ref_pago_pos = serializers.CharField(max_length=100, required=False, allow_blank=True)
    ref_pg_transf = serializers.CharField(max_length=100, required=False, allow_blank=True)
    banco_emisor = serializers.CharField(max_length=100, required=False, allow_blank=True)


class VentasSerializer(serializers.ModelSerializer):
    detalles = DetallesVentaSerializer(many=True, read_only=True, source="detallesventa_set")
    pagos = PagosVentaSerializer(many=True, read_only=True, source="pagosventa_set")
    cliente_nombre = serializers.CharField(source="id_cliente.nombres", read_only=True)
    cliente_apellido = serializers.CharField(source="id_cliente.apellidos", read_only=True)
    cajero_nombre = serializers.CharField(source="id_empleado_cajero.nombre", read_only=True)

    # Número de documento tributario (factura) auto-generado por signal
    nro_documento_tributario = serializers.SerializerMethodField(read_only=True)

    # Campo write-only para recibir array de pagos en POST
    pagos_data = PagoDataSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Ventas
        fields = "__all__"

    def get_nro_documento_tributario(self, obj):
        """Retorna el nro_secuencial del DocumentoTributario asociado a esta venta."""
        try:
            from apps.contabilidad.models import DocumentosTributarios

            doc = (
                DocumentosTributarios.objects.filter(nro_preimpreso_interno=str(obj.pk))
                .order_by("-id_documento")
                .first()
            )
            return doc.nro_secuencial if doc else None
        except Exception:
            return None

    def create(self, validated_data):
        """
        Sobrescribir create para remover pagos_data de validated_data.
        Los pagos se manejan en perform_create() del ViewSet.
        """
        # Remover pagos_data si existe (no es campo del modelo)
        validated_data.pop("pagos_data", None)
        return super().create(validated_data)


class NotasCreditoClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="id_cliente.nombres", read_only=True)

    class Meta:
        model = NotasCreditoCliente
        fields = "__all__"


class CondicionVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicionVenta
        fields = "__all__"


class PromocionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promociones
        fields = "__all__"
