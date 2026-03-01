"""
Permisos personalizados para la API
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que solo permite a los propietarios editar un objeto.
    """
    def has_object_permission(self, request, view, obj):
        # Los permisos de lectura están permitidos para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Los permisos de escritura solo están permitidos al propietario
        return obj.owner == request.user
