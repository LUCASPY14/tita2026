"""
Admin para la app api_integrations
Gestión de proveedores API, endpoints, credenciales, webhooks y logs
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    ProveedorApi,
    EndpointApi,
    CredencialApi,
    WebhookEndpoint,
    LogLlamadaApi,
    LogWebhook,
)


# ==============================================================================
# PROVEEDOR DE API
# ==============================================================================

@admin.register(ProveedorApi)
class ProveedorApiAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "tipo_servicio_badge",
        "url_base",
        "tipo_auth_badge",
        "activo",
    ]
    list_filter = ["activo", "tipo_servicio", "tipo_auth"]
    search_fields = ["nombre", "url_base"]
    readonly_fields = ["fecha_creacion"]
    fieldsets = (
        ("Datos del Proveedor", {
            "fields": ("nombre", "descripcion", "tipo_servicio", "activo")
        }),
        ("Conexión", {
            "fields": ("url_base", "version", "documentacion")
        }),
        ("Autenticación", {
            "fields": ("tipo_auth", "config_auth")
        }),
        ("Configuración", {
            "fields": ("timeout", "max_reintentos")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def tipo_servicio_badge(self, obj):
        colors = {
            "PAGOS_QR": "#28a745",
            "BANCO": "#0d6efd",
            "NOTIFICACIONES": "#ffc107",
            "OTRO": "#6c757d",
        }
        color = colors.get(obj.tipo_servicio, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_servicio_display(),
        )
    tipo_servicio_badge.short_description = "Tipo Servicio"

    def tipo_auth_badge(self, obj):
        return format_html(
            '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
            obj.get_tipo_auth_display(),
        )
    tipo_auth_badge.short_description = "Auth"


# ==============================================================================
# ENDPOINT DE API
# ==============================================================================

@admin.register(EndpointApi)
class EndpointApiAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "nombre",
        "metodo_badge",
        "path",
        "activo",
    ]
    list_filter = ["activo", "proveedor", "metodo"]
    search_fields = ["nombre", "path", "proveedor__nombre"]
    list_select_related = ["proveedor"]

    def proveedor_link(self, obj):
        url = reverse("admin:api_integrations_proveedorapi_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.nombre)
    proveedor_link.short_description = "Proveedor"

    def metodo_badge(self, obj):
        colors = {
            "GET": "#28a745",
            "POST": "#0d6efd",
            "PUT": "#ffc107",
            "PATCH": "#fd7e14",
            "DELETE": "#dc3545",
        }
        color = colors.get(obj.metodo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_metodo_display(),
        )
    metodo_badge.short_description = "Método"


# ==============================================================================
# CREDENCIAL DE API
# ==============================================================================

@admin.register(CredencialApi)
class CredencialApiAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "ambiente_badge",
        "activo",
        "fecha_actualizacion",
    ]
    list_filter = ["activo", "ambiente", "proveedor"]
    search_fields = ["proveedor__nombre"]
    readonly_fields = ["fecha_actualizacion"]
    list_select_related = ["proveedor"]
    fieldsets = (
        ("Datos de la Credencial", {
            "fields": ("proveedor", "ambiente", "activo")
        }),
        ("Claves (ocultas en lista)", {
            "fields": ("api_key", "secret", "token"),
        }),
        ("Configuración", {
            "fields": ("configuracion", "fecha_expiracion")
        }),
        ("Auditoría", {
            "fields": ("fecha_actualizacion",),
            "classes": ("collapse",),
        }),
    )

    def proveedor_link(self, obj):
        url = reverse("admin:api_integrations_proveedorapi_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.nombre)
    proveedor_link.short_description = "Proveedor"

    def ambiente_badge(self, obj):
        colors = {"SANDBOX": "#ffc107", "PRODUCCION": "#28a745"}
        color = colors.get(obj.ambiente, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_ambiente_display(),
        )
    ambiente_badge.short_description = "Ambiente"


# ==============================================================================
# WEBHOOK ENDPOINT
# ==============================================================================

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "nombre",
        "path",
        "requiere_verificacion_badge",
        "activo",
    ]
    list_filter = ["activo", "requiere_verificacion", "proveedor"]
    search_fields = ["nombre", "path", "proveedor__nombre"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["proveedor"]
    fieldsets = (
        ("Datos del Webhook", {
            "fields": ("proveedor", "nombre", "descripcion", "path", "activo")
        }),
        ("Verificación", {
            "fields": ("requiere_verificacion", "secret_key", "header_verificacion")
        }),
        ("Eventos", {
            "fields": ("eventos", "handler")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def proveedor_link(self, obj):
        url = reverse("admin:api_integrations_proveedorapi_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.nombre)
    proveedor_link.short_description = "Proveedor"

    def requiere_verificacion_badge(self, obj):
        if obj.requiere_verificacion:
            return format_html('<span style="color:#0d6efd;">✓</span>')
        return "-"
    requiere_verificacion_badge.short_description = "Verificación"


# ==============================================================================
# LOG DE LLAMADA API
# ==============================================================================

@admin.register(LogLlamadaApi)
class LogLlamadaApiAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "metodo_badge",
        "url",
        "status_code_badge",
        "tiempo_ms",
        "exitoso",
        "timestamp",
    ]
    list_filter = ["metodo", "exitoso", "timestamp"]
    search_fields = ["url", "endpoint__nombre"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def get_readonly_fields(self, request, obj=None):
        """Log inmutable."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def metodo_badge(self, obj):
        colors = {
            "GET": "#28a745",
            "POST": "#0d6efd",
            "PUT": "#ffc107",
            "PATCH": "#fd7e14",
            "DELETE": "#dc3545",
        }
        color = colors.get(obj.metodo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.metodo,
        )
    metodo_badge.short_description = "Método"

    def status_code_badge(self, obj):
        if 200 <= obj.status_code < 300:
            color = "#28a745"
        elif 400 <= obj.status_code < 500:
            color = "#ffc107"
        else:
            color = "#dc3545"
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.status_code,
        )
    status_code_badge.short_description = "Status"


# ==============================================================================
# LOG DE WEBHOOK
# ==============================================================================

@admin.register(LogWebhook)
class LogWebhookAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "webhook_link",
        "evento_tipo",
        "verificacion_badge",
        "procesado_badge",
        "timestamp",
    ]
    list_filter = ["verificacion_ok", "procesado_ok", "evento_tipo", "timestamp"]
    search_fields = ["webhook__nombre", "evento_tipo", "ip_origen"]
    readonly_fields = ["timestamp"]
    list_select_related = ["webhook"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def get_readonly_fields(self, request, obj=None):
        """Log inmutable."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def webhook_link(self, obj):
        if obj.webhook:
            url = reverse("admin:api_integrations_webhookendpoint_change", args=[obj.webhook.pk])
            return format_html('<a href="{}">{}</a>', url, obj.webhook.nombre)
        return "-"
    webhook_link.short_description = "Webhook"

    def verificacion_badge(self, obj):
        if obj.verificacion_ok:
            return format_html('<span style="color:#28a745;">✓</span>')
        return format_html('<span style="color:#dc3545;">✗</span>')
    verificacion_badge.short_description = "Verificación"

    def procesado_badge(self, obj):
        if obj.procesado_ok:
            return format_html('<span style="color:#28a745;">✓</span>')
        return format_html('<span style="color:#dc3545;">✗</span>')
    procesado_badge.short_description = "Procesado"