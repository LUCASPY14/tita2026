"""
Serializers para la app productos
"""

from rest_framework import serializers

from .models import (
    Categoria,
    Producto,
    UnidadMedida,
    ListaPrecio,
    PrecioPorLista,
    HistoricoPrecio,
    Impuesto,
    ProductoImpuesto,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    precio_actual = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Producto
        fields = "__all__"


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = "__all__"


class ListaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListaPrecio
        fields = "__all__"


class PrecioPorListaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    lista_nombre = serializers.CharField(source="lista.nombre", read_only=True)

    class Meta:
        model = PrecioPorLista
        fields = "__all__"
        read_only_fields = ["fecha_vigencia"]


class HistoricoPrecioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    variacion_porcentual = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = HistoricoPrecio
        fields = "__all__"
        read_only_fields = ["fecha_cambio"]


class ImpuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impuesto
        fields = "__all__"


class ProductoImpuestoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    impuesto_nombre = serializers.CharField(source="impuesto.nombre", read_only=True)

    class Meta:
        model = ProductoImpuesto
        fields = "__all__"
        read_only_fields = ["fecha_asignacion"]