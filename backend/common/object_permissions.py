"""
Object-level permission mixins para DRF.

Uso: agregar `CajaOwnerQuerysetMixin` al ViewSet antes de `viewsets.ModelViewSet`.
El mixin sobreescribe `get_queryset()` llamando primero al super() y luego filtrando
por usuario cuando el rol es CAJERO, sin afectar ADMIN/SUPERVISOR.
"""
from rest_framework.permissions import BasePermission


ROL_CAJERO = "CAJERO"


class CajaOwnerQuerysetMixin:
    """
    Cajeros solo ven registros donde *ellos* son el empleado/cajero.
    ADMIN y SUPERVISOR ven todo.

    Requiere que el ViewSet tenga definido `cajero_field`: el nombre del campo
    FK que apunta al usuario en el queryset base (ej. 'cajero', 'empleado').
    """
    cajero_field: str = "cajero"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "rol", None) == ROL_CAJERO:
            qs = qs.filter(**{self.cajero_field: user})
        return qs


class IsCajaOwnerOrAdmin(BasePermission):
    """
    A nivel de objeto: el cajero solo puede leer/modificar su propio CierreCaja.
    ADMIN puede hacer cualquier cosa.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, "rol", None) == "ADMIN":
            return True
        # Soporte para objetos con campo `empleado` (CierreCaja) o `cajero` (Venta)
        owner = getattr(obj, "empleado", None) or getattr(obj, "cajero", None)
        return owner == user
