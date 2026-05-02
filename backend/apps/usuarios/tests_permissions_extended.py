"""
Tests comprehensivos para apps/usuarios/permissions.py
Cubre PermissionService, clases de permisos DRF y decoradores
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.usuarios.models import Roles, Empleados
from apps.usuarios.permissions import (
    Permisos,
    RolesPermisos,
    PermissionService,
    TienePermiso,
    TieneAlgunosPermisos,
    TieneTodosPermisos,
    EsAdministrador,
    requiere_permiso,
    requiere_algunos_permisos,
)


def crear_empleado_basico(nombre="Test", apellido="User", usuario="tu", rol=None):
    """Crea empleado de prueba; si no se provee rol, el manager asigna uno por defecto."""
    if rol is not None:
        return Empleados.objects.create(
            nombre=nombre,
            apellido=apellido,
            usuario=usuario,
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )
    # Sin rol explícito: el manager EmpleadosManager asigna Cajero por defecto
    return Empleados.objects.create(
        nombre=nombre,
        apellido=apellido,
        usuario=usuario,
        contrasena_hash="$2b$12$hash",
        fecha_ingreso=timezone.now(),
        estado=True,
    )


class PermissionServiceInicializarTest(TestCase):

    def test_inicializar_permisos_primera_vez(self):
        result = PermissionService.inicializar_permisos()
        self.assertTrue(result["permisos_creados"] > 0)
        self.assertEqual(result["permisos_existentes"], 0)
        self.assertIn("total", result)

    def test_inicializar_permisos_idempotente(self):
        PermissionService.inicializar_permisos()
        result2 = PermissionService.inicializar_permisos()
        self.assertEqual(result2["permisos_creados"], 0)
        self.assertTrue(result2["permisos_existentes"] > 0)


class PermissionServiceEmpleadoTienePermisoTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="Vendedor", estado=True)
        self.empleado = crear_empleado_basico(usuario="emp1", rol=self.rol)

    def test_sin_empleado_retorna_false(self):
        self.assertFalse(PermissionService.empleado_tiene_permiso(None, "ventas.crear"))

    def test_empleado_sin_rol_retorna_false(self):
        emp_sin_rol = crear_empleado_basico(usuario="emp2", rol=None)
        self.assertFalse(PermissionService.empleado_tiene_permiso(emp_sin_rol, "ventas.crear"))

    def test_empleado_con_acceso_total(self):
        # Asignar admin.acceso_total al rol
        permiso_acceso = Permisos.objects.get(codigo_permiso="admin.acceso_total")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso_acceso)
        self.assertTrue(PermissionService.empleado_tiene_permiso(self.empleado, "ventas.crear"))
        self.assertTrue(PermissionService.empleado_tiene_permiso(self.empleado, "reportes.auditoria"))

    def test_empleado_con_permiso_especifico(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)
        self.assertTrue(PermissionService.empleado_tiene_permiso(self.empleado, "ventas.ver"))
        self.assertFalse(PermissionService.empleado_tiene_permiso(self.empleado, "ventas.crear"))

    def test_empleado_sin_el_permiso(self):
        self.assertFalse(PermissionService.empleado_tiene_permiso(self.empleado, "usuarios.eliminar"))


class PermissionServiceAlgunosPermisosTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="Cajero2", estado=True)
        self.empleado = crear_empleado_basico(usuario="caj2", rol=self.rol)

    def test_tiene_al_menos_uno(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)
        result = PermissionService.empleado_tiene_algunos_permisos(self.empleado, ["ventas.ver", "ventas.crear"])
        self.assertTrue(result)

    def test_no_tiene_ninguno(self):
        result = PermissionService.empleado_tiene_algunos_permisos(self.empleado, ["ventas.ver", "ventas.crear"])
        self.assertFalse(result)


class PermissionServiceTodosPermisosTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="Cajero3", estado=True)
        self.empleado = crear_empleado_basico(usuario="caj3", rol=self.rol)

    def test_tiene_todos(self):
        for codigo in ["ventas.ver", "ventas.crear"]:
            p = Permisos.objects.get(codigo_permiso=codigo)
            RolesPermisos.objects.create(id_rol=self.rol, id_permiso=p)
        result = PermissionService.empleado_tiene_todos_permisos(self.empleado, ["ventas.ver", "ventas.crear"])
        self.assertTrue(result)

    def test_le_falta_uno(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)
        result = PermissionService.empleado_tiene_todos_permisos(self.empleado, ["ventas.ver", "ventas.crear"])
        self.assertFalse(result)


class PermissionServiceObtenerPermisosTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="Cajero4", estado=True)
        self.empleado = crear_empleado_basico(usuario="caj4", rol=self.rol)

    def test_sin_rol_retorna_lista_vacia(self):
        emp = crear_empleado_basico(usuario="emp_norole", rol=None)
        self.assertEqual(PermissionService.obtener_permisos_empleado(emp), [])

    def test_con_acceso_total_retorna_todos(self):
        permiso_acceso = Permisos.objects.get(codigo_permiso="admin.acceso_total")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso_acceso)
        permisos = PermissionService.obtener_permisos_empleado(self.empleado)
        self.assertIn("ventas.crear", permisos)
        self.assertIn("admin.acceso_total", permisos)

    def test_retorna_permisos_especificos(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)
        permisos = PermissionService.obtener_permisos_empleado(self.empleado)
        self.assertIn("ventas.ver", permisos)
        self.assertNotIn("ventas.crear", permisos)


class PermissionServiceAsignarPermisosTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="RolAsignar", estado=True)
        self.asignador = crear_empleado_basico(usuario="asignador", rol=None)

    def test_asignar_permiso_exitoso(self):
        result = PermissionService.asignar_permiso_a_rol(self.rol, "ventas.ver", self.asignador)
        self.assertTrue(result["success"])

    def test_asignar_permiso_ya_existe(self):
        PermissionService.asignar_permiso_a_rol(self.rol, "ventas.ver", self.asignador)
        result2 = PermissionService.asignar_permiso_a_rol(self.rol, "ventas.ver", self.asignador)
        self.assertFalse(result2["success"])

    def test_asignar_permiso_no_existe(self):
        result = PermissionService.asignar_permiso_a_rol(self.rol, "inexistente.permiso", self.asignador)
        self.assertFalse(result["success"])


class PermissionServiceRemoverPermisosTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="RolRemover", estado=True)
        self.asignador = crear_empleado_basico(usuario="remover", rol=None)

    def test_remover_permiso_exitoso(self):
        PermissionService.asignar_permiso_a_rol(self.rol, "ventas.ver", self.asignador)
        result = PermissionService.remover_permiso_de_rol(self.rol, "ventas.ver")
        self.assertTrue(result["success"])

    def test_remover_permiso_que_no_existe(self):
        result = PermissionService.remover_permiso_de_rol(self.rol, "ventas.ver")
        self.assertFalse(result["success"])


class TienePermisoClassTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.permiso_class = TienePermiso()

    def test_usuario_no_autenticado_retorna_false(self):
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))

    def test_usuario_sin_empleado_retorna_false(self):
        """El código busca por id= (campo 'id'); cuando no existe retorna False"""
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = 99999
        request.user = user
        view = MagicMock()
        view.permission_required = "ventas.ver"
        # Mockear para que Empleados.DoesNotExist sea levantado
        with patch("apps.usuarios.permissions.Empleados.objects.get", side_effect=Empleados.DoesNotExist()):
            self.assertFalse(self.permiso_class.has_permission(request, view))

    def test_sin_permiso_requerido_retorna_true(self):
        """Si el view no define permission_required, se permite tras encontrar empleado"""
        PermissionService.inicializar_permisos()
        rol = Roles.objects.create(nombre_rol="RolTP", estado=True)
        emp = crear_empleado_basico(usuario="usrtp", rol=rol)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = emp.id_empleado
        request.user = user
        view = MagicMock(spec=[])  # sin permission_required
        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=emp):
            self.assertTrue(self.permiso_class.has_permission(request, view))

    def test_con_permiso_retorna_true(self):
        """Con empleado que tiene el permiso, has_permission devuelve True"""
        PermissionService.inicializar_permisos()
        rol = Roles.objects.create(nombre_rol="RolTPperm", estado=True)
        emp = crear_empleado_basico(usuario="usrtpperm", rol=rol)
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=rol, id_permiso=permiso)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = emp.id_empleado
        request.user = user
        view = MagicMock()
        view.permission_required = "ventas.ver"
        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=emp):
            self.assertTrue(self.permiso_class.has_permission(request, view))


class TieneAlgunosPermisosClassTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.permiso_class = TieneAlgunosPermisos()

    def test_usuario_no_autenticado_retorna_false(self):
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))

    def test_usuario_sin_empleado_retorna_false(self):
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = 99999
        request.user = user
        view = MagicMock()
        view.permisos_requeridos = ["ventas.ver"]
        with patch("apps.usuarios.permissions.Empleados.objects.get", side_effect=Empleados.DoesNotExist()):
            self.assertFalse(self.permiso_class.has_permission(request, view))

    def test_sin_permisos_requeridos_retorna_true(self):
        PermissionService.inicializar_permisos()
        rol = Roles.objects.create(nombre_rol="RolTAP", estado=True)
        emp = crear_empleado_basico(usuario="usrtap", rol=rol)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = emp.id_empleado
        request.user = user
        view = MagicMock(spec=[])  # sin permisos_requeridos
        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=emp):
            self.assertTrue(self.permiso_class.has_permission(request, view))


class TieneTodosPermisosClassTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.permiso_class = TieneTodosPermisos()

    def test_usuario_no_autenticado_retorna_false(self):
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))

    def test_usuario_sin_empleado_retorna_false(self):
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = 99999
        request.user = user
        view = MagicMock()
        view.permisos_requeridos = ["ventas.ver"]
        with patch("apps.usuarios.permissions.Empleados.objects.get", side_effect=Empleados.DoesNotExist()):
            self.assertFalse(self.permiso_class.has_permission(request, view))

    def test_sin_permisos_requeridos_retorna_true(self):
        PermissionService.inicializar_permisos()
        rol = Roles.objects.create(nombre_rol="RolTTP", estado=True)
        emp = crear_empleado_basico(usuario="usrttp", rol=rol)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = emp.id_empleado
        request.user = user
        view = MagicMock(spec=[])  # sin permisos_requeridos
        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=emp):
            self.assertTrue(self.permiso_class.has_permission(request, view))


class EsAdministradorClassTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.permiso_class = EsAdministrador()

    def test_no_autenticado_retorna_false(self):
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))

    def test_usuario_sin_empleado_retorna_false(self):
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = "noexiste_999"
        request.user = user
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))

    def test_admin_por_nombre_rol(self):
        rola = Roles.objects.create(nombre_rol="Admin", estado=True)
        emp = crear_empleado_basico(usuario="admintest2", rol=rola)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = emp.usuario
        request.user = user
        self.assertTrue(self.permiso_class.has_permission(request, MagicMock()))

    def test_administrador_por_nombre_rol(self):
        PermissionService.inicializar_permisos()
        rola = Roles.objects.create(nombre_rol="Administrador", estado=True)
        emp = crear_empleado_basico(usuario="admintest3", rol=rola)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = emp.usuario
        request.user = user
        self.assertTrue(self.permiso_class.has_permission(request, MagicMock()))

    def test_no_administrador(self):
        PermissionService.inicializar_permisos()
        rola = Roles.objects.create(nombre_rol="Cajero", estado=True)
        emp = crear_empleado_basico(usuario="nonadmin", rol=rola)
        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = emp.usuario
        request.user = user
        self.assertFalse(self.permiso_class.has_permission(request, MagicMock()))


class RequierePermisoDecoradorTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="RolDec", estado=True)
        self.empleado = crear_empleado_basico(usuario="dec1", rol=self.rol)
        self.factory = RequestFactory()

    def test_usuario_no_autenticado_lanza_excepcion(self):
        @requiere_permiso("ventas.crear")
        def mi_funcion(request):
            return "ok"

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        with self.assertRaises(PermissionDenied):
            mi_funcion(request)

    def test_usuario_sin_empleado_lanza_excepcion(self):
        @requiere_permiso("ventas.crear")
        def mi_funcion(request):
            return "ok"

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = "usuario_inexistente_999"
        request.user = user

        with self.assertRaises(PermissionDenied):
            mi_funcion(request)

    def test_sin_permiso_lanza_excepcion(self):
        @requiere_permiso("ventas.crear")
        def mi_funcion(request):
            return "ok"

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = self.empleado.usuario
        request.user = user

        with self.assertRaises(PermissionDenied):
            mi_funcion(request)

    def test_con_permiso_ejecuta_funcion(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.crear")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)

        @requiere_permiso("ventas.crear")
        def mi_funcion(request):
            return "executed"

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.username = self.empleado.usuario
        request.user = user

        result = mi_funcion(request)
        self.assertEqual(result, "executed")


class RequiereAlgunosPermisosDecoradorTest(TestCase):

    def setUp(self):
        PermissionService.inicializar_permisos()
        self.rol = Roles.objects.create(nombre_rol="RolDec2", estado=True)
        self.empleado = crear_empleado_basico(usuario="dec2", rol=self.rol)
        self.factory = RequestFactory()

    def test_usuario_no_autenticado_lanza_excepcion(self):
        @requiere_algunos_permisos("ventas.ver", "ventas.crear")
        def mi_funcion(request):
            return "ok"

        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False

        with self.assertRaises(PermissionDenied):
            mi_funcion(request)

    def test_sin_ningun_permiso_lanza_excepcion(self):
        @requiere_algunos_permisos("ventas.ver", "ventas.crear")
        def mi_funcion(request):
            return "ok"

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = self.empleado.id_empleado
        user.username = self.empleado.usuario
        request.user = user

        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=self.empleado):
            with self.assertRaises(PermissionDenied):
                mi_funcion(request)

    def test_con_al_menos_un_permiso_ejecuta(self):
        permiso = Permisos.objects.get(codigo_permiso="ventas.ver")
        RolesPermisos.objects.create(id_rol=self.rol, id_permiso=permiso)

        @requiere_algunos_permisos("ventas.ver", "ventas.crear")
        def mi_funcion(request):
            return "ran"

        request = self.factory.get("/")
        user = MagicMock()
        user.is_authenticated = True
        user.id = self.empleado.id_empleado
        user.username = self.empleado.usuario
        request.user = user

        with patch("apps.usuarios.permissions.Empleados.objects.get", return_value=self.empleado):
            self.assertEqual(mi_funcion(request), "ran")
