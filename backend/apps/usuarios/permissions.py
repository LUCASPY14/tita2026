"""
Sistema de permisos granulares para cantina_tita
Integración con Django REST Framework
"""

from typing import List, Optional, Dict
from functools import wraps

from django.db import models, transaction
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.usuarios.models import Empleados, Roles

# ==================== MODELO DE PERMISOS ====================


class Permisos(models.Model):
    """
    Tabla de permisos disponibles en el sistema.
    """

    id = models.AutoField(primary_key=True)
    codigo_permiso = models.CharField(
        max_length=100, unique=True, help_text="Código único del permiso (ej: 'ventas.crear')"
    )
    nombre = models.CharField(max_length=100, help_text="Nombre descriptivo del permiso")
    modulo = models.CharField(
        max_length=50, help_text="Módulo al que pertenece (ventas, inventario, usuarios, etc)"
    )
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permisos"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ["modulo", "codigo_permiso"]

    def __str__(self):
        return f"{self.codigo_permiso} - {self.nombre}"


class RolesPermisos(models.Model):
    """
    Relación muchos a muchos entre roles y permisos.
    """

    id = models.AutoField(primary_key=True)
    id_rol = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column="id_rol")
    id_permiso = models.ForeignKey(Permisos, on_delete=models.CASCADE, db_column="id_permiso")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        Empleados, on_delete=models.SET_NULL, null=True, blank=True, db_column="asignado_por"
    )

    class Meta:
        db_table = "roles_permisos"
        verbose_name = "Rol-Permiso"
        verbose_name_plural = "Roles-Permisos"
        unique_together = [["id_rol", "id_permiso"]]

    def __str__(self):
        return f"{self.id_rol.nombre_rol} - {self.id_permiso.codigo_permiso}"


# ==================== SERVICIO DE PERMISOS ====================


class PermissionService:
    """
    Servicio centralizado para gestionar y verificar permisos.
    """

    # Permisos predefinidos del sistema
    PERMISOS_SISTEMA = {
        # Usuarios
        "usuarios.ver": "Ver usuarios",
        "usuarios.crear": "Crear usuarios",
        "usuarios.editar": "Editar usuarios",
        "usuarios.eliminar": "Eliminar usuarios",
        "usuarios.administrar_roles": "Administrar roles y permisos",
        "usuarios.ver_auditoria": "Ver auditoría de usuarios",
        # Ventas
        "ventas.ver": "Ver ventas",
        "ventas.crear": "Crear ventas",
        "ventas.editar": "Editar ventas",
        "ventas.anular": "Anular ventas",
        "ventas.ver_reportes": "Ver reportes de ventas",
        "ventas.aplicar_descuentos": "Aplicar descuentos",
        # Compras
        "compras.ver": "Ver compras",
        "compras.crear": "Crear órdenes de compra",
        "compras.editar": "Editar órdenes de compra",
        "compras.aprobar": "Aprobar órdenes de compra",
        "compras.anular": "Anular compras",
        # Inventario
        "inventario.ver": "Ver inventario",
        "inventario.ajustar": "Realizar ajustes de inventario",
        "inventario.transferir": "Transferir stock",
        "inventario.ver_valorizado": "Ver inventario valorizado",
        # Productos
        "productos.ver": "Ver productos",
        "productos.crear": "Crear productos",
        "productos.editar": "Editar productos",
        "productos.eliminar": "Eliminar productos",
        "productos.gestionar_precios": "Gestionar precios",
        # Clientes
        "clientes.ver": "Ver clientes",
        "clientes.crear": "Crear clientes",
        "clientes.editar": "Editar clientes",
        "clientes.eliminar": "Eliminar clientes",
        "clientes.ver_creditos": "Ver créditos de clientes",
        # Reportes
        "reportes.ventas": "Ver reportes de ventas",
        "reportes.inventario": "Ver reportes de inventario",
        "reportes.financieros": "Ver reportes financieros",
        "reportes.auditoria": "Ver reportes de auditoría",
        # Configuración
        "configuracion.ver": "Ver configuración",
        "configuracion.editar": "Editar configuración del sistema",
        "configuracion.gestionar_impuestos": "Gestionar impuestos",
        # Administración
        "admin.acceso_total": "Acceso total al sistema",
        "admin.gestionar_backups": "Gestionar copias de seguridad",
        "admin.ver_logs": "Ver logs del sistema",
    }

    @staticmethod
    @transaction.atomic
    def inicializar_permisos() -> Dict:
        """
        Crea todos los permisos predefinidos en la base de datos.
        Debe ejecutarse una vez al configurar el sistema.

        Returns:
            {'permisos_creados': int, 'permisos_existentes': int}
        """
        permisos_creados = 0
        permisos_existentes = 0

        for codigo, nombre in PermissionService.PERMISOS_SISTEMA.items():
            # Extraer módulo del código (antes del punto)
            modulo = codigo.split(".")[0]

            permiso, creado = Permisos.objects.get_or_create(
                codigo_permiso=codigo, defaults={"nombre": nombre, "modulo": modulo, "activo": True}
            )

            if creado:
                permisos_creados += 1
            else:
                permisos_existentes += 1

        return {
            "permisos_creados": permisos_creados,
            "permisos_existentes": permisos_existentes,
            "total": len(PermissionService.PERMISOS_SISTEMA),
        }

    @staticmethod
    def empleado_tiene_permiso(empleado: Empleados, codigo_permiso: str) -> bool:
        """
        Verifica si un empleado tiene un permiso específico.

        Args:
            empleado: Instancia del empleado
            codigo_permiso: Código del permiso (ej: 'ventas.crear')

        Returns:
            True si tiene el permiso, False caso contrario
        """
        if not empleado or not empleado.id_rol:
            return False

        # Verificar si el rol tiene acceso total
        if RolesPermisos.objects.filter(
            id_rol=empleado.id_rol,
            id_permiso__codigo_permiso="admin.acceso_total",
            id_permiso__activo=True,
        ).exists():
            return True

        # Verificar permiso específico
        return RolesPermisos.objects.filter(
            id_rol=empleado.id_rol,
            id_permiso__codigo_permiso=codigo_permiso,
            id_permiso__activo=True,
        ).exists()

    @staticmethod
    def empleado_tiene_algunos_permisos(empleado: Empleados, codigos_permisos: List[str]) -> bool:
        """
        Verifica si un empleado tiene AL MENOS UNO de los permisos especificados.

        Returns:
            True si tiene al menos uno, False si no tiene ninguno
        """
        for codigo in codigos_permisos:
            if PermissionService.empleado_tiene_permiso(empleado, codigo):
                return True
        return False

    @staticmethod
    def empleado_tiene_todos_permisos(empleado: Empleados, codigos_permisos: List[str]) -> bool:
        """
        Verifica si un empleado tiene TODOS los permisos especificados.

        Returns:
            True si tiene todos, False si le falta alguno
        """
        for codigo in codigos_permisos:
            if not PermissionService.empleado_tiene_permiso(empleado, codigo):
                return False
        return True

    @staticmethod
    def obtener_permisos_empleado(empleado: Empleados) -> List[str]:
        """
        Obtiene lista de todos los permisos de un empleado.

        Returns:
            Lista de códigos de permisos
        """
        if not empleado or not empleado.id_rol:
            return []

        # Si tiene acceso total, retornar todos los permisos
        if RolesPermisos.objects.filter(
            id_rol=empleado.id_rol, id_permiso__codigo_permiso="admin.acceso_total"
        ).exists():
            return list(PermissionService.PERMISOS_SISTEMA.keys())

        # Retornar permisos específicos del rol
        permisos = (
            RolesPermisos.objects.filter(id_rol=empleado.id_rol, id_permiso__activo=True)
            .select_related("id_permiso")
            .values_list("id_permiso__codigo_permiso", flat=True)
        )

        return list(permisos)

    @staticmethod
    @transaction.atomic
    def asignar_permiso_a_rol(rol: Roles, codigo_permiso: str, asignado_por: Empleados) -> Dict:
        """
        Asigna un permiso a un rol.

        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            permiso = Permisos.objects.get(codigo_permiso=codigo_permiso, activo=True)

            relacion, creado = RolesPermisos.objects.get_or_create(
                id_rol=rol, id_permiso=permiso, defaults={"asignado_por": asignado_por}
            )

            if creado:
                return {
                    "success": True,
                    "mensaje": f"Permiso {codigo_permiso} asignado al rol {rol.nombre_rol}",
                }
            else:  # pragma: no cover
                return {"success": False, "mensaje": "El rol ya tiene este permiso"}

        except Permisos.DoesNotExist:  # pragma: no cover
            return {"success": False, "mensaje": f"Permiso {codigo_permiso} no existe"}
        except Exception as e:  # pragma: no cover
            return {"success": False, "mensaje": f"Error al asignar permiso: {str(e)}"}

    @staticmethod
    @transaction.atomic
    def remover_permiso_de_rol(rol: Roles, codigo_permiso: str) -> Dict:
        """
        Remueve un permiso de un rol.

        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            eliminados = RolesPermisos.objects.filter(
                id_rol=rol, id_permiso__codigo_permiso=codigo_permiso
            ).delete()[0]

            if eliminados > 0:
                return {
                    "success": True,
                    "mensaje": f"Permiso {codigo_permiso} removido del rol {rol.nombre_rol}",
                }
            else:  # pragma: no cover
                return {"success": False, "mensaje": "El rol no tiene este permiso"}

        except Exception as e:  # pragma: no cover
            return {"success": False, "mensaje": f"Error al remover permiso: {str(e)}"}


# ==================== PERMISSION CLASSES (Django REST Framework) ====================


class TienePermiso(permissions.BasePermission):
    """
    Permission class que verifica permisos específicos.

    Uso en ViewSet:
        permission_classes = [TienePermiso]
        permission_required = 'ventas.crear'
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Verificar que el usuario esté autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # Obtener empleado del request (asumiendo que está en request.user)
        try:
            empleado = Empleados.objects.get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return False

        # Obtener permiso requerido del view
        permiso_requerido = getattr(view, "permission_required", None)

        if not permiso_requerido:
            # Si no se especifica permiso, permitir acceso
            return True

        return PermissionService.empleado_tiene_permiso(empleado, permiso_requerido)


class TieneAlgunosPermisos(permissions.BasePermission):
    """
    Permission class que verifica si tiene AL MENOS UNO de los permisos.

    Uso en ViewSet:
        permission_classes = [TieneAlgunosPermisos]
        permisos_requeridos = ['ventas.ver', 'ventas.crear']
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            empleado = Empleados.objects.get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return False

        permisos_requeridos = getattr(view, "permisos_requeridos", [])

        if not permisos_requeridos:
            return True

        return PermissionService.empleado_tiene_algunos_permisos(empleado, permisos_requeridos)


class TieneTodosPermisos(permissions.BasePermission):
    """
    Permission class que verifica si tiene TODOS los permisos.

    Uso en ViewSet:
        permission_classes = [TieneTodosPermisos]
        permisos_requeridos = ['ventas.crear', 'ventas.aplicar_descuentos']
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            empleado = Empleados.objects.get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return False

        permisos_requeridos = getattr(view, "permisos_requeridos", [])

        if not permisos_requeridos:
            return True

        return PermissionService.empleado_tiene_todos_permisos(empleado, permisos_requeridos)


class EsAdministrador(permissions.BasePermission):
    """
    Permission class que verifica si es administrador (acceso total).
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            empleado = Empleados.objects.get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return False

        # Verificar si es administrador por rol
        if empleado.id_rol and empleado.id_rol.nombre_rol in ["Admin", "Administrador"]:
            return True

        # También verificar permiso específico si existe
        return PermissionService.empleado_tiene_permiso(empleado, "admin.acceso_total")


# ==================== DECORADORES ====================


def requiere_permiso(codigo_permiso: str):
    """
    Decorador para funciones que requieren un permiso específico.

    Uso:
        @requiere_permiso('ventas.crear')
        def crear_venta(request):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Debe estar autenticado")

            try:
                empleado = Empleados.objects.get(usuario=request.user.username)
            except Empleados.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Usuario no encontrado")

            if not PermissionService.empleado_tiene_permiso(empleado, codigo_permiso):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(f"No tiene permiso: {codigo_permiso}")

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def requiere_algunos_permisos(*codigos_permisos):
    """
    Decorador para funciones que requieren AL MENOS UNO de los permisos.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Debe estar autenticado")

            try:
                empleado = Empleados.objects.get(usuario=request.user.username)
            except Empleados.DoesNotExist:  # pragma: no cover
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Usuario no encontrado")

            if not PermissionService.empleado_tiene_algunos_permisos(
                empleado, list(codigos_permisos)
            ):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(f"No tiene ninguno de los permisos requeridos")

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
