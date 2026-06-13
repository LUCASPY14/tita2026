"""
Admin para la app notificaciones
Gestión de notificaciones, plantillas, preferencias y emails
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Notificacion,
    PreferenciaNotificacion,
    PlantillaEmail,
    EmailEnviado,
    SolicitudNotificacion,
)


# ==============================================================================
# NOTIFICACIÓN
# ==============================================================================

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "usuario_link",
        "tipo_badge",
        "titulo",
        "destino_badge",
        "leida",
        "fecha_envio",
    ]
    list_filter = ["tipo", "destino", "leida", "fecha_envio"]
    search_fields = ["usuario__email", "usuario__nombre", "titulo", "mensaje"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["usuario"]
    date_hierarchy = "fecha_envio"
    ordering = ["-fecha_envio"]

    def get_readonly_fields(self, request, obj=None):
        """Notificación inmutable una vez creada."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.nombre_completo)
    usuario_link.short_description = "Usuario"

    def tipo_badge(self, obj):
        colors = {
            "SALDO_BAJO": "#dc3545",
            "RECARGA": "#28a745",
            "CONSUMO": "#0d6efd",
            "VENCIMIENTO": "#ffc107",
            "ALMUERZO": "#fd7e14",
            "SISTEMA": "#6c757d",
        }
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def destino_badge(self, obj):
        colors = {"EMAIL": "#0d6efd", "SISTEMA": "#17a2b8"}
        color = colors.get(obj.destino, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_destino_display(),
        )
    destino_badge.short_description = "Destino"


# ==============================================================================
# PREFERENCIA DE NOTIFICACIÓN
# ==============================================================================

@admin.register(PreferenciaNotificacion)
class PreferenciaNotificacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "usuario_link",
        "tipo_notificacion",
        "email_activo",
        "sistema_activo",
    ]
    list_filter = ["email_activo", "sistema_activo", "tipo_notificacion"]
    search_fields = ["usuario__email", "tipo_notificacion"]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]
    list_select_related = ["usuario"]

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.nombre_completo)
    usuario_link.short_description = "Usuario"


# ==============================================================================
# PLANTILLA DE EMAIL
# ==============================================================================

@admin.register(PlantillaEmail)
class PlantillaEmailAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "categoria", "asunto", "activo"]
    list_filter = ["activo", "categoria"]
    search_fields = ["codigo", "nombre", "asunto"]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]

    fieldsets = (
        ("Identificación", {
            "fields": ("codigo", "nombre", "categoria", "activo")
        }),
        ("Contenido", {
            "fields": ("asunto", "cuerpo_html", "cuerpo_texto")
        }),
        ("Variables", {
            "fields": ("variables", "descripcion"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion", "fecha_actualizacion"),
            "classes": ("collapse",),
        }),
    )


# ==============================================================================
# EMAIL ENVIADO
# ==============================================================================

@admin.register(EmailEnviado)
class EmailEnviadoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "destinatario_email",
        "asunto",
        "estado_badge",
        "fecha_envio",
    ]
    list_filter = ["estado", "fecha_envio"]
    search_fields = ["destinatario_email", "destinatario_nombre", "asunto"]
    readonly_fields = ["fecha_creacion"]
    date_hierarchy = "fecha_envio"
    ordering = ["-fecha_envio"]
    fieldsets = (
        ("Datos del Email", {
            "fields": ("destinatario_email", "destinatario_nombre", "asunto")
        }),
        ("Contenido", {
            "fields": ("cuerpo",)
        }),
        ("Estado", {
            "fields": ("estado", "intentos", "mensaje_error")
        }),
        ("Seguimiento", {
            "fields": ("fecha_envio", "fecha_entrega", "fecha_apertura")
        }),
        ("Referencias", {
            "fields": ("plantilla", "cliente", "enviado_por"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Email enviado inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def estado_badge(self, obj):
        colors = {
            "ENVIADO": "#0d6efd",
            "ENTREGADO": "#28a745",
            "ABIERTO": "#17a2b8",
            "REBOTADO": "#dc3545",
            "ERROR": "#dc3545",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# SOLICITUD DE NOTIFICACIÓN
# ==============================================================================

@admin.register(SolicitudNotificacion)
class SolicitudNotificacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cliente_link",
        "tipo",
        "destino",
        "estado_badge",
        "fecha_solicitud",
    ]
    list_filter = ["estado", "destino", "fecha_solicitud"]
    search_fields = ["cliente__ruc_ci", "cliente__nombres", "mensaje"]
    readonly_fields = ["fecha_solicitud"]
    list_select_related = ["cliente"]
    date_hierarchy = "fecha_solicitud"
    ordering = ["-fecha_solicitud"]

    def get_readonly_fields(self, request, obj=None):
        """Solicitud inmutable una vez procesada."""
        if obj and obj.estado in ("ENVIADA", "FALLIDA"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def estado_badge(self, obj):
        colors = {"PENDIENTE": "#ffc107", "ENVIADA": "#28a745", "FALLIDA": "#dc3545"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"
