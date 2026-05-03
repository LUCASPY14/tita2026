"""
Admin configuration for Clientes module - Simple version for testing
"""

from django.contrib import admin

from .models import (
    AutorizacionesSaldoNegativo,
    Ciudad,
    Clientes,
    Grados,
    Hijos,
    HistorialGradosHijos,
    LogsAutorizaciones,
    Pais,
    RestriccionesHijos,
    TiposCliente,
)


@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ["id_cliente", "nombres", "apellidos", "ruc_ci", "email", "estado"]
    list_filter = ["estado"]
    search_fields = ["nombres", "apellidos", "ruc_ci", "email"]


@admin.register(TiposCliente)
class TiposClienteAdmin(admin.ModelAdmin):
    list_display = ["id_tipo_cliente", "nombre_tipo", "estado"]
    list_filter = ["estado"]
    search_fields = ["nombre_tipo"]


@admin.register(Hijos)
class HijosAdmin(admin.ModelAdmin):
    list_display = ["id_hijo", "nombre", "apellido", "grado", "estado"]
    list_filter = ["estado", "grado"]
    search_fields = ["nombre", "apellido"]

    fieldsets = (
        (
            "Información Personal",
            {"fields": ("nombre", "apellido", "fecha_nacimiento", "grado", "id_cliente_responsable")},
        ),
        ("Foto de Perfil", {"fields": ("foto_perfil", "fecha_foto")}),
        ("Estado", {"fields": ("estado",)}),
    )

    readonly_fields = ["fecha_foto"]


@admin.register(Grados)
class GradosAdmin(admin.ModelAdmin):
    list_display = ["id_grado", "nombre_grado", "nivel", "estado"]
    list_filter = ["estado", "nivel"]
    search_fields = ["nombre_grado"]


@admin.register(HistorialGradosHijos)
class HistorialGradosHijosAdmin(admin.ModelAdmin):
    list_display = [
        "id_historial",
        "id_hijo",
        "grado_anterior",
        "grado_nuevo",
        "anio_escolar",
        "fecha_cambio",
    ]
    list_filter = ["anio_escolar", "motivo"]
    search_fields = ["id_hijo__nombre", "id_hijo__apellido"]


@admin.register(RestriccionesHijos)
class RestriccionesHijosAdmin(admin.ModelAdmin):
    list_display = ["id_restriccion", "id_hijo", "tipo_restriccion", "severidad", "estado"]
    list_filter = ["estado", "severidad"]
    search_fields = ["tipo_restriccion"]


@admin.register(AutorizacionesSaldoNegativo)
class AutorizacionesSaldoNegativoAdmin(admin.ModelAdmin):
    list_display = [
        "id_autorizacion",
        "id_cliente",
        "monto_autorizado",
        "estado",
        "fecha_autorizacion",
    ]
    list_filter = ["estado"]
    search_fields = ["id_cliente__nombres", "id_cliente__apellidos"]


@admin.register(LogsAutorizaciones)
class LogsAutorizacionesAdmin(admin.ModelAdmin):
    list_display = ["id_log", "tipo_operacion", "resultado", "codigo_barra", "fecha_hora"]
    list_filter = ["tipo_operacion", "resultado"]
    search_fields = ["codigo_barra"]
    readonly_fields = ["id_log", "fecha_hora"]


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ["id_pais", "nombre"]
    search_fields = ["nombre"]


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ["id_ciudad", "nombre"]
    search_fields = ["nombre"]
