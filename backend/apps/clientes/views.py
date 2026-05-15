"""
Views para la app clientes
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Cliente,
    CuentaCorrienteCliente,
    TipoCliente,
    Hijo,
    Grado,
    HistorialGrado,
    RestriccionHijo,
    AutorizacionSaldoNegativo,
    Pais,
    Ciudad,
)
from .serializers import (
    ClienteSerializer,
    CuentaCorrienteClienteSerializer,
    TipoClienteSerializer,
    HijoSerializer,
    GradoSerializer,
    HistorialGradoSerializer,
    RestriccionHijoSerializer,
    AutorizacionSaldoNegativoSerializer,
    PaisSerializer,
    CiudadSerializer,
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related("tipo_cliente", "lista_precio").all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "tipo_cliente"]
    search_fields = ["ruc_ci", "nombres", "apellidos"]


class CuentaCorrienteClienteViewSet(viewsets.ModelViewSet):
    queryset = CuentaCorrienteCliente.objects.select_related("cliente").all()
    serializer_class = CuentaCorrienteClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]


class TipoClienteViewSet(viewsets.ModelViewSet):
    queryset = TipoCliente.objects.all()
    serializer_class = TipoClienteSerializer
    permission_classes = [IsAuthenticated]


class HijoViewSet(viewsets.ModelViewSet):
    queryset = Hijo.objects.select_related("cliente_responsable").all()
    serializer_class = HijoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "cliente_responsable"]
    search_fields = ["nombre", "apellido"]


class GradoViewSet(viewsets.ModelViewSet):
    queryset = Grado.objects.all()
    serializer_class = GradoSerializer
    permission_classes = [IsAuthenticated]


class HistorialGradoViewSet(viewsets.ModelViewSet):
    queryset = HistorialGrado.objects.select_related("hijo").all()
    serializer_class = HistorialGradoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "anio_escolar"]


class RestriccionHijoViewSet(viewsets.ModelViewSet):
    queryset = RestriccionHijo.objects.select_related("hijo").all()
    serializer_class = RestriccionHijoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "severidad", "activo"]


class AutorizacionSaldoNegativoViewSet(viewsets.ModelViewSet):
    queryset = AutorizacionSaldoNegativo.objects.select_related("cliente", "venta").all()
    serializer_class = AutorizacionSaldoNegativoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "estado"]


class PaisViewSet(viewsets.ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    permission_classes = [IsAuthenticated]


class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.all()
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticated]