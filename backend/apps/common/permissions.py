"""
Permisos personalizados para la API REST
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite:
    - Lectura para cualquier usuario autenticado
    - Escritura solo para administradores
    """
    def has_permission(self, request, view):
        # Permitir métodos SAFE (GET, HEAD, OPTIONS) a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Permitir métodos de escritura solo a administradores
        return request.user and request.user.is_staff


class IsCajeroOrAdmin(permissions.BasePermission):
    """
    Permiso para cajeros y administradores
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # Verificar si el usuario tiene rol de cajero
        # Esto asume que existe un modelo Empleado vinculado al usuario
        try:
            empleado = request.user.empleado
            return empleado.id_rol.nombre_rol.lower() in ['cajero', 'administrador']
        except:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite:
    - Acceso total a administradores
    - Acceso solo a sus propios datos para usuarios normales
    """
    def has_object_permission(self, request, view, obj):
        # Administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # Verificar si el objeto pertenece al usuario
        # Esto asume que el objeto tiene un campo 'id_cliente' o 'usuario'
        if hasattr(obj, 'id_cliente'):
            try:
                return obj.id_cliente.user == request.user
            except:
                return False
        
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        return False


class IsClienteOrAdmin(permissions.BasePermission):
    """
    Permiso para clientes autenticados y administradores
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los administradores tienen acceso total
        if request.user.is_staff:
            return True
        
        # Verificar si el usuario está asociado a un cliente
        try:
            return hasattr(request.user, 'cliente')
        except:
            return False


class CanManageVentas(permissions.BasePermission):
    """
    Permiso para gestionar ventas
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores tienen acceso
        if request.user.is_staff:
            return True
        
        # Cajeros pueden crear y ver ventas
        try:
            empleado = request.user.empleado
            roles_permitidos = ['cajero', 'administrador', 'gerente']
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        except:
            return False


class CanManageInventario(permissions.BasePermission):
    """
    Permiso para gestionar inventario
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores tienen acceso
        if request.user.is_staff:
            return True
        
        # Solo roles específicos pueden gestionar inventario
        try:
            empleado = request.user.empleado
            roles_permitidos = ['administrador', 'gerente', 'encargado_inventario']
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        except:
            return False


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura para todos los usuarios autenticados
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS and request.user.is_authenticated
