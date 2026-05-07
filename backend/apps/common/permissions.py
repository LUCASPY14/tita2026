"""
Permisos personalizados para la API REST
"""

from rest_framework import permissions


def _get_empleado_from_request(request):
    """
    Obtiene el Empleado a partir de los claims del JWT en el token de acceso.
    Si no hay JWT, intenta usar request.user.empleado (session auth / tests).
    Retorna None si no está disponible.
    """
    try:
        if request.auth and hasattr(request.auth, "payload"):
            id_empleado = request.auth.payload.get("id_empleado")
            if id_empleado:
                from apps.usuarios.models import Empleados

                return Empleados.objects.select_related("id_rol").get(pk=id_empleado)
    except Exception:
        pass
    # Fallback: user.empleado attribute (session auth / test mocks)
    try:
        emp = getattr(request.user, "empleado", None)
        if emp is not None and hasattr(emp, "id_rol"):
            return emp
    except Exception:
        pass
    return None


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite:
    - Lectura para cualquier usuario autenticado
    - Escritura solo para administradores/gerentes/supervisores
    """

    def has_permission(self, request, view):
        # Permitir métodos SAFE (GET, HEAD, OPTIONS) a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Permitir métodos de escritura a administradores Django (retrocompatibilidad)
        if request.user and request.user.is_staff:
            return True

        # Permitir escritura a empleados con roles de gestión
        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            roles_permitidos = ["administrador", "admin", "gerente", "supervisor"]
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        return False


class IsCajeroOrAdmin(permissions.BasePermission):
    """
    Permiso para cajeros y administradores
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Los administradores Django tienen acceso total
        if request.user.is_staff:
            return True

        # Verificar el rol del empleado vía JWT
        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            return empleado.id_rol.nombre_rol.lower() in ["cajero", "administrador", "admin", "gerente"]
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
        if hasattr(obj, "id_cliente"):
            try:
                return obj.id_cliente.user == request.user
            except:  # pragma: no cover
                return False

        if hasattr(obj, "usuario"):
            return obj.usuario == request.user

        return False


class IsClienteOrAdmin(permissions.BasePermission):
    """
    Permiso para clientes autenticados y administradores (empleados).
    Permite acceso a cualquier empleado autenticado vía JWT o a clientes de portal.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Administradores Django tienen acceso total (retrocompatibilidad)
        if request.user.is_staff:
            return True

        # Empleados autenticados vía JWT tienen acceso
        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            return True

        # Verificar si el usuario está asociado a un cliente (portal de clientes)
        try:
            return hasattr(request.user, "cliente")
        except:  # pragma: no cover
            return False


class CanManageVentas(permissions.BasePermission):
    """
    Permiso para gestionar ventas
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Administradores Django tienen acceso
        if request.user.is_staff:
            return True

        # Cajeros, administradores y gerentes pueden gestionar ventas
        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            roles_permitidos = ["cajero", "administrador", "admin", "gerente"]
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        return False


class CanManageInventario(permissions.BasePermission):
    """
    Permiso para gestionar inventario
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Administradores Django tienen acceso
        if request.user.is_staff:
            return True

        # Solo roles específicos pueden gestionar inventario
        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            roles_permitidos = ["administrador", "admin", "gerente", "encargado_inventario", "encargado compras"]
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        return False


class CanManageCompras(permissions.BasePermission):
    """
    Permite lecturas a cualquier empleado autenticado.
    Escritura restringida a administradores, gerentes y encargados de compras.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        empleado = _get_empleado_from_request(request)
        if empleado is not None:
            roles_permitidos = ["administrador", "admin", "gerente", "encargado compras", "encargado_compras"]
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura para todos los usuarios autenticados
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS and request.user.is_authenticated
