from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    NotificacionViewSet,
    PreferenciaNotificacionViewSet,
    EmailEnviadoViewSet,
    SolicitudNotificacionViewSet,
    EnviarNotificacionView,
    VapidPublicKeyView,
    PushSubscriptionView,
    WAHAEstadoView,
)

router = DefaultRouter()
router.register(r"notificaciones", NotificacionViewSet, basename="notificaciones")
router.register(r"preferencias", PreferenciaNotificacionViewSet, basename="preferencias")
router.register(r"emails-enviados", EmailEnviadoViewSet, basename="emails-enviados")
router.register(r"solicitudes", SolicitudNotificacionViewSet, basename="solicitudes")

urlpatterns = [
    path("", include(router.urls)),
    path("enviar/",              EnviarNotificacionView.as_view(),  name="notificaciones-enviar"),
    path("vapid-public-key/",   VapidPublicKeyView.as_view(),      name="vapid-public-key"),
    path("push-subscription/",  PushSubscriptionView.as_view(),    name="push-subscription"),
    path("whatsapp-estado/",    WAHAEstadoView.as_view(),           name="whatsapp-estado"),
]
