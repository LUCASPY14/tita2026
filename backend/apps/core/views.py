"""
Views para la app core
"""

from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from common.permissions import IsAdmin, IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb

from django_filters.rest_framework import DjangoFilterBackend

# Los medios de pago y límites cambian rarísimo → TTL de 1 hora
_CACHE_TTL_LONG = 3600


def _invalidar_cache_core(*prefixes):
    for prefix in prefixes:
        try:
            cache.delete_pattern(f"{prefix}*")
        except (AttributeError, NotImplementedError):
            cache.clear()
            return

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
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado"]
    search_fields = ["nro_tarjeta", "hijo__nombre", "hijo__apellido"]
    ordering = ["nro_tarjeta"]


class MovimientoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = MovimientoTarjetaSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "tipo"]


class TarjetaAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = TarjetaAutorizacion.objects.select_related("empleado").all()
    serializer_class = TarjetaAutorizacionSerializer
    permission_classes = [IsCajeroOrAdmin]


METODOS_CONFIRMACION_INMEDIATA = ("EFECTIVO", "POS DEBITO", "POS CREDITO")


class CargaSaldoViewSet(viewsets.ModelViewSet):
    queryset = CargaSaldo.objects.select_related("tarjeta", "cliente_origen").all()
    serializer_class = CargaSaldoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "estado"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        metodo = data.get("metodo_pago", "")

        if metodo in METODOS_CONFIRMACION_INMEDIATA:
            # El servicio crea la CargaSaldo + actualiza saldo + crea MovimientoTarjeta atomicamente
            carga = TarjetaService.cargar_saldo(
                tarjeta=data["tarjeta"],
                monto=data["monto_cargado"],
                cliente_origen=data.get("cliente_origen"),
                responsable=self.request.user,
                metodo_pago=metodo,
                referencia=data.get("referencia") or "",
            )
            out = self.get_serializer(carga)
            return Response(out.data, status=status.HTTP_201_CREATED)

        # Pagos por transferencia u otros: quedan PENDIENTE para confirmacion manual
        carga = serializer.save(responsable=self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar(self, request, pk=None):
        """POST /api/core/cargas-saldo/<id>/confirmar/ — confirma una carga PENDIENTE."""
        carga = self.get_object()
        if carga.estado != CargaSaldo.Estado.PENDIENTE:
            return Response(
                {"error": f"Solo se pueden confirmar cargas PENDIENTE. Estado actual: {carga.estado}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        carga_confirmada = TarjetaService.confirmar_carga(
            carga=carga,
            responsable=request.user,
        )
        return Response(self.get_serializer(carga_confirmada).data)


class ConsumoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = ConsumoTarjetaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta"]


class MedioPagoViewSet(viewsets.ModelViewSet):
    queryset = MedioPago.objects.all()
    serializer_class = MedioPagoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        cache_key = f"medios_pago_list_{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, _CACHE_TTL_LONG)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _invalidar_cache_core("medios_pago_list_")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _invalidar_cache_core("medios_pago_list_")

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        _invalidar_cache_core("medios_pago_list_")


class LimiteTransaccionViewSet(viewsets.ModelViewSet):
    queryset = LimiteTransaccion.objects.select_related("rol").all()
    serializer_class = LimiteTransaccionSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["rol", "tipo_operacion", "activo"]


class RegistroAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = RegistroAutorizacion.objects.select_related("solicitante", "autorizador").all()
    serializer_class = RegistroAutorizacionSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_operacion"]