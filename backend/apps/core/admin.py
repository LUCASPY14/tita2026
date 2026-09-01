"""
Admin para la app core
Gestión de tarjetas, movimientos y medios de pago
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    CargaSaldo,
    ConsumoTarjeta,
    MedioPago,
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

    def save_model(self, request, obj, form, change):
        """
        Si se edita saldo_actual a mano desde el admin, generar el
        MovimientoTarjeta correspondiente (tipo AJUSTE) — mismo patrón que
        usa bancard_service.py para reversos: monto negativo = aumenta el
        saldo (ver MovimientoTarjeta.save()). Sin esto, un cambio manual de
        saldo no queda en el historial que ve cajero/portal, solo en el
        historial interno de Django admin.
        """
        if change and "saldo_actual" in form.changed_data:
            anterior = Tarjeta.objects.get(pk=obj.pk).saldo_actual
            nuevo = obj.saldo_actual
            diferencia = nuevo - anterior
            super().save_model(request, obj, form, change)
            if diferencia != 0:
                MovimientoTarjeta.objects.create(
                    tarjeta=obj,
                    tipo=MovimientoTarjeta.Tipo.AJUSTE,
                    monto=-diferencia,
                    saldo_anterior=anterior,
                    saldo_resultante=nuevo,
                    descripcion=f"Ajuste manual desde el admin ({request.user.email})",
                    creado_por=request.user,
                )
        else:
            super().save_model(request, obj, form, change)

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
