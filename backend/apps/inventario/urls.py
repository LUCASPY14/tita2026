from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StockViewSet,
    MovimientoStockViewSet,
    AjusteInventarioViewSet,
    DetalleAjusteViewSet,
    CostoHistoricoViewSet,
    AlertaStockViewSet,
    StockCriticoView,
    ReporteStockView,
)

router = DefaultRouter()
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"movimientos", MovimientoStockViewSet, basename="movimientos")
router.register(r"ajustes", AjusteInventarioViewSet, basename="ajustes")
router.register(r"detalles-ajuste", DetalleAjusteViewSet, basename="detalles-ajuste")
router.register(r"costos-historicos", CostoHistoricoViewSet, basename="costos-historicos")
router.register(r"alertas-stock", AlertaStockViewSet, basename="alertas-stock")

urlpatterns = [
    path("", include(router.urls)),
    path("stock-critico/", StockCriticoView.as_view(), name="stock-critico"),
    path("reporte-stock/", ReporteStockView.as_view(), name="reporte-stock"),
]
