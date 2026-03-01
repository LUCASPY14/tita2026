from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones
from .serializers import VentasSerializer, DetallesVentaSerializer, PagosVentaSerializer, NotasCreditoClienteSerializer, PromocionesSerializer


class VentasViewSet(viewsets.ModelViewSet):
    queryset = Ventas.objects.all()
    serializer_class = VentasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_pago', 'estado', 'tipo_venta', 'id_cliente', 'fecha']
    search_fields = ['nro_factura_venta', 'id_cliente__nombre', 'id_cliente__apellido']
    ordering_fields = ['fecha', 'monto_total']
    ordering = ['-fecha']


class DetallesVentaViewSet(viewsets.ModelViewSet):
    queryset = DetallesVenta.objects.all()
    serializer_class = DetallesVentaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_venta', 'id_producto']


class PagosVentaViewSet(viewsets.ModelViewSet):
    queryset = PagosVenta.objects.all()
    serializer_class = PagosVentaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_venta', 'id_medio_pago']
    ordering_fields = ['fecha_pago']
    ordering = ['-fecha_pago']


class NotasCreditoClienteViewSet(viewsets.ModelViewSet):
    queryset = NotasCreditoCliente.objects.all()
    serializer_class = NotasCreditoClienteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_cliente']
    ordering = ['-fecha_emision']


class PromocionesViewSet(viewsets.ModelViewSet):
    queryset = Promociones.objects.all()
    serializer_class = PromocionesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'tipo_promocion']
    search_fields = ['nombre', 'codigo_promocion']
