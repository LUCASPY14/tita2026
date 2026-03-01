from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.common.permissions import CanManageInventario, IsAdminOrReadOnly
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle
from .models import StockUnico, MovimientosStock, AjustesInventario
from .serializers import StockUnicoSerializer, MovimientosStockSerializer, AjustesInventarioSerializer


class StockUnicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar stock de productos.
    
    Permisos:
    - Admin y Encargados de Inventario: CRUD completo
    - Otros: Solo lectura
    """
    queryset = StockUnico.objects.all()
    serializer_class = StockUnicoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id_producto']
    search_fields = ['id_producto__descripcion']


class MovimientosStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet para movimientos de inventario.
    
    Permisos:
    - Solo personal autorizado puede gestionar movimientos
    """
    queryset = MovimientosStock.objects.all()
    serializer_class = MovimientosStockSerializer
    permission_classes = [IsAuthenticated, CanManageInventario]
    throttle_classes = [SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_movimiento', 'id_producto']
    ordering_fields = ['fecha_hora']
    ordering = ['-fecha_hora']


class AjustesInventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ajustes de inventario.
    
    Permisos:
    - Solo gerentes y encargados de inventario
    """
    queryset = AjustesInventario.objects.all()
    serializer_class = AjustesInventarioSerializer
    permission_classes = [IsAuthenticated, CanManageInventario]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_ajuste', 'estado']
    ordering = ['-fecha_hora']
