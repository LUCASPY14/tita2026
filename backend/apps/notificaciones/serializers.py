"""
Serializers para la app notificaciones
"""

from rest_framework import serializers

from .models import (
    Notificacion,
    PreferenciaNotificacion,
    PlantillaEmail,
    EmailEnviado,
    SolicitudNotificacion,
)


class NotificacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre_completo", read_only=True)

    class Meta:
        model = Notificacion
        fields = "__all__"
        read_only_fields = ["fecha_envio", "fecha_lectura", "fecha_creacion"]


class PreferenciaNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciaNotificacion
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "fecha_actualizacion"]


class PlantillaEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantillaEmail
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "fecha_actualizacion"]


class EmailEnviadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailEnviado
        fields = "__all__"
        read_only_fields = ["fecha_envio", "fecha_entrega", "fecha_apertura", "fecha_creacion"]


class SolicitudNotificacionSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)

    class Meta:
        model = SolicitudNotificacion
        fields = "__all__"
        read_only_fields = ["fecha_solicitud", "fecha_envio"]