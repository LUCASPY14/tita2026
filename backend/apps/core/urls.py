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
    ReporteTarjetasView,
)
from .bancard_views import (
    bancard_iniciar,
    bancard_iniciar_almuerzo,
    bancard_confirmar,
    bancard_retorno,
    bancard_estado,
    bancard_catastro_tarjeta,
    bancard_retorno_catastro,
    bancard_listar_tarjetas,
    bancard_eliminar_tarjeta,
    bancard_pagar_con_tarjeta,
    bancard_pagar_almuerzo_con_tarjeta,
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
    path("reporte-tarjetas/", ReporteTarjetasView.as_view(), name="reporte-tarjetas"),
    # Bancard vPOS
    path("bancard/iniciar/",              bancard_iniciar,              name="bancard-iniciar"),
    path("bancard/iniciar-almuerzo/",     bancard_iniciar_almuerzo,     name="bancard-iniciar-almuerzo"),
    path("bancard/confirmar/",            bancard_confirmar,            name="bancard-confirmar"),
    path("bancard/retorno/",              bancard_retorno,              name="bancard-retorno"),
    path("bancard/estado/<str:shop_process_id>/", bancard_estado,       name="bancard-estado"),
    # Bancard — tarjetas guardadas (catastro y pago con token)
    path("bancard/tarjetas/catastro/",           bancard_catastro_tarjeta,        name="bancard-catastro-tarjeta"),
    path("bancard/tarjetas/retorno-catastro/",   bancard_retorno_catastro,        name="bancard-retorno-catastro"),
    path("bancard/tarjetas/",                    bancard_listar_tarjetas,         name="bancard-listar-tarjetas"),
    path("bancard/tarjetas/<int:card_id>/",      bancard_eliminar_tarjeta,        name="bancard-eliminar-tarjeta"),
    path("bancard/pagar-con-tarjeta/",           bancard_pagar_con_tarjeta,       name="bancard-pagar-con-tarjeta"),
    path("bancard/pagar-almuerzo-con-tarjeta/",  bancard_pagar_almuerzo_con_tarjeta, name="bancard-pagar-almuerzo-con-tarjeta"),
]
