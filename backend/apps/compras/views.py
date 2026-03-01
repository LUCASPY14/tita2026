from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Proveedores, Compras, DetallesCompra, PagosProveedores, NotasCreditoProveedor
from .serializers import ProveedoresSerializer, ComprasSerializer, DetallesCompraSerializer, PagosProveedoresSerializer, NotasCreditoProveedorSerializer


class ProveedoresViewSet(viewsets.ModelViewSet):
    queryset = Proveedores.objects.all()
    serializer_class = ProveedoresSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'ciudad']
    search_fields = ['razon_social', 'ruc', 'email']
    ordering_fields = ['razon_social']
    ordering = ['razon_social']


class ComprasViewSet(viewsets.ModelViewSet):
    queryset = Compras.objects.all()
    serializer_class = ComprasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_pago', 'id_proveedor']
    search_fields = ['nro_factura']
    ordering_fields = ['fecha', 'monto_total']
    ordering = ['-fecha']


class DetallesCompraViewSet(viewsets.ModelViewSet):
    queryset = DetallesCompra.objects.all()
    serializer_class = DetallesCompraSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_compra', 'id_producto']


class PagosProveedoresViewSet(viewsets.ModelViewSet):
    queryset = PagosProveedores.objects.all()
    serializer_class = PagosProveedoresSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id_medio_pago']
    ordering = ['-fecha_creacion']


class NotasCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotasCreditoProveedor.objects.all()
    serializer_class = NotasCreditoProveedorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_proveedor']
    ordering = ['-fecha']
