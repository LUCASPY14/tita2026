"""
Views para la app compras
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Proveedor,
    CuentaCorrienteProveedor,
    Compra,
    DetalleCompra,
    PagoProveedor,
    AplicacionPagoCompra,
    NotaCreditoProveedor,
    DetalleNotaCreditoProveedor,
)
from .serializers import (
    ProveedorSerializer,
    CuentaCorrienteProveedorSerializer,
    CompraSerializer,
    DetalleCompraSerializer,
    PagoProveedorSerializer,
    AplicacionPagoCompraSerializer,
    NotaCreditoProveedorSerializer,
    DetalleNotaCreditoProveedorSerializer,
)


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo"]
    search_fields = ["ruc", "razon_social"]


class CuentaCorrienteProveedorViewSet(viewsets.ModelViewSet):
    queryset = CuentaCorrienteProveedor.objects.select_related("proveedor").all()
    serializer_class = CuentaCorrienteProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "tipo"]


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.select_related("proveedor").prefetch_related("detalles").all()
    serializer_class = CompraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado_pago", "tipo_pago"]


class DetalleCompraViewSet(viewsets.ModelViewSet):
    queryset = DetalleCompra.objects.select_related("compra", "producto").all()
    serializer_class = DetalleCompraSerializer
    permission_classes = [IsAuthenticated]


class PagoProveedorViewSet(viewsets.ModelViewSet):
    queryset = PagoProveedor.objects.select_related("proveedor", "medio_pago").all()
    serializer_class = PagoProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado", "medio_pago"]


class AplicacionPagoCompraViewSet(viewsets.ModelViewSet):
    queryset = AplicacionPagoCompra.objects.select_related("pago", "compra").all()
    serializer_class = AplicacionPagoCompraSerializer
    permission_classes = [IsAuthenticated]


class NotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotaCreditoProveedor.objects.select_related("proveedor").prefetch_related("detalles").all()
    serializer_class = NotaCreditoProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado"]


class DetalleNotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = DetalleNotaCreditoProveedor.objects.select_related("nota_credito", "producto").all()
    serializer_class = DetalleNotaCreditoProveedorSerializer
    permission_classes = [IsAuthenticated]