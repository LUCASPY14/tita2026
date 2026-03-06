"""
Serializers para app de Notificaciones
"""

from rest_framework import serializers
from .models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion,
    EmailsEnviados,
    SmsEnviados,
)


class NotificacionPortalSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones del portal"""

    class Meta:
        model = NotificacionesPortal
        fields = [
            "id_notificacion",
            "tipo",
            "titulo",
            "mensaje",
            "leida",
            "fecha_envio",
            "fecha_lectura",
            "creado_en",
            "id_usuario_portal",
        ]


class NotificacionSaldoSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones de saldo"""

    hijo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = NotificacionesSaldo
        fields = [
            "id_notificacion",
            "tipo_notificacion",
            "saldo_actual",
            "mensaje",
            "enviada_email",
            "enviada_sms",
            "leida",
            "email_destinatario",
            "fecha_creacion",
            "fecha_envio",
            "nro_tarjeta",
            "hijo_nombre",
        ]

    def get_hijo_nombre(self, obj):
        try:
            hijo = obj.nro_tarjeta.id_hijo
            return f"{hijo.nombre} {hijo.apellido}"
        except:
            return None


class AlertaSistemaSerializer(serializers.ModelSerializer):
    """Serializer para alertas del sistema"""

    empleado_nombre = serializers.SerializerMethodField()

    class Meta:
        model = AlertasSistema
        fields = [
            "id_alerta",
            "tipo",
            "mensaje",
            "fecha_creacion",
            "fecha_leida",
            "estado",
            "id_empleado_resuelve",
            "fecha_resolucion",
            "observaciones",
            "empleado_nombre",
        ]

    def get_empleado_nombre(self, obj):
        # Por ahora retorna None, se puede implementar después
        return None


class PreferenciasNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para preferencias de notificación"""

    class Meta:
        model = PreferenciasNotificacion
        fields = [
            "id_preferencia",
            "tipo_notificacion",
            "email_activo",
            "push_activo",
            "creado_en",
            "actualizado_en",
            "id_usuario_portal",
        ]


class EmailEnviadoSerializer(serializers.ModelSerializer):
    """Serializer para emails enviados"""

    class Meta:
        model = EmailsEnviados
        fields = [
            "id_email",
            "email_destinatario",
            "nombre_destinatario",
            "asunto",
            "estado",
            "fecha_envio",
            "fecha_entrega",
            "fecha_apertura",
            "mensaje_error",
            "intentos",
        ]


class SMSEnviadoSerializer(serializers.ModelSerializer):
    """Serializer para SMS enviados"""

    class Meta:
        model = SmsEnviados
        fields = [
            "id_sms",
            "telefono",
            "mensaje",
            "estado",
            "fecha_envio",
            "fecha_entrega",
            "costo",
        ]
