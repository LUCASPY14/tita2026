from django.contrib import admin

from .models import CierreCuentaAlumno, ResolucionSaldo


@admin.register(CierreCuentaAlumno)
class CierreCuentaAlumnoAdmin(admin.ModelAdmin):
    list_display = ["hijo", "anio", "estado", "saldo_cantina_inicial", "saldo_almuerzo_inicial", "fecha_apertura"]
    list_filter = ["anio", "estado"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    readonly_fields = [f.name for f in CierreCuentaAlumno._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ResolucionSaldo)
class ResolucionSaldoAdmin(admin.ModelAdmin):
    list_display = ["id_resolucion", "cierre", "tipo", "monto", "estado", "solicitado_por", "fecha_solicitud"]
    list_filter = ["tipo", "estado"]
    readonly_fields = [f.name for f in ResolucionSaldo._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
