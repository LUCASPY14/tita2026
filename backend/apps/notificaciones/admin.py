from django.contrib import admin
from .models import (
    NotificacionesPortal,
    EmailsEnviados,
    SmsEnviados,
    PlantillasEmail,
    AlertasAutomaticas,
    AlertasSistema
)

@admin.register(NotificacionesPortal)
class NotificacionesPortalAdmin(admin.ModelAdmin):
    list_display = ['id_notificacion', 'tipo', 'titulo', 'id_usuario_portal', 'fecha_envio', 'leida']
    list_filter = ['tipo', 'leida', 'fecha_envio']
    search_fields = ['titulo', 'mensaje']
    ordering = ['-fecha_envio']

@admin.register(EmailsEnviados)
class EmailsEnviadosAdmin(admin.ModelAdmin):
    list_display = ['id_email', 'email_destinatario', 'nombre_destinatario', 'asunto', 'estado', 'fecha_envio']
    list_filter = ['estado', 'fecha_envio']
    search_fields = ['email_destinatario', 'asunto']
    ordering = ['-fecha_envio']

@admin.register(SmsEnviados)
class SmsEnviadosAdmin(admin.ModelAdmin):
    list_display = ['id_sms', 'telefono', 'mensaje', 'estado', 'fecha_envio']
    list_filter = ['estado', 'fecha_envio']
    search_fields = ['telefono', 'mensaje']
    ordering = ['-fecha_envio']

@admin.register(PlantillasEmail)
class PlantillasEmailAdmin(admin.ModelAdmin):
    list_display = ['id_template', 'codigo', 'nombre', 'categoria', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['codigo', 'nombre', 'asunto']
    ordering = ['categoria', 'nombre']

@admin.register(AlertasAutomaticas)
class AlertasAutomaticasAdmin(admin.ModelAdmin):
    list_display = ['id_alerta', 'nombre', 'tipo_alerta', 'criticidad', 'activo']
    list_filter = ['tipo_alerta', 'criticidad', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['criticidad', 'nombre']

@admin.register(AlertasSistema)
class AlertasSistemaAdmin(admin.ModelAdmin):
    list_display = ['id_alerta', 'tipo', 'mensaje', 'fecha_creacion', 'estado']
    list_filter = ['tipo', 'estado', 'fecha_creacion']
    search_fields = ['mensaje']
    ordering = ['-fecha_creacion']
