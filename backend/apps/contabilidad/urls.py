from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CajaViewSet,
    CierreCajaViewSet,
    MovimientoCajaViewSet,
    ConciliacionPagoViewSet,
    FacturaViewSet,
    DatosEmpresaViewSet,
)

router = DefaultRouter()
router.register(r"cajas", CajaViewSet, basename="cajas")
router.register(r"cierres-caja", CierreCajaViewSet, basename="cierres-caja")
router.register(r"movimientos-caja", MovimientoCajaViewSet, basename="movimientos-caja")
router.register(r"conciliaciones", ConciliacionPagoViewSet, basename="conciliaciones")
router.register(r"facturas", FacturaViewSet, basename="facturas")
router.register(r"datos-empresa", DatosEmpresaViewSet, basename="datos-empresa")

urlpatterns = [
    path("", include(router.urls)),
]