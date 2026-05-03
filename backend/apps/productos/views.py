from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsAdminOrReadOnly
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle

from .models import Categorias, ListasPrecios, PreciosPorLista, Productos, UnidadesMedida
from .serializers import (
    CategoriasSerializer,
    ListasPreciosSerializer,
    PreciosPorListaSerializer,
    ProductosSerializer,
    UnidadesMedidaSerializer,
)


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
    filterset_fields = ["estado", "id_categoria", "es_servicio"]
    search_fields = ["codigo_barra", "descripcion"]
    ordering_fields = ["descripcion", "stock_minimo"]
    ordering = ["descripcion"]


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
    filterset_fields = ["estado"]
    search_fields = ["nombre"]
    ordering = ["nombre"]


class UnidadesMedidaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar unidades de medida.
    """

    queryset = UnidadesMedida.objects.filter(estado=True)
    serializer_class = UnidadesMedidaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]
    ordering = ["nombre"]


class ListasPreciosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar listas de precios.
    """

    queryset = ListasPrecios.objects.filter(estado=True)
    serializer_class = ListasPreciosSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]
    ordering = ["nombre_lista"]


class PreciosPorListaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar precios por lista de productos.
    """

    queryset = PreciosPorLista.objects.select_related("id_producto", "id_lista").all()
    serializer_class = PreciosPorListaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id_producto", "id_lista"]
    ordering = ["id_lista", "id_producto"]
