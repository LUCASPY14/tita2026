from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.common.permissions import IsAdminOrReadOnly, IsClienteOrAdmin
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle
from .models import Clientes, Hijos, TiposCliente, Grados, RestriccionesHijos, Pais, Ciudad
from .serializers import ClientesSerializer, HijosSerializer, TiposClienteSerializer, GradosSerializer, RestriccionesHijosSerializer, PaisSerializer, CiudadSerializer


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
    filterset_fields = ["estado", "id_tipo_cliente"]
    search_fields = ["nombres", "apellidos", "ruc_ci", "email"]
    ordering_fields = ["nombres", "apellidos", "fecha_registro"]
    ordering = ["apellidos", "nombres"]

    @action(detail=True, methods=["get"])
    def cuenta_corriente(self, request, pk=None):
        """
        Obtiene el estado de cuenta corriente del cliente.

        GET /api/v1/clientes/{id}/cuenta_corriente/
        """
        cliente = self.get_object()
        cuenta = cliente.cuenta_corriente
        cuenta["cliente"] = {
            "id": cliente.id_cliente,
            "nombre": f"{cliente.nombres} {cliente.apellidos}",
            "ruc_ci": cliente.ruc_ci,
        }
        return Response(cuenta)


class TiposClienteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para tipos de cliente."""
    queryset = TiposCliente.objects.filter(estado=True)
    serializer_class = TiposClienteSerializer
    permission_classes = [IsAuthenticated]


class GradosViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para grados escolares."""
    queryset = Grados.objects.filter(estado=True).order_by('orden_visualizacion')
    serializer_class = GradosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


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
    filterset_fields = ["estado", "grado", "id_cliente_responsable"]
    search_fields = ["nombre", "apellido", "tarjetas__nro_tarjeta", "tarjetas__codigo_barras"]
    ordering = ["apellido", "nombre"]


class RestriccionesHijosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar restricciones de compra de los hijos.
    Accesible por administradores y por el cliente (padre) responsable del hijo.
    """

    queryset = RestriccionesHijos.objects.all()
    serializer_class = RestriccionesHijosSerializer
    permission_classes = [IsAuthenticated, IsClienteOrAdmin]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id_hijo", "estado", "severidad"]
    search_fields = ["tipo_restriccion", "descripcion"]
    ordering = ["-severidad", "tipo_restriccion"]


class PaisViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar el catálogo de países."""
    queryset = Pais.objects.all().order_by('nombre')
    serializer_class = PaisSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    ordering = ['nombre']


class CiudadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar el catálogo de ciudades."""
    queryset = Ciudad.objects.all().order_by('nombre')
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    ordering = ['nombre']
