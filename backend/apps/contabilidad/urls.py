from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CajaViewSet,
    CierreCajaViewSet,
    MovimientoCajaViewSet,
    FacturaViewSet,
    DatosEmpresaViewSet,
    DashboardResumenView,
    DashboardTendenciaView,
    ReportePeriodoView,
    ReporteDiferenciasCajaView,
)

router = DefaultRouter()
router.register(r"cajas", CajaViewSet, basename="cajas")
router.register(r"cierres-caja", CierreCajaViewSet, basename="cierres-caja")
router.register(r"movimientos-caja", MovimientoCajaViewSet, basename="movimientos-caja")
router.register(r"facturas", FacturaViewSet, basename="facturas")
router.register(r"datos-empresa", DatosEmpresaViewSet, basename="datos-empresa")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", DashboardResumenView.as_view(), name="dashboard-resumen"),
    path("dashboard/tendencia/", DashboardTendenciaView.as_view(), name="dashboard-tendencia"),
    path("reportes/", ReportePeriodoView.as_view(), name="reportes-periodo"),
    path("reporte-diferencias-caja/", ReporteDiferenciasCajaView.as_view(), name="reporte-diferencias-caja"),
]
