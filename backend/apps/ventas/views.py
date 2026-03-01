from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.common.permissions import CanManageVentas, IsAdminOrReadOnly
from apps.common.throttling import VentasRateThrottle, BurstRateThrottle
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones
from .serializers import VentasSerializer, DetallesVentaSerializer, PagosVentaSerializer, NotasCreditoClienteSerializer, PromocionesSerializer


class VentasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar ventas.
    
    Permisos:
    - Admin, Gerentes y Cajeros: Acceso total
    - Otros: Sin acceso
    """
    queryset = Ventas.objects.all()
    serializer_class = VentasSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle, BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_pago', 'estado', 'tipo_venta', 'id_cliente', 'fecha']
    search_fields = ['nro_factura_venta', 'id_cliente__nombres', 'id_cliente__apellidos']
    ordering_fields = ['fecha', 'monto_total']
    ordering = ['-fecha']


class DetallesVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para detalles de venta.
    """
    queryset = DetallesVenta.objects.all()
    serializer_class = DetallesVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_venta', 'id_producto']


class PagosVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos de ventas.
    """
    queryset = PagosVenta.objects.all()
    serializer_class = PagosVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_venta', 'id_medio_pago']
    ordering_fields = ['fecha_pago']
    ordering = ['-fecha_pago']


class NotasCreditoClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notas de crédito.
    """
    queryset = NotasCreditoCliente.objects.all()
    serializer_class = NotasCreditoClienteSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_cliente']
    ordering = ['-fecha_emision']


class PromocionesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar promociones.
    
    Permisos:
    - Admin: CRUD completo
    - Otros autenticados: Solo lectura
    """
    queryset = Promociones.objects.all()
    serializer_class = PromocionesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'tipo_promocion']
    search_fields = ['nombre', 'codigo_promocion']
