from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Empleados, Roles, PerfilesUsuario, UsuariosPortal
from .serializers import EmpleadosSerializer, RolesSerializer, PerfilesUsuarioSerializer, UsuariosPortalSerializer


class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre_rol']


class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset = Empleados.objects.all()
    serializer_class = EmpleadosSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'id_rol']
    search_fields = ['nombre', 'apellido', 'usuario', 'email']
    ordering_fields = ['apellido', 'nombre']
    ordering = ['apellido', 'nombre']


class PerfilesUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilesUsuario.objects.all()
    serializer_class = PerfilesUsuarioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_empleado']


class UsuariosPortalViewSet(viewsets.ModelViewSet):
    queryset = UsuariosPortal.objects.all()
    serializer_class = UsuariosPortalSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'id_cliente']
    search_fields = ['email']
