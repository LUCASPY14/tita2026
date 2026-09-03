"""
Admin para la app contabilidad
Gestión de cajas, cierres, movimientos, facturación y comisiones
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Caja,
    CierreCaja,
    MovimientoCaja,
    Factura,
    DatosEmpresa,
)


# ==============================================================================
# CAJA
# ==============================================================================

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ubicacion", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "ubicacion"]


# ==============================================================================
# CIERRE DE CAJA
# ==============================================================================

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "caja_link",
        "empleado_link",
        "fecha_apertura",
        "fecha_cierre",
        "monto_inicial_display",
        "diferencia_display",
        "estado_badge",
    ]
    list_filter = ["estado", "caja", "fecha_apertura"]
    search_fields = ["caja__nombre", "empleado__nombre", "empleado__apellido"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["caja", "empleado"]
    date_hierarchy = "fecha_apertura"
    ordering = ["-fecha_apertura"]
    fieldsets = (
        ("Datos del Cierre", {
            "fields": ("caja", "empleado", "estado")
        }),
        ("Fechas", {
            "fields": ("fecha_apertura", "fecha_cierre")
        }),
        ("Montos", {
            "fields": ("monto_inicial", "monto_contado_fisico", "diferencia_efectivo")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Cierre inmutable cuando está cerrado o conciliado."""
        if obj and obj.estado in ("CERRADO", "CONCILIADO"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def caja_link(self, obj):
        url = reverse("admin:contabilidad_caja_change", args=[obj.caja.pk])
        return format_html('<a href="{}">{}</a>', url, obj.caja.nombre)
    caja_link.short_description = "Caja"

    def empleado_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.empleado.pk])
        return format_html('<a href="{}">{}</a>', url, obj.empleado.nombre_completo)
    empleado_link.short_description = "Empleado"

    def monto_inicial_display(self, obj):
        return f"₲{obj.monto_inicial:,.0f}"
    monto_inicial_display.short_description = "Monto Inicial"

    def diferencia_display(self, obj):
        if obj.diferencia_efectivo is not None:
            color = "#dc3545" if obj.diferencia_efectivo != 0 else "#28a745"
            return format_html('<strong style="color:{};">₲{:,}</strong>', color, obj.diferencia_efectivo)
        return "-"
    diferencia_display.short_description = "Diferencia"

    def estado_badge(self, obj):
        colors = {"ABIERTO": "#28a745", "CERRADO": "#ffc107", "CONCILIADO": "#0d6efd"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# MOVIMIENTO DE CAJA
# ==============================================================================

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cierre_link",
        "tipo_badge",
        "monto_display",
        "medio_pago_link",
        "venta_link",
        "fecha",
    ]
    list_filter = ["tipo", "medio_pago", "fecha"]
    search_fields = ["descripcion", "venta__id"]
    list_select_related = ["cierre", "medio_pago", "venta"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    fieldsets = (
        ("Datos del Movimiento", {
            "fields": ("cierre", "tipo", "monto", "monto_comision", "medio_pago")
        }),
        ("Referencia", {
            "fields": ("venta", "descripcion")
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Movimiento inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def cierre_link(self, obj):
        if obj.cierre:
            url = reverse("admin:contabilidad_cierrecaja_change", args=[obj.cierre.pk])
            return format_html('<a href="{}">Cierre #{}</a>', url, obj.cierre.pk)
        return "-"
    cierre_link.short_description = "Cierre"

    def tipo_badge(self, obj):
        colors = {"INGRESO": "#28a745", "EGRESO": "#dc3545"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def monto_display(self, obj):
        signo = "+" if obj.tipo == "INGRESO" else "-"
        return f"{signo}₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

    def medio_pago_link(self, obj):
        url = reverse("admin:core_mediopago_change", args=[obj.medio_pago.pk])
        return format_html('<a href="{}">{}</a>', url, obj.medio_pago.descripcion)
    medio_pago_link.short_description = "Medio de Pago"

    def venta_link(self, obj):
        if obj.venta:
            url = reverse("admin:ventas_venta_change", args=[obj.venta.pk])
            return format_html('<a href="{}">Venta #{}</a>', url, obj.venta.pk)
        return "-"
    venta_link.short_description = "Venta"


# ==============================================================================
# FACTURA
# ==============================================================================

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = [
        "nro_factura",
        "cliente_link",
        "venta_link",
        "monto_total_display",
        "iva_display",
        "estado_badge",
        "fecha_emision",
    ]
    list_filter = ["estado", "fecha_emision"]
    search_fields = ["nro_factura", "cliente__ruc_ci", "cliente__nombres"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["cliente", "venta"]
    date_hierarchy = "fecha_emision"
    ordering = ["-fecha_emision"]
    fieldsets = (
        ("Datos de la Factura", {
            "fields": ("nro_factura", "cliente", "venta", "estado")
        }),
        ("Montos", {
            "fields": ("monto_total", "iva_10", "iva_5", "monto_exenta")
        }),
        ("Auditoría", {
            "fields": ("observaciones", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Factura anulada inmutable."""
        if obj and obj.estado == "ANULADA":
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def has_add_permission(self, request):
        """
        No se crean facturas a mano desde el admin: el IVA queda en 0 por
        defecto y no hay forma de vincularlas a un origen (carga, recarga,
        pago de almuerzo, venta o cobro de CC). Usar POST /facturas/emitir/,
        que calcula el IVA y deja el vínculo con el origen — igual que ya
        exige FacturaViewSet.create() en la API.
        """
        return False

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def venta_link(self, obj):
        if obj.venta:
            url = reverse("admin:ventas_venta_change", args=[obj.venta.pk])
            return format_html('<a href="{}">Venta #{}</a>', url, obj.venta.pk)
        return "-"
    venta_link.short_description = "Venta"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}"
    monto_total_display.short_description = "Total"

    def iva_display(self, obj):
        return f"IVA10: ₲{obj.iva_10:,.0f} / IVA5: ₲{obj.iva_5:,.0f}"
    iva_display.short_description = "IVA"

    def estado_badge(self, obj):
        colors = {"EMITIDA": "#28a745", "ANULADA": "#dc3545"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# DATOS DE LA EMPRESA
# ==============================================================================

@admin.register(DatosEmpresa)
class DatosEmpresaAdmin(admin.ModelAdmin):
    list_display = ["ruc", "razon_social", "telefono", "email", "activo"]

    def has_add_permission(self, request):
        """Solo permite un registro de datos de empresa."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar los datos de la empresa."""
        return False
