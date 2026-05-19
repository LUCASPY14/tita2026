"""
Views para la app api_integrations
"""

from rest_framework import viewsets

from common.permissions import IsAdmin

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ProveedorApi,
    EndpointApi,
    CredencialApi,
    WebhookEndpoint,
    LogLlamadaApi,
    LogWebhook,
)
from .serializers import (
    ProveedorApiSerializer,
    EndpointApiSerializer,
    CredencialApiSerializer,
    WebhookEndpointSerializer,
    LogLlamadaApiSerializer,
    LogWebhookSerializer,
)


class ProveedorApiViewSet(viewsets.ModelViewSet):
    queryset = ProveedorApi.objects.all()
    serializer_class = ProveedorApiSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "tipo_servicio"]


class EndpointApiViewSet(viewsets.ModelViewSet):
    queryset = EndpointApi.objects.select_related("proveedor").all()
    serializer_class = EndpointApiSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "activo"]


class CredencialApiViewSet(viewsets.ModelViewSet):
    queryset = CredencialApi.objects.select_related("proveedor").all()
    serializer_class = CredencialApiSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "ambiente", "activo"]


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    queryset = WebhookEndpoint.objects.select_related("proveedor").all()
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "activo"]


class LogLlamadaApiViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogLlamadaApi.objects.select_related("endpoint").all()
    serializer_class = LogLlamadaApiSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["endpoint", "exitoso", "metodo"]


class LogWebhookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogWebhook.objects.select_related("webhook").all()
    serializer_class = LogWebhookSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["webhook", "procesado_ok", "evento_tipo"]