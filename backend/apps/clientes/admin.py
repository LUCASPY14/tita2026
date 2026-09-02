"""
Admin para la app clientes
Gestión de clientes, hijos, cuentas corrientes y restricciones
"""

from django.contrib import admin
from django.db import models
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Cliente,
    CuentaCorrienteCliente,
    TipoCliente,
    Hijo,
    Grado,
    HistorialGrado,
    RestriccionHijo,
    AutorizacionSaldoNegativo,
    Pais,
    Ciudad,
    AlumnoResponsable,
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "ruc_ci",
        "nombre_completo",
        "telefono",
        "email",
        "limite_credito_display",
        "permite_cuenta_corriente",
        "saldo_display",
        "tipo_cliente_link",
        "activo",
    ]
    list_filter = ["activo", "permite_cuenta_corriente", "tipo_cliente"]
    search_fields = ["ruc_ci", "nombres", "apellidos", "email"]
    ordering = ["apellidos", "nombres"]
    readonly_fields = ["fecha_registro"]
    list_select_related = ["tipo_cliente", "lista_precio"]
    fieldsets = (
        ("Datos Personales", {
            "fields": ("nombres", "apellidos", "razon_social", "ruc_ci")
        }),
        ("Contacto", {
            "fields": ("telefono", "email", "direccion", "ciudad", "ciudad_catalogo")
        }),
        ("Configuración", {
            "fields": ("tipo_cliente", "lista_precio", "permite_cuenta_corriente", "limite_credito", "activo")
        }),
        ("Auditoría", {
            "fields": ("fecha_registro",),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        cero = Value(0, output_field=models.DecimalField())
        return super().get_queryset(request).annotate(
            _saldo_cc=Coalesce(
                Sum("movimientos_cuenta__monto", filter=Q(movimientos_cuenta__tipo="DEBITO")),
                cero,
            ) - Coalesce(
                Sum("movimientos_cuenta__monto", filter=~Q(movimientos_cuenta__tipo="DEBITO")),
                cero,
            )
        )

    def saldo_display(self, obj):
        saldo = obj._saldo_cc or 0
        color = "#dc3545" if saldo > 0 else "#28a745"
        monto_formateado = "₲{:,.0f}".format(saldo)
        return format_html('<strong style="color:{};">{}</strong>', color, monto_formateado)
    saldo_display.short_description = "Saldo Cta. Cte."

    def limite_credito_display(self, obj):
        return "₲{:,.0f}".format(obj.limite_credito)
    limite_credito_display.short_description = "Límite Crédito"

    def tipo_cliente_link(self, obj):
        url = reverse("admin:clientes_tipocliente_change", args=[obj.tipo_cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.tipo_cliente.nombre)
    tipo_cliente_link.short_description = "Tipo"


@admin.register(CuentaCorrienteCliente)
class CuentaCorrienteClienteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cliente_link",
        "fecha",
        "tipo_badge",
        "monto_display",
        "saldo_resultante_display",
        "descripcion",
    ]
    list_filter = ["tipo", "fecha"]
    search_fields = [
        "cliente__ruc_ci", "cliente__nombres", "cliente__apellidos", "descripcion"
    ]
    readonly_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]
    date_hierarchy = "fecha"
    ordering = ["-fecha", "-id"]
    list_select_related = ["cliente"]

    def has_add_permission(self, _request):
        return False

    def has_delete_permission(self, _request, _obj=None):
        return False

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def tipo_badge(self, obj):
        colors = {"DEBITO": "#dc3545", "CREDITO": "#28a745", "AJUSTE": "#ffc107"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def monto_display(self, obj):
        return "₲{:,.0f}".format(obj.monto)
    monto_display.short_description = "Monto"

    def saldo_resultante_display(self, obj):
        color = "#dc3545" if obj.saldo_resultante > 0 else "#28a745"
        monto_formateado = "₲{:,.0f}".format(obj.saldo_resultante)
        return format_html('<strong style="color:{};">{}</strong>', color, monto_formateado)
    saldo_resultante_display.short_description = "Saldo Resultante"


@admin.register(TipoCliente)
class TipoClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    search_fields = ["nombre"]


@admin.register(Hijo)
class HijoAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "grado", "cliente_responsable_link", "activo"]
    list_filter = ["activo", "grado"]
    search_fields = ["nombre", "apellido", "cliente_responsable__ruc_ci"]
    list_select_related = ["cliente_responsable", "grado"]
    fieldsets = (
        ("Datos del Estudiante", {
            "fields": ("nombre", "apellido", "fecha_nacimiento", "grado")
        }),
        ("Responsable", {
            "fields": ("cliente_responsable",)
        }),
        ("Foto", {
            "fields": ("foto_perfil", "fecha_foto"),
        }),
        ("Estado", {
            "fields": ("activo",),
        }),
    )

    def cliente_responsable_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente_responsable.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente_responsable.nombre_completo)
    cliente_responsable_link.short_description = "Responsable"


@admin.register(Grado)
class GradoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "nivel", "orden", "es_ultimo", "activo"]
    list_filter = ["activo", "es_ultimo"]
    search_fields = ["nombre"]
    ordering = ["orden"]


@admin.register(HistorialGrado)
class HistorialGradoAdmin(admin.ModelAdmin):
    list_display = ["hijo_link", "grado_anterior", "grado_nuevo", "anio_escolar", "fecha_cambio"]
    list_filter = ["anio_escolar"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    ordering = ["-fecha_cambio"]
    list_select_related = ["hijo"]

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"


@admin.register(RestriccionHijo)
class RestriccionHijoAdmin(admin.ModelAdmin):
    list_display = ["hijo_link", "tipo", "severidad_badge", "requiere_autorizacion", "activo"]
    list_filter = ["severidad", "activo", "requiere_autorizacion"]
    search_fields = ["hijo__nombre", "hijo__apellido", "tipo"]
    list_select_related = ["hijo"]

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"

    def severidad_badge(self, obj):
        colors = {"BAJA": "#28a745", "MEDIA": "#ffc107", "ALTA": "#fd7e14", "CRITICA": "#dc3545"}
        color = colors.get(obj.severidad, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;">{}</span>',
            color,
            obj.get_severidad_display(),
        )
    severidad_badge.short_description = "Severidad"


@admin.register(AutorizacionSaldoNegativo)
class AutorizacionSaldoNegativoAdmin(admin.ModelAdmin):
    list_display = [
        "cliente_link",
        "venta_link",
        "monto_autorizado_display",
        "empleado_autoriza_link",
        "estado_badge",
        "fecha_autorizacion",
    ]
    list_filter = ["estado"]
    search_fields = ["cliente__ruc_ci", "cliente__nombres", "motivo"]
    readonly_fields = ["fecha_autorizacion", "saldo_anterior", "saldo_resultante"]
    list_select_related = ["cliente", "venta", "empleado_autoriza"]
    fieldsets = (
        ("Datos de la Autorización", {
            "fields": ("cliente", "venta", "empleado_autoriza")
        }),
        ("Montos", {
            "fields": ("monto_autorizado", "saldo_anterior", "saldo_resultante")
        }),
        ("Detalle", {
            "fields": ("motivo", "estado", "fecha_autorizacion")
        }),
    )

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def venta_link(self, obj):
        url = reverse("admin:ventas_venta_change", args=[obj.venta.pk])
        return format_html('<a href="{}">Venta #{}</a>', url, obj.venta.pk)
    venta_link.short_description = "Venta"

    def empleado_autoriza_link(self, obj):
        url = reverse("admin:usuarios_empleado_change", args=[obj.empleado_autoriza.pk])
        return format_html('<a href="{}">{}</a>', url, obj.empleado_autoriza)
    empleado_autoriza_link.short_description = "Autorizado por"

    def monto_autorizado_display(self, obj):
        return "₲{:,.0f}".format(obj.monto_autorizado)
    monto_autorizado_display.short_description = "Monto Autorizado"

    def estado_badge(self, obj):
        colors = {"APROBADA": "#28a745", "USADA": "#ffc107", "CANCELADA": "#6c757d"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ["nombre"]
    search_fields = ["nombre"]


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ["nombre", "pais"]
    list_filter = ["pais"]
    search_fields = ["nombre"]


@admin.register(AlumnoResponsable)
class AlumnoResponsableAdmin(admin.ModelAdmin):
    list_display = ["hijo", "cliente", "parentesco", "es_titular", "orden_cobro", "activo"]
    list_filter = ["es_titular", "activo", "parentesco"]
    search_fields = ["hijo__nombre", "hijo__apellido", "cliente__nombres", "cliente__apellidos"]
    list_select_related = ["hijo", "cliente"]
    ordering = ["hijo", "orden_cobro"]
