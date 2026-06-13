"""
Admin para la app usuarios
Gestion de usuarios, empleados, roles y permisos
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Usuario,
    Empleado,
    Rol,
    Permiso,
    RolPermiso,
    PerfilUsuario,
    Autenticacion2FA,
    Intento2FA,
    IntentoLogin,
    SesionActiva,
    RenovacionSesion,
    PatronAcceso,
    BloqueoCuenta,
    TokenRecuperacion,
    TokenVerificacion,
    AuditoriaEmpleado,
    AuditoriaOperacion,
    AuditoriaUsuarioWeb,
)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "nombre_completo",
        "rol_badge",
        "is_active",
        "is_staff",
        "ultimo_acceso",
    ]
    list_filter = ["rol", "is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "nombre", "apellido"]
    ordering = ["email"]
    readonly_fields = ["fecha_creacion", "ultimo_acceso"]
    fieldsets = (
        ("Credenciales", {
            "fields": ("email", "password")
        }),
        ("Datos Personales", {
            "fields": ("nombre", "apellido", "rol")
        }),
        ("Relaciones", {
            "fields": ("cliente", "empleado_legacy")
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Auditoria", {
            "fields": ("email_verificado", "ultimo_acceso", "fecha_creacion", "fecha_baja"),
            "classes": ("collapse",),
        }),
    )
    add_fieldsets = (
        ("Credenciales", {
            "fields": ("email", "password1", "password2")
        }),
        ("Datos Personales", {
            "fields": ("nombre", "apellido", "rol")
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser")
        }),
    )

    def rol_badge(self, obj):
        colors = {
            "ADMIN": "#6610f2",
            "CAJERO": "#0d6efd",
            "COCINA": "#17a2b8",
            "CLIENTE_WEB": "#6c757d",
        }
        color = colors.get(obj.rol, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_rol_display(),
        )
    rol_badge.short_description = "Rol"


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre_completo",
        "email",
        "telefono",
        "rol_link",
        "estado",
        "fecha_ingreso",
    ]
    list_filter = ["estado", "id_rol"]
    search_fields = ["nombre", "apellido", "email"]
    ordering = ["apellido", "nombre"]
    list_select_related = ["id_rol"]

    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = "Nombre"

    def rol_link(self, obj):
        url = reverse("admin:usuarios_rol_change", args=[obj.id_rol.pk])
        return format_html('<a href="{}">{}</a>', url, obj.id_rol.nombre_rol)
    rol_link.short_description = "Rol"


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["nombre_rol", "descripcion", "estado"]
    list_filter = ["estado"]
    search_fields = ["nombre_rol"]


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ["codigo_permiso", "nombre", "modulo", "estado"]
    list_filter = ["estado", "modulo"]
    search_fields = ["codigo_permiso", "nombre"]
    readonly_fields = ["fecha_creacion"]
    ordering = ["modulo", "codigo_permiso"]


@admin.register(RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ["pk", "rol_link", "permiso_link", "fecha_asignacion"]
    list_filter = ["id_rol"]
    search_fields = ["id_rol__nombre_rol", "id_permiso__codigo_permiso"]
    readonly_fields = ["fecha_asignacion"]
    list_select_related = ["id_rol", "id_permiso"]

    def rol_link(self, obj):
        url = reverse("admin:usuarios_rol_change", args=[obj.id_rol.pk])
        return format_html('<a href="{}">{}</a>', url, obj.id_rol.nombre_rol)
    rol_link.short_description = "Rol"

    def permiso_link(self, obj):
        url = reverse("admin:usuarios_permiso_change", args=[obj.id_permiso.pk])
        return format_html('<a href="{}">{}</a>', url, obj.id_permiso.codigo_permiso)
    permiso_link.short_description = "Permiso"


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "tema", "idioma", "moneda"]
    list_filter = ["tema", "idioma"]
    search_fields = ["usuario__email"]
    list_select_related = ["usuario"]
    readonly_fields = ["created_at", "updated_at"]

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(Autenticacion2FA)
class Autenticacion2FAAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "habilitado", "fecha_activacion", "ultima_verificacion"]
    list_filter = ["habilitado"]
    search_fields = ["usuario__email"]
    readonly_fields = ["fecha_creacion", "secret_key", "backup_codes"]
    list_select_related = ["usuario"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(Intento2FA)
class Intento2FAAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "exitoso", "ip_address", "fecha_intento"]
    list_filter = ["exitoso", "fecha_intento"]
    search_fields = ["usuario__email", "ip_address"]
    readonly_fields = ["fecha_intento"]
    list_select_related = ["usuario"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(IntentoLogin)
class IntentoLoginAdmin(admin.ModelAdmin):
    list_display = ["email", "exitoso", "ip_address", "motivo_fallo", "fecha_intento"]
    list_filter = ["exitoso", "fecha_intento"]
    search_fields = ["email", "ip_address"]
    readonly_fields = ["fecha_intento"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields


@admin.register(SesionActiva)
class SesionActivaAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "session_key", "ip_address", "activa", "fecha_inicio"]
    list_filter = ["activa"]
    search_fields = ["usuario__email", "ip_address"]
    readonly_fields = ["fecha_inicio", "ultima_actividad"]
    list_select_related = ["usuario"]

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(RenovacionSesion)
class RenovacionSesionAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "ip_address", "fecha_renovacion"]
    search_fields = ["usuario__email", "ip_address"]
    readonly_fields = ["fecha_renovacion"]
    list_select_related = ["usuario"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(PatronAcceso)
class PatronAccesoAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "ip_address", "es_habitual", "frecuencia_accesos"]
    list_filter = ["es_habitual"]
    search_fields = ["usuario__email", "ip_address"]
    readonly_fields = ["primera_deteccion", "ultima_deteccion"]
    list_select_related = ["usuario"]

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(BloqueoCuenta)
class BloqueoCuentaAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "motivo", "estado", "fecha_bloqueo", "fecha_desbloqueo"]
    list_filter = ["estado"]
    search_fields = ["usuario__email", "motivo"]
    readonly_fields = ["fecha_bloqueo"]
    list_select_related = ["usuario"]

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "usado", "fecha_creacion", "fecha_expiracion"]
    list_filter = ["usado"]
    search_fields = ["usuario__email"]
    readonly_fields = ["fecha_creacion", "token"]
    list_select_related = ["usuario"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(TokenVerificacion)
class TokenVerificacionAdmin(admin.ModelAdmin):
    list_display = ["usuario_link", "tipo", "usado", "fecha_creacion"]
    list_filter = ["tipo", "usado"]
    search_fields = ["usuario__email"]
    readonly_fields = ["fecha_creacion", "token"]
    list_select_related = ["usuario"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
    usuario_link.short_description = "Usuario"


@admin.register(AuditoriaEmpleado)
class AuditoriaEmpleadoAdmin(admin.ModelAdmin):
    list_display = ["empleado_link", "campo_modificado", "fecha_cambio"]
    list_filter = ["fecha_cambio"]
    search_fields = ["empleado__nombre", "empleado__apellido", "campo_modificado"]
    readonly_fields = ["fecha_cambio"]
    list_select_related = ["empleado"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def empleado_link(self, obj):
        if obj.empleado:
            url = reverse("admin:usuarios_empleado_change", args=[obj.empleado.pk])
            return format_html('<a href="{}">{}</a>', url, obj.empleado)
        return "-"
    empleado_link.short_description = "Empleado"


@admin.register(AuditoriaOperacion)
class AuditoriaOperacionAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "usuario_link",
        "operacion",
        "tabla_afectada",
        "resultado",
        "fecha_operacion",
    ]
    list_filter = ["resultado", "fecha_operacion"]
    search_fields = ["usuario__email", "operacion", "tabla_afectada"]
    readonly_fields = ["fecha_operacion"]
    list_select_related = ["usuario"]
    date_hierarchy = "fecha_operacion"
    ordering = ["-fecha_operacion"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def usuario_link(self, obj):
        if obj.usuario:
            url = reverse("admin:usuarios_usuario_change", args=[obj.usuario.pk])
            return format_html('<a href="{}">{}</a>', url, obj.usuario.email)
        return "-"
    usuario_link.short_description = "Usuario"


@admin.register(AuditoriaUsuarioWeb)
class AuditoriaUsuarioWebAdmin(admin.ModelAdmin):
    list_display = ["cliente_link", "campo_modificado", "fecha_cambio"]
    list_filter = ["fecha_cambio"]
    search_fields = ["cliente__ruc_ci", "cliente__nombres", "campo_modificado"]
    readonly_fields = ["fecha_cambio"]
    list_select_related = ["cliente"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def cliente_link(self, obj):
        if obj.cliente:
            url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
            return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
        return "-"
    cliente_link.short_description = "Cliente"
