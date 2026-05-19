"""
Permisos personalizados para la API
"""
from rest_framework import permissions


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
