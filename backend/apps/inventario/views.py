"""
Views para la app inventario
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Stock,
    MovimientoStock,
    AjusteInventario,
    DetalleAjuste,
    CostoHistorico,
    AlertaStock,
    LoteProducto,
    AlertaVencimiento,
)
from .serializers import (
    StockSerializer,
    MovimientoStockSerializer,
    AjusteInventarioSerializer,
    DetalleAjusteSerializer,
    CostoHistoricoSerializer,
    AlertaStockSerializer,
    LoteProductoSerializer,
    AlertaVencimientoSerializer,
)


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related("producto").all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["producto__descripcion", "producto__codigo_barra"]


class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.select_related("producto").all()
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "tipo", "motivo"]


class AjusteInventarioViewSet(viewsets.ModelViewSet):
    queryset = AjusteInventario.objects.select_related("solicitado_por").prefetch_related("detalles").all()
    serializer_class = AjusteInventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "estado"]


class DetalleAjusteViewSet(viewsets.ModelViewSet):
    queryset = DetalleAjuste.objects.select_related("ajuste", "producto").all()
    serializer_class = DetalleAjusteSerializer
    permission_classes = [IsAuthenticated]


class CostoHistoricoViewSet(viewsets.ModelViewSet):
    queryset = CostoHistorico.objects.select_related("producto").all()
    serializer_class = CostoHistoricoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto"]


class AlertaStockViewSet(viewsets.ModelViewSet):
    queryset = AlertaStock.objects.select_related("producto").all()
    serializer_class = AlertaStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "tipo", "activa"]


class LoteProductoViewSet(viewsets.ModelViewSet):
    queryset = LoteProducto.objects.select_related("producto").all()
    serializer_class = LoteProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "bloqueado"]


class AlertaVencimientoViewSet(viewsets.ModelViewSet):
    queryset = AlertaVencimiento.objects.select_related("lote").all()
    serializer_class = AlertaVencimientoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lote", "tipo"]