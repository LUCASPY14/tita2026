"""
Serializers para la app reportes
"""

from rest_framework import serializers

from .models import PlantillaReporte


class PlantillaReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantillaReporte
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]