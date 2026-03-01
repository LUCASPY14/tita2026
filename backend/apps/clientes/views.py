from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Clientes, Hijos
from .serializers import ClientesSerializer, HijosSerializer

# Create your views here.
class ClientesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar clientes.
    Permite listar, crear, editar y eliminar clientes.
    """
    queryset = Clientes.objects.all()
    serializer_class = ClientesSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'ruc', 'email']
    ordering_fields = ['nombre']
    ordering = ['nombre']

class HijosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar hijos/estudiantes.
    """
    queryset = Hijos.objects.all()
    serializer_class = HijosSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'grado']
    search_fields = ['nombres', 'apellidos']
    ordering = ['apellidos', 'nombres']
