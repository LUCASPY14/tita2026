"""
Serializers para la app api_integrations
"""

from rest_framework import serializers

from .models import (
    ProveedorApi,
    EndpointApi,
    CredencialApi,
    WebhookEndpoint,
    LogLlamadaApi,
    LogWebhook,
)


class ProveedorApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProveedorApi
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class EndpointApiSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)

    class Meta:
        model = EndpointApi
        fields = "__all__"


class CredencialApiSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)

    class Meta:
        model = CredencialApi
        fields = "__all__"
        read_only_fields = ["fecha_actualizacion"]


class WebhookEndpointSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)

    class Meta:
        model = WebhookEndpoint
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class LogLlamadaApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogLlamadaApi
        fields = "__all__"
        read_only_fields = ["timestamp"]


class LogWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogWebhook
        fields = "__all__"
        read_only_fields = ["timestamp"]
