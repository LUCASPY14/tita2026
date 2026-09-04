"""
Admin para la app almuerzos
Gestión de precios, planes, suscripciones, consumo y alérgenos
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    PrecioAlmuerzo,
    TipoAlmuerzo,
    PlanAlmuerzo,
    SuscripcionAlmuerzo,
    RegistroConsumoAlmuerzo,
    CuentaAlmuerzoMensual,
    PagoCuentaAlmuerzo,
    Alergeno,
    ProductoAlergeno,
    MenuDiario,
    DetalleMenuDiario,
)


# ==============================================================================
# PRECIO DE ALMUERZO
# ==============================================================================

@admin.register(PrecioAlmuerzo)
class PrecioAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ["precio_unitario_display", "fecha_inicio_vigencia", "fecha_fin_vigencia", "descripcion", "activo"]
    list_filter = ["activo"]
    search_fields = ["descripcion"]
    ordering = ["-fecha_inicio_vigencia"]

    def precio_unitario_display(self, obj):
        return f"₲{obj.precio_unitario:,.0f}"
    precio_unitario_display.short_description = "Precio"


# ==============================================================================
# TIPO DE ALMUERZO
# ==============================================================================

@admin.register(TipoAlmuerzo)
class TipoAlmuerzoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "precio_unitario_display",
        "incluye_plato_principal",
        "incluye_postre",
        "incluye_bebida",
        "activo",
        "es_predeterminado",
    ]
    list_filter = ["activo", "es_predeterminado", "incluye_plato_principal", "incluye_postre", "incluye_bebida"]
    search_fields = ["nombre"]

    def precio_unitario_display(self, obj):
        return f"₲{obj.precio_unitario:,.0f}"
    precio_unitario_display.short_description = "Precio"


# ==============================================================================
# PLAN DE ALMUERZO
# ==============================================================================

@admin.register(PlanAlmuerzo)
class PlanAlmuerzoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "tipo_badge",
        "precio_mensual_display",
        "cantidad_almuerzos_mes",
        "dias_semana_incluidos",
        "activo",
        "es_predeterminado",
    ]
    list_filter = ["activo", "es_predeterminado", "tipo"]
    search_fields = ["nombre"]

    def tipo_badge(self, obj):
        colors = {"CANTIDAD": "#0d6efd", "SIN_LIMITE": "#28a745"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def precio_mensual_display(self, obj):
        return f"₲{obj.precio_mensual:,.0f}"
    precio_mensual_display.short_description = "Precio Mensual"


# ==============================================================================
# SUSCRIPCIÓN DE ALMUERZO
# ==============================================================================

@admin.register(SuscripcionAlmuerzo)
class SuscripcionAlmuerzoAdmin(admin.ModelAdmin):
    list_display = [
        "id_suscripcion",
        "hijo_link",
        "plan_link",
        "fecha_inicio",
        "fecha_fin",
        "estado_badge",
    ]
    list_filter = ["estado", "plan"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["hijo", "plan"]
    ordering = ["-fecha_inicio"]
    fieldsets = (
        ("Datos de la Suscripción", {
            "fields": ("hijo", "plan", "estado")
        }),
        ("Vigencia", {
            "fields": ("fecha_inicio", "fecha_fin")
        }),
    )

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"

    def plan_link(self, obj):
        url = reverse("admin:almuerzos_planalmuerzo_change", args=[obj.plan.pk])
        return format_html('<a href="{}">{}</a>', url, obj.plan.nombre)
    plan_link.short_description = "Plan"

    def estado_badge(self, obj):
        colors = {"ACTIVA": "#28a745", "SUSPENDIDA": "#ffc107", "CANCELADA": "#6c757d"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# REGISTRO DE CONSUMO DE ALMUERZO
# ==============================================================================

@admin.register(RegistroConsumoAlmuerzo)
class RegistroConsumoAlmuerzoAdmin(admin.ModelAdmin):
    list_display = [
        "id_registro_consumo",
        "hijo_link",
        "fecha_consumo",
        "tipo_almuerzo_link",
        "costo_display",
        "estado_badge",
    ]
    list_filter = ["estado", "fecha_consumo", "tipo_almuerzo"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["hijo", "tipo_almuerzo"]
    date_hierarchy = "fecha_consumo"
    ordering = ["-fecha_consumo", "-hora_registro"]
    fieldsets = (
        ("Datos del Consumo", {
            "fields": ("hijo", "suscripcion", "tipo_almuerzo", "fecha_consumo", "hora_registro")
        }),
        ("Costo y Cobro", {
            "fields": ("costo_almuerzo", "ya_cobrado", "marcado_en_cuenta")
        }),
        ("Estado", {
            "fields": ("estado", "motivo_rechazo")
        }),
        ("Registro", {
            "fields": ("nro_tarjeta", "registrado_por_display", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def registrado_por_display(self, obj):
        if not obj.registrado_por:
            return "-"
        return obj.registrado_por.get_full_name() or obj.registrado_por.username
    registrado_por_display.short_description = "Registrado por"

    def get_readonly_fields(self, request, obj=None):
        """Permite editar mientras el consumo está REGISTRADO y no cobrado; bloquea en otros casos."""
        if obj and (obj.estado != "REGISTRADO" or obj.ya_cobrado):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"

    def tipo_almuerzo_link(self, obj):
        if obj.tipo_almuerzo:
            url = reverse("admin:almuerzos_tipoalmuerzo_change", args=[obj.tipo_almuerzo.pk])
            return format_html('<a href="{}">{}</a>', url, obj.tipo_almuerzo.nombre)
        return "-"
    tipo_almuerzo_link.short_description = "Tipo"

    def costo_display(self, obj):
        if obj.costo_almuerzo:
            return f"₲{obj.costo_almuerzo:,.0f}"
        return "-"
    costo_display.short_description = "Costo"

    def estado_badge(self, obj):
        colors = {"REGISTRADO": "#28a745", "RECHAZADO": "#dc3545", "ANULADO": "#6c757d"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# CUENTA MENSUAL DE ALMUERZO
# ==============================================================================

@admin.register(CuentaAlmuerzoMensual)
class CuentaAlmuerzoMensualAdmin(admin.ModelAdmin):
    list_display = [
        "id_cuenta_mensual",
        "hijo_link",
        "periodo",
        "cantidad_almuerzos",
        "monto_total_display",
        "monto_pagado_display",
        "saldo_pendiente_display",
        "estado_badge",
    ]
    list_filter = ["estado", "anio", "mes"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    readonly_fields = ["fecha_generacion", "fecha_actualizacion", "fecha_creacion"]
    list_select_related = ["hijo"]
    ordering = ["-anio", "-mes"]
    fieldsets = (
        ("Datos de la Cuenta", {
            "fields": ("hijo", "anio", "mes", "cantidad_almuerzos", "monto_total")
        }),
        ("Pago", {
            "fields": ("forma_cobro", "monto_pagado", "estado")
        }),
        ("Facturación", {
            "fields": ("factura", "nro_comprobante", "comprobante_pago", "fecha_pago")
        }),
        ("Auditoría", {
            "fields": ("fecha_generacion", "fecha_actualizacion", "observaciones"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Cuenta inmutable cuando está pagada o anulada."""
        if obj and obj.estado in ("PAGADO", "ANULADO"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def hijo_link(self, obj):
        url = reverse("admin:clientes_hijo_change", args=[obj.hijo.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hijo.nombre_completo)
    hijo_link.short_description = "Estudiante"

    def periodo(self, obj):
        return f"{obj.mes:02d}/{obj.anio}"
    periodo.short_description = "Período"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}"
    monto_total_display.short_description = "Total"

    def monto_pagado_display(self, obj):
        return f"₲{obj.monto_pagado:,.0f}"
    monto_pagado_display.short_description = "Pagado"

    def saldo_pendiente_display(self, obj):
        saldo = obj.saldo_pendiente
        if saldo < 0:
            return format_html('<span style="color:#fd7e14;">-₲{:,}</span>', abs(int(saldo)))
        if saldo == 0:
            return format_html('<span style="color:#28a745;">₲0</span>')
        return format_html('<span style="color:#dc3545;">₲{:,}</span>', int(saldo))
    saldo_pendiente_display.short_description = "Saldo Pend."

    def estado_badge(self, obj):
        colors = {
            "PENDIENTE": "#dc3545",
            "VALIDACION": "#ffc107",
            "PAGADO": "#28a745",
            "PARCIAL": "#fd7e14",
            "ANULADO": "#6c757d",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# PAGO DE CUENTA DE ALMUERZO
# ==============================================================================

@admin.register(PagoCuentaAlmuerzo)
class PagoCuentaAlmuerzoAdmin(admin.ModelAdmin):
    list_display = [
        "id_pago_cuenta",
        "cuenta_link",
        "monto_display",
        "medio_pago",
        "fecha_pago",
    ]
    list_filter = ["fecha_pago"]
    search_fields = ["cuenta__hijo__nombre", "cuenta__hijo__apellido", "referencia"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["cuenta", "cuenta__hijo"]
    date_hierarchy = "fecha_pago"
    ordering = ["-fecha_pago"]

    def get_readonly_fields(self, request, obj=None):
        """Pago inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        """Los pagos solo se ven; no se modifican."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar pagos."""
        return False

    def cuenta_link(self, obj):
        url = reverse("admin:almuerzos_cuentaalmuerzomensual_change", args=[obj.cuenta.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cuenta)
    cuenta_link.short_description = "Cuenta"

    def monto_display(self, obj):
        return f"₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"


# ==============================================================================
# PAGO MENSUAL DE SUSCRIPCIÓN
# ==============================================================================

# ==============================================================================
# ALÉRGENO
# ==============================================================================

@admin.register(Alergeno)
class AlergenoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "severidad_badge", "activo"]
    list_filter = ["activo", "severidad"]
    search_fields = ["nombre"]
    readonly_fields = ["fecha_creacion"]
    fieldsets = (
        ("Datos del Alérgeno", {
            "fields": ("nombre", "descripcion", "severidad", "icono")
        }),
        ("Palabras Clave", {
            "fields": ("palabras_clave",),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def severidad_badge(self, obj):
        colors = {"BAJA": "#28a745", "MEDIA": "#ffc107", "ALTA": "#fd7e14", "CRITICA": "#dc3545"}
        color = colors.get(obj.severidad, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;">{}</span>',
            color,
            obj.get_severidad_display(),
        )
    severidad_badge.short_description = "Severidad"


# ==============================================================================
# PRODUCTO - ALÉRGENO
# ==============================================================================

@admin.register(MenuDiario)
class MenuDiarioAdmin(admin.ModelAdmin):
    list_display = ["fecha", "plato_principal", "guarnicion", "postre", "bebida", "activo"]
    list_filter = ["activo"]
    search_fields = ["plato_principal", "guarnicion"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    readonly_fields = ["fecha_creacion"]


@admin.register(DetalleMenuDiario)
class DetalleMenuDiarioAdmin(admin.ModelAdmin):
    list_display = ["menu", "producto", "curso", "cantidad", "es_opcional"]
    list_filter = ["curso", "es_opcional"]
    search_fields = ["menu__plato_principal", "producto__descripcion"]
    list_select_related = ["menu", "producto"]
    ordering = ["-menu__fecha", "curso"]


@admin.register(ProductoAlergeno)
class ProductoAlergenoAdmin(admin.ModelAdmin):
    list_display = ["producto_link", "alergeno_link", "contiene_badge"]
    list_filter = ["alergeno", "contiene"]
    search_fields = ["producto__descripcion", "alergeno__nombre"]
    list_select_related = ["producto", "alergeno"]

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def alergeno_link(self, obj):
        url = reverse("admin:almuerzos_alergeno_change", args=[obj.alergeno.pk])
        return format_html('<a href="{}">{}</a>', url, obj.alergeno.nombre)
    alergeno_link.short_description = "Alérgeno"

    def contiene_badge(self, obj):
        if obj.contiene:
            return format_html('<span style="color:#dc3545;">⚠ Contiene</span>')
        return format_html('<span style="color:#6c757d;">Trazas</span>')
    contiene_badge.short_description = "Contiene"
