from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProveedorApiViewSet,
    EndpointApiViewSet,
    CredencialApiViewSet,
    WebhookEndpointViewSet,
    LogLlamadaApiViewSet,
    LogWebhookViewSet,
)

router = DefaultRouter()
router.register(r"proveedores", ProveedorApiViewSet, basename="proveedores-api")
router.register(r"endpoints", EndpointApiViewSet, basename="endpoints-api")
router.register(r"credenciales", CredencialApiViewSet, basename="credenciales-api")
router.register(r"webhooks", WebhookEndpointViewSet, basename="webhooks")
router.register(r"logs-llamadas", LogLlamadaApiViewSet, basename="logs-llamadas")
router.register(r"logs-webhooks", LogWebhookViewSet, basename="logs-webhooks")

urlpatterns = [
    path("", include(router.urls)),
]
