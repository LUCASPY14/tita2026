"""
Views para gestión completa de usuarios con seguridad empresarial
Incluye: Autenticación, 2FA, Permisos, Sesiones, Recuperación de contraseñas
"""

from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import PortalJWTAuthentication, PortalUserProxy
from .models import (
    AuditoriaOperaciones,
    Empleados,
    PerfilesUsuario,
    Roles,
    UsuariosPortal,
)
from .permissions import (
    EsAdministrador,
    IsPortalAuthenticated,
    Permisos,
    PermissionService,
    RolesPermisos,
)
from .serializers import (
    AuditoriaOperacionesSerializer,
    EmpleadosSerializer,
    PerfilesUsuarioSerializer,
    RolesSerializer,
    UsuariosPortalSerializer,
)
from .services import (
    AuthenticationService,
    PasswordRecoveryService,
    SessionService,
    TwoFactorAuthService,
)
from .services.portal_service import PortalAuthService

# ==================== AUTENTICACIÓN ====================


@method_decorator(csrf_exempt, name="dispatch")
class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para autenticación (login, logout, cambio de contraseña).
    """

    permission_classes = [AllowAny]  # Permitir acceso sin autenticación para login

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login con usuario y contraseña.
        Retorna tokens JWT si es exitoso.

        POST /api/v1/auth/login/
        Body:
        {
            "usuario": "admin",
            "password": "Admin123!@#"
        }
        """
        usuario = request.data.get("usuario") or request.data.get("username")
        password = request.data.get("password")

        if not usuario or not password:
            return Response(
                {"success": False, "mensaje": "Usuario y contraseña son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener IP y User-Agent
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Intentar login
        resultado = AuthenticationService.login(usuario, password, ip_address, user_agent)

        if resultado["success"]:
            # Verificar si tiene 2FA habilitado
            empleado = Empleados.objects.get(usuario=usuario)
            tiene_2fa = TwoFactorAuthService.verificar_2fa_habilitado(empleado)

            if tiene_2fa:
                # Requiere 2FA - devolver token temporal
                return Response(
                    {
                        "success": True,
                        "requiere_2fa": True,
                        "mensaje": "Por favor, ingrese su código 2FA",
                        "token_temporal": resultado["tokens"]["access"],  # Token con duración corta
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # Login completo sin 2FA
                return Response(
                    {
                        "success": True,
                        "requiere_2fa": False,
                        "tokens": resultado["tokens"],
                        "empleado": resultado["empleado"],
                        "mensaje": resultado["mensaje"],
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            if resultado["codigo"] == "CUENTA_BLOQUEADA" or resultado["codigo"] == "CUENTA_BLOQUEADA_INTENTOS":
                status_code = status.HTTP_403_FORBIDDEN

            return Response(resultado, status=status_code)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Cierra la sesión actual.

        POST /api/v1/auth/logout/
        Headers: Authorization: Bearer <access_token>
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)

        # Obtener refresh token del request
        refresh_token = request.data.get("refresh_token", "")

        resultado = AuthenticationService.logout(empleado, refresh_token, ip_address)

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def cambiar_password(self, request):
        """
        Cambia la contraseña del empleado actual.

        POST /api/v1/auth/cambiar_password/
        Body:
        {
            "password_actual": "OldPass123!",
            "password_nueva": "NewPass456@"
        }
        """
        password_actual = request.data.get("password_actual")
        password_nueva = request.data.get("password_nueva")

        if not password_actual or not password_nueva:
            return Response(
                {"success": False, "mensaje": "Ambas contraseñas son requeridas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener instancia de Empleados (request.user es Django auth.User)
        try:
            empleado = Empleados.objects.get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return Response(
                {"success": False, "mensaje": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        ip_address = self._get_client_ip(request)

        resultado = AuthenticationService.cambiar_password(empleado, password_actual, password_nueva, ip_address)

        if resultado["success"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def perfil(self, request):
        """
        Obtiene información del empleado autenticado.

        GET /api/v1/auth/perfil/
        """
        try:
            empleado = Empleados.objects.select_related("id_rol").get(usuario=request.user.username)
        except Empleados.DoesNotExist:
            return Response({"error": "Empleado no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmpleadosSerializer(empleado)

        # Agregar permisos
        permisos = PermissionService.obtener_permisos_empleado(empleado)

        # Agregar estadísticas 2FA
        stats_2fa = TwoFactorAuthService.obtener_estadisticas_2fa(empleado)

        return Response(
            {"empleado": serializer.data, "permisos": permisos, "stats_2fa": stats_2fa},
            status=status.HTTP_200_OK,
        )

    def _get_client_ip(self, request):
        """Helper para obtener IP del cliente."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


# ==================== 2FA ====================


class TwoFactorViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de autenticación de dos factores.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def habilitar(self, request):
        """
        Habilita 2FA para el empleado actual.
        Retorna QR code y códigos de respaldo.

        POST /api/v1/2fa/habilitar/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)

        resultado = TwoFactorAuthService.habilitar_2fa_empleado(empleado, ip_address)

        if resultado["success"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(ratelimit(key="user", rate="10/m", method="POST"))
    @action(detail=False, methods=["post"])
    def verificar(self, request):
        """
        Verifica un código 2FA.

        POST /api/v1/2fa/verificar/
        Body:
        {
            "codigo": "123456"
        }
        """
        codigo = request.data.get("codigo")

        if not codigo:
            return Response(
                {"success": False, "mensaje": "Código es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empleado = request.user
        ip_address = self._get_client_ip(request)

        resultado = TwoFactorAuthService.verificar_codigo_2fa(empleado, codigo, ip_address)

        if resultado["success"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def deshabilitar(self, request):
        """
        Deshabilita 2FA para el empleado actual.

        POST /api/v1/2fa/deshabilitar/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)

        resultado = TwoFactorAuthService.deshabilitar_2fa_empleado(empleado, ip_address)

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def regenerar_backup_codes(self, request):
        """
        Regenera códigos de respaldo.

        POST /api/v1/2fa/regenerar_backup_codes/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)

        resultado = TwoFactorAuthService.regenerar_backup_codes(empleado, ip_address)

        if resultado["success"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de 2FA del empleado actual.

        GET /api/v1/2fa/estadisticas/
        """
        empleado = request.user
        stats = TwoFactorAuthService.obtener_estadisticas_2fa(empleado)

        return Response(stats, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


# ==================== SESIONES ====================


class SesionesViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de sesiones activas.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def activas(self, request):
        """
        Lista todas las sesiones activas del empleado.

        GET /api/v1/sesiones/activas/
        """
        empleado = request.user
        sesiones = SessionService.listar_sesiones_activas(empleado)

        return Response({"sesiones": sesiones, "total": len(sesiones)}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def cerrar(self, request):
        """
        Cierra una sesión específica.

        POST /api/v1/sesiones/cerrar/
        Body:
        {
            "session_key": "..."
        }
        """
        session_key = request.data.get("session_key")

        if not session_key:
            return Response(
                {"success": False, "mensaje": "session_key es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empleado = request.user
        ip_address = self._get_client_ip(request)

        resultado = SessionService.cerrar_sesion(empleado, session_key, ip_address)

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def cerrar_todas(self, request):
        """
        Cierra todas las sesiones excepto la actual.

        POST /api/v1/sesiones/cerrar_todas/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)

        # Obtener session_key actual del token
        session_key_actual = request.data.get("session_key_actual")

        resultado = SessionService.cerrar_todas_sesiones(empleado, ip_address, session_key_actual)

        return Response(resultado, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


# ==================== RECUPERACIÓN DE CONTRASEÑA ====================


class PasswordRecoveryViewSet(viewsets.ViewSet):
    """
    ViewSet para recuperación de contraseñas.
    """

    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="3/h", method="POST"))
    @action(detail=False, methods=["post"])
    def solicitar(self, request):
        """
        Solicita recuperación de contraseña.

        POST /api/v1/password/solicitar/
        Body:
        {
            "email": "usuario@example.com"
        }
        """
        email = request.data.get("email")

        if not email:
            return Response(
                {"success": False, "mensaje": "Email es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip_address = self._get_client_ip(request)

        PasswordRecoveryService.solicitar_recuperacion_empleado(email, ip_address)

        # NOTA: En producción, enviar el token por email aquí
        # Para desarrollo, lo retornamos en la respuesta (NO HACER EN PRODUCCIÓN)

        return Response(
            {
                "success": True,
                "mensaje": "Si el email existe, recibirá instrucciones para recuperar su contraseña",
                # 'token': resultado.get('token')  # SOLO PARA DESARROLLO - QUITAR EN PRODUCCIÓN
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def validar_token(self, request):
        """
        Valida un token de recuperación.

        POST /api/v1/password/validar_token/
        Body:
        {
            "token": "..."
        }
        """
        token = request.data.get("token")

        if not token:
            return Response(
                {"valido": False, "mensaje": "Token es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultado = PasswordRecoveryService.validar_token_recuperacion(token)

        if resultado["valido"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def restablecer(self, request):
        """
        Restablece la contraseña usando el token.

        POST /api/v1/password/restablecer/
        Body:
        {
            "token": "...",
            "nueva_password": "NewPass123!@#"
        }
        """
        token = request.data.get("token")
        nueva_password = request.data.get("nueva_password")

        if not token or not nueva_password:
            return Response(
                {"success": False, "mensaje": "Token y nueva contraseña son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip_address = self._get_client_ip(request)

        resultado = PasswordRecoveryService.restablecer_password_con_token(token, nueva_password, ip_address)

        if resultado["success"]:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


# ==================== PERMISOS ====================


class PermisosViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de permisos.
    """

    permission_classes = [IsAuthenticated, EsAdministrador]

    @action(detail=False, methods=["get"])
    def listar(self, request):
        """
        Lista todos los permisos del sistema.

        GET /api/v1/permisos/listar/
        """
        permisos = Permisos.objects.filter(estado=True).values(
            "id", "codigo_permiso", "nombre", "modulo", "descripcion"
        )

        # Agrupar por módulo
        permisos_por_modulo = {}
        for permiso in permisos:
            modulo = permiso["modulo"]
            if modulo not in permisos_por_modulo:
                permisos_por_modulo[modulo] = []
            permisos_por_modulo[modulo].append(permiso)

        return Response(
            {
                "permisos": list(permisos),
                "permisos_por_modulo": permisos_por_modulo,
                "total": len(permisos),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def inicializar(self, request):
        """
        Inicializa todos los permisos del sistema.
        Solo ejecutar en setup inicial.

        POST /api/v1/permisos/inicializar/
        """
        resultado = PermissionService.inicializar_permisos()

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def asignar_a_rol(self, request):
        """
        Asigna un permiso a un rol.

        POST /api/v1/permisos/asignar_a_rol/
        Body:
        {
            "id_rol": 1,
            "codigo_permiso": "ventas.crear"
        }
        """
        id_rol = request.data.get("id_rol")
        codigo_permiso = request.data.get("codigo_permiso")

        if not id_rol or not codigo_permiso:
            return Response(
                {"success": False, "mensaje": "id_rol y codigo_permiso son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rol = Roles.objects.get(pk=id_rol)
            empleado = request.user

            resultado = PermissionService.asignar_permiso_a_rol(rol, codigo_permiso, empleado)

            if resultado["success"]:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        except Roles.DoesNotExist:
            return Response({"success": False, "mensaje": "Rol no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"])
    def remover_de_rol(self, request):
        """
        Remueve un permiso de un rol.

        POST /api/v1/permisos/remover_de_rol/
        Body:
        {
            "id_rol": 1,
            "codigo_permiso": "ventas.crear"
        }
        """
        id_rol = request.data.get("id_rol")
        codigo_permiso = request.data.get("codigo_permiso")

        if not id_rol or not codigo_permiso:
            return Response(
                {"success": False, "mensaje": "id_rol y codigo_permiso son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rol = Roles.objects.get(pk=id_rol)

            resultado = PermissionService.remover_permiso_de_rol(rol, codigo_permiso)

            if resultado["success"]:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        except Roles.DoesNotExist:
            return Response({"success": False, "mensaje": "Rol no encontrado"}, status=status.HTTP_404_NOT_FOUND)


# ==================== CRUD BÁSICOS ====================


class RolesViewSet(viewsets.ModelViewSet):
    """
    CRUD de roles con permisos.
    """

    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado"]
    search_fields = ["nombre_rol"]

    @action(detail=True, methods=["get"])
    def permisos(self, request, pk=None):
        """
        Obtiene permisos de un rol específico.

        GET /api/v1/roles/{id}/permisos/
        """
        rol = self.get_object()

        permisos = (
            RolesPermisos.objects.filter(id_rol=rol)
            .select_related("id_permiso")
            .values(
                "id_permiso__id",
                "id_permiso__codigo_permiso",
                "id_permiso__nombre",
                "id_permiso__modulo",
                "fecha_asignacion",
            )
        )

        return Response(
            {
                "rol": {"id": rol.pk, "nombre_rol": rol.nombre_rol, "descripcion": rol.descripcion},
                "permisos": list(permisos),
                "total": len(permisos),
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Empleados.objects.filter(id_rol=instance).exists():
            return Response(
                {"error": "No se puede eliminar el rol porque tiene empleados asignados."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class EmpleadosViewSet(viewsets.ModelViewSet):
    """
    CRUD de empleados con validaciones de seguridad.
    """

    queryset = Empleados.objects.all()
    serializer_class = EmpleadosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "id_rol"]
    search_fields = ["nombre", "apellido", "usuario", "email"]
    ordering_fields = ["apellido", "nombre"]
    ordering = ["apellido", "nombre"]

    def create(self, request, *args, **kwargs):
        """
        Crea un empleado con contraseña segura.
        """
        nombre = request.data.get("nombre")
        apellido = request.data.get("apellido")
        usuario = request.data.get("usuario")
        request.data.get("email")
        # Accept contrasena_hash as alias for password
        password = request.data.get("password") or request.data.get("contrasena_hash")
        id_rol = request.data.get("id_rol")
        fecha_ingreso = request.data.get("fecha_ingreso")

        missing_fields = {}
        if not nombre:
            missing_fields["nombre"] = ["Este campo es requerido."]
        if not apellido:
            missing_fields["apellido"] = ["Este campo es requerido."]
        if not usuario:
            missing_fields["usuario"] = ["Este campo es requerido."]
        if not password:
            missing_fields["contrasena_hash"] = ["Este campo es requerido."]
        if not fecha_ingreso:
            missing_fields["fecha_ingreso"] = ["Este campo es requerido."]
        if not id_rol:
            missing_fields["id_rol"] = ["Este campo es requerido."]

        if missing_fields:
            return Response(missing_fields, status=status.HTTP_400_BAD_REQUEST)

        # Check for duplicate usuario
        if Empleados.objects.filter(usuario=usuario).exists():
            return Response(
                {"usuario": ["Ya existe un empleado con este nombre de usuario."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user
        self._get_client_ip(request)

        # Use serializer to create directly (bypassing password strength validation for hashed passwords)
        data = dict(request.data)
        data["contrasena_hash"] = password
        serializer = EmpleadosSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cambiar_password(self, request, pk=None):
        """
        Cambia la contraseña de un empleado (solo para administradores).

        POST /api/v1/empleados/{id}/cambiar_password/
        Body:
        {
            "password": "NewPassword123!"
        }
        """
        try:
            empleado_target = self.get_object()
            new_password = request.data.get("password")

            if not new_password:
                return Response(
                    {"success": False, "mensaje": "La nueva contraseña es requerida"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar longitud mínima
            if len(new_password) < 8:
                return Response(
                    {"success": False, "mensaje": "La contraseña debe tener al menos 8 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verificar si el usuario actual tiene permisos de admin
            empleado_actual_user = request.user
            try:
                empleado_actual = Empleados.objects.get(usuario=empleado_actual_user.username)
                if not empleado_actual.id_rol or empleado_actual.id_rol.nombre_rol not in [
                    "Admin",
                    "Administrador",
                ]:
                    return Response(
                        {
                            "success": False,
                            "mensaje": "No tienes permisos para cambiar contraseñas de otros usuarios",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except Empleados.DoesNotExist:
                return Response(
                    {"success": False, "mensaje": "Usuario no encontrado en el sistema"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Cambiar la contraseña
            import bcrypt

            hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            empleado_target.contrasena_hash = hashed_password.decode("utf-8")
            empleado_target.save()

            # Actualizar el User de Django también si existe
            from django.contrib.auth.models import User

            try:
                django_user = User.objects.get(username=empleado_target.usuario)
                django_user.set_password(new_password)
                django_user.save()
            except User.DoesNotExist:  # pragma: no cover
                pass  # No existe user de Django asociado

            # Log de la operación (opcional)
            # from django.utils import timezone
            # ip_address = self._get_client_ip(request)
            # Auditoría simplificada por ahora
            print(f"Admin {empleado_actual.usuario} cambió password de {empleado_target.usuario}")

            return Response(
                {
                    "success": True,
                    "mensaje": f"Contraseña actualizada exitosamente para {empleado_target.nombre} {empleado_target.apellido}",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:  # pragma: no cover
            return Response(
                {"success": False, "mensaje": f"Error al cambiar la contraseña: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


class PerfilesUsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de perfiles de usuario.
    """

    queryset = PerfilesUsuario.objects.all()
    serializer_class = PerfilesUsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id_empleado"]


class UsuariosPortalViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuarios del portal (clientes). Requiere ser empleado autenticado.
    Al crear o actualizar, la contraseña se hashea automáticamente.
    """

    queryset = UsuariosPortal.objects.all()
    serializer_class = UsuariosPortalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado", "id_cliente"]
    search_fields = ["email"]

    def perform_create(self, serializer):
        """Hash the password before saving a new portal user."""
        raw_password = self.request.data.get("password")
        instance = serializer.save(
            email_verificado=False,
        )
        if raw_password:
            instance.set_password(raw_password)
            instance.save(update_fields=["password_hash"])

    def perform_update(self, serializer):
        """If password is provided in the update, hash it."""
        raw_password = self.request.data.get("password")
        instance = serializer.save()
        if raw_password:
            instance.set_password(raw_password)
            instance.save(update_fields=["password_hash"])


class PortalAuthViewSet(viewsets.ViewSet):
    """
    Autenticación y datos del portal para clientes.

    Endpoints públicos:
      POST /portal-auth/login/      → email + password → token

    Endpoints protegidos (requieren token de portal):
      GET  /portal-auth/perfil/     → datos del cliente autenticado
      GET  /portal-auth/dashboard/  → hijos + saldos + consumos recientes
      POST /portal-auth/cambiar-password/
    """

    authentication_classes = [PortalJWTAuthentication]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def login(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"detail": "Email y contraseña son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = PortalAuthService.login(email, password)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {"token": result["token"], "usuario": result["portal_user"]},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsPortalAuthenticated])
    def perfil(self, request):
        proxy: PortalUserProxy = request.user
        pu = proxy.portal_user
        cliente = pu.id_cliente
        return Response(
            {
                "id_usuario_portal": pu.id_usuario_portal,
                "email": pu.email,
                "email_verificado": pu.email_verificado,
                "ultimo_acceso": pu.ultimo_acceso,
                "cliente": {
                    "id_cliente": cliente.id_cliente,
                    "nombre_completo": cliente.nombre_completo,
                    "ruc_ci": cliente.ruc_ci,
                    "email": cliente.email,
                    "telefono": cliente.telefono,
                    "limite_credito": str(cliente.limite_credito),
                    "credito_disponible": str(cliente.credito_disponible),
                },
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[IsPortalAuthenticated])
    def dashboard(self, request):
        pass

        from apps.core.models import ConsumosTarjeta, Tarjetas
        from apps.ventas.models import Ventas

        proxy: PortalUserProxy = request.user
        cliente = proxy.portal_user.id_cliente

        hijos_data = []
        for hijo in cliente.hijos.filter(estado=True).order_by("apellido", "nombre"):
            tarjeta_data = None
            try:
                tarjeta = Tarjetas.objects.get(id_hijo=hijo.id_hijo)
                consumos = (
                    ConsumosTarjeta.objects.filter(nro_tarjeta=tarjeta)
                    .order_by("-fecha_consumo")[:10]
                    .values(
                        "id_consumo",
                        "fecha_consumo",
                        "monto_consumido",
                        "detalle",
                        "saldo_posterior",
                    )
                )
                tarjeta_data = {
                    "nro_tarjeta": tarjeta.nro_tarjeta,
                    "saldo_actual": str(tarjeta.saldo_actual),
                    "estado": tarjeta.estado,
                    "esta_en_alerta": tarjeta.esta_en_alerta,
                    "ultimos_consumos": list(consumos),
                }
            except Tarjetas.DoesNotExist:
                pass

            hijos_data.append(
                {
                    "id_hijo": hijo.id_hijo,
                    "nombre": hijo.nombre,
                    "apellido": hijo.apellido,
                    "nombre_completo": hijo.nombre_completo,
                    "grado": hijo.grado,
                    "tarjeta": tarjeta_data,
                }
            )

        # Obtener información de cuenta corriente (facturas pendientes)
        facturas_pendientes = Ventas.objects.filter(id_cliente=cliente, saldo_pendiente__gt=0).order_by("-fecha")[
            :10
        ]  # Últimas 10 facturas pendientes

        total_deuda = sum(f.saldo_pendiente for f in facturas_pendientes)
        cantidad_facturas_pendientes = Ventas.objects.filter(id_cliente=cliente, saldo_pendiente__gt=0).count()

        facturas_data = [
            {
                "id_venta": f.id_venta,
                "nro_factura_venta": f.nro_factura_venta,
                "fecha": f.fecha.isoformat() if f.fecha else None,
                "total_venta": str(f.total_venta),
                "saldo_pendiente": str(f.saldo_pendiente),
            }
            for f in facturas_pendientes
        ]

        return Response(
            {
                "cliente": {
                    "nombre_completo": cliente.nombre_completo,
                    "ruc_ci": cliente.ruc_ci,
                    "email": cliente.email,
                    "limite_credito": str(cliente.limite_credito),
                    "credito_disponible": str(cliente.credito_disponible),
                },
                "hijos": hijos_data,
                "cuenta_corriente": {
                    "total_deuda": str(total_deuda),
                    "cantidad_facturas_pendientes": cantidad_facturas_pendientes,
                    "facturas_recientes": facturas_data,
                },
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[IsPortalAuthenticated])
    def cambiar_password(self, request):
        proxy: PortalUserProxy = request.user
        pu = proxy.portal_user

        password_actual = request.data.get("password_actual", "")
        password_nuevo = request.data.get("password_nuevo", "")

        if not password_actual or not password_nuevo:
            return Response(
                {"detail": "password_actual y password_nuevo son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not pu.check_password(password_actual):
            return Response(
                {"detail": "La contraseña actual es incorrecta"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password_nuevo) < 8:
            return Response(
                {"detail": "La contraseña nueva debe tener al menos 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pu.set_password(password_nuevo)
        pu.save(update_fields=["password_hash"])

        return Response({"detail": "Contraseña actualizada correctamente"})


class AuditoriaOperacionesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consulta de logs de auditoría.
    Incluye filtros avanzados por usuario, operación, tabla, fechas y resultado.
    """

    queryset = AuditoriaOperaciones.objects.all().order_by("-fecha_operacion")
    serializer_class = AuditoriaOperacionesSerializer
    permission_classes = [IsAuthenticated, EsAdministrador]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["tipo_usuario", "operacion", "tabla_afectada", "resultado"]
    search_fields = ["usuario", "descripcion", "ip_address", "ciudad"]
    ordering_fields = ["fecha_operacion", "usuario", "operacion", "resultado"]

    def get_queryset(self):
        """
        Filtra queryset con parámetros adicionales:
        - fecha_desde / fecha_hasta: rango de fechas
        - id_usuario: filtrar por usuario específico
        - tabla: tabla afectada
        """
        queryset = super().get_queryset()

        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get("fecha_desde", None)
        fecha_hasta = self.request.query_params.get("fecha_hasta", None)

        if fecha_desde:
            queryset = queryset.filter(fecha_operacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_operacion__lte=fecha_hasta)

        # Filtro por ID de usuario
        id_usuario = self.request.query_params.get("id_usuario", None)
        if id_usuario:
            queryset = queryset.filter(id_usuario=id_usuario)

        # Filtro por tabla afectada
        tabla = self.request.query_params.get("tabla", None)
        if tabla:
            queryset = queryset.filter(tabla_afectada=tabla)

        return queryset

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de auditoría:
        - Total de operaciones por tipo
        - Total de operaciones por resultado
        - Usuarios más activos
        - Tablas más modificadas
        """
        from django.db.models import Count

        queryset = self.get_queryset()

        # Operaciones por tipo
        ops_por_tipo = queryset.values("operacion").annotate(total=Count("id_auditoria")).order_by("-total")[:10]

        # Operaciones por resultado
        ops_por_resultado = queryset.values("resultado").annotate(total=Count("id_auditoria"))

        # Usuarios más activos
        usuarios_activos = (
            queryset.values("usuario", "tipo_usuario")
            .annotate(total_operaciones=Count("id_auditoria"))
            .order_by("-total_operaciones")[:10]
        )

        # Tablas más modificadas
        tablas_modificadas = (
            queryset.exclude(tabla_afectada__isnull=True)
            .values("tabla_afectada")
            .annotate(total=Count("id_auditoria"))
            .order_by("-total")[:10]
        )

        return Response(
            {
                "operaciones_por_tipo": ops_por_tipo,
                "operaciones_por_resultado": ops_por_resultado,
                "usuarios_mas_activos": usuarios_activos,
                "tablas_mas_modificadas": tablas_modificadas,
                "total_registros": queryset.count(),
            }
        )

    @action(detail=False, methods=["get"])
    def timeline(self, request):
        """
        Retorna timeline de operaciones agrupadas por día.
        Útil para gráficos de actividad en el tiempo.
        """
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        queryset = self.get_queryset()

        timeline = (
            queryset.annotate(fecha=TruncDate("fecha_operacion"))
            .values("fecha")
            .annotate(total=Count("id_auditoria"))
            .order_by("fecha")
        )

        return Response(list(timeline))

    @action(detail=False, methods=["get"])
    def actividad_usuario(self, request):
        """
        Retorna actividad detallada de un usuario específico.
        Requiere parámetro: id_usuario
        """
        id_usuario = request.query_params.get("id_usuario", None)

        if not id_usuario:
            return Response({"error": "Se requiere el parámetro id_usuario"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(id_usuario=id_usuario)

        # Resumen de actividad
        total_operaciones = queryset.count()
        ultima_actividad = queryset.first()

        ops_por_tipo = queryset.values("operacion").annotate(total=Count("id_auditoria")).order_by("-total")

        ops_exitosas = queryset.filter(resultado="EXITO").count()
        ops_fallidas = queryset.exclude(resultado="EXITO").count()

        return Response(
            {
                "id_usuario": id_usuario,
                "total_operaciones": total_operaciones,
                "ultima_actividad": (
                    AuditoriaOperacionesSerializer(ultima_actividad).data if ultima_actividad else None
                ),
                "operaciones_por_tipo": ops_por_tipo,
                "operaciones_exitosas": ops_exitosas,
                "operaciones_fallidas": ops_fallidas,
                "tasa_exito": (round((ops_exitosas / total_operaciones * 100), 2) if total_operaciones > 0 else 0),
            }
        )
