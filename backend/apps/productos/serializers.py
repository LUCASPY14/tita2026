from rest_framework import serializers
from .models import Productos, Categorias, UnidadesMedida, ListasPrecios, PreciosPorLista

# Create your serializers here.
class CategoriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'

class UnidadesMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadesMedida
        fields = '__all__'

class ListasPreciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListasPrecios
        fields = '__all__'

class PreciosPorListaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreciosPorLista
        fields = '__all__'

class ProductosSerializer(serializers.ModelSerializer):
    stock_actual = serializers.SerializerMethodField()
    requiere_reposicion = serializers.SerializerMethodField()

    class Meta:
        model = Productos
        fields = '__all__'

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
