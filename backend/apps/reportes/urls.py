from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PlantillaReporteViewSet

router = DefaultRouter()
router.register(r"plantillas", PlantillaReporteViewSet, basename="plantillas-reporte")

urlpatterns = [
    path("", include(router.urls)),
]