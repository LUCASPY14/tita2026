from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    EmpleadoViewSet,
    RolViewSet,
    PermisoViewSet,
    RolPermisoViewSet,
    PerfilUsuarioViewSet,
)

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"empleados", EmpleadoViewSet, basename="empleados")
router.register(r"roles", RolViewSet, basename="roles")
router.register(r"permisos", PermisoViewSet, basename="permisos")
router.register(r"roles-permisos", RolPermisoViewSet, basename="roles-permisos")
router.register(r"perfiles", PerfilUsuarioViewSet, basename="perfiles")

urlpatterns = [
    path("", include(router.urls)),
]