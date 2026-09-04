from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlumnoResponsableViewSet,
    AutorizacionSaldoNegativoViewSet,
    CiudadViewSet,
    ClienteViewSet,
    CuentaCorrienteClienteViewSet,
    DepartamentoViewSet,
    GradoViewSet,
    HistorialGradoViewSet,
    HijoViewSet,
    PaisViewSet,
    ReporteCuentaCorrienteView,
    RestriccionHijoViewSet,
    TipoClienteViewSet,
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
router.register(r"departamentos", DepartamentoViewSet, basename="departamentos")
router.register(r"ciudades", CiudadViewSet, basename="ciudades")
router.register(r"responsables", AlumnoResponsableViewSet, basename="responsables")

urlpatterns = [
    path("", include(router.urls)),
    path("reporte-cuenta-corriente/", ReporteCuentaCorrienteView.as_view(), name="reporte-cc"),
]
