"""
Permisos personalizados para la API
"""
import functools
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsAdmin(permissions.BasePermission):
    """Solo usuarios con rol ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == "ADMIN")


class IsCajeroOrAdmin(permissions.BasePermission):
    """Cajeros y administradores."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in ("ADMIN", "CAJERO")
        )


class IsStaffUser(permissions.BasePermission):
    """Cualquier usuario interno (ADMIN, CAJERO, COCINA) — excluye CLIENTE_WEB."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in ("ADMIN", "CAJERO", "COCINA")
        )


class IsClienteWeb(permissions.BasePermission):
    """Solo usuarios del portal de padres (CLIENTE_WEB)."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol == "CLIENTE_WEB"
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Solo ADMIN puede escribir; staff puede leer."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return request.user.rol in ("ADMIN", "CAJERO", "COCINA")
        return request.user.rol == "ADMIN"


class IsStaffOrClienteWeb(permissions.BasePermission):
    """Staff puede leer y escribir; CLIENTE_WEB solo puede leer (GET/HEAD/OPTIONS)."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.rol in ("ADMIN", "CAJERO", "COCINA"):
            return True
        if request.user.rol == "CLIENTE_WEB":
            return request.method in permissions.SAFE_METHODS
        return False


def require_permission(modulo: str, accion: str):
    """
    Decorador para vistas de clase o acciones de ViewSet que verifica que
    el usuario tenga el permiso (modulo, accion) en RolPermiso.

    Uso:
        @require_permission("ventas", "anular")
        def anular(self, request, pk=None): ...

    Los ADMINs siempre pasan. Para otros roles se consulta RolPermiso.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(self_or_view, request, *args, **kwargs):
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                raise PermissionDenied("Autenticación requerida.")
            if user.rol == "ADMIN":
                return view_func(self_or_view, request, *args, **kwargs)
            # Verificar en RolPermiso
            try:
                from apps.usuarios.models import RolPermiso, Permiso
                tiene = RolPermiso.objects.filter(
                    id_rol__nombre=user.rol,
                    id_permiso__modulo=modulo,
                    id_permiso__accion=accion,
                ).exists()
            except Exception:
                tiene = False
            if not tiene:
                raise PermissionDenied(f"No tenés permiso para '{accion}' en '{modulo}'.")
            return view_func(self_or_view, request, *args, **kwargs)
        return wrapper
    return decorator
