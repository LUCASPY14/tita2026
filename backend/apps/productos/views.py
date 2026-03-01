from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.common.permissions import IsAdminOrReadOnly
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle
from .models import Productos, Categorias
from .serializers import ProductosSerializer, CategoriasSerializer

# Create your views here.
class ProductosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos.
    Permite listar, crear, editar y eliminar productos.
    
    Permisos:
    - Admin: CRUD completo
    - Usuarios autenticados: Solo lectura
    """
    queryset = Productos.objects.all()
    serializer_class = ProductosSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'id_categoria']
    search_fields = ['codigo_barra', 'descripcion']
    ordering_fields = ['descripcion', 'stock_minimo']
    ordering = ['descripcion']

class CategoriasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de productos.
    
    Permisos:
    - Admin: CRUD completo
    - Usuarios autenticados: Solo lectura
    """
    queryset = Categorias.objects.all()
    serializer_class = CategoriasSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']
