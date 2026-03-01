from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Productos, Categorias
from .serializers import ProductosSerializer, CategoriasSerializer

# Create your views here.
class ProductosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos.
    Permite listar, crear, editar y eliminar productos.
    """
    queryset = Productos.objects.all()
    serializer_class = ProductosSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'codigo_barra', 'descripcion']
    ordering_fields = ['nombre']
    ordering = ['nombre']

class CategoriasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de productos.
    """
    queryset = Categorias.objects.all()
    serializer_class = CategoriasSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre_categoria', 'descripcion']
    ordering = ['nombre_categoria']
