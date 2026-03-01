from django.contrib import admin
from .models import (
    Empleados,
    Roles,
    PerfilesUsuario,
    UsuariosPortal,
    SesionesActivas,
    IntentosLogin
)

@admin.register(Empleados)
class EmpleadosAdmin(admin.ModelAdmin):
    list_display = ['id_empleado', 'nombre', 'apellido', 'usuario', 'email', 'activo']
    list_filter = ['activo', 'fecha_ingreso']
    search_fields = ['nombre', 'apellido', 'email', 'usuario']
    ordering = ['apellido', 'nombre']

@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ['id_rol', 'nombre_rol', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre_rol']
    ordering = ['nombre_rol']

@admin.register(PerfilesUsuario)
class PerfilesUsuarioAdmin(admin.ModelAdmin):
    list_display = ['id_perfil', 'id_empleado', 'tema', 'idioma', 'timezone']
    search_fields = ['tema', 'idioma']
    ordering = ['id_empleado']

@admin.register(UsuariosPortal)
class UsuariosPortalAdmin(admin.ModelAdmin):
    list_display = ['id_usuario_portal', 'email', 'id_cliente', 'activo', 'fecha_registro']
    list_filter = ['activo', 'fecha_registro']
    search_fields = ['email']
    ordering = ['email']

@admin.register(SesionesActivas)
class SesionesActivasAdmin(admin.ModelAdmin):
    list_display = ['id_sesion', 'usuario', 'tipo_usuario', 'fecha_inicio', 'activa']
    list_filter = ['activa', 'tipo_usuario']
    search_fields = ['usuario']
    ordering = ['-fecha_inicio']

@admin.register(IntentosLogin)
class IntentosLoginAdmin(admin.ModelAdmin):
    list_display = ['id_intento', 'usuario', 'ip_address', 'fecha_intento', 'exitoso']
    list_filter = ['exitoso', 'fecha_intento']
    search_fields = ['usuario', 'ip_address']
    ordering = ['-fecha_intento']
