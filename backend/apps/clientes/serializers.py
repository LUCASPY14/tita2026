from rest_framework import serializers
from .models import Clientes, Hijos, TiposCliente


# Create your serializers here.
class TiposClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TiposCliente
        fields = "__all__"


class ClientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clientes
        fields = "__all__"


class HijosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hijos
        fields = "__all__"
