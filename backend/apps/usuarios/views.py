"""
Views para gestión completa de usuarios con seguridad empresarial
Incluye: Autenticación, 2FA, Permisos, Sesiones, Recuperación de contraseñas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import (
    Empleados, Roles, PerfilesUsuario, UsuariosPortal,
    SesionesActivas, BloqueosCuenta
)
from .serializers import (
    EmpleadosSerializer, RolesSerializer, 
    PerfilesUsuarioSerializer, UsuariosPortalSerializer
)
from .services import (
    AuthenticationService,
    TwoFactorAuthService,
    SessionService,
    PasswordRecoveryService
)
from .permissions import (
    PermissionService,
    TienePermiso,
    EsAdministrador,
    Permisos,
    RolesPermisos
)


# ==================== AUTENTICACIÓN ====================

class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para autenticación (login, logout, cambio de contraseña).
    """
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
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
        usuario = request.data.get('usuario')
        password = request.data.get('password')
        
        if not usuario or not password:
            return Response({
                'success': False,
                'mensaje': 'Usuario y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener IP y User-Agent
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Intentar login
        resultado = AuthenticationService.login(
            usuario, password, ip_address, user_agent
        )
        
        if resultado['success']:
            # Verificar si tiene 2FA habilitado
            empleado = Empleados.objects.get(usuario=usuario)
            tiene_2fa = TwoFactorAuthService.verificar_2fa_habilitado(empleado)
            
            if tiene_2fa:
                # Requiere 2FA - devolver token temporal
                return Response({
                    'success': True,
                    'requiere_2fa': True,
                    'mensaje': 'Por favor, ingrese su código 2FA',
                    'token_temporal': resultado['tokens']['access']  # Token con duración corta
                }, status=status.HTTP_200_OK)
            else:
                # Login completo sin 2FA
                return Response({
                    'success': True,
                    'requiere_2fa': False,
                    'tokens': resultado['tokens'],
                    'empleado': resultado['empleado'],
                    'mensaje': resultado['mensaje']
                }, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            if resultado['codigo'] == 'CUENTA_BLOQUEADA' or resultado['codigo'] == 'CUENTA_BLOQUEADA_INTENTOS':
                status_code = status.HTTP_403_FORBIDDEN
            
            return Response(resultado, status=status_code)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Cierra la sesión actual.
        
        POST /api/v1/auth/logout/
        Headers: Authorization: Bearer <access_token>
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        # Obtener refresh token del request
        refresh_token = request.data.get('refresh_token', '')
        
        resultado = AuthenticationService.logout(
            empleado, refresh_token, ip_address
        )
        
        return Response(resultado, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
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
        password_actual = request.data.get('password_actual')
        password_nueva = request.data.get('password_nueva')
        
        if not password_actual or not password_nueva:
            return Response({
                'success': False,
                'mensaje': 'Ambas contraseñas son requeridas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = AuthenticationService.cambiar_password(
            empleado, password_actual, password_nueva, ip_address
        )
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def perfil(self, request):
        """
        Obtiene información del empleado autenticado.
        
        GET /api/v1/auth/perfil/
        """
        empleado = request.user
        serializer = EmpleadosSerializer(empleado)
        
        # Agregar permisos
        permisos = PermissionService.obtener_permisos_empleado(empleado)
        
        # Agregar estadísticas 2FA
        stats_2fa = TwoFactorAuthService.obtener_estadisticas_2fa(empleado)
        
        return Response({
            'empleado': serializer.data,
            'permisos': permisos,
            'stats_2fa': stats_2fa
        }, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        """Helper para obtener IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


# ==================== 2FA ====================

class TwoFactorViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de autenticación de dos factores.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def habilitar(self, request):
        """
        Habilita 2FA para el empleado actual.
        Retorna QR code y códigos de respaldo.
        
        POST /api/v1/2fa/habilitar/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(empleado, ip_address)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'])
    def verificar(self, request):
        """
        Verifica un código 2FA.
        
        POST /api/v1/2fa/verificar/
        Body:
        {
            "codigo": "123456"
        }
        """
        codigo = request.data.get('codigo')
        
        if not codigo:
            return Response({
                'success': False,
                'mensaje': 'Código es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado, codigo, ip_address
        )
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def deshabilitar(self, request):
        """
        Deshabilita 2FA para el empleado actual.
        
        POST /api/v1/2fa/deshabilitar/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = TwoFactorAuthService.deshabilitar_2fa_empleado(empleado, ip_address)
        
        return Response(resultado, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def regenerar_backup_codes(self, request):
        """
        Regenera códigos de respaldo.
        
        POST /api/v1/2fa/regenerar_backup_codes/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = TwoFactorAuthService.regenerar_backup_codes(empleado, ip_address)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de 2FA del empleado actual.
        
        GET /api/v1/2fa/estadisticas/
        """
        empleado = request.user
        stats = TwoFactorAuthService.obtener_estadisticas_2fa(empleado)
        
        return Response(stats, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


# ==================== SESIONES ====================

class SesionesViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de sesiones activas.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Lista todas las sesiones activas del empleado.
        
        GET /api/v1/sesiones/activas/
        """
        empleado = request.user
        sesiones = SessionService.listar_sesiones_activas(empleado)
        
        return Response({
            'sesiones': sesiones,
            'total': len(sesiones)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def cerrar(self, request):
        """
        Cierra una sesión específica.
        
        POST /api/v1/sesiones/cerrar/
        Body:
        {
            "session_key": "..."
        }
        """
        session_key = request.data.get('session_key')
        
        if not session_key:
            return Response({
                'success': False,
                'mensaje': 'session_key es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = SessionService.cerrar_sesion(empleado, session_key, ip_address)
        
        return Response(resultado, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def cerrar_todas(self, request):
        """
        Cierra todas las sesiones excepto la actual.
        
        POST /api/v1/sesiones/cerrar_todas/
        """
        empleado = request.user
        ip_address = self._get_client_ip(request)
        
        # Obtener session_key actual del token
        session_key_actual = request.data.get('session_key_actual')
        
        resultado = SessionService.cerrar_todas_sesiones(
            empleado, ip_address, session_key_actual
        )
        
        return Response(resultado, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


# ==================== RECUPERACIÓN DE CONTRASEÑA ====================

class PasswordRecoveryViewSet(viewsets.ViewSet):
    """
    ViewSet para recuperación de contraseñas.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST'))
    @action(detail=False, methods=['post'])
    def solicitar(self, request):
        """
        Solicita recuperación de contraseña.
        
        POST /api/v1/password/solicitar/
        Body:
        {
            "email": "usuario@example.com"
        }
        """
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'mensaje': 'Email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ip_address = self._get_client_ip(request)
        
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(email, ip_address)
        
        # NOTA: En producción, enviar el token por email aquí
        # Para desarrollo, lo retornamos en la respuesta (NO HACER EN PRODUCCIÓN)
        
        return Response({
            'success': True,
            'mensaje': 'Si el email existe, recibirá instrucciones para recuperar su contraseña',
            # 'token': resultado.get('token')  # SOLO PARA DESARROLLO - QUITAR EN PRODUCCIÓN
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def validar_token(self, request):
        """
        Valida un token de recuperación.
        
        POST /api/v1/password/validar_token/
        Body:
        {
            "token": "..."
        }
        """
        token = request.data.get('token')
        
        if not token:
            return Response({
                'valido': False,
                'mensaje': 'Token es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        resultado = PasswordRecoveryService.validar_token_recuperacion(token)
        
        if resultado['valido']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
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
        token = request.data.get('token')
        nueva_password = request.data.get('nueva_password')
        
        if not token or not nueva_password:
            return Response({
                'success': False,
                'mensaje': 'Token y nueva contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ip_address = self._get_client_ip(request)
        
        resultado = PasswordRecoveryService.restablecer_password_con_token(
            token, nueva_password, ip_address
        )
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


# ==================== PERMISOS ====================

class PermisosViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión de permisos.
    """
    permission_classes = [IsAuthenticated, EsAdministrador]
    
    @action(detail=False, methods=['get'])
    def listar(self, request):
        """
        Lista todos los permisos del sistema.
        
        GET /api/v1/permisos/listar/
        """
        permisos = Permisos.objects.filter(activo=True).values(
            'id', 'codigo_permiso', 'nombre', 'modulo', 'descripcion'
        )
        
        # Agrupar por módulo
        permisos_por_modulo = {}
        for permiso in permisos:
            modulo = permiso['modulo']
            if modulo not in permisos_por_modulo:
                permisos_por_modulo[modulo] = []
            permisos_por_modulo[modulo].append(permiso)
        
        return Response({
            'permisos': list(permisos),
            'permisos_por_modulo': permisos_por_modulo,
            'total': len(permisos)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def inicializar(self, request):
        """
        Inicializa todos los permisos del sistema.
        Solo ejecutar en setup inicial.
        
        POST /api/v1/permisos/inicializar/
        """
        resultado = PermissionService.inicializar_permisos()
        
        return Response(resultado, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
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
        id_rol = request.data.get('id_rol')
        codigo_permiso = request.data.get('codigo_permiso')
        
        if not id_rol or not codigo_permiso:
            return Response({
                'success': False,
                'mensaje': 'id_rol y codigo_permiso son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rol = Roles.objects.get(id=id_rol)
            empleado = request.user
            
            resultado = PermissionService.asignar_permiso_a_rol(
                rol, codigo_permiso, empleado
            )
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
                
        except Roles.DoesNotExist:
            return Response({
                'success': False,
                'mensaje': 'Rol no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


# ==================== CRUD BÁSICOS ====================

class RolesViewSet(viewsets.ModelViewSet):
    """
    CRUD de roles con permisos.
    """
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre_rol']
    
    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        """
        Obtiene permisos de un rol específico.
        
        GET /api/v1/roles/{id}/permisos/
        """
        rol = self.get_object()
        
        permisos = RolesPermisos.objects.filter(
            id_rol=rol
        ).select_related('id_permiso').values(
            'id_permiso__id',
            'id_permiso__codigo_permiso',
            'id_permiso__nombre',
            'id_permiso__modulo',
            'fecha_asignacion'
        )
        
        return Response({
            'rol': {
                'id': rol.pk,
                'nombre_rol': rol.nombre_rol,
                'descripcion': rol.descripcion
            },
            'permisos': list(permisos),
            'total': len(permisos)
        }, status=status.HTTP_200_OK)


class EmpleadosViewSet(viewsets.ModelViewSet):
    """
    CRUD de empleados con validaciones de seguridad.
    """
    queryset = Empleados.objects.all()
    serializer_class = EmpleadosSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'id_rol']
    search_fields = ['nombre', 'apellido', 'usuario', 'email']
    ordering_fields = ['apellido', 'nombre']
    ordering = ['apellido', 'nombre']
    
    def create(self, request, *args, **kwargs):
        """
        Crea un empleado con contraseña segura.
        """
        nombre = request.data.get('nombre')
        apellido = request.data.get('apellido')
        usuario = request.data.get('usuario')
        email = request.data.get('email')
        password = request.data.get('password')
        id_rol = request.data.get('id_rol')
        
        if not all([nombre, apellido, usuario, email, password, id_rol]):
            return Response({
                'success': False,
                'mensaje': 'Todos los campos son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        empleado_actual = request.user
        ip_address = self._get_client_ip(request)
        
        resultado = AuthenticationService.crear_empleado(
            nombre, apellido, usuario, email, password, id_rol,
            empleado_actual, ip_address
        )
        
        if resultado['success']:
            serializer = EmpleadosSerializer(resultado['empleado'])
            return Response({
                'success': True,
                'empleado': serializer.data,
                'mensaje': resultado['mensaje']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'mensaje': resultado['mensaje']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


class PerfilesUsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de perfiles de usuario.
    """
    queryset = PerfilesUsuario.objects.all()
    serializer_class = PerfilesUsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_empleado']


class UsuariosPortalViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuarios del portal (clientes).
    """
    queryset = UsuariosPortal.objects.all()
    serializer_class = UsuariosPortalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'id_cliente']
    search_fields = ['email']
