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
    OrdenCompra,
    DetalleOrdenCompra,
    ProductoProveedor,
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


class DetalleCompraWriteSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = serializers.DecimalField(max_digits=12, decimal_places=0)


class CompraWriteSerializer(serializers.Serializer):
    """Serializer de escritura para crear/editar compras vía CompraService."""
    proveedor = serializers.IntegerField()
    tipo_pago = serializers.ChoiceField(choices=["CONTADO", "CREDITO"])
    nro_factura_proveedor = serializers.CharField(required=False, allow_blank=True, default="")
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")
    items = DetalleCompraWriteSerializer(many=True)


class PagoProveedorSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    medio_pago_nombre = serializers.CharField(source="medio_pago.descripcion", read_only=True)
    compra_id = serializers.SerializerMethodField()

    def get_compra_id(self, obj):
        ap = obj.aplicaciones.first()
        return ap.compra_id if ap else None

    class Meta:
        model = PagoProveedor
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class PagoProveedorWriteSerializer(serializers.Serializer):
    """Serializer de escritura para registrar un pago a proveedor."""
    compra = serializers.IntegerField()
    monto = serializers.DecimalField(max_digits=12, decimal_places=0)
    medio_pago = serializers.IntegerField()
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")


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


# ── Producto-Proveedor ────────────────────────────────────────────────────────

class ProductoProveedorSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)

    class Meta:
        model = ProductoProveedor
        fields = "__all__"
        read_only_fields = ["fecha_ultima_compra"]


# ── Orden de Compra ───────────────────────────────────────────────────────────

class DetalleOrdenCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)

    class Meta:
        model = DetalleOrdenCompra
        fields = "__all__"


class DetalleOrdenCompraWriteSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = serializers.DecimalField(max_digits=12, decimal_places=0)


class OrdenCompraSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    creado_por_nombre = serializers.SerializerMethodField(read_only=True)
    aprobado_por_nombre = serializers.SerializerMethodField(read_only=True)
    detalles = DetalleOrdenCompraSerializer(many=True, read_only=True)
    items = DetalleOrdenCompraWriteSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = OrdenCompra
        fields = "__all__"
        read_only_fields = [
            "estado", "monto_total", "aprobado_por", "fecha_aprobacion",
            "compra_generada", "motivo_rechazo", "creado_por",
            "fecha_creacion", "fecha_actualizacion",
        ]

    @staticmethod
    def _nombre_usuario(usuario) -> str:
        return f"{usuario.nombre} {usuario.apellido}".strip() or usuario.email

    def get_creado_por_nombre(self, obj):
        return self._nombre_usuario(obj.creado_por) if obj.creado_por else None

    def get_aprobado_por_nombre(self, obj):
        return self._nombre_usuario(obj.aprobado_por) if obj.aprobado_por else None

    def create(self, validated_data):
        from decimal import Decimal
        from apps.productos.models import Producto

        items = validated_data.pop("items")
        request = self.context["request"]
        validated_data["creado_por"] = request.user

        monto_total = Decimal("0")
        detalles_data = []
        for item in items:
            producto = Producto.objects.get(pk=item["producto"])
            cantidad = item["cantidad"]
            costo = item["costo_unitario"]
            subtotal = cantidad * costo
            monto_total += subtotal
            detalles_data.append({
                "producto": producto,
                "cantidad": cantidad,
                "costo_unitario": costo,
                "subtotal": subtotal,
            })

        validated_data["monto_total"] = monto_total
        orden = OrdenCompra.objects.create(**validated_data)
        for det in detalles_data:
            DetalleOrdenCompra.objects.create(orden=orden, **det)
        return orden

    def update(self, instance, validated_data):
        from decimal import Decimal
        from apps.productos.models import Producto

        if instance.estado not in (OrdenCompra.Estado.BORRADOR,):
            raise serializers.ValidationError(
                {"error": "Solo se puede editar una OC en estado Borrador."}
            )

        items = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if items is not None:
            instance.detalles.all().delete()
            monto_total = Decimal("0")
            for item in items:
                producto = Producto.objects.get(pk=item["producto"])
                cantidad = item["cantidad"]
                costo = item["costo_unitario"]
                subtotal = cantidad * costo
                monto_total += subtotal
                DetalleOrdenCompra.objects.create(
                    orden=instance,
                    producto=producto,
                    cantidad=cantidad,
                    costo_unitario=costo,
                    subtotal=subtotal,
                )
            instance.monto_total = monto_total

        instance.save()
        return instance
