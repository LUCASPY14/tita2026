"""
URLs para el módulo de usuarios
Incluye autenticación, 2FA, sesiones, permisos y CRUD
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AuthViewSet,
    TwoFactorViewSet,
    SesionesViewSet,
    PasswordRecoveryViewSet,
    PermisosViewSet,
    RolesViewSet,
    EmpleadosViewSet,
    PerfilesUsuarioViewSet,
    UsuariosPortalViewSet
)


# Router principal
router = DefaultRouter()

# Registrar ViewSets CRUD
router.register(r'roles', RolesViewSet, basename='roles')
router.register(r'empleados', EmpleadosViewSet, basename='empleados')
router.register(r'perfiles', PerfilesUsuarioViewSet, basename='perfiles')
router.register(r'portal', UsuariosPortalViewSet, basename='portal')

# Registrar ViewSets de funcionalidad
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'2fa', TwoFactorViewSet, basename='2fa')
router.register(r'sesiones', SesionesViewSet, basename='sesiones')
router.register(r'password', PasswordRecoveryViewSet, basename='password')
router.register(r'permisos', PermisosViewSet, basename='permisos')


urlpatterns = [
    path('', include(router.urls)),
]
