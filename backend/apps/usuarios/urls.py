"""
URLs para el módulo de usuarios
Incluye autenticación, 2FA, sesiones, permisos y CRUD
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny

from .views import (
    AuthViewSet,
    TwoFactorViewSet,
    SesionesViewSet,
    PasswordRecoveryViewSet,
    PermisosViewSet,
    RolesViewSet,
    EmpleadosViewSet,
    PerfilesUsuarioViewSet,
    UsuariosPortalViewSet,
    PortalAuthViewSet,
    AuditoriaOperacionesViewSet,
)


class PublicRolesViewSet(RolesViewSet):
    """Public read-only alias for RolesViewSet (used by /api/usuarios/ routes)."""

    permission_classes = [AllowAny]
    pagination_class = None


class PublicEmpleadosViewSet(EmpleadosViewSet):
    """Public read-only alias for EmpleadosViewSet (used by /api/usuarios/ routes)."""

    permission_classes = [AllowAny]
    pagination_class = None


# Router principal
router = DefaultRouter()

# Registrar ViewSets CRUD (public versions for /api/usuarios/ path)
router.register(r"roles", PublicRolesViewSet, basename="usuarios-roles")
router.register(r"empleados", PublicEmpleadosViewSet, basename="usuarios-empleados")
router.register(r"perfiles", PerfilesUsuarioViewSet, basename="perfiles")
router.register(r"portal", UsuariosPortalViewSet, basename="portal")
router.register(r"portal-auth", PortalAuthViewSet, basename="portal-auth")

# Registrar ViewSets de funcionalidad
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"2fa", TwoFactorViewSet, basename="2fa")
router.register(r"sesiones", SesionesViewSet, basename="sesiones")
router.register(r"password", PasswordRecoveryViewSet, basename="password")
router.register(r"permisos", PermisosViewSet, basename="permisos")
router.register(r"auditoria", AuditoriaOperacionesViewSet, basename="auditoria")


urlpatterns = [
    path("", include(router.urls)),
]
