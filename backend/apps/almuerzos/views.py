from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import PlanesAlmuerzo, TiposAlmuerzo, SuscripcionesAlmuerzo, RegistrosConsumoAlmuerzo, Alergenos
from .serializers import PlanesAlmuerzoSerializer, TiposAlmuerzoSerializer, SuscripcionesAlmuerzoSerializer, RegistrosConsumoAlmuerzoSerializer, AlergenosSerializer


class PlanesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanesAlmuerzo.objects.all()
    serializer_class = PlanesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre_plan']


class TiposAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TiposAlmuerzo.objects.all()
    serializer_class = TiposAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre']


class SuscripcionesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionesAlmuerzo.objects.all()
    serializer_class = SuscripcionesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo', 'id_plan_almuerzo']
    ordering = ['-fecha_inicio']


class RegistrosConsumoAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = RegistrosConsumoAlmuerzo.objects.all()
    serializer_class = RegistrosConsumoAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo', 'fecha_consumo']
    ordering = ['-fecha_consumo']


class AlergenosViewSet(viewsets.ModelViewSet):
    queryset = Alergenos.objects.all()
    serializer_class = AlergenosSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'nivel_severidad']
    search_fields = ['nombre']
