from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Cajas,
    CierresCaja,
    MovimientosCaja,
    TarifasComision,
    AuditoriaComisiones,
    ConciliacionPagos,
    DocumentosTributarios,
    DocumentoImpuestos,
    Timbrados,
    PuntosExpedicion,
    DatosEmpresa,
    Impuestos,
)

# =============================================================================
# 1. CAJAS
# =============================================================================


@admin.register(Cajas)
class CajasAdmin(admin.ModelAdmin):
    list_display = ["id_caja", "nombre_caja", "ubicacion", "activo_badge"]
    list_filter = ["estado"]
    search_fields = ["nombre_caja", "ubicacion"]
    ordering = ["nombre_caja"]

    fieldsets = (
        ("Información General", {"fields": ("nombre_caja", "ubicacion")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def activo_badge(self, obj):
        if obj.estado:
            color = "green"
            icon = "✓"
            texto = "Activa"
        else:
            color = "red"
            icon = "✗"
            texto = "Inactiva"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>', color, icon, texto
        )

    activo_badge.short_description = "Estado"


# =============================================================================
# 2. CIERRES DE CAJA
# =============================================================================


@admin.register(CierresCaja)
class CierresCajaAdmin(admin.ModelAdmin):
    list_display = [
        "id_cierre",
        "id_caja",
        "fecha_hora_apertura",
        "fecha_hora_cierre",
        "monto_inicial_display",
        "monto_contado_display",
        "diferencia_display",
        "estado_badge",
    ]
    list_filter = ["estado", "id_caja", "fecha_hora_apertura"]
    search_fields = ["id_caja__nombre_caja"]
    ordering = ["-fecha_hora_apertura"]
    readonly_fields = ["id_cierre", "duracion_display"]

    fieldsets = (
        ("Información del Cierre", {"fields": ("id_cierre", "id_caja", "id_empleado")}),
        ("Fechas", {"fields": ("fecha_hora_apertura", "fecha_hora_cierre", "duracion_display")}),
        ("Montos", {"fields": ("monto_inicial", "monto_contado_fisico", "diferencia_efectivo")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def estado_badge(self, obj):
        colores = {
            "Abierto": "blue",
            "Cerrado": "green",
        }
        color = colores.get(obj.estado, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.estado if obj.estado else "N/A",
        )

    estado_badge.short_description = "Estado"

    def monto_inicial_display(self, obj):
        if obj.monto_inicial:
            return format_html("₲{:,.0f}", obj.monto_inicial)
        return "-"

    monto_inicial_display.short_description = "Inicial"

    def monto_contado_display(self, obj):
        if obj.monto_contado_fisico:
            return format_html("₲{:,.0f}", obj.monto_contado_fisico)
        return "-"

    monto_contado_display.short_description = "Contado"

    def diferencia_display(self, obj):
        if obj.diferencia_efectivo:
            color = (
                "red"
                if obj.diferencia_efectivo < 0
                else ("green" if obj.diferencia_efectivo > 0 else "gray")
            )
            return format_html(
                '<span style="color: {}; font-weight: bold;">₲{:,.0f}</span>',
                color,
                obj.diferencia_efectivo,
            )
        return "-"

    diferencia_display.short_description = "Diferencia"

    def duracion_display(self, obj):
        if obj.fecha_hora_cierre and obj.fecha_hora_apertura:
            diff = obj.fecha_hora_cierre - obj.fecha_hora_apertura
            hours = diff.total_seconds() / 3600
            return format_html("{:.1f} horas", hours)
        return "En curso"

    duracion_display.short_description = "Duración"


# =============================================================================
# 3. MOVIMIENTOS DE CAJA
# =============================================================================


@admin.register(MovimientosCaja)
class MovimientosCajaAdmin(admin.ModelAdmin):
    list_display = [
        "id_movimiento",
        "id_cierre",
        "tipo_movimiento_badge",
        "monto_display",
        "monto_comision_display",
        "fecha_movimiento",
    ]
    list_filter = ["tipo_movimiento", "id_medio_pago", "fecha_movimiento"]
    search_fields = ["descripcion", "id_cierre__id_cierre"]
    ordering = ["-fecha_movimiento"]
    readonly_fields = ["id_movimiento"]

    fieldsets = (
        (
            "Información del Movimiento",
            {"fields": ("id_movimiento", "id_cierre", "tipo_movimiento", "id_medio_pago")},
        ),
        ("Montos", {"fields": ("monto", "monto_comision")}),
        ("Detalles", {"fields": ("fecha_movimiento", "descripcion", "id_venta")}),
    )

    def tipo_movimiento_badge(self, obj):
        colores = {
            "Ingreso": "green",
            "Egreso": "red",
            "Transferencia": "blue",
            "Apertura": "orange",
            "Cierre": "purple",
        }
        color = colores.get(obj.tipo_movimiento, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.tipo_movimiento,
        )

    tipo_movimiento_badge.short_description = "Tipo"

    def monto_display(self, obj):
        return format_html("₲{:,.0f}", obj.monto)

    monto_display.short_description = "Monto"

    def monto_comision_display(self, obj):
        if obj.monto_comision > 0:
            return format_html('<span style="color: orange;">₲{:,.0f}</span>', obj.monto_comision)
        return "₲0"

    monto_comision_display.short_description = "Comisión"


# =============================================================================
# 4. TARIFAS DE COMISIÓN
# =============================================================================


@admin.register(TarifasComision)
class TarifasComisionAdmin(admin.ModelAdmin):
    list_display = [
        "id_tarifa",
        "id_medio_pago",
        "porcentaje_display",
        "monto_fijo_display",
        "fecha_inicio_vigencia",
        "fecha_fin_vigencia",
        "activo_badge",
    ]
    list_filter = ["estado", "id_medio_pago", "fecha_inicio_vigencia"]
    ordering = ["-fecha_inicio_vigencia"]
    readonly_fields = ["id_tarifa"]

    fieldsets = (
        ("Información General", {"fields": ("id_tarifa", "id_medio_pago")}),
        ("Comisiones", {"fields": ("porcentaje_comision", "monto_fijo_comision")}),
        ("Vigencia", {"fields": ("fecha_inicio_vigencia", "fecha_fin_vigencia")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def porcentaje_display(self, obj):
        return format_html(
            "<strong>{:.2f}%</strong>",
            obj.porcentaje_comision * 100 if obj.porcentaje_comision else 0,
        )

    porcentaje_display.short_description = "Porcentaje"

    def monto_fijo_display(self, obj):
        if obj.monto_fijo_comision:
            return format_html("₲{:,.0f}", obj.monto_fijo_comision)
        return "-"

    monto_fijo_display.short_description = "Monto Fijo"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ Activa</span>')
        return format_html('<span style="color: red;">✗ Inactiva</span>')

    activo_badge.short_description = "Estado"


# =============================================================================
# 5. AUDITORÍA DE COMISIONES
# =============================================================================


@admin.register(AuditoriaComisiones)
class AuditoriaComisionesAdmin(admin.ModelAdmin):
    list_display = [
        "id_auditoria",
        "id_tarifa",
        "campo_modificado",
        "valor_anterior_display",
        "valor_nuevo_display",
        "id_empleado_modifico",
        "fecha_cambio",
    ]
    list_filter = ["campo_modificado", "fecha_cambio"]
    search_fields = ["campo_modificado"]
    ordering = ["-fecha_cambio"]
    readonly_fields = [
        "id_auditoria",
        "fecha_cambio",
        "id_tarifa",
        "campo_modificado",
        "valor_anterior",
        "valor_nuevo",
        "id_empleado_modifico",
    ]

    def has_add_permission(self, request):
        return False  # Solo creado por triggers/signals

    def has_delete_permission(self, request, obj=None):
        return False  # No se pueden eliminar registros de auditoría

    def valor_anterior_display(self, obj):
        if obj.valor_anterior is not None:
            return format_html('<span style="color: red;">{:.4f}</span>', obj.valor_anterior)
        return "-"

    valor_anterior_display.short_description = "Valor Anterior"

    def valor_nuevo_display(self, obj):
        if obj.valor_nuevo is not None:
            return format_html(
                '<span style="color: green; font-weight: bold;">{:.4f}</span>', obj.valor_nuevo
            )
        return "-"

    valor_nuevo_display.short_description = "Valor Nuevo"


# =============================================================================
# 6. CONCILIACIÓN DE PAGOS
# =============================================================================


@admin.register(ConciliacionPagos)
class ConciliacionPagosAdmin(admin.ModelAdmin):
    list_display = [
        "id_conciliacion",
        "id_pago_venta",
        "estado_badge",
        "fecha_conciliacion",
        "fecha_acreditacion",
        "monto_acreditado_display",
    ]
    list_filter = ["estado", "fecha_conciliacion", "fecha_acreditacion"]
    ordering = ["-fecha_conciliacion"]
    readonly_fields = ["id_conciliacion", "fecha_creacion"]

    fieldsets = (
        ("Información General", {"fields": ("id_conciliacion", "id_pago_venta", "estado")}),
        (
            "Fechas",
            {
                "fields": (
                    "fecha_conciliacion",
                    "fecha_acreditacion",
                    "fecha_creacion",
                    "fecha_actualizacion",
                )
            },
        ),
        ("Montos", {"fields": ("monto_acreditado",)}),
        ("Observaciones", {"fields": ("observaciones",)}),
    )

    def estado_badge(self, obj):
        colores = {
            "Pendiente": "orange",
            "Conciliado": "green",
            "Rechazado": "red",
            "En Proceso": "blue",
        }
        color = colores.get(obj.estado, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.estado,
        )

    estado_badge.short_description = "Estado"

    def monto_acreditado_display(self, obj):
        if obj.monto_acreditado:
            return format_html("₲{:,.0f}", obj.monto_acreditado)
        return "-"

    monto_acreditado_display.short_description = "Monto Acreditado"


# =============================================================================
# 7. DOCUMENTOS TRIBUTARIOS
# =============================================================================


@admin.register(DocumentosTributarios)
class DocumentosTributariosAdmin(admin.ModelAdmin):
    list_display = [
        "id_documento",
        "nro_secuencial",
        "tipo_documento_badge",
        "monto_total_display",
        "fecha_emision",
        "estado_sifen_badge",
        "nro_timbrado",
    ]
    list_filter = ["tipo_documento", "estado_sifen", "fecha_emision"]
    search_fields = ["cdc", "nro_secuencial", "nro_preimpreso_interno"]
    ordering = ["-fecha_emision"]
    readonly_fields = ["id_documento"]

    fieldsets = (
        (
            "Información General",
            {"fields": ("id_documento", "nro_secuencial", "tipo_documento", "nro_timbrado")},
        ),
        ("Montos", {"fields": ("monto_total",)}),
        ("Documentación Electrónica", {"fields": ("cdc", "url_kude", "estado_sifen")}),
        ("Fechas", {"fields": ("fecha_emision", "fecha_envio", "fecha_respuesta")}),
        ("Otros", {"fields": ("nro_preimpreso_interno",)}),
    )

    def tipo_documento_badge(self, obj):
        colores = {
            "Factura": "green",
            "NotaCredito": "orange",
            "NotaDebito": "red",
            "Recibo": "blue",
        }
        color = colores.get(obj.tipo_documento, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.tipo_documento,
        )

    tipo_documento_badge.short_description = "Tipo"

    def estado_sifen_badge(self, obj):
        if not obj.estado_sifen:
            return format_html('<span style="color: gray;">Pendiente</span>')

        colores = {
            "Aprobado": "green",
            "Rechazado": "red",
            "Pendiente": "orange",
        }
        color = colores.get(obj.estado_sifen, "gray")
        iconos = {
            "Aprobado": "✓",
            "Rechazado": "✗",
            "Pendiente": "⏳",
        }
        icono = iconos.get(obj.estado_sifen, "?")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icono,
            obj.estado_sifen,
        )

    estado_sifen_badge.short_description = "Estado SIFEN"

    def monto_total_display(self, obj):
        return format_html("<strong>₲{:,.0f}</strong>", obj.monto_total)

    monto_total_display.short_description = "Monto Total"


# =============================================================================
# 8. DOCUMENTO IMPUESTOS (INLINE ONLY)
# =============================================================================


class DocumentoImpuestosInline(admin.TabularInline):
    model = DocumentoImpuestos
    extra = 1
    fields = ["id_impuesto", "base_imponible", "monto_impuesto"]
    readonly_fields = []


# =============================================================================
# 9. TIMBRADOS
# =============================================================================


@admin.register(Timbrados)
class TimbradosAdmin(admin.ModelAdmin):
    list_display = [
        "nro_timbrado",
        "tipo_documento",
        "fecha_inicio",
        "fecha_fin",
        "numeros_display",
        "es_electronico_badge",
        "activo_badge",
    ]
    list_filter = ["estado", "tipo_documento", "es_electronico"]
    search_fields = ["nro_timbrado"]
    ordering = ["-fecha_inicio"]
    readonly_fields = ["nro_timbrado", "disponibles_display"]

    fieldsets = (
        (
            "Información del Timbrado",
            {"fields": ("nro_timbrado", "tipo_documento", "id_punto", "es_electronico")},
        ),
        ("Vigencia", {"fields": ("fecha_inicio", "fecha_fin")}),
        ("Numeración", {"fields": ("nro_inicial", "nro_final", "disponibles_display")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def numeros_display(self, obj):
        total = obj.nro_final - obj.nro_inicial + 1
        return format_html("{} - {} ({:,} docs)", obj.nro_inicial, obj.nro_final, total)

    numeros_display.short_description = "Rango"

    def es_electronico_badge(self, obj):
        if obj.es_electronico:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 3px 8px; border-radius: 3px;">📱 Digital</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px;">📄 Papel</span>'
        )

    es_electronico_badge.short_description = "Tipo"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ estado</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')

    activo_badge.short_description = "Estado"

    def disponibles_display(self, obj):
        total = obj.nro_final - obj.nro_inicial + 1
        # Esto podría calcularse desde DocumentosTributarios
        return format_html("<strong>{:,}</strong> documentos disponibles", total)

    disponibles_display.short_description = "Disponibles"


# =============================================================================
# 10. PUNTOS DE EXPEDICIÓN
# =============================================================================


@admin.register(PuntosExpedicion)
class PuntosExpedicionAdmin(admin.ModelAdmin):
    list_display = ["id_punto", "codigo_completo_display", "descripcion_ubicacion", "activo_badge"]
    list_filter = ["estado"]
    search_fields = ["codigo_establecimiento", "codigo_punto_expedicion", "descripcion_ubicacion"]
    ordering = ["codigo_establecimiento", "codigo_punto_expedicion"]
    readonly_fields = ["id_punto", "codigo_completo_display"]

    fieldsets = (
        (
            "Información del Punto",
            {
                "fields": (
                    "id_punto",
                    "codigo_establecimiento",
                    "codigo_punto_expedicion",
                    "codigo_completo_display",
                )
            },
        ),
        ("Detalles", {"fields": ("descripcion_ubicacion",)}),
        ("Estado", {"fields": ("estado",)}),
    )

    def codigo_completo_display(self, obj):
        return format_html(
            "<strong>{}-{}</strong>", obj.codigo_establecimiento, obj.codigo_punto_expedicion
        )

    codigo_completo_display.short_description = "Código Completo"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ estado</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')

    activo_badge.short_description = "Estado"


# =============================================================================
# 11. DATOS EMPRESA
# =============================================================================


@admin.register(DatosEmpresa)
class DatosEmpresaAdmin(admin.ModelAdmin):
    list_display = [
        "id_empresa",
        "razon_social",
        "ruc",
        "ciudad",
        "telefono",
        "email",
        "activo_badge",
    ]
    list_filter = ["estado", "ciudad", "pais"]
    search_fields = ["razon_social", "ruc", "email"]
    ordering = ["razon_social"]
    readonly_fields = ["id_empresa"]

    fieldsets = (
        ("Información Fiscal", {"fields": ("id_empresa", "ruc", "razon_social")}),
        ("Ubicación", {"fields": ("direccion", "ciudad", "pais")}),
        ("Contacto", {"fields": ("telefono", "email")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ Activa</span>')
        return format_html('<span style="color: red;">✗ Inactiva</span>')

    activo_badge.short_description = "Estado"


# =============================================================================
# 12. IMPUESTOS
# =============================================================================


@admin.register(Impuestos)
class ImpuestosAdmin(admin.ModelAdmin):
    list_display = [
        "id_impuesto",
        "nombre_impuesto",
        "porcentaje_display",
        "vigente_desde",
        "vigente_hasta",
        "activo_badge",
    ]
    list_filter = ["estado", "vigente_desde"]
    search_fields = ["nombre_impuesto"]
    ordering = ["nombre_impuesto"]
    readonly_fields = ["id_impuesto"]

    fieldsets = (
        ("Información del Impuesto", {"fields": ("id_impuesto", "nombre_impuesto", "porcentaje")}),
        ("Vigencia", {"fields": ("vigente_desde", "vigente_hasta")}),
        ("Estado", {"fields": ("estado",)}),
    )

    def porcentaje_display(self, obj):
        return format_html("<strong>{:.2f}%</strong>", obj.porcentaje if obj.porcentaje else 0)

    porcentaje_display.short_description = "Porcentaje"

    def activo_badge(self, obj):
        if obj.estado:
            return format_html('<span style="color: green; font-weight: bold;">✓ estado</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')

    activo_badge.short_description = "Estado"
