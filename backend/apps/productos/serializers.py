from rest_framework import serializers

from .models import Categorias, ListasPrecios, PreciosPorLista, Productos, UnidadesMedida


# Create your serializers here.
class CategoriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = "__all__"


class UnidadesMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadesMedida
        fields = "__all__"


class ListasPreciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListasPrecios
        fields = "__all__"


class PreciosPorListaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreciosPorLista
        fields = "__all__"


class ProductosSerializer(serializers.ModelSerializer):
    stock_actual = serializers.SerializerMethodField()
    requiere_reposicion = serializers.SerializerMethodField()
    precio = serializers.SerializerMethodField()
    categoria_nombre = serializers.SerializerMethodField()
    impuesto_nombre = serializers.SerializerMethodField()
    id_impuesto = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.contabilidad.models", fromlist=["Impuestos"]).Impuestos.objects.all(),
        required=False,
    )

    class Meta:
        model = Productos
        fields = "__all__"

    def create(self, validated_data):
        if "id_impuesto" not in validated_data:
            from apps.contabilidad.models import Impuestos

            impuesto, _ = Impuestos.objects.get_or_create(
                nombre_impuesto="IVA 10%",
                defaults={"porcentaje": 10, "estado": True},
            )
            validated_data["id_impuesto"] = impuesto
        return super().create(validated_data)

    def get_stock_actual(self, obj):
        try:
            return float(obj.stock.cantidad)
        except Exception:
            return None

    def get_requiere_reposicion(self, obj):
        try:
            return obj.stock.cantidad <= obj.stock_minimo
        except Exception:
            return False

    def get_categoria_nombre(self, obj):
        try:
            return obj.id_categoria.nombre if obj.id_categoria else None
        except Exception:
            return None

    def get_impuesto_nombre(self, obj):
        try:
            return obj.id_impuesto.nombre_impuesto if obj.id_impuesto else None
        except Exception:
            return None

    def get_precio(self, obj):
        try:
            precio = obj.precios.order_by("id_precio").first()
            return float(precio.precio_unitario) if precio else None
        except Exception:
            return None
