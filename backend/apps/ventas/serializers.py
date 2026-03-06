from rest_framework import serializers
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones


class DetallesVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="id_producto.descripcion", read_only=True)

    class Meta:
        model = DetallesVenta
        fields = "__all__"


class PagosVentaSerializer(serializers.ModelSerializer):
    medio_pago_descripcion = serializers.CharField(
        source="id_medio_pago.descripcion", read_only=True
    )

    class Meta:
        model = PagosVenta
        fields = "__all__"


class VentasSerializer(serializers.ModelSerializer):
    detalles = DetallesVentaSerializer(many=True, read_only=True, source="detallesventa_set")
    pagos = PagosVentaSerializer(many=True, read_only=True, source="pagosventa_set")
    cliente_nombre = serializers.CharField(source="id_cliente.nombres", read_only=True)
    cliente_apellido = serializers.CharField(source="id_cliente.apellidos", read_only=True)
    cajero_nombre = serializers.CharField(source="id_empleado_cajero.nombre", read_only=True)

    class Meta:
        model = Ventas
        fields = "__all__"


class NotasCreditoClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="id_cliente.nombres", read_only=True)

    class Meta:
        model = NotasCreditoCliente
        fields = "__all__"


class PromocionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promociones
        fields = "__all__"
