from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlergenoViewSet,
    CuentaAlmuerzoMensualViewSet,
    DetalleMenuDiarioViewSet,
    MenuDiarioViewSet,
    PagoCuentaAlmuerzoViewSet,
    PagoAlmuerzoMensualViewSet,
    PlanAlmuerzoViewSet,
    PrecioAlmuerzoViewSet,
    ProductoAlergenoViewSet,
    RecargaSaldoAlmuerzoViewSet,
    RegistroConsumoAlmuerzoViewSet,
    ReporteAlmuerzosView,
    ReporteConsumoGradoView,
    ReporteCobranzaAlmuerzosView,
    SaldoAlmuerzoViewSet,
    SuscripcionAlmuerzoViewSet,
    TipoAlmuerzoViewSet,
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
router.register(r"saldos", SaldoAlmuerzoViewSet, basename="saldos-almuerzo")
router.register(r"recargas-saldo", RecargaSaldoAlmuerzoViewSet, basename="recargas-saldo-almuerzo")
router.register(r"alergenos", AlergenoViewSet, basename="alergenos")
router.register(r"productos-alergenos", ProductoAlergenoViewSet, basename="productos-alergenos")
router.register(r"menu", MenuDiarioViewSet, basename="menu")
router.register(r"detalle-menu", DetalleMenuDiarioViewSet, basename="detalle-menu")

urlpatterns = [
    path("", include(router.urls)),
    path("reportes/", ReporteAlmuerzosView.as_view(), name="reporte-almuerzos"),
    path("reporte-consumo-grado/", ReporteConsumoGradoView.as_view(), name="reporte-consumo-grado"),
    path("reporte-cobranza/", ReporteCobranzaAlmuerzosView.as_view(), name="reporte-cobranza-almuerzos"),
]
