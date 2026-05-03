from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Dashboards,
    DestinatariosTarea,
    EjecucionesTarea,
    KpiMetricas,
    PlantillasReporte,
    PlantillasTarea,
    ValoresKpi,
)

# =============================================================================
# ADMIN - PLANTILLAS DE REPORTE
# =============================================================================


@admin.register(PlantillasReporte)
class PlantillasReporteAdmin(admin.ModelAdmin):
    list_display = [
        "id_template",
        "nombre",
        "tipo_reporte_badge",
        "frecuencia_badge",
        "activo_badge",
        "created_at",
    ]
    list_filter = ["tipo_reporte", "frecuencia", "estado", "created_at"]
    search_fields = ["nombre", "descripcion"]
    ordering = ["nombre"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Información General", {"fields": ("nombre", "descripcion", "estado")}),
        (
            "Configuración del Reporte",
            {"fields": ("query_sql", "parametros", "tipo_reporte", "frecuencia")},
        ),
        ("Auditoría", {"fields": ("created_by", "created_at"), "classes": ("collapse",)}),
    )

    def tipo_reporte_badge(self, obj):
        """Muestra el tipo de reporte con badge de color"""
        colores = {
            "Ventas": "green",
            "Inventario": "blue",
            "Compras": "orange",
            "Financiero": "purple",
            "Cliente": "cyan",
            "Empleado": "pink",
            "Personalizado": "gray",
        }
        color = colores.get(obj.tipo_reporte, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.tipo_reporte,
        )

    tipo_reporte_badge.short_description = "Tipo"

    def frecuencia_badge(self, obj):
        """Muestra la frecuencia con badge de color"""
        colores = {
            "Diario": "green",
            "Semanal": "blue",
            "Mensual": "orange",
            "Trimestral": "purple",
            "Anual": "red",
            "Manual": "gray",
        }
        color = colores.get(obj.frecuencia, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            color,
            obj.frecuencia,
        )

    frecuencia_badge.short_description = "Frecuencia"

    def activo_badge(self, obj):
        """Muestra el estado estado con badge de color"""
        if obj.estado:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓ estado",
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "✗ Inactivo",
        )

    activo_badge.short_description = "Estado"


# =============================================================================
# ADMIN - DASHBOARDS
# =============================================================================


@admin.register(Dashboards)
class DashboardsAdmin(admin.ModelAdmin):
    list_display = [
        "id_dashboard",
        "nombre",
        "id_empleado",
        "es_publico_badge",
        "predeterminado_badge",
        "activo_badge",
    ]
    list_filter = ["es_publico", "predeterminado", "estado", "created_at"]
    search_fields = ["nombre", "descripcion"]
    ordering = ["nombre"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Información General", {"fields": ("nombre", "descripcion", "id_empleado", "estado")}),
        ("Configuración", {"fields": ("configuracion", "es_publico", "predeterminado")}),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def es_publico_badge(self, obj):
        """Muestra si es público con badge de color"""
        if obj.es_publico == 1:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "🌐 Público",
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "🔒 Privado",
        )

    es_publico_badge.short_description = "Acceso"

    def predeterminado_badge(self, obj):
        """Muestra si es predeterminado con badge de color"""
        if obj.predeterminado == 1:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "⭐ Predeterminado",
            )
        return format_html(
            '<span style="background-color: lightgray; color: black; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            "Normal",
        )

    predeterminado_badge.short_description = "Tipo"

    def activo_badge(self, obj):
        """Muestra el estado estado con badge de color"""
        if obj.estado:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓ estado",
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "✗ Inactivo",
        )

    activo_badge.short_description = "Estado"


# =============================================================================
# ADMIN - KPI MÉTRICAS
# =============================================================================


@admin.register(KpiMetricas)
class KpiMetricasAdmin(admin.ModelAdmin):
    list_display = [
        "id_kpi",
        "nombre",
        "unidad",
        "valor_objetivo_display",
        "categoria_badge",
        "frecuencia_badge",
        "activo_badge",
    ]
    list_filter = ["estado", "categoria", "frecuencia", "unidad"]
    search_fields = ["nombre", "descripcion"]
    ordering = ["nombre"]

    fieldsets = (
        ("Información General", {"fields": ("nombre", "descripcion", "estado")}),
        (
            "Configuración del KPI",
            {"fields": ("formula", "unidad", "valor_objetivo", "categoria", "frecuencia")},
        ),
    )

    def valor_objetivo_display(self, obj):
        """Muestra el valor objetivo con formato"""
        if obj.valor_objetivo:
            return f"{obj.valor_objetivo:,.2f} {obj.unidad}"
        return "-"

    valor_objetivo_display.short_description = "Objetivo"

    def categoria_badge(self, obj):
        """Muestra la categoría con badge de color"""
        colores = {
            "Ventas": "green",
            "Inventario": "blue",
            "Compras": "orange",
            "Financiero": "purple",
            "Cliente": "cyan",
            "Empleado": "pink",
            "Operacional": "brown",
        }
        color = colores.get(obj.categoria, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            color,
            obj.categoria,
        )

    categoria_badge.short_description = "Categoría"

    def frecuencia_badge(self, obj):
        """Muestra la frecuencia con badge de color"""
        colores = {
            "Diario": "green",
            "Semanal": "blue",
            "Mensual": "orange",
            "Trimestral": "purple",
            "Anual": "red",
        }
        color = colores.get(obj.frecuencia, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            color,
            obj.frecuencia,
        )

    frecuencia_badge.short_description = "Frecuencia"

    def activo_badge(self, obj):
        """Muestra el estado estado con badge de color"""
        if obj.estado:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓ estado",
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "✗ Inactivo",
        )

    activo_badge.short_description = "Estado"


# =============================================================================
# ADMIN - VALORES KPI
# =============================================================================


@admin.register(ValoresKpi)
class ValoresKpiAdmin(admin.ModelAdmin):
    list_display = ["id_valor", "id_kpi", "fecha", "valor_display", "auto_calc_badge", "created_at"]
    list_filter = ["fecha", "auto_calc", "created_at"]
    search_fields = ["id_kpi__nombre", "notas"]
    ordering = ["-fecha"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Información General", {"fields": ("id_kpi", "fecha", "valor", "auto_calc")}),
        ("Detalles", {"fields": ("notas", "created_at"), "classes": ("collapse",)}),
    )

    def valor_display(self, obj):
        """Muestra el valor con formato y unidad"""
        unidad = obj.id_kpi.unidad if obj.id_kpi else ""
        return f"{obj.valor:,.2f} {unidad}"

    valor_display.short_description = "Valor"

    def auto_calc_badge(self, obj):
        """Muestra si es auto-calculado con badge de color"""
        if obj.auto_calc == 1:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "🤖 Auto",
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "👤 Manual",
        )

    auto_calc_badge.short_description = "Tipo"


# =============================================================================
# ADMIN - PLANTILLAS DE TAREA
# =============================================================================


@admin.register(PlantillasTarea)
class PlantillasTareaAdmin(admin.ModelAdmin):
    list_display = [
        "id_plantilla",
        "nombre",
        "tipo_tarea_badge",
        "frecuencia_badge",
        "cron_display",
        "timeout_display",
        "activo_badge",
    ]
    list_filter = ["tipo_tarea", "frecuencia", "estado", "created_at"]
    search_fields = ["nombre", "descripcion", "comando"]
    ordering = ["nombre"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Información General", {"fields": ("nombre", "descripcion", "tipo_tarea", "estado")}),
        (
            "Configuración de Ejecución",
            {
                "fields": (
                    "comando",
                    "parametros",
                    "frecuencia",
                    "cron",
                    "timeout",
                    "max_reintentos",
                )
            },
        ),
        ("Notificaciones", {"fields": ("notif_exito", "notif_error")}),
        ("Auditoría", {"fields": ("created_by", "created_at"), "classes": ("collapse",)}),
    )

    def tipo_tarea_badge(self, obj):
        """Muestra el tipo de tarea con badge de color"""
        colores = {
            "Reporte": "blue",
            "Backup": "green",
            "Limpieza": "orange",
            "Sincronización": "purple",
            "Cálculo": "cyan",
            "Notificación": "pink",
            "Personalizado": "gray",
        }
        color = colores.get(obj.tipo_tarea, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.tipo_tarea,
        )

    tipo_tarea_badge.short_description = "Tipo"

    def frecuencia_badge(self, obj):
        """Muestra la frecuencia con badge de color"""
        colores = {
            "Cada hora": "green",
            "Diario": "blue",
            "Semanal": "orange",
            "Mensual": "purple",
            "Personalizado": "gray",
        }
        color = colores.get(obj.frecuencia, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            color,
            obj.frecuencia,
        )

    frecuencia_badge.short_description = "Frecuencia"

    def cron_display(self, obj):
        """Muestra la expresión cron de forma legible"""
        if obj.cron:
            return format_html("<code>{}</code>", obj.cron)
        return "-"

    cron_display.short_description = "Cron"

    def timeout_display(self, obj):
        """Muestra el timeout en formato legible"""
        if obj.timeout:
            hours = obj.timeout // 3600
            minutes = (obj.timeout % 3600) // 60
            seconds = obj.timeout % 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"

    timeout_display.short_description = "Timeout"

    def activo_badge(self, obj):
        """Muestra el estado estado con badge de color"""
        if obj.estado:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓ estado",
            )
        return format_html(
            '<span style="background-color: red; color: white; padding: 3px 10px; ' 'border-radius: 3px;">{}</span>',
            "✗ Inactivo",
        )

    activo_badge.short_description = "Estado"


# =============================================================================
# ADMIN - EJECUCIONES DE TAREA
# =============================================================================


@admin.register(EjecucionesTarea)
class EjecucionesTareaAdmin(admin.ModelAdmin):
    list_display = [
        "id_ejecucion",
        "id_plantilla",
        "fecha_inicio",
        "estado_badge",
        "duracion_display",
        "ejecutado_por",
        "servidor",
    ]
    list_filter = ["estado", "fecha_inicio", "servidor"]
    search_fields = ["id_plantilla__nombre", "servidor", "resultado", "error_msg"]
    ordering = ["-fecha_inicio"]
    readonly_fields = ["fecha_inicio", "fecha_fin", "duracion_seg"]

    fieldsets = (
        ("Información General", {"fields": ("id_plantilla", "estado", "servidor", "pid")}),
        ("Tiempos de Ejecución", {"fields": ("fecha_inicio", "fecha_fin", "duracion_seg")}),
        ("Resultados", {"fields": ("resultado", "error_msg", "logs")}),
        ("Auditoría", {"fields": ("ejecutado_por", "parametros"), "classes": ("collapse",)}),
    )

    def estado_badge(self, obj):
        """Muestra el estado con badge de color"""
        colores = {
            "Pendiente": "orange",
            "Ejecutando": "blue",
            "Exitoso": "green",
            "Fallido": "red",
            "Cancelado": "gray",
            "Timeout": "darkred",
        }
        iconos = {
            "Pendiente": "⏳",
            "Ejecutando": "▶",
            "Exitoso": "✓",
            "Fallido": "✗",
            "Cancelado": "⊘",
            "Timeout": "⏱",
        }
        color = colores.get(obj.estado, "gray")
        icono = iconos.get(obj.estado, "•")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icono,
            obj.estado,
        )

    estado_badge.short_description = "Estado"

    def duracion_display(self, obj):
        """Muestra la duración en formato legible"""
        if obj.duracion_seg is not None:
            hours = obj.duracion_seg // 3600
            minutes = (obj.duracion_seg % 3600) // 60
            seconds = obj.duracion_seg % 60

            if hours > 0:
                return format_html("<strong>{}h {}m {}s</strong>", hours, minutes, seconds)
            elif minutes > 0:
                return format_html("<strong>{}m {}s</strong>", minutes, seconds)
            else:
                return format_html("<strong>{}s</strong>", seconds)
        return "-"

    duracion_display.short_description = "Duración"


# =============================================================================
# ADMIN - DESTINATARIOS DE TAREA
# =============================================================================


@admin.register(DestinatariosTarea)
class DestinatariosTareaAdmin(admin.ModelAdmin):
    list_display = [
        "id_destinatario",
        "id_plantilla",
        "id_empleado",
        "notif_inicio_badge",
        "notif_fin_badge",
        "notif_error_badge",
    ]
    list_filter = ["notif_inicio", "notif_fin", "notif_error"]
    search_fields = ["id_plantilla__nombre", "id_empleado__nombre"]
    ordering = ["id_plantilla", "id_empleado"]

    fieldsets = (
        ("Información General", {"fields": ("id_plantilla", "id_empleado")}),
        ("Preferencias de Notificación", {"fields": ("notif_inicio", "notif_fin", "notif_error")}),
    )

    def notif_inicio_badge(self, obj):
        """Muestra si se notifica al inicio con badge"""
        if obj.notif_inicio == 1:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓",
            )
        return format_html(
            '<span style="background-color: lightgray; color: black; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            "✗",
        )

    notif_inicio_badge.short_description = "Inicio"

    def notif_fin_badge(self, obj):
        """Muestra si se notifica al finalizar con badge"""
        if obj.notif_fin == 1:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓",
            )
        return format_html(
            '<span style="background-color: lightgray; color: black; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            "✗",
        )

    notif_fin_badge.short_description = "Fin"

    def notif_error_badge(self, obj):
        """Muestra si se notifica en error con badge"""
        if obj.notif_error == 1:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; '
                'border-radius: 3px;">{}</span>',
                "✓",
            )
        return format_html(
            '<span style="background-color: lightgray; color: black; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            "✗",
        )

    notif_error_badge.short_description = "Error"
