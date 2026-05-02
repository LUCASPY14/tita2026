from rest_framework import serializers
from .models import Proveedores, Compras, DetallesCompra, PagosProveedores, NotasCreditoProveedor


class ProveedoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedores
        fields = "__all__"


class DetallesCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="id_producto.nombre", read_only=True)

    class Meta:
        model = DetallesCompra
        fields = "__all__"


class ComprasSerializer(serializers.ModelSerializer):
    detalles = DetallesCompraSerializer(many=True, read_only=True, source="detallescompra_set")
    proveedor_nombre = serializers.CharField(source="id_proveedor.razon_social", read_only=True)
    medio_pago_descripcion = serializers.CharField(source="id_medio_pago.descripcion", read_only=True, allow_null=True)
    # Hacer estos campos opcionales para creación (se calculan en perform_create)
    monto_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    estado_pago = serializers.CharField(max_length=10, required=False, default="Pendiente")
    saldo_pendiente = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = Compras
        fields = "__all__"


class PagosProveedoresSerializer(serializers.ModelSerializer):
    medio_pago_descripcion = serializers.CharField(source="id_medio_pago.descripcion", read_only=True)

    class Meta:
        model = PagosProveedores
        fields = "__all__"


class NotasCreditoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="id_proveedor.razon_social", read_only=True)

    class Meta:
        model = NotasCreditoProveedor
        fields = "__all__"
