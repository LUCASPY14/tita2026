"""
Admin para la app core
Gestión de tarjetas, movimientos, medios de pago, límites de transacción y autorizaciones
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    TarjetaAutorizacion,
    CargaSaldo,
    ConsumoTarjeta,
    MedioPago,
    LimiteTransaccion,
    RegistroAutorizacion,
    PagoBancard,
    SolicitudCatastroBancard,
)


# ==============================================================================
# TARJETA
# ==============================================================================

@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = [
        "nro_tarjeta",
        "codigo_barras",
        "hijo_link",
        "saldo_display",
        "limite_credito_display",
        "estado_badge",
        "fecha_vencimiento",
    ]
    list_filter = ["estado", "permite_saldo_negativo"]
    search_fields = ["nro_tarjeta", "codigo_barras", "hijo__nombre", "hijo__apellido"]
    readonly_fields = ["fecha_creacion", "ultima_notificacion_saldo"]
    list_select_related = ["hijo"]
    fieldsets = (
        ("Datos de la Tarjeta", {
            "fields": ("nro_tarjeta", "codigo_barras", "hijo", "estado")
        }),
        ("Saldo y Crédito", {
            "fields": ("saldo_actual", "saldo_alerta", "limite_credito", "permite_saldo_negativo")
        }),
        ("Notificaciones", {
            "fields": ("notificar_saldo_bajo", "ultima_notificacion_saldo"),
            "classes": ("collapse",),
        }),
        ("Vigencia", {
            "fields": ("fecha_vencimiento", "fecha_creacion"),
        }),
    )

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"

    def saldo_display(self, obj):
        color = "#dc3545" if obj.saldo_actual < 0 else "#28a745"
        monto_formateado = "₲{:,.0f}".format(obj.saldo_actual)
        return format_html('<strong style="color:{};">{}</strong>', color, monto_formateado)
    saldo_display.short_description = "Saldo"

    def limite_credito_display(self, obj):
        return f"₲{obj.limite_credito:,.0f}"
    limite_credito_display.short_description = "Límite Crédito"

    def estado_badge(self, obj):
        colors = {
            "ACTIVA": "#28a745",
            "BLOQUEADA": "#ffc107",
            "VENCIDA": "#6c757d",
            "CANCELADA": "#dc3545",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# MOVIMIENTO DE TARJETA
# ==============================================================================

@admin.register(MovimientoTarjeta)
class MovimientoTarjetaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tarjeta_link",
        "tipo_badge",
        "monto_display",
        "saldo_resultante_display",
        "fecha",
    ]
    list_filter = ["tipo", "fecha"]
    search_fields = ["tarjeta__nro_tarjeta", "descripcion"]
    readonly_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]
    list_select_related = ["tarjeta"]
    date_hierarchy = "fecha"
    ordering = ["-fecha", "-id"]

    def get_readonly_fields(self, request, obj=None):
        """Movimiento inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def tarjeta_link(self, obj):
        url = reverse("admin:core_tarjeta_change", args=[obj.tarjeta.pk])
        return format_html('<a href="{}">{}</a>', url, obj.tarjeta.nro_tarjeta)
    tarjeta_link.short_description = "Tarjeta"

    def tipo_badge(self, obj):
        colors = {
            "RECARGA": "#28a745",
            "CONSUMO": "#dc3545",
            "AJUSTE": "#ffc107",
            "REVERSO": "#0d6efd",
        }
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def monto_display(self, obj):
        signo = "+" if obj.tipo in ("RECARGA", "REVERSO") else "-"
        return f"{signo}₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

    def saldo_resultante_display(self, obj):
        color = "#dc3545" if obj.saldo_resultante < 0 else "#28a745"
        return format_html('<strong style="color:{};">₲{:,}</strong>', color, obj.saldo_resultante)
    saldo_resultante_display.short_description = "Saldo Resultante"


# ==============================================================================
# TARJETA DE AUTORIZACIÓN
# ==============================================================================

@admin.register(TarjetaAutorizacion)
class TarjetaAutorizacionAdmin(admin.ModelAdmin):
    list_display = [
        "codigo_barra",
        "tipo_autorizacion",
        "empleado_link",
        "permisos_display",
        "activo",
        "fecha_vencimiento",
    ]
    list_filter = ["tipo_autorizacion", "activo"]
    search_fields = ["codigo_barra", "empleado__nombre", "empleado__apellido"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["empleado"]
    fieldsets = (
        ("Datos de la Tarjeta", {
            "fields": ("codigo_barra", "tipo_autorizacion", "empleado", "activo")
        }),
        ("Permisos", {
            "fields": (
                "puede_anular_almuerzos",
                "puede_anular_ventas",
                "puede_anular_recargas",
                "puede_modificar_precios",
            )
        }),
        ("Vigencia", {
            "fields": ("fecha_vencimiento", "fecha_creacion"),
        }),
        ("Observaciones", {
            "fields": ("observaciones",),
            "classes": ("collapse",),
        }),
    )

    def empleado_link(self, obj):
        if obj.empleado:
            url = reverse("admin:usuarios_usuario_change", args=[obj.empleado.pk])
            return format_html('<a href="{}">{}</a>', url, obj.empleado.nombre_completo)
        return "-"
    empleado_link.short_description = "Empleado"

    def permisos_display(self, obj):
        permisos = []
        if obj.puede_anular_almuerzos:
            permisos.append("Almuerzos")
        if obj.puede_anular_ventas:
            permisos.append("Ventas")
        if obj.puede_anular_recargas:
            permisos.append("Recargas")
        if obj.puede_modificar_precios:
            permisos.append("Precios")
        return ", ".join(permisos) if permisos else "-"
    permisos_display.short_description = "Permisos"


# ==============================================================================
# CARGA DE SALDO
# ==============================================================================

@admin.register(CargaSaldo)
class CargaSaldoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tarjeta_link",
        "cliente_origen_link",
        "monto_cargado_display",
        "estado_badge",
        "fecha_carga",
    ]
    list_filter = ["estado", "fecha_carga"]
    search_fields = ["tarjeta__nro_tarjeta", "referencia"]
    readonly_fields = [
        "fecha_carga",
        "fecha_confirmacion",
        "fecha_aprobacion",
        "pay_request_id",
        "tx_id",
        "custom_identifier",
        "numero_comprobante_externo",
        "referencia_externa",
        "fecha_creacion",
    ]
    list_select_related = ["tarjeta", "cliente_origen"]
    date_hierarchy = "fecha_carga"
    ordering = ["-fecha_carga"]
    fieldsets = (
        ("Datos de la Recarga", {
            "fields": ("tarjeta", "cliente_origen", "monto_cargado", "comision", "total_cobrado")
        }),
        ("Estado", {
            "fields": ("estado", "fecha_carga", "fecha_confirmacion", "fecha_aprobacion")
        }),
        ("Referencias", {
            "fields": ("referencia", "metodo_pago")
        }),
        ("Responsables", {
            "fields": ("responsable", "supervisor_aprobador")
        }),
        ("Pasarela de Pago (solo lectura)", {
            "fields": (
                "pay_request_id", "tx_id", "custom_identifier",
                "numero_comprobante_externo", "referencia_externa",
            ),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Campos de pasarela siempre readonly. Monto/tarjeta bloqueados en estados finales."""
        readonly = list(self.readonly_fields)
        if obj and obj.estado in ("CONFIRMADA", "RECHAZADA"):
            readonly.extend(["monto_cargado", "tarjeta", "cliente_origen"])
        return readonly

    def tarjeta_link(self, obj):
        if obj.tarjeta:
            url = reverse("admin:core_tarjeta_change", args=[obj.tarjeta.pk])
            return format_html('<a href="{}">{}</a>', url, obj.tarjeta.nro_tarjeta)
        return "-"
    tarjeta_link.short_description = "Tarjeta"

    def cliente_origen_link(self, obj):
        if obj.cliente_origen:
            url = reverse("admin:clientes_cliente_change", args=[obj.cliente_origen.pk])
            return format_html('<a href="{}">{}</a>', url, obj.cliente_origen.nombre_completo)
        return "-"
    cliente_origen_link.short_description = "Cliente Origen"

    def monto_cargado_display(self, obj):
        return f"₲{obj.monto_cargado:,.0f}"
    monto_cargado_display.short_description = "Monto"

    def estado_badge(self, obj):
        colors = {
            "PENDIENTE": "#ffc107",
            "CONFIRMADA": "#28a745",
            "RECHAZADA": "#dc3545",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# CONSUMO DE TARJETA
# ==============================================================================

@admin.register(ConsumoTarjeta)
class ConsumoTarjetaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tarjeta_link",
        "monto_consumido_display",
        "saldo_anterior_display",
        "saldo_posterior_display",
        "registrado_por_link",
        "detalle",
        "fecha_consumo",
    ]
    list_filter = ["fecha_consumo"]
    search_fields = ["tarjeta__nro_tarjeta", "detalle"]
    readonly_fields = ["fecha_consumo", "saldo_anterior", "saldo_posterior", "fecha_creacion"]
    list_select_related = ["tarjeta", "registrado_por"]
    date_hierarchy = "fecha_consumo"
    ordering = ["-fecha_consumo"]

    def get_readonly_fields(self, request, obj=None):
        """Registro inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def tarjeta_link(self, obj):
        url = reverse("admin:core_tarjeta_change", args=[obj.tarjeta.pk])
        return format_html('<a href="{}">{}</a>', url, obj.tarjeta.nro_tarjeta)
    tarjeta_link.short_description = "Tarjeta"

    def monto_consumido_display(self, obj):
        return f"-₲{obj.monto_consumido:,.0f}"
    monto_consumido_display.short_description = "Monto"

    def saldo_anterior_display(self, obj):
        return f"₲{obj.saldo_anterior:,.0f}"
    saldo_anterior_display.short_description = "Saldo Anterior"

    def saldo_posterior_display(self, obj):
        color = "#dc3545" if obj.saldo_posterior < 0 else "#28a745"
        return format_html('<strong style="color:{};">₲{:,}</strong>', color, obj.saldo_posterior)
    saldo_posterior_display.short_description = "Saldo Posterior"

    def registrado_por_link(self, obj):
        if obj.registrado_por:
            url = reverse("admin:usuarios_usuario_change", args=[obj.registrado_por.pk])
            return format_html('<a href="{}">{}</a>', url, obj.registrado_por.nombre_completo)
        return "-"
    registrado_por_link.short_description = "Registrado por"


# ==============================================================================
# MEDIO DE PAGO
# ==============================================================================

@admin.register(MedioPago)
class MedioPagoAdmin(admin.ModelAdmin):
    list_display = ["descripcion", "requiere_validacion_badge", "activo"]
    list_filter = ["activo", "requiere_validacion"]
    search_fields = ["descripcion"]

    def requiere_validacion_badge(self, obj):
        if obj.requiere_validacion:
            return mark_safe('<span style="color:#0d6efd;">✓</span>')  # nosec B308
        return "-"
    requiere_validacion_badge.short_description = "Validación"


# ==============================================================================
# LÍMITE DE TRANSACCIÓN
# ==============================================================================

@admin.register(LimiteTransaccion)
class LimiteTransaccionAdmin(admin.ModelAdmin):
    list_display = [
        "rol_link",
        "tipo_operacion_badge",
        "monto_maximo_display",
        "doble_autorizacion_badge",
        "activo",
    ]
    list_filter = ["rol", "tipo_operacion", "requiere_autorizacion_doble", "activo"]
    search_fields = ["rol__nombre_rol"]
    readonly_fields = ["fecha_creacion", "fecha_modificacion"]
    list_select_related = ["rol"]
    filter_horizontal = ["roles_autorizadores"]
    fieldsets = (
        ("Configuración", {
            "fields": ("rol", "tipo_operacion", "monto_maximo")
        }),
        ("Autorización", {
            "fields": ("requiere_autorizacion_doble", "roles_autorizadores")
        }),
        ("Estado", {
            "fields": ("activo", "observaciones")
        }),
        ("Auditoría", {
            "fields": ("configurado_por", "fecha_creacion", "fecha_modificacion"),
            "classes": ("collapse",),
        }),
    )

    def rol_link(self, obj):
        url = reverse("admin:usuarios_rol_change", args=[obj.rol.pk])
        return format_html('<a href="{}">{}</a>', url, obj.rol.nombre_rol)
    rol_link.short_description = "Rol"

    def tipo_operacion_badge(self, obj):
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:3px;font-size:10px;">{}</span>',
            obj.get_tipo_operacion_display(),
        )
    tipo_operacion_badge.short_description = "Operación"

    def monto_maximo_display(self, obj):
        return f"₲{obj.monto_maximo:,.0f}"
    monto_maximo_display.short_description = "Monto Máximo"

    def doble_autorizacion_badge(self, obj):
        if obj.requiere_autorizacion_doble:
            return format_html('<span style="color:#dc3545;">⚠️ Doble</span>')
        return "Simple"
    doble_autorizacion_badge.short_description = "Autorización"


# ==============================================================================
# REGISTRO DE AUTORIZACIÓN
# ==============================================================================

@admin.register(RegistroAutorizacion)
class RegistroAutorizacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tipo_operacion_badge",
        "monto_display",
        "solicitante_link",
        "autorizador_link",
        "fecha_autorizacion",
    ]
    list_filter = ["tipo_operacion", "fecha_autorizacion"]
    search_fields = [
        "solicitante__nombre", "solicitante__apellido",
        "autorizador__nombre", "autorizador__apellido",
        "motivo",
    ]
    readonly_fields = ["fecha_autorizacion", "ip_address"]
    list_select_related = ["solicitante", "autorizador"]
    date_hierarchy = "fecha_autorizacion"
    ordering = ["-fecha_autorizacion"]
    fieldsets = (
        ("Operación", {
            "fields": ("tipo_operacion", "monto", "motivo")
        }),
        ("Participantes", {
            "fields": ("solicitante", "autorizador", "autorizador_2")
        }),
        ("Referencias", {
            "fields": ("venta", "compra", "ajuste"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("fecha_autorizacion", "ip_address"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Registro de autorización inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def tipo_operacion_badge(self, obj):
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:3px;font-size:10px;">{}</span>',
            obj.tipo_operacion,
        )
    tipo_operacion_badge.short_description = "Operación"

    def monto_display(self, obj):
        return f"₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

    def solicitante_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.solicitante.pk])
        return format_html('<a href="{}">{}</a>', url, obj.solicitante.nombre_completo)
    solicitante_link.short_description = "Solicitante"

    def autorizador_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.autorizador.pk])
        return format_html('<a href="{}">{}</a>', url, obj.autorizador.nombre_completo)
    autorizador_link.short_description = "Autorizador"


# ==============================================================================
# PAGO BANCARD
# ==============================================================================

@admin.register(PagoBancard)
class PagoBancardAdmin(admin.ModelAdmin):
    list_display = ["id", "tipo_badge", "monto_display", "estado_badge", "shop_process_id", "fecha_creacion"]
    list_filter = ["estado", "tipo"]
    search_fields = ["shop_process_id", "descripcion"]
    readonly_fields = [f.name for f in PagoBancard._meta.fields]
    ordering = ["-fecha_creacion"]
    date_hierarchy = "fecha_creacion"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def tipo_badge(self, obj):
        colors = {"TARJETA": "#0d6efd", "ALMUERZO": "#28a745"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color, obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def monto_display(self, obj):
        return f"₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

    def estado_badge(self, obj):
        colors = {
            "PENDIENTE": "#ffc107",
            "APROBADO":  "#28a745",
            "RECHAZADO": "#dc3545",
            "CANCELADO": "#6c757d",
            "ERROR":     "#dc3545",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color, obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


@admin.register(SolicitudCatastroBancard)
class SolicitudCatastroBancardAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "card_id", "referencia", "resuelto", "fecha_creacion"]
    list_filter = ["resuelto"]
    search_fields = ["referencia", "cliente__nombres", "cliente__apellidos"]
    readonly_fields = [f.name for f in SolicitudCatastroBancard._meta.fields]
    ordering = ["-fecha_creacion"]
    date_hierarchy = "fecha_creacion"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
