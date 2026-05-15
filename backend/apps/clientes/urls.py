from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClienteViewSet,
    CuentaCorrienteClienteViewSet,
    TipoClienteViewSet,
    HijoViewSet,
    GradoViewSet,
    HistorialGradoViewSet,
    RestriccionHijoViewSet,
    AutorizacionSaldoNegativoViewSet,
    PaisViewSet,
    CiudadViewSet,
)

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet, basename="clientes")
router.register(r"cuentas-corrientes", CuentaCorrienteClienteViewSet, basename="cuentas-corrientes")
router.register(r"tipos-cliente", TipoClienteViewSet, basename="tipos-cliente")
router.register(r"hijos", HijoViewSet, basename="hijos")
router.register(r"grados", GradoViewSet, basename="grados")
router.register(r"historial-grados", HistorialGradoViewSet, basename="historial-grados")
router.register(r"restricciones", RestriccionHijoViewSet, basename="restricciones")
router.register(r"autorizaciones-saldo", AutorizacionSaldoNegativoViewSet, basename="autorizaciones-saldo")
router.register(r"paises", PaisViewSet, basename="paises")
router.register(r"ciudades", CiudadViewSet, basename="ciudades")

urlpatterns = [
    path("", include(router.urls)),
]