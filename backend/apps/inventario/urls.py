from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StockViewSet,
    MovimientoStockViewSet,
    AjusteInventarioViewSet,
    DetalleAjusteViewSet,
    CostoHistoricoViewSet,
    AlertaStockViewSet,
    LoteProductoViewSet,
    AlertaVencimientoViewSet,
)

router = DefaultRouter()
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"movimientos", MovimientoStockViewSet, basename="movimientos")
router.register(r"ajustes", AjusteInventarioViewSet, basename="ajustes")
router.register(r"detalles-ajuste", DetalleAjusteViewSet, basename="detalles-ajuste")
router.register(r"costos-historicos", CostoHistoricoViewSet, basename="costos-historicos")
router.register(r"alertas-stock", AlertaStockViewSet, basename="alertas-stock")
router.register(r"lotes", LoteProductoViewSet, basename="lotes")
router.register(r"alertas-vencimiento", AlertaVencimientoViewSet, basename="alertas-vencimiento")

urlpatterns = [
    path("", include(router.urls)),
]