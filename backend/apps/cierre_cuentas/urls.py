from rest_framework.routers import DefaultRouter

from .views import CierreCuentaViewSet, ResolucionSaldoViewSet

router = DefaultRouter()
router.register(r"cierres", CierreCuentaViewSet, basename="cierres-cuenta")
router.register(r"resoluciones", ResolucionSaldoViewSet, basename="resoluciones-saldo")

urlpatterns = router.urls
