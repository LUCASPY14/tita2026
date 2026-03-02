"""
Servicio de recuperación de contraseñas
Maneja tokens seguros, validación y expiración
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets
import hashlib

from django.db import transaction
from django.utils import timezone

from apps.usuarios.models import (
    Empleados,
    UsuariosPortal,
    TokensRecuperacion,
    TokensVerificacion,
    AuditoriaOperaciones
)

from apps.usuarios.services.auth_service import AuthenticationService


class PasswordRecoveryService:
    """
    Servicio de recuperación y restablecimiento de contraseñas.
    Implementa tokens seguros con expiración.
    """
    
    # Configuración
    TOKEN_EXPIRACION_HORAS = 2
    TOKEN_LENGTH = 32  # 32 bytes = 64 caracteres hex
    MAX_INTENTOS_RECUPERACION_DIA = 5
    
    @staticmethod
    def _generar_token_seguro() -> str:
        """
        Genera un token criptográficamente seguro.
        
        Returns:
            Token hexadecimal de 64 caracteres
        """
        return secrets.token_hex(PasswordRecoveryService.TOKEN_LENGTH)
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash del token para almacenamiento seguro.
        
        Returns:
            Hash SHA-256 del token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    @transaction.atomic
    def solicitar_recuperacion_empleado(email: str, ip_address: str) -> Dict:
        """
        Solicita recuperación de contraseña para un empleado.
        
        Args:
            email: Email del empleado
            ip_address: IP desde donde se solicita
            
        Returns:
            {
                'success': bool,
                'token': str (solo si success=True),
                'mensaje': str,
                'expira_en_minutos': int
            }
        """
        try:
            # Buscar empleado por email
            empleado = Empleados.objects.filter(email=email, activo=True).first()
            
            if not empleado:
                # No revelar si el email existe (seguridad)
                return {
                    'success': True,
                    'mensaje': 'Si el email existe, recibirá instrucciones para recuperar su contraseña',
                    'token': None  # No se genera token si no existe
                }
            
            # Verificar límite de solicitudes diarias
            hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            solicitudes_hoy = TokensVerificacion.objects.filter(
                id_empleado=empleado,
                tipo='password_reset',
                fecha_creacion__gte=hoy_inicio
            ).count()
            
            if solicitudes_hoy >= PasswordRecoveryService.MAX_INTENTOS_RECUPERACION_DIA:
                return {
                    'success': False,
                    'mensaje': f'Ha excedido el límite de {PasswordRecoveryService.MAX_INTENTOS_RECUPERACION_DIA} solicitudes por día'
                }
            
            # Invalidar tokens anteriores no usados
            TokensVerificacion.objects.filter(
                id_empleado=empleado,
                tipo='password_reset',
                usado=False,
                fecha_expiracion__gt=timezone.now()
            ).update(usado=True)
            
            # Generar nuevo token
            token = PasswordRecoveryService._generar_token_seguro()
            token_hash = PasswordRecoveryService._hash_token(token)
            
            fecha_expiracion = timezone.now() + timedelta(
                hours=PasswordRecoveryService.TOKEN_EXPIRACION_HORAS
            )
            
            # Crear registro de token
            TokensVerificacion.objects.create(
                id_empleado=empleado,
                tipo='password_reset',
                token=token_hash,
                fecha_expiracion=fecha_expiracion,
                ip_solicitud=ip_address,
                usado=False
            )
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='SOLICITAR_RECUPERACION_PASSWORD',
                tabla_afectada='TokensVerificacion',
                ip_origen=ip_address,
                datos_nuevos={
                    'email': email,
                    'expira_en_horas': PasswordRecoveryService.TOKEN_EXPIRACION_HORAS,
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'token': token,  # Este token se envía por email (el hash se guarda en BD)
                'mensaje': 'Token de recuperación generado exitosamente',
                'expira_en_minutos': PasswordRecoveryService.TOKEN_EXPIRACION_HORAS * 60
            }
            
        except Exception as e:
            print(f"Error al solicitar recuperación: {str(e)}")
            return {
                'success': False,
                'mensaje': 'Error al procesar solicitud de recuperación'
            }
    
    @staticmethod
    def validar_token_recuperacion(token: str, tipo_usuario: str = 'empleado') -> Dict:
        """
        Valida un token de recuperación.
        
        Args:
            token: Token en texto plano
            tipo_usuario: 'empleado' o 'portal'
            
        Returns:
            {
                'valido': bool,
                'empleado': Empleados (si es válido),
                'mensaje': str
            }
        """
        try:
            token_hash = PasswordRecoveryService._hash_token(token)
            
            # Buscar token
            registro_token = TokensVerificacion.objects.filter(
                token=token_hash,
                tipo='password_reset',
                usado=False,
                fecha_expiracion__gt=timezone.now()
            ).select_related('id_empleado').first()
            
            if not registro_token:
                return {
                    'valido': False,
                    'mensaje': 'Token inválido o expirado'
                }
            
            return {
                'valido': True,
                'empleado': registro_token.id_empleado,
                'mensaje': 'Token válido'
            }
            
        except Exception as e:
            print(f"Error al validar token: {str(e)}")
            return {
                'valido': False,
                'mensaje': 'Error al validar token'
            }
    
    @staticmethod
    @transaction.atomic
    def restablecer_password_con_token(token: str, nueva_password: str, 
                                       ip_address: str) -> Dict:
        """
        Restablece la contraseña usando un token de recuperación.
        
        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            # Validar token
            resultado_validacion = PasswordRecoveryService.validar_token_recuperacion(token)
            
            if not resultado_validacion['valido']:
                return {
                    'success': False,
                    'mensaje': resultado_validacion['mensaje']
                }
            
            empleado = resultado_validacion['empleado']
            
            # Validar fortaleza de nueva contraseña
            es_valida, mensaje_error = AuthenticationService.validar_fortaleza_password(nueva_password)
            if not es_valida:
                return {
                    'success': False,
                    'mensaje': mensaje_error
                }
            
            # Cambiar contraseña
            hash_anterior = empleado.contrasena_hash
            empleado.contrasena_hash = AuthenticationService._hash_password(nueva_password)
            empleado.save()
            
            # Marcar token como usado
            token_hash = PasswordRecoveryService._hash_token(token)
            TokensVerificacion.objects.filter(
                token=token_hash,
                tipo='password_reset'
            ).update(
                usado=True,
                fecha_uso=timezone.now(),
                ip_uso=ip_address
            )
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='RESTABLECER_PASSWORD_TOKEN',
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
            
            # Invalidar todas las sesiones activas (seguridad)
            from apps.usuarios.models import SesionesActivas
            SesionesActivas.objects.filter(
                id_empleado=empleado,
                activa=True
            ).update(
                activa=False,
                fecha_cierre=timezone.now()
            )
            
            return {
                'success': True,
                'mensaje': 'Contraseña restablecida exitosamente. Por favor, inicie sesión con su nueva contraseña.'
            }
            
        except Exception as e:
            print(f"Error al restablecer contraseña: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al restablecer contraseña: {str(e)}'
            }
    
    @staticmethod
    @transaction.atomic
    def solicitar_verificacion_email(empleado: Empleados, ip_address: str) -> Dict:
        """
        Genera token para verificación de email.
        
        Returns:
            {'success': bool, 'token': str, 'mensaje': str}
        """
        try:
            # Invalidar tokens anteriores
            TokensVerificacion.objects.filter(
                id_empleado=empleado,
                tipo='email_verification',
                usado=False
            ).update(usado=True)
            
            # Generar nuevo token
            token = PasswordRecoveryService._generar_token_seguro()
            token_hash = PasswordRecoveryService._hash_token(token)
            
            # Token de verificación válido por 24 horas
            fecha_expiracion = timezone.now() + timedelta(hours=24)
            
            TokensVerificacion.objects.create(
                id_empleado=empleado,
                tipo='email_verification',
                token=token_hash,
                fecha_expiracion=fecha_expiracion,
                ip_solicitud=ip_address,
                usado=False
            )
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='SOLICITAR_VERIFICACION_EMAIL',
                tabla_afectada='TokensVerificacion',
                ip_origen=ip_address,
                datos_nuevos={
                    'email': empleado.email,
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'token': token,
                'mensaje': 'Token de verificación generado'
            }
            
        except Exception as e:
            print(f"Error al generar token de verificación: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al generar token: {str(e)}'
            }
    
    @staticmethod
    @transaction.atomic
    def verificar_email(token: str, ip_address: str) -> Dict:
        """
        Verifica el email de un empleado usando el token.
        
        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            token_hash = PasswordRecoveryService._hash_token(token)
            
            # Buscar token
            registro_token = TokensVerificacion.objects.filter(
                token=token_hash,
                tipo='email_verification',
                usado=False,
                fecha_expiracion__gt=timezone.now()
            ).select_related('id_empleado').first()
            
            if not registro_token:
                return {
                    'success': False,
                    'mensaje': 'Token inválido o expirado'
                }
            
            empleado = registro_token.id_empleado
            
            # Marcar token como usado
            registro_token.usado = True
            registro_token.fecha_uso = timezone.now()
            registro_token.ip_uso = ip_address
            registro_token.save()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='VERIFICAR_EMAIL',
                tabla_afectada='Empleados',
                ip_origen=ip_address,
                datos_nuevos={
                    'email_verificado': True,
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'mensaje': 'Email verificado exitosamente'
            }
            
        except Exception as e:
            print(f"Error al verificar email: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al verificar email: {str(e)}'
            }
    
    @staticmethod
    @transaction.atomic
    def limpiar_tokens_expirados() -> Dict:
        """
        Limpia tokens expirados.
        Debe ejecutarse periódicamente (ej: diariamente con cron job).
        
        Returns:
            {'tokens_eliminados': int, 'mensaje': str}
        """
        try:
            # Eliminar tokens expirados hace más de 7 días
            fecha_limite = timezone.now() - timedelta(days=7)
            
            tokens_eliminados = TokensVerificacion.objects.filter(
                fecha_expiracion__lt=fecha_limite
            ).count()
            
            TokensVerificacion.objects.filter(
                fecha_expiracion__lt=fecha_limite
            ).delete()
            
            # También limpiar TokensRecuperacion para clientes (modelo separado)
            tokens_recuperacion_eliminados = TokensRecuperacion.objects.filter(
                fecha_expiracion__lt=fecha_limite
            ).count()
            
            TokensRecuperacion.objects.filter(
                fecha_expiracion__lt=fecha_limite
            ).delete()
            
            total = tokens_eliminados + tokens_recuperacion_eliminados
            
            return {
                'tokens_eliminados': total,
                'mensaje': f'{total} tokens expirados eliminados'
            }
            
        except Exception as e:
            print(f"Error al limpiar tokens: {str(e)}")
            return {
                'tokens_eliminados': 0,
                'mensaje': f'Error al limpiar tokens: {str(e)}'
            }
