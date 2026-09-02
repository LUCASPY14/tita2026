"""
Permisos personalizados para la API
"""
from rest_framework import permissions

# Roles internos del sistema (excluye CLIENTE_WEB)
_STAFF_ROLES = frozenset({"ADMIN", "CAJERO", "COCINA", "SUPERVISOR", "COBRADOR"})

# Roles que operan el POS directamente
_POS_ROLES = frozenset({"ADMIN", "CAJERO"})


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
    """Operadores del POS: cajeros y administradores."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in _POS_ROLES
        )


class IsCajeroCobradorOrAdmin(permissions.BasePermission):
    """Cajeros, cobradores y administradores — operaciones de cobranza presencial."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in {"ADMIN", "CAJERO", "COBRADOR"}
        )


class IsCajeroCobradorSupervisorOrAdmin(permissions.BasePermission):
    """Cajeros, cobradores, supervisores y administradores — cobranza presencial y su supervisión."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in {"ADMIN", "CAJERO", "COBRADOR", "SUPERVISOR"}
        )


class IsStaffUser(permissions.BasePermission):
    """Cualquier usuario interno (excluye CLIENTE_WEB)."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in _STAFF_ROLES
        )


class IsClienteWeb(permissions.BasePermission):
    """Solo usuarios del portal de padres (CLIENTE_WEB)."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol == "CLIENTE_WEB"
        )


class IsAdminOrSupervisor(permissions.BasePermission):
    """Solo ADMIN y SUPERVISOR."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol in {"ADMIN", "SUPERVISOR"}
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Solo ADMIN puede escribir; cualquier staff puede leer."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return request.user.rol in _STAFF_ROLES
        return request.user.rol == "ADMIN"


class IsStaffOrClienteWeb(permissions.BasePermission):
    """Staff puede leer y escribir; CLIENTE_WEB solo puede leer (GET/HEAD/OPTIONS)."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.rol in _STAFF_ROLES:
            return True
        if request.user.rol == "CLIENTE_WEB":
            return request.method in permissions.SAFE_METHODS
        return False
