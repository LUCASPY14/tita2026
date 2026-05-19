from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    EmpleadoViewSet,
    RolViewSet,
    PermisoViewSet,
    RolPermisoViewSet,
    PerfilUsuarioViewSet,
    PortalMiHijoView,
    RecuperarPasswordView,
    ConfirmarPasswordView,
    TwoFAEstadoView,
    TwoFAConfigurarView,
    TwoFAActivarView,
    TwoFAVerificarView,
    TwoFADesactivarView,
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
    path("recuperar-password/", RecuperarPasswordView.as_view(), name="recuperar-password"),
    path("recuperar-password/confirmar/", ConfirmarPasswordView.as_view(), name="confirmar-password"),
    path("portal/mi-hijo/", PortalMiHijoView.as_view(), name="portal-mi-hijo"),
    path("2fa/estado/", TwoFAEstadoView.as_view(), name="2fa-estado"),
    path("2fa/configurar/", TwoFAConfigurarView.as_view(), name="2fa-configurar"),
    path("2fa/activar/", TwoFAActivarView.as_view(), name="2fa-activar"),
    path("2fa/verificar/", TwoFAVerificarView.as_view(), name="2fa-verificar"),
    path("2fa/desactivar/", TwoFADesactivarView.as_view(), name="2fa-desactivar"),
]