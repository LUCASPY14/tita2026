from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    TarjetaViewSet,
    MovimientoTarjetaViewSet,
    TarjetaAutorizacionViewSet,
    CargaSaldoViewSet,
    ConsumoTarjetaViewSet,
    MedioPagoViewSet,
    LimiteTransaccionViewSet,
    RegistroAutorizacionViewSet,
)

router = DefaultRouter()
router.register(r"tarjetas", TarjetaViewSet, basename="tarjetas")
router.register(r"movimientos-tarjeta", MovimientoTarjetaViewSet, basename="movimientos-tarjeta")
router.register(r"tarjetas-autorizacion", TarjetaAutorizacionViewSet, basename="tarjetas-autorizacion")
router.register(r"cargas-saldo", CargaSaldoViewSet, basename="cargas-saldo")
router.register(r"consumos", ConsumoTarjetaViewSet, basename="consumos")
router.register(r"medios-pago", MedioPagoViewSet, basename="medios-pago")
router.register(r"limites-transaccion", LimiteTransaccionViewSet, basename="limites-transaccion")
router.register(r"registros-autorizacion", RegistroAutorizacionViewSet, basename="registros-autorizacion")

urlpatterns = [
    path("", include(router.urls)),
]