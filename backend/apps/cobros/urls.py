"""
URLs para el módulo de cobros.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PagosClientesViewSet

router = DefaultRouter()
router.register(r"cobros", PagosClientesViewSet, basename="cobros")

urlpatterns = [
    path("", include(router.urls)),
]
