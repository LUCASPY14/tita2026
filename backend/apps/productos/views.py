"""
Views para la app productos
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrReadOnly, IsStaffUser

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
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo"]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("categoria", "unidad_medida").all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "categoria", "es_servicio"]
    search_fields = ["descripcion", "codigo_barra", "codigo"]


class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = [IsAdminOrReadOnly]


class ListaPrecioViewSet(viewsets.ModelViewSet):
    queryset = ListaPrecio.objects.all()
    serializer_class = ListaPrecioSerializer
    permission_classes = [IsAdminOrReadOnly]


class PrecioPorListaViewSet(viewsets.ModelViewSet):
    queryset = PrecioPorLista.objects.select_related("producto", "lista").all()
    serializer_class = PrecioPorListaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "lista"]


class HistoricoPrecioViewSet(viewsets.ModelViewSet):
    queryset = HistoricoPrecio.objects.select_related("producto", "modificado_por").all()
    serializer_class = HistoricoPrecioSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto"]

    @action(detail=False, methods=["get"], url_path="reporte", permission_classes=[IsStaffUser])
    def reporte(self, request):
        """
        GET /api/productos/historico-precios/reporte/?producto=1&desde=YYYY-MM-DD&hasta=YYYY-MM-DD
        Retorna variación de precios para un producto en el período indicado.
        """
        producto_id = request.query_params.get("producto")
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        if not producto_id:
            return Response(
                {"error": "Se requiere el parámetro 'producto'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = HistoricoPrecio.objects.filter(
            producto_id=producto_id
        ).select_related("modificado_por").order_by("fecha_cambio")

        if desde:
            qs = qs.filter(fecha_cambio__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_cambio__date__lte=hasta)

        historial = [
            {
                "id": h.pk,
                "fecha": h.fecha_cambio,
                "precio_anterior": int(h.precio_anterior),
                "precio_nuevo": int(h.precio_nuevo),
                "variacion_porcentual": round(float(h.variacion_porcentual), 2),
                "modificado_por": str(h.modificado_por) if h.modificado_por else None,
            }
            for h in qs
        ]

        return Response({
            "producto_id": int(producto_id),
            "periodo": {"desde": desde, "hasta": hasta},
            "registros": len(historial),
            "historial": historial,
        })


class ImpuestoViewSet(viewsets.ModelViewSet):
    queryset = Impuesto.objects.all()
    serializer_class = ImpuestoSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductoImpuestoViewSet(viewsets.ModelViewSet):
    queryset = ProductoImpuesto.objects.select_related("producto", "impuesto").all()
    serializer_class = ProductoImpuestoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "impuesto"]