from rest_framework import serializers
from .models import Impuestos, DatosEmpresa, Timbrados, PuntosExpedicion, DocumentosTributarios


class ImpuestosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impuestos
        fields = "__all__"


class DatosEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosEmpresa
        fields = "__all__"


class PuntosExpedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntosExpedicion
        fields = "__all__"


class TimbradoSerializer(serializers.ModelSerializer):
    punto_detalle = PuntosExpedicionSerializer(source="id_punto", read_only=True)
    nro_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Timbrados
        fields = "__all__"

    def get_nro_disponibles(self, obj):
        from .models import DocumentosTributarios
        usados = DocumentosTributarios.objects.filter(nro_timbrado=obj).count()
        return max(0, obj.nro_final - obj.nro_inicial + 1 - usados)


class DocumentosTributariosSerializer(serializers.ModelSerializer):
    timbrado_detalle = TimbradoSerializer(source="nro_timbrado", read_only=True)

    class Meta:
        model = DocumentosTributarios
        fields = "__all__"
