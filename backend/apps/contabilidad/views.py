"""
Views para la app contabilidad
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Caja,
    CierreCaja,
    MovimientoCaja,
    ConciliacionPago,
    Factura,
    DatosEmpresa,
)
from .serializers import (
    CajaSerializer,
    CierreCajaSerializer,
    MovimientoCajaSerializer,
    ConciliacionPagoSerializer,
    FacturaSerializer,
    DatosEmpresaSerializer,
)


class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]


class CierreCajaViewSet(viewsets.ModelViewSet):
    queryset = CierreCaja.objects.select_related("caja", "empleado").all()
    serializer_class = CierreCajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["caja", "estado"]


class MovimientoCajaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoCaja.objects.select_related("cierre", "medio_pago").all()
    serializer_class = MovimientoCajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cierre", "tipo", "medio_pago"]


class ConciliacionPagoViewSet(viewsets.ModelViewSet):
    queryset = ConciliacionPago.objects.select_related("pago_venta").all()
    serializer_class = ConciliacionPagoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.select_related("cliente", "venta").all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "cliente"]


class DatosEmpresaViewSet(viewsets.ModelViewSet):
    queryset = DatosEmpresa.objects.all()
    serializer_class = DatosEmpresaSerializer
    permission_classes = [IsAuthenticated]