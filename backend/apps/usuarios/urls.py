from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    EmpleadoViewSet,
    RolViewSet,
    PortalMiHijoView,
    PortalHistorialConsumos,
    PortalHistorialCantina,
    PortalMisFacturas,
    RecuperarPasswordView,
    ConfirmarPasswordView,
    TwoFAEstadoView,
    TwoFAConfigurarView,
    TwoFAActivarView,
    TwoFAVerificarView,
    TwoFADesactivarView,
    TwoFALoginVerificarView,
    WebAuthnRegistrarOpcionesView,
    WebAuthnRegistrarVerificarView,
    WebAuthnLoginOpcionesView,
    WebAuthnLoginVerificarView,
    WebAuthnDesactivarView,
    LogoutView,
    ReporteAuditoriaView,
    AuditoriaOpcionesView,
    ReporteIntentosLoginView,
    ReportePersonalInactivoView,
)

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"empleados", EmpleadoViewSet, basename="empleados")
router.register(r"roles", RolViewSet, basename="roles")

urlpatterns = [
    path("", include(router.urls)),
    path("recuperar-password/", RecuperarPasswordView.as_view(), name="recuperar-password"),
    path("recuperar-password/confirmar/", ConfirmarPasswordView.as_view(), name="confirmar-password"),
    path("portal/mi-hijo/", PortalMiHijoView.as_view(), name="portal-mi-hijo"),
    path("portal/historial-consumos/", PortalHistorialConsumos.as_view(), name="portal-historial"),
    path("portal/historial-cantina/", PortalHistorialCantina.as_view(), name="portal-historial-cantina"),
    path("portal/mis-facturas/", PortalMisFacturas.as_view(), name="portal-facturas"),
    path("2fa/estado/", TwoFAEstadoView.as_view(), name="2fa-estado"),
    path("2fa/configurar/", TwoFAConfigurarView.as_view(), name="2fa-configurar"),
    path("2fa/activar/", TwoFAActivarView.as_view(), name="2fa-activar"),
    path("2fa/verificar/", TwoFAVerificarView.as_view(), name="2fa-verificar"),
    path("2fa/desactivar/", TwoFADesactivarView.as_view(), name="2fa-desactivar"),
    path("2fa/login/", TwoFALoginVerificarView.as_view(), name="2fa-login"),
    path("webauthn/registrar-opciones/", WebAuthnRegistrarOpcionesView.as_view(), name="webauthn-registrar-opciones"),
    path("webauthn/registrar-verificar/", WebAuthnRegistrarVerificarView.as_view(), name="webauthn-registrar-verificar"),
    path("webauthn/login-opciones/", WebAuthnLoginOpcionesView.as_view(), name="webauthn-login-opciones"),
    path("webauthn/login-verificar/", WebAuthnLoginVerificarView.as_view(), name="webauthn-login-verificar"),
    path("webauthn/desactivar/", WebAuthnDesactivarView.as_view(), name="webauthn-desactivar"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("reporte-auditoria/", ReporteAuditoriaView.as_view(), name="reporte-auditoria"),
    path("reporte-auditoria/opciones/", AuditoriaOpcionesView.as_view(), name="reporte-auditoria-opciones"),
    path("reporte-intentos-login/", ReporteIntentosLoginView.as_view(), name="reporte-intentos-login"),
    path("reporte-personal-inactivo/", ReportePersonalInactivoView.as_view(), name="reporte-personal-inactivo"),
]
