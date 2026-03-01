from django.contrib import admin
from .models import (
    PlantillasReporte,
    Dashboards,
    KpiMetricas,
    ValoresKpi
)

@admin.register(PlantillasReporte)
class PlantillasReporteAdmin(admin.ModelAdmin):
    list_display = ['id_template', 'nombre', 'tipo_reporte', 'frecuencia', 'activo']
    list_filter = ['tipo_reporte', 'frecuencia', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

@admin.register(Dashboards)
class DashboardsAdmin(admin.ModelAdmin):
    list_display = ['id_dashboard', 'nombre', 'id_empleado', 'es_publico', 'activo']
    list_filter = ['es_publico', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

@admin.register(KpiMetricas)
class KpiMetricasAdmin(admin.ModelAdmin):
    list_display = ['id_kpi', 'nombre', 'unidad', 'categoria', 'activo']
    list_filter = ['activo', 'categoria']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(ValoresKpi)
class ValoresKpiAdmin(admin.ModelAdmin):
    list_display = ['id_valor', 'id_kpi', 'fecha', 'valor']
    list_filter = ['fecha']
    ordering = ['-fecha']
