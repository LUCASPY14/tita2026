from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Tarjetas, CargasSaldo, ConsumosTarjeta, MediosPago, ConfiguracionSistema
from .serializers import TarjetasSerializer, CargasSaldoSerializer, ConsumosTarjetaSerializer, MediosPagoSerializer, ConfiguracionSistemaSerializer


class TarjetasViewSet(viewsets.ModelViewSet):
    queryset = Tarjetas.objects.all()
    serializer_class = TarjetasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo']
    search_fields = ['nro_tarjeta', 'codigo_barras']
    ordering_fields = ['fecha_creacion']
    ordering = ['nro_tarjeta']


class CargasSaldoViewSet(viewsets.ModelViewSet):
    queryset = CargasSaldo.objects.all()
    serializer_class = CargasSaldoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'nro_tarjeta']
    search_fields = ['referencia']
    ordering_fields = ['fecha_carga']
    ordering = ['-fecha_carga']


class ConsumosTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumosTarjeta.objects.all()
    serializer_class = ConsumosTarjetaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['nro_tarjeta']
    ordering_fields = ['fecha_consumo']
    ordering = ['-fecha_consumo']


class MediosPagoViewSet(viewsets.ModelViewSet):
    queryset = MediosPago.objects.all()
    serializer_class = MediosPagoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['descripcion']


class ConfiguracionSistemaViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionSistema.objects.all()
    serializer_class = ConfiguracionSistemaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tipo', 'categoria']
    search_fields = ['clave', 'descripcion']
