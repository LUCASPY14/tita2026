from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductosViewSet, CategoriasViewSet

router = DefaultRouter()
router.register(r'productos', ProductosViewSet, basename='productos')
router.register(r'categorias', CategoriasViewSet, basename='categorias')

urlpatterns = [
    path('', include(router.urls)),
]
