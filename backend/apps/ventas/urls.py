from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    VentaViewSet,
    DetalleVentaViewSet,
    PagoVentaViewSet,
    AplicacionPagoViewSet,
    NotaCreditoViewSet,
    DetalleNotaCreditoViewSet,
    CondicionVentaViewSet,
    ReporteVentasProductoView,
    ReporteVentasCajeroView,
)

router = DefaultRouter()
router.register(r"ventas", VentaViewSet, basename="ventas")
router.register(r"detalles-venta", DetalleVentaViewSet, basename="detalles-venta")
router.register(r"pagos", PagoVentaViewSet, basename="pagos")
router.register(r"aplicaciones-pago", AplicacionPagoViewSet, basename="aplicaciones-pago")
router.register(r"notas-credito", NotaCreditoViewSet, basename="notas-credito")
router.register(r"detalles-nota-credito", DetalleNotaCreditoViewSet, basename="detalles-nota-credito")
router.register(r"condiciones-venta", CondicionVentaViewSet, basename="condiciones-venta")

urlpatterns = [
    path("", include(router.urls)),
    path("reporte-productos/", ReporteVentasProductoView.as_view(), name="reporte-ventas-producto"),
    path("reporte-cajeros/", ReporteVentasCajeroView.as_view(), name="reporte-ventas-cajero"),
]