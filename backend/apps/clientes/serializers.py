from rest_framework import serializers

from .models import Ciudad, Clientes, Grados, Hijos, Pais, RestriccionesHijos, TiposCliente


# Create your serializers here.
class TiposClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TiposCliente
        fields = "__all__"


class GradosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grados
        fields = "__all__"


class ClientesSerializer(serializers.ModelSerializer):
    id_lista = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.productos.models", fromlist=["ListasPrecios"]).ListasPrecios.objects.all(),
        required=False,
    )

    class Meta:
        model = Clientes
        fields = "__all__"

    def create(self, validated_data):
        if "id_lista" not in validated_data:
            from apps.productos.models import ListasPrecios

            lista, _ = ListasPrecios.objects.get_or_create(
                nombre_lista="General",
                defaults={"estado": True, "moneda": "PYG"},
            )
            validated_data["id_lista"] = lista
        return super().create(validated_data)


class HijosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hijos
        fields = "__all__"


class RestriccionesHijosSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestriccionesHijos
        fields = "__all__"
        read_only_fields = ["fecha_registro", "fecha_ultima_actualizacion"]


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = "__all__"


class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = "__all__"
