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
    class Meta:
        model = Productos
        fields = '__all__'
