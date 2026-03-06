from rest_framework import serializers
from .models import Clientes, Hijos


# Create your serializers here.
class ClientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clientes
        fields = "__all__"


class HijosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hijos
        fields = "__all__"
