from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PrecioAlmuerzoViewSet,
    TipoAlmuerzoViewSet,
    PlanAlmuerzoViewSet,
    SuscripcionAlmuerzoViewSet,
    RegistroConsumoAlmuerzoViewSet,
    CuentaAlmuerzoMensualViewSet,
    PagoCuentaAlmuerzoViewSet,
    PagoAlmuerzoMensualViewSet,
    AlergenoViewSet,
    ProductoAlergenoViewSet,
    MenuDiarioViewSet,
    ReporteAlmuerzosView,
)

router = DefaultRouter()
router.register(r"precios-almuerzo", PrecioAlmuerzoViewSet, basename="precios-almuerzo")
router.register(r"tipos-almuerzo", TipoAlmuerzoViewSet, basename="tipos-almuerzo")
router.register(r"planes-almuerzo", PlanAlmuerzoViewSet, basename="planes-almuerzo")
router.register(r"suscripciones", SuscripcionAlmuerzoViewSet, basename="suscripciones")
router.register(r"registros-consumo", RegistroConsumoAlmuerzoViewSet, basename="registros-consumo")
router.register(r"cuentas-mensuales", CuentaAlmuerzoMensualViewSet, basename="cuentas-mensuales")
router.register(r"pagos-cuentas", PagoCuentaAlmuerzoViewSet, basename="pagos-cuentas")
router.register(r"pagos-mensuales", PagoAlmuerzoMensualViewSet, basename="pagos-mensuales")
router.register(r"alergenos", AlergenoViewSet, basename="alergenos")
router.register(r"productos-alergenos", ProductoAlergenoViewSet, basename="productos-alergenos")
router.register(r"menu", MenuDiarioViewSet, basename="menu")

urlpatterns = [
    path("", include(router.urls)),
    path("reportes/", ReporteAlmuerzosView.as_view(), name="reporte-almuerzos"),
]