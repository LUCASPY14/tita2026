from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientesViewSet, HijosViewSet

router = DefaultRouter()
router.register(r'clientes', ClientesViewSet, basename='clientes')
router.register(r'hijos', HijosViewSet, basename='hijos')

urlpatterns = [
    path('', include(router.urls)),
]
