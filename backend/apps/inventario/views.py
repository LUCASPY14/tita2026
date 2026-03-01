from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import StockUnico, MovimientosStock, AjustesInventario
from .serializers import StockUnicoSerializer, MovimientosStockSerializer, AjustesInventarioSerializer


class StockUnicoViewSet(viewsets.ModelViewSet):
    queryset = StockUnico.objects.all()
    serializer_class = StockUnicoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id_producto']
    search_fields = ['id_producto__nombre']


class MovimientosStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientosStock.objects.all()
    serializer_class = MovimientosStockSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_movimiento', 'id_producto']
    ordering_fields = ['fecha_hora']
    ordering = ['-fecha_hora']


class AjustesInventarioViewSet(viewsets.ModelViewSet):
    queryset = AjustesInventario.objects.all()
    serializer_class = AjustesInventarioSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_ajuste', 'estado']
    ordering = ['-fecha_hora']
