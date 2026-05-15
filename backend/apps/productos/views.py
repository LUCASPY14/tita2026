"""
Views para la app productos
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Categoria,
    Producto,
    UnidadMedida,
    ListaPrecio,
    PrecioPorLista,
    HistoricoPrecio,
    Impuesto,
    ProductoImpuesto,
)
from .serializers import (
    CategoriaSerializer,
    ProductoSerializer,
    UnidadMedidaSerializer,
    ListaPrecioSerializer,
    PrecioPorListaSerializer,
    HistoricoPrecioSerializer,
    ImpuestoSerializer,
    ProductoImpuestoSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.select_related("categoria_padre").all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo"]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("categoria", "unidad_medida").all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "categoria", "es_servicio"]
    search_fields = ["descripcion", "codigo_barra", "codigo"]


class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = [IsAuthenticated]


class ListaPrecioViewSet(viewsets.ModelViewSet):
    queryset = ListaPrecio.objects.all()
    serializer_class = ListaPrecioSerializer
    permission_classes = [IsAuthenticated]


class PrecioPorListaViewSet(viewsets.ModelViewSet):
    queryset = PrecioPorLista.objects.select_related("producto", "lista").all()
    serializer_class = PrecioPorListaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "lista"]


class HistoricoPrecioViewSet(viewsets.ModelViewSet):
    queryset = HistoricoPrecio.objects.select_related("producto").all()
    serializer_class = HistoricoPrecioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto"]


class ImpuestoViewSet(viewsets.ModelViewSet):
    queryset = Impuesto.objects.all()
    serializer_class = ImpuestoSerializer
    permission_classes = [IsAuthenticated]


class ProductoImpuestoViewSet(viewsets.ModelViewSet):
    queryset = ProductoImpuesto.objects.select_related("producto", "impuesto").all()
    serializer_class = ProductoImpuestoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "impuesto"]