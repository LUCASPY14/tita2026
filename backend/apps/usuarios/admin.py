from django.contrib import admin
from django import forms
from django.utils import timezone
from django.utils.formats import sanitize_separators
from .models import (
    Empleados,
    Roles,
    PerfilesUsuario,
    UsuariosPortal,
    SesionesActivas,
    IntentosLogin,
)


class EmpleadosAdminForm(forms.ModelForm):
    fecha_ingreso = forms.DateTimeField(
        input_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
        widget=forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S'),
    )

    class Meta:
        model = Empleados
        fields = "__all__"


@admin.register(Empleados)
class EmpleadosAdmin(admin.ModelAdmin):
    form = EmpleadosAdminForm
    list_display = ["id_empleado", "nombre", "apellido", "usuario", "email", "estado"]
    list_filter = ["estado", "fecha_ingreso"]
    search_fields = ["nombre", "apellido", "email", "usuario"]
    ordering = ["apellido", "nombre"]


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ["id_rol", "nombre_rol", "descripcion", "estado"]
    list_filter = ["estado"]
    search_fields = ["nombre_rol"]
    ordering = ["nombre_rol"]


@admin.register(PerfilesUsuario)
class PerfilesUsuarioAdmin(admin.ModelAdmin):
    list_display = ["id_perfil", "id_empleado", "tema", "idioma", "timezone"]
    search_fields = ["tema", "idioma"]
    ordering = ["id_empleado"]


@admin.register(UsuariosPortal)
class UsuariosPortalAdmin(admin.ModelAdmin):
    list_display = ["id_usuario_portal", "email", "id_cliente", "estado", "fecha_registro"]
    list_filter = ["estado", "fecha_registro"]
    search_fields = ["email"]
    ordering = ["email"]


@admin.register(SesionesActivas)
class SesionesActivasAdmin(admin.ModelAdmin):
    list_display = ["id_sesion", "usuario", "tipo_usuario", "fecha_inicio", "activa"]
    list_filter = ["activa", "tipo_usuario"]
    search_fields = ["usuario"]
    ordering = ["-fecha_inicio"]


@admin.register(IntentosLogin)
class IntentosLoginAdmin(admin.ModelAdmin):
    list_display = ["id_intento", "usuario", "ip_address", "fecha_intento", "exitoso"]
    list_filter = ["exitoso", "fecha_intento"]
    search_fields = ["usuario", "ip_address"]
    ordering = ["-fecha_intento"]
