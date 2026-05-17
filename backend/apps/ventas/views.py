"""
Views para la app ventas
"""

from django.db import models, transaction

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from .services import VentaService

from .models import (
    Venta,
    DetalleVenta,
    PagoVenta,
    AplicacionPago,
    NotaCredito,
    DetalleNotaCredito,
    CondicionVenta,
)
from .serializers import (
    VentaSerializer,
    DetalleVentaSerializer,
    PagoVentaSerializer,
    AplicacionPagoSerializer,
    NotaCreditoSerializer,
    DetalleNotaCreditoSerializer,
    CondicionVentaSerializer,
)


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.select_related("cliente", "cajero").prefetch_related("detalles").all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "estado_pago", "tipo", "cliente", "fecha"]
    def perform_create(self, serializer):
        data = serializer.validated_data
        items = self.request.data.get('items', [])
        
        VentaService.registrar_venta(
            cliente=data.get('cliente'),
            cajero=self.request.user,
            tipo=data.get('tipo', 'CONTADO'),
            medio_pago=data.get('medio_pago'),
            tarjeta=data.get('tarjeta'),
            items=items,
        )

class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.select_related("venta", "producto").all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [IsAuthenticated]


class PagoVentaViewSet(viewsets.ModelViewSet):
    queryset = PagoVenta.objects.select_related("cliente", "venta", "medio_pago").all()
    serializer_class = PagoVentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "medio_pago", "cliente", "venta"]


class AplicacionPagoViewSet(viewsets.ModelViewSet):
    queryset = AplicacionPago.objects.select_related("pago", "venta").all()
    serializer_class = AplicacionPagoSerializer
    permission_classes = [IsAuthenticated]


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.select_related("cliente", "empleado_autoriza").prefetch_related("detalles").all()
    serializer_class = NotaCreditoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "cliente"]


class DetalleNotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = DetalleNotaCredito.objects.select_related("nota_credito", "producto").all()
    serializer_class = DetalleNotaCreditoSerializer
    permission_classes = [IsAuthenticated]


class CondicionVentaViewSet(viewsets.ModelViewSet):
    queryset = CondicionVenta.objects.all()
    serializer_class = CondicionVentaSerializer
    permission_classes = [IsAuthenticated]