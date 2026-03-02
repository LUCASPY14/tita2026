"""
Servicio de autenticación empresarial para cantina_tita
Incluye: JWT, validación de contraseñas, bloqueo de cuentas, auditoría
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from decimal import Decimal
import bcrypt
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import (
    Empleados, 
    IntentosLogin, 
    BloqueosCuenta, 
    SesionesActivas,
    AuditoriaOperaciones
)


class AuthenticationService:
    """
    Servicio centralizado para autenticación y seguridad de empleados.
    Implementa mejores prácticas de seguridad empresarial.
    """
    
    # Configuración de seguridad
    MAX_LOGIN_INTENTOS = 5
    TIEMPO_BLOQUEO_MINUTOS = 30
    TIEMPO_EXPIRACION_SESSION_HORAS = 24
    MIN_PASSWORD_LENGTH = 8
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash de contraseña usando bcrypt con salt automático.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash bcrypt de la contraseña
        """
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds para equilibrio seguridad/rendimiento
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica contraseña contra hash bcrypt.
        
        Args:
            password: Contraseña en texto plano
            password_hash: Hash almacenado
            
        Returns:
            True si coinciden, False caso contrario
        """
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False
    
    @staticmethod
    def validar_fortaleza_password(password: str) -> Tuple[bool, str]:
        """
        Valida que la contraseña cumpla con requisitos de seguridad.
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 minúscula
        - Al menos 1 número
        - Al menos 1 carácter especial
        
        Returns:
            (es_valida, mensaje_error)
        """
        if len(password) < AuthenticationService.MIN_PASSWORD_LENGTH:
            return False, f"La contraseña debe tener al menos {AuthenticationService.MIN_PASSWORD_LENGTH} caracteres"
        
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una letra mayúscula"
        
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una letra minúscula"
        
        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*...)"
        
        return True, ""
    
    @staticmethod
    def verificar_cuenta_bloqueada(empleado: Empleados) -> Tuple[bool, Optional[str]]:
        """
        Verifica si la cuenta del empleado está bloqueada.
        
        Returns:
            (esta_bloqueada, motivo)
        """
        # Verificar si el empleado está marcado como inactivo
        if not empleado.activo:
            return True, "Cuenta desactivada"
        
        # Buscar bloqueos activos
        bloqueo_activo = BloqueosCuenta.objects.filter(
            id_empleado=empleado,
            activo=True
        ).first()
        
        if bloqueo_activo:
            # Verificar si el bloqueo temporal ha expirado
            if bloqueo_activo.fecha_desbloqueo and timezone.now() > bloqueo_activo.fecha_desbloqueo:
                bloqueo_activo.activo = False
                bloqueo_activo.save()
                return False, None
            
            return True, bloqueo_activo.motivo
        
        return False, None
    
    @staticmethod
    def _bloquear_cuenta(empleado: Empleados, motivo: str, ip_address: str, 
                         temporal: bool = True) -> BloqueosCuenta:
        """
        Bloquea una cuenta de empleado.
        
        Args:
            empleado: Instancia del empleado
            motivo: Razón del bloqueo
            ip_address: IP desde donde se originó el bloqueo
            temporal: Si es temporal (30 min) o permanente
            
        Returns:
            Instancia de BloqueosCuenta creada
        """
        fecha_desbloqueo = None
        if temporal:
            fecha_desbloqueo = timezone.now() + timedelta(
                minutes=AuthenticationService.TIEMPO_BLOQUEO_MINUTOS
            )
        
        bloqueo = BloqueosCuenta.objects.create(
            id_empleado=empleado,
            motivo=motivo,
            ip_origen=ip_address,
            fecha_bloqueo=timezone.now(),
            fecha_desbloqueo=fecha_desbloqueo,
            activo=True
        )
        
        # Registrar en auditoría
        AuditoriaOperaciones.objects.create(
            id_empleado=empleado,
            operacion='BLOQUEO_CUENTA',
            tabla_afectada='BloqueosCuenta',
            ip_origen=ip_address,
            datos_nuevos={
                'id_bloqueo': bloqueo.id,
                'motivo': motivo,
                'temporal': temporal,
                'fecha_desbloqueo': str(fecha_desbloqueo) if fecha_desbloqueo else None
            }
        )
        
        return bloqueo
    
    @staticmethod
    def _registrar_intento_login(empleado: Empleados, ip_address: str, 
                                 exitoso: bool, motivo_fallo: str = None,
                                 navegador: str = None, dispositivo: str = None) -> IntentosLogin:
        """
        Registra un intento de login en la base de datos.
        
        Returns:
            Instancia de IntentosLogin creada
        """
        return IntentosLogin.objects.create(
            id_empleado=empleado,
            ip_address=ip_address,
            exitoso=exitoso,
            motivo_fallo=motivo_fallo,
            navegador=navegador,
            dispositivo=dispositivo,
            fecha_intento=timezone.now()
        )
    
    @staticmethod
    def _contar_intentos_fallidos_recientes(empleado: Empleados, minutos: int = 30) -> int:
        """
        Cuenta intentos fallidos en los últimos X minutos.
        """
        tiempo_limite = timezone.now() - timedelta(minutes=minutos)
        return IntentosLogin.objects.filter(
            id_empleado=empleado,
            exitoso=False,
            fecha_intento__gte=tiempo_limite
        ).count()
    
    @staticmethod
    def _generar_tokens_jwt(empleado: Empleados) -> Dict[str, str]:
        """
        Genera tokens JWT (access y refresh) para el empleado.
        
        Returns:
            {
                'access': token_acceso,
                'refresh': token_refresco
            }
        """
        refresh = RefreshToken.for_user(empleado)
        
        # Agregar claims personalizados
        refresh['id_empleado'] = empleado.id
        refresh['usuario'] = empleado.usuario
        refresh['id_rol'] = empleado.id_rol.id if empleado.id_rol else None
        refresh['nombre_completo'] = f"{empleado.nombre} {empleado.apellido}"
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    
    @staticmethod
    @transaction.atomic
    def login(usuario: str, password: str, ip_address: str, 
              user_agent: str = None) -> Dict:
        """
        Realiza login completo con validaciones de seguridad.
        
        Args:
            usuario: Nombre de usuario
            password: Contraseña en texto plano
            ip_address: IP del cliente
            user_agent: User Agent del navegador
            
        Returns:
            {
                'success': bool,
                'tokens': {'access': str, 'refresh': str},
                'empleado': {...datos empleado...},
                'mensaje': str
            }
            
        Raises:
            Exception: Si hay errores críticos
        """
        try:
            # Buscar empleado
            empleado = Empleados.objects.select_related('id_rol').filter(
                usuario=usuario
            ).first()
            
            if not empleado:
                # No revelar si el usuario existe o no (seguridad)
                return {
                    'success': False,
                    'mensaje': 'Credenciales inválidas',
                    'codigo': 'CREDENCIALES_INVALIDAS'
                }
            
            # Verificar si la cuenta está bloqueada
            bloqueada, motivo_bloqueo = AuthenticationService.verificar_cuenta_bloqueada(empleado)
            if bloqueada:
                AuthenticationService._registrar_intento_login(
                    empleado, ip_address, False, f"Cuenta bloqueada: {motivo_bloqueo}"
                )
                return {
                    'success': False,
                    'mensaje': f'Cuenta bloqueada: {motivo_bloqueo}',
                    'codigo': 'CUENTA_BLOQUEADA'
                }
            
            # Verificar contraseña
            if not AuthenticationService._verify_password(password, empleado.contrasena_hash):
                # Contraseña incorrecta
                AuthenticationService._registrar_intento_login(
                    empleado, ip_address, False, "Contraseña incorrecta"
                )
                
                # Contar intentos fallidos recientes
                intentos_fallidos = AuthenticationService._contar_intentos_fallidos_recientes(empleado)
                
                if intentos_fallidos >= AuthenticationService.MAX_LOGIN_INTENTOS - 1:
                    # Bloquear cuenta
                    AuthenticationService._bloquear_cuenta(
                        empleado, 
                        f"Demasiados intentos fallidos de login ({intentos_fallidos + 1})",
                        ip_address,
                        temporal=True
                    )
                    return {
                        'success': False,
                        'mensaje': f'Cuenta bloqueada temporalmente por {AuthenticationService.TIEMPO_BLOQUEO_MINUTOS} minutos debido a múltiples intentos fallidos',
                        'codigo': 'CUENTA_BLOQUEADA_INTENTOS'
                    }
                
                return {
                    'success': False,
                    'mensaje': 'Credenciales inválidas',
                    'codigo': 'CREDENCIALES_INVALIDAS',
                    'intentos_restantes': AuthenticationService.MAX_LOGIN_INTENTOS - intentos_fallidos - 1
                }
            
            # Login exitoso
            AuthenticationService._registrar_intento_login(
                empleado, ip_address, True
            )
            
            # Generar tokens JWT
            tokens = AuthenticationService._generar_tokens_jwt(empleado)
            
            # Crear sesión activa
            session_key = tokens['refresh']  # Usar refresh token como session_key
            SesionesActivas.objects.create(
                id_empleado=empleado,
                session_key=session_key[:255],  # Truncar si es muy largo
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
                fecha_inicio=timezone.now(),
                fecha_expiracion=timezone.now() + timedelta(hours=AuthenticationService.TIEMPO_EXPIRACION_SESSION_HORAS),
                activa=True
            )
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='LOGIN',
                tabla_afectada='Empleados',
                ip_origen=ip_address,
                datos_nuevos={
                    'usuario': usuario,
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'tokens': tokens,
                'empleado': {
                    'id': empleado.id,
                    'usuario': empleado.usuario,
                    'nombre': empleado.nombre,
                    'apellido': empleado.apellido,
                    'email': empleado.email,
                    'rol': empleado.id_rol.nombre_rol if empleado.id_rol else None,
                    'id_rol': empleado.id_rol.id if empleado.id_rol else None
                },
                'mensaje': 'Login exitoso',
                'codigo': 'LOGIN_EXITOSO'
            }
            
        except Exception as e:
            # Log del error
            print(f"Error en login: {str(e)}")
            return {
                'success': False,
                'mensaje': 'Error interno del servidor',
                'codigo': 'ERROR_SERVIDOR'
            }
    
    @staticmethod
    @transaction.atomic
    def logout(empleado: Empleados, session_key: str, ip_address: str) -> Dict:
        """
        Realiza logout invalidando la sesión.
        
        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            # Invalidar sesión
            sesion = SesionesActivas.objects.filter(
                id_empleado=empleado,
                session_key=session_key[:255],
                activa=True
            ).first()
            
            if sesion:
                sesion.activa = False
                sesion.fecha_cierre = timezone.now()
                sesion.save()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='LOGOUT',
                tabla_afectada='SesionesActivas',
                ip_origen=ip_address,
                datos_nuevos={
                    'session_key': session_key[:50],
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'mensaje': 'Logout exitoso'
            }
            
        except Exception as e:
            print(f"Error en logout: {str(e)}")
            return {
                'success': False,
                'mensaje': 'Error al cerrar sesión'
            }
    
    @staticmethod
    @transaction.atomic
    def cambiar_password(empleado: Empleados, password_actual: str, 
                        password_nueva: str, ip_address: str) -> Dict:
        """
        Cambia la contraseña de un empleado.
        
        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            # Verificar contraseña actual
            if not AuthenticationService._verify_password(password_actual, empleado.contrasena_hash):
                return {
                    'success': False,
                    'mensaje': 'Contraseña actual incorrecta'
                }
            
            # Validar fortaleza de nueva contraseña
            es_valida, mensaje_error = AuthenticationService.validar_fortaleza_password(password_nueva)
            if not es_valida:
                return {
                    'success': False,
                    'mensaje': mensaje_error
                }
            
            # Verificar que no sea igual a la actual
            if password_actual == password_nueva:
                return {
                    'success': False,
                    'mensaje': 'La nueva contraseña debe ser diferente a la actual'
                }
            
            # Cambiar contraseña
            hash_anterior = empleado.contrasena_hash
            empleado.contrasena_hash = AuthenticationService._hash_password(password_nueva)
            empleado.save()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='CAMBIO_PASSWORD',
                tabla_afectada='Empleados',
                ip_origen=ip_address,
                datos_anteriores={
                    'hash_password': hash_anterior[:20] + '...'
                },
                datos_nuevos={
                    'hash_password': empleado.contrasena_hash[:20] + '...',
                    'timestamp': str(timezone.now())
                }
            )
            
            # Invalidar todas las sesiones activas (forzar re-login)
            SesionesActivas.objects.filter(
                id_empleado=empleado,
                activa=True
            ).update(
                activa=False,
                fecha_cierre=timezone.now()
            )
            
            return {
                'success': True,
                'mensaje': 'Contraseña cambiada exitosamente. Por favor, vuelva a iniciar sesión.'
            }
            
        except Exception as e:
            print(f"Error al cambiar contraseña: {str(e)}")
            return {
                'success': False,
                'mensaje': 'Error al cambiar contraseña'
            }
    
    @staticmethod
    @transaction.atomic
    def crear_empleado(nombre: str, apellido: str, usuario: str, 
                      email: str, password: str, id_rol: int, 
                      creado_por: Empleados, ip_address: str) -> Dict:
        """
        Crea un nuevo empleado con validaciones de seguridad.
        
        Returns:
            {'success': bool, 'empleado': Empleados, 'mensaje': str}
        """
        try:
            # Validar fortaleza de contraseña
            es_valida, mensaje_error = AuthenticationService.validar_fortaleza_password(password)
            if not es_valida:
                return {
                    'success': False,
                    'mensaje': mensaje_error
                }
            
            # Verificar que el usuario no exista
            if Empleados.objects.filter(usuario=usuario).exists():
                return {
                    'success': False,
                    'mensaje': 'El nombre de usuario ya está en uso'
                }
            
            # Verificar que el email no exista
            if Empleados.objects.filter(email=email).exists():
                return {
                    'success': False,
                    'mensaje': 'El email ya está registrado'
                }
            
            # Crear empleado
            from apps.usuarios.models import Roles
            rol = Roles.objects.get(id_rol=id_rol)
            
            empleado = Empleados.objects.create(
                nombre=nombre,
                apellido=apellido,
                usuario=usuario,
                email=email,
                contrasena_hash=AuthenticationService._hash_password(password),
                id_rol=rol,
                fecha_ingreso=timezone.now(),
                activo=True
            )
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                usuario=creado_por.usuario if creado_por else 'sistema',
                tipo_usuario='empleado',
                id_usuario=creado_por.id_empleado if creado_por else None,
                operacion='CREAR_EMPLEADO',
                tabla_afectada='Empleados',
                id_registro=empleado.id_empleado,
                ip_address=ip_address,
                datos_nuevos={
                    'id_empleado': empleado.id_empleado,
                    'usuario': usuario,
                    'email': email,
                    'id_rol': id_rol,
                    'timestamp': str(timezone.now())
                },
                fecha_operacion=timezone.now(),
                resultado='OK'
            )
            
            return {
                'success': True,
                'empleado': empleado,
                'mensaje': 'Empleado creado exitosamente'
            }
            
        except Roles.DoesNotExist:
            return {
                'success': False,
                'mensaje': 'El rol especificado no existe'
            }
        except Exception as e:
            print(f"Error al crear empleado: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al crear empleado: {str(e)}'
            }
