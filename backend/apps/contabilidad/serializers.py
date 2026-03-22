from rest_framework import serializers
from .models import Impuestos


class ImpuestosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impuestos
        fields = "__all__"
