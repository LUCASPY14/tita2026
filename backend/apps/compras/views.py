"""
Views para la app compras
"""

from rest_framework import viewsets, filters

from common.permissions import IsCajeroOrAdmin
from common.mixins import ExportCSVMixin
from .filters import CompraFilter

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


class ProveedorViewSet(ExportCSVMixin, viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo"]
    search_fields = ["ruc", "razon_social"]
    ordering_fields = ["razon_social", "ruc"]
    ordering = ["razon_social"]
    export_filename = "proveedores"
    export_fields = [
        ("RUC", "ruc"),
        ("Razón Social", "razon_social"),
        ("Teléfono", "telefono"),
        ("Email", "email"),
        ("Activo", "activo"),
    ]


class CuentaCorrienteProveedorViewSet(viewsets.ModelViewSet):
    queryset = CuentaCorrienteProveedor.objects.select_related("proveedor").all()
    serializer_class = CuentaCorrienteProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "tipo"]


class CompraViewSet(ExportCSVMixin, viewsets.ModelViewSet):
    queryset = Compra.objects.select_related("proveedor").prefetch_related("detalles").all()
    serializer_class = CompraSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CompraFilter
    search_fields = ["proveedor__razon_social", "nro_factura"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]
    export_filename = "compras"
    export_fields = [
        ("Fecha", lambda o: str(o.fecha)[:10]),
        ("Proveedor", "proveedor__razon_social"),
        ("Nro. Factura", "nro_factura"),
        ("Monto Total", "monto_total"),
        ("Estado", "estado"),
    ]


class DetalleCompraViewSet(viewsets.ModelViewSet):
    queryset = DetalleCompra.objects.select_related("compra", "producto").all()
    serializer_class = DetalleCompraSerializer
    permission_classes = [IsCajeroOrAdmin]


class PagoProveedorViewSet(viewsets.ModelViewSet):
    queryset = PagoProveedor.objects.select_related("proveedor", "medio_pago").all()
    serializer_class = PagoProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado", "medio_pago"]


class AplicacionPagoCompraViewSet(viewsets.ModelViewSet):
    queryset = AplicacionPagoCompra.objects.select_related("pago", "compra").all()
    serializer_class = AplicacionPagoCompraSerializer
    permission_classes = [IsCajeroOrAdmin]


class NotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotaCreditoProveedor.objects.select_related("proveedor").prefetch_related("detalles").all()
    serializer_class = NotaCreditoProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado"]


class DetalleNotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = DetalleNotaCreditoProveedor.objects.select_related("nota_credito", "producto").all()
    serializer_class = DetalleNotaCreditoProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]