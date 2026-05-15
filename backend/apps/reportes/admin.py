"""
Admin para la app reportes
Gestión de plantillas de reportes
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import PlantillaReporte


@admin.register(PlantillaReporte)
class PlantillaReporteAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "tipo_badge",
        "frecuencia_badge",
        "descripcion",
        "activo",
    ]
    list_filter = ["activo", "tipo", "frecuencia"]
    search_fields = ["nombre", "descripcion"]
    readonly_fields = ["fecha_creacion"]
    ordering = ["tipo", "nombre"]
    fieldsets = (
        ("Datos del Reporte", {
            "fields": ("nombre", "descripcion", "tipo", "frecuencia", "activo")
        }),
        ("Configuración", {
            "fields": ("query_sql", "parametros"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def tipo_badge(self, obj):
        colors = {
            "VENTAS": "#28a745",
            "COMPRAS": "#0d6efd",
            "INVENTARIO": "#ffc107",
            "CUENTA_CORRIENTE": "#17a2b8",
            "ALMUERZOS": "#fd7e14",
            "CAJA": "#6610f2",
            "TRIBUTARIO": "#dc3545",
        }
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def frecuencia_badge(self, obj):
        colors = {
            "DIARIO": "#0d6efd",
            "SEMANAL": "#17a2b8",
            "MENSUAL": "#28a745",
            "ANUAL": "#6610f2",
            "PERSONALIZADO": "#fd7e14",
        }
        color = colors.get(obj.frecuencia, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_frecuencia_display(),
        )
    frecuencia_badge.short_description = "Frecuencia"