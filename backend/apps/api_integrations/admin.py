"""
Configuración del panel de administración para api_integrations
Gestión de proveedores API, endpoints, webhooks, credenciales y logs
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ProveedoresApi,
    EndpointsApi,
    LogsLlamadasApi,
    CredencialesApi,
    LogsWebhooks,
    WebhookEndpoints,
)


# ============================================================================
# PROVEEDORES API
# ============================================================================
@admin.register(ProveedoresApi)
class ProveedoresApiAdmin(admin.ModelAdmin):
    """Panel de administración para Proveedores API"""

    list_display = (
        "id_proveedor",
        "nombre",
        "tipo_servicio",
        "url_base",
        "version",
        "estado",
        "created_at",
    )

    list_filter = ("estado", "tipo_servicio", "tipo_auth", "created_at")

    search_fields = ("nombre", "descripcion", "url_base", "version", "tipo_servicio")

    readonly_fields = ("id_proveedor", "created_at")

    ordering = ["nombre"]

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("id_proveedor", "nombre", "descripcion", "tipo_servicio")},
        ),
        (
            "Configuración de API",
            {"fields": ("url_base", "version", "documentacion", "timeout", "max_reintentos")},
        ),
        ("Autenticación", {"fields": ("tipo_auth", "config_auth")}),
        ("Estado", {"fields": ("estado", "created_at")}),
    )

    def tipo_servicio_badge(self, obj):
        colores = {
            "REST": "#28a745",  # Verde
            "SOAP": "#007bff",  # Azul
            "GraphQL": "#e83e8c",  # Rosa
            "WebSocket": "#fd7e14",  # Naranja
            "gRPC": "#6f42c1",  # Púrpura
            "XML-RPC": "#20c997",  # Teal
            "OData": "#6610f2",  # Índigo
        }
        color = colores.get(obj.tipo_servicio, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.tipo_servicio,
        )

    tipo_servicio_badge.short_description = "Tipo Servicio"

    def tipo_auth_badge(self, obj):
        colores = {
            "API_KEY": "#007bff",
            "OAuth2": "#28a745",
            "Bearer": "#17a2b8",
            "Basic": "#ffc107",
            "JWT": "#e83e8c",
            "None": "#6c757d",
            "HMAC": "#6f42c1",
            "Custom": "#fd7e14",
        }
        color = colores.get(obj.tipo_auth, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">🔐 {}</span>',
            color,
            obj.tipo_auth,
        )

    tipo_auth_badge.short_description = "Autenticación"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✓ estado')
        return format_html('<span style="color: red; font-weight: bold;">{}</span>', '✗ Inactivo')

    activo_badge.short_description = "Estado"


# ============================================================================
# ENDPOINTS API
# ============================================================================
@admin.register(EndpointsApi)
class EndpointsApiAdmin(admin.ModelAdmin):
    """Panel de administración para Endpoints API"""

    list_display = (
        "id_endpoint",
        "nombre",
        "proveedor_nombre",
        "metodo",
        "path",
        "requiere_auth",
        "estado",
    )

    list_filter = ("metodo", "requiere_auth", "estado", "id_proveedor")

    search_fields = ("nombre", "descripcion", "path")

    readonly_fields = ("id_endpoint",)

    raw_id_fields = ("id_proveedor",)

    fieldsets = (
        (
            "🔌 Información del Endpoint",
            {"fields": ("id_endpoint", "nombre", "descripcion", "id_proveedor")},
        ),
        ("🌐 Configuración HTTP", {"fields": ("path", "metodo", "headers", "parametros")}),
        ("📋 Esquemas", {"fields": ("schema_request", "schema_response")}),
        ("⚙️ Opciones", {"fields": ("requiere_auth", "cache_segundos", "estado")}),
    )

    def metodo_badge(self, obj):
        colores = {
            "GET": "#28a745",
            "POST": "#007bff",
            "PUT": "#ffc107",
            "DELETE": "#dc3545",
            "PATCH": "#17a2b8",
            "HEAD": "#6c757d",
            "OPTIONS": "#6f42c1",
        }
        color = colores.get(obj.metodo, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.metodo,
        )

    metodo_badge.short_description = "Método"

    def requiere_auth_badge(self, obj):
        if obj.requiere_auth:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{}</span>', '🔒 Requiere Auth'
            )
        return format_html('<span style="color: #6c757d;">{}</span>', '🔓 Público')

    requiere_auth_badge.short_description = "Autenticación"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✓ estado')
        return format_html('<span style="color: red; font-weight: bold;">{}</span>', '✗ Inactivo')

    activo_badge.short_description = "Estado"

    def proveedor_nombre(self, obj):
        return obj.id_proveedor.nombre if obj.id_proveedor else "-"

    proveedor_nombre.short_description = "Proveedor"


# ============================================================================
# LOGS LLAMADAS API
# ============================================================================
@admin.register(LogsLlamadasApi)
class LogsLlamadasApiAdmin(admin.ModelAdmin):
    """Panel de administración para Logs de Llamadas API"""

    list_display = (
        "id_log",
        "timestamp",
        "metodo",
        "url",
        "status_code",
        "tiempo_ms",
        "exitoso",
        "intento",
        "ip_origen",
    )

    list_filter = ("exitoso", "metodo", "timestamp", "status_code", "id_endpoint")

    search_fields = ("url", "error_msg", "ip_origen")

    readonly_fields = ("id_log", "timestamp")

    date_hierarchy = "timestamp"

    ordering = ["-timestamp"]

    fieldsets = (
        (
            "📊 Información del Log",
            {"fields": ("id_log", "timestamp", "id_endpoint", "id_empleado")},
        ),
        ("📤 Request", {"fields": ("metodo", "url", "headers_req", "payload_req", "bytes_sent")}),
        (
            "📥 Response",
            {"fields": ("status_code", "headers_res", "payload_res", "bytes_received")},
        ),
        ("⏱️ Rendimiento", {"fields": ("tiempo_ms", "exitoso", "intento")}),
        ("🔍 Detalles", {"fields": ("error_msg", "ip_origen", "contexto")}),
    )

    def metodo_badge(self, obj):
        colores = {
            "GET": "#28a745",
            "POST": "#007bff",
            "PUT": "#ffc107",
            "DELETE": "#dc3545",
            "PATCH": "#17a2b8",
        }
        color = colores.get(obj.metodo, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.metodo,
        )

    metodo_badge.short_description = "Método"

    def url_corta(self, obj):
        if len(obj.url) > 50:
            return obj.url[:47] + "..."
        return obj.url

    url_corta.short_description = "URL"

    def status_badge(self, obj):
        if 200 <= obj.status_code < 300:
            color = "#28a745"  # Verde
        elif 300 <= obj.status_code < 400:
            color = "#17a2b8"  # Azul claro
        elif 400 <= obj.status_code < 500:
            color = "#ffc107"  # Amarillo
        else:
            color = "#dc3545"  # Rojo

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-weight: bold; font-size: 10px;">{}</span>',
            color,
            obj.status_code,
        )

    status_badge.short_description = "Status"

    def exitoso_badge(self, obj):
        if obj.exitoso:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✓ OK')
        return format_html('<span style="color: red; font-weight: bold;">{}</span>', '✗ Error')

    exitoso_badge.short_description = "Resultado"

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs existentes"""
        return False


# ============================================================================
# CREDENCIALES API
# ============================================================================
@admin.register(CredencialesApi)
class CredencialesApiAdmin(admin.ModelAdmin):
    """Panel de administración para Credenciales API"""

    list_display = (
        "id_credencial",
        "proveedor_nombre",
        "ambiente",
        "tiene_api_key",
        "tiene_secret",
        "tiene_token",
        "fecha_expiracion",
        "estado",
        "updated_at",
    )

    list_filter = ("estado", "ambiente", "id_proveedor", "fecha_expiracion", "updated_at")

    search_fields = ("id_proveedor__nombre",)

    readonly_fields = ("id_credencial", "updated_at")

    fieldsets = (
        ("🔑 Información de Credencial", {"fields": ("id_credencial", "id_proveedor", "ambiente")}),
        (
            "🔐 Credenciales (Sensible)",
            {"fields": ("api_key", "secret", "token"), "classes": ("collapse",)},
        ),
        ("⚙️ Configuración", {"fields": ("configuracion", "fecha_expiracion")}),
        ("📅 Estado", {"fields": ("estado", "updated_at")}),
    )

    def ambiente_badge(self, obj):
        colores = {
            "development": "#6c757d",
            "staging": "#ffc107",
            "production": "#dc3545",
            "testing": "#17a2b8",
        }
        color = colores.get(obj.ambiente, "#6c757d")
        iconos = {"development": "🛠️", "staging": "🚧", "production": "🔴", "testing": "🧪"}
        icono = iconos.get(obj.ambiente, "📌")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{} {}</span>',
            color,
            icono,
            obj.ambiente.upper(),
        )

    ambiente_badge.short_description = "Ambiente"

    def tiene_api_key(self, obj):
        if obj.api_key:
            return format_html('<span style="color: green;">{}</span>', '✓')
        return format_html('<span style="color: #ccc;">{}</span>', '—')

    tiene_api_key.short_description = "API Key"

    def tiene_secret(self, obj):
        if obj.secret:
            return format_html('<span style="color: green;">{}</span>', '✓')
        return format_html('<span style="color: #ccc;">{}</span>', '—')

    tiene_secret.short_description = "Secret"

    def tiene_token(self, obj):
        if obj.token:
            return format_html('<span style="color: green;">{}</span>', '✓')
        return format_html('<span style="color: #ccc;">{}</span>', '—')

    tiene_token.short_description = "Token"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✓ estado')
        return format_html('<span style="color: red; font-weight: bold;">{}</span>', '✗ Inactivo')

    activo_badge.short_description = "Estado"

    def proveedor_nombre(self, obj):
        return obj.id_proveedor.nombre if obj.id_proveedor else "-"

    proveedor_nombre.short_description = "Proveedor"


# ============================================================================
# LOGS WEBHOOKS
# ============================================================================
@admin.register(LogsWebhooks)
class LogsWebhooksAdmin(admin.ModelAdmin):
    """Panel de administración para Logs de Webhooks"""

    list_display = (
        "id_log",
        "timestamp",
        "evento_tipo",
        "ip_origen",
        "verificacion_ok",
        "procesado_ok",
        "tiempo_proc_ms",
        "id_webhook",
    )

    list_filter = ("verificacion_ok", "procesado_ok", "timestamp", "evento_tipo", "id_webhook")

    search_fields = ("evento_tipo", "ip_origen", "error_msg", "user_agent")

    readonly_fields = ("id_log", "timestamp", "payload", "headers")

    date_hierarchy = "timestamp"

    fieldsets = (
        (
            "📨 Información del Webhook",
            {"fields": ("id_log", "timestamp", "id_webhook", "evento_tipo")},
        ),
        ("📬 Datos Recibidos", {"fields": ("headers", "payload", "ip_origen", "user_agent")}),
        (
            "✅ Procesamiento",
            {"fields": ("verificacion_ok", "procesado_ok", "tiempo_proc_ms", "error_msg")},
        ),
    )

    def verificacion_badge(self, obj):
        if obj.verificacion_ok:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verificado</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ No Verificado</span>')

    verificacion_badge.short_description = "Verificación"

    def procesado_badge(self, obj):
        if obj.procesado_ok:
            return format_html('<span style="color: green; font-weight: bold;">✓ Procesado</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Error</span>')

    procesado_badge.short_description = "Procesamiento"

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs existentes"""
        return False


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================
@admin.register(WebhookEndpoints)
class WebhookEndpointsAdmin(admin.ModelAdmin):
    """Panel de administración para Webhook Endpoints"""

    list_display = (
        "id_webhook",
        "nombre",
        "proveedor_nombre",
        "path",
        "requiere_verificacion",
        "estado",
        "created_at",
    )

    list_filter = ("estado", "requiere_verificacion", "id_proveedor", "created_at")

    search_fields = ("nombre", "descripcion", "path", "handler_func")

    readonly_fields = ("id_webhook", "created_at")

    fieldsets = (
        (
            "🔗 Información del Webhook",
            {"fields": ("id_webhook", "nombre", "descripcion", "id_proveedor")},
        ),
        ("🌐 Configuración", {"fields": ("path", "eventos", "handler_func")}),
        (
            "🔒 Seguridad",
            {"fields": ("requiere_verificacion", "secret_key", "header_verificacion")},
        ),
        ("⚙️ Estado", {"fields": ("estado", "created_at")}),
    )

    def requiere_verificacion_badge(self, obj):
        if obj.requiere_verificacion:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">🔒 Verificación Req.</span>'
            )
        return format_html('<span style="color: #6c757d;">🔓 Sin Verificación</span>')

    requiere_verificacion_badge.short_description = "Verificación"

    def eventos_count(self, obj):
        if isinstance(obj.eventos, list):
            count = len(obj.eventos)
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 2px 6px; '
                'border-radius: 3px; font-size: 10px;">{} eventos</span>',
                count,
            )
        return "—"

    eventos_count.short_description = "Eventos"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ estado</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactivo</span>')

    activo_badge.short_description = "Estado"

    def proveedor_nombre(self, obj):
        return obj.id_proveedor.nombre if obj.id_proveedor else "-"

    proveedor_nombre.short_description = "Proveedor"
