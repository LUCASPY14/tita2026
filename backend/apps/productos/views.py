"""
Views para la app productos
"""

from django.core.cache import cache
from django.db import transaction
from django.db.models import DecimalField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

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


_CACHE_TTL = 300  # 5 minutos


def _invalidar_cache(*prefixes):
    """Borra claves de caché por prefijo (Redis) o todo el caché (LocMem)."""
    for prefix in prefixes:
        try:
            cache.delete_pattern(f"{prefix}*")
        except (AttributeError, NotImplementedError):
            cache.clear()
            return


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.select_related("categoria_padre").all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo"]

    def list(self, request, *args, **kwargs):
        cache_key = f"categorias_list_{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, _CACHE_TTL)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _invalidar_cache("categorias_list_")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _invalidar_cache("categorias_list_")

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        _invalidar_cache("categorias_list_")


class ProductoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "categoria", "es_servicio"]
    search_fields = ["descripcion", "codigo_barra", "codigo"]

    def get_queryset(self):
        from apps.inventario.models import Stock

        precio_default_sq = PrecioPorLista.objects.filter(
            producto=OuterRef("pk"),
            lista__es_por_defecto=True,
            lista__activo=True,
        ).values("precio_unitario")[:1]

        precio_fallback_sq = PrecioPorLista.objects.filter(
            producto=OuterRef("pk"),
        ).order_by("lista__nombre").values("precio_unitario")[:1]

        stock_sq = Stock.objects.filter(
            producto=OuterRef("pk")
        ).values("cantidad")[:1]

        return (
            Producto.objects
            .select_related("categoria", "unidad_medida")
            .annotate(
                _precio_actual=Coalesce(
                    Subquery(precio_default_sq),
                    Subquery(precio_fallback_sq),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                ),
                _stock_actual=Coalesce(
                    Subquery(stock_sq),
                    Value(0, output_field=DecimalField(max_digits=10, decimal_places=3)),
                ),
            )
        )

    def list(self, request, *args, **kwargs):
        cache_key = f"productos_list_{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, _CACHE_TTL)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _invalidar_cache("productos_list_")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _invalidar_cache("productos_list_")

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        _invalidar_cache("productos_list_")


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

    def perform_update(self, serializer):
        with transaction.atomic():
            old_price = serializer.instance.precio_unitario
            instance = serializer.save()
            if instance.precio_unitario != old_price:
                HistoricoPrecio.objects.create(
                    producto=instance.producto,
                    precio_anterior=old_price,
                    precio_nuevo=instance.precio_unitario,
                    modificado_por=self.request.user if self.request.user.is_authenticated else None,
                )
        _invalidar_cache("productos_list_")


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

        qs = qs[:500]

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