"""
Views para la app reportes
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import PlantillaReporte
from .serializers import PlantillaReporteSerializer


class PlantillaReporteViewSet(viewsets.ModelViewSet):
    queryset = PlantillaReporte.objects.all()
    serializer_class = PlantillaReporteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "tipo", "frecuencia"]
    search_fields = ["nombre", "descripcion"]