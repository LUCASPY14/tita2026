from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaViewSet,
    ProductoViewSet,
    UnidadMedidaViewSet,
    ListaPrecioViewSet,
    PrecioPorListaViewSet,
    HistoricoPrecioViewSet,
    ImpuestoViewSet,
    ProductoImpuestoViewSet,
)

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"productos", ProductoViewSet, basename="productos")
router.register(r"unidades-medida", UnidadMedidaViewSet, basename="unidades-medida")
router.register(r"listas-precio", ListaPrecioViewSet, basename="listas-precio")
router.register(r"precios-por-lista", PrecioPorListaViewSet, basename="precios-por-lista")
router.register(r"historico-precios", HistoricoPrecioViewSet, basename="historico-precios")
router.register(r"impuestos", ImpuestoViewSet, basename="impuestos")
router.register(r"productos-impuestos", ProductoImpuestoViewSet, basename="productos-impuestos")

urlpatterns = [
    path("", include(router.urls)),
]