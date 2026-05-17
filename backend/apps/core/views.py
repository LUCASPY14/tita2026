"""
Views para la app core
"""

from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    TarjetaAutorizacion,
    CargaSaldo,
    ConsumoTarjeta,
    MedioPago,
    LimiteTransaccion,
    RegistroAutorizacion,
)
from .serializers import (
    TarjetaSerializer,
    MovimientoTarjetaSerializer,
    TarjetaAutorizacionSerializer,
    CargaSaldoSerializer,
    ConsumoTarjetaSerializer,
    MedioPagoSerializer,
    LimiteTransaccionSerializer,
    RegistroAutorizacionSerializer,
)
from .services import TarjetaService


class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.select_related("hijo").all()
    serializer_class = TarjetaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado"]
    search_fields = ["nro_tarjeta", "hijo__nombre", "hijo__apellido"]
    ordering = ["nro_tarjeta"]


class MovimientoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = MovimientoTarjetaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "tipo"]


class TarjetaAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = TarjetaAutorizacion.objects.select_related("empleado").all()
    serializer_class = TarjetaAutorizacionSerializer
    permission_classes = [IsAuthenticated]


class CargaSaldoViewSet(viewsets.ModelViewSet):
    queryset = CargaSaldo.objects.select_related("tarjeta", "cliente_origen").all()
    serializer_class = CargaSaldoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "estado"]

    def perform_create(self, serializer):
        """Si es carga en caja (EFECTIVO/POS), confirmar automaticamente."""
        carga = serializer.save()
        
        # Si es pago en caja, confirmar inmediatamente
        if carga.metodo_pago in ("EFECTIVO", "POS DEBITO", "POS CREDITO"):
            TarjetaService.cargar_saldo(
                tarjeta=carga.tarjeta,
                monto=carga.monto_cargado,
                cliente_origen=carga.cliente_origen,
                responsable=carga.responsable or self.request.user,
                metodo_pago=carga.metodo_pago,
                referencia=carga.referencia or "",
            )


class ConsumoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = ConsumoTarjetaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta"]


class MedioPagoViewSet(viewsets.ModelViewSet):
    queryset = MedioPago.objects.all()
    serializer_class = MedioPagoSerializer
    permission_classes = [IsAuthenticated]


class LimiteTransaccionViewSet(viewsets.ModelViewSet):
    queryset = LimiteTransaccion.objects.select_related("rol").all()
    serializer_class = LimiteTransaccionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["rol", "tipo_operacion", "activo"]


class RegistroAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = RegistroAutorizacion.objects.select_related("solicitante", "autorizador").all()
    serializer_class = RegistroAutorizacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_operacion"]