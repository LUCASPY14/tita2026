from django.urls import include, path

from rest_framework.routers import DefaultRouter

# URLs de compras ahora están centralizadas en api/v1/urls.py
# Este archivo se mantiene para compatibilidad legacy
router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
]
