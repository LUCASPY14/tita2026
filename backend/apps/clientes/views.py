from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.common.permissions import IsAdminOrReadOnly, IsClienteOrAdmin
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle
from .models import Clientes, Hijos
from .serializers import ClientesSerializer, HijosSerializer


# Create your views here.
class ClientesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar clientes.
    Permite listar, crear, editar y eliminar clientes.

    Permisos:
    - Admin: Acceso total
    - Clientes autenticados: Solo lectura de sus propios datos
    """

    queryset = Clientes.objects.all()
    serializer_class = ClientesSerializer
    permission_classes = [IsAuthenticated, IsClienteOrAdmin]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo", "id_tipo_cliente"]
    search_fields = ["nombres", "apellidos", "ruc_ci", "email"]
    ordering_fields = ["nombres", "apellidos", "fecha_registro"]
    ordering = ["apellidos", "nombres"]


class HijosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar hijos/estudiantes.

    Permisos:
    - Admin: Acceso total
    - Clientes: Solo sus propios hijos
    """

    queryset = Hijos.objects.all()
    serializer_class = HijosSerializer
    permission_classes = [IsAuthenticated, IsClienteOrAdmin]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo", "grado", "id_cliente_responsable"]
    search_fields = ["nombre", "apellido"]
    ordering = ["apellido", "nombre"]
