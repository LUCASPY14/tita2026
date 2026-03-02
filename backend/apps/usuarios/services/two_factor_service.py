"""
Servicio de autenticación de dos factores (2FA) con TOTP
Implementa Google Authenticator compatible
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pyotp
import qrcode
import io
import base64
import secrets
import json

from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import (
    Empleados,
    UsuariosPortal,
    Autenticacion2Fa,
    Intentos2Fa,
    AuditoriaOperaciones
)


class TwoFactorAuthService:
    """
    Servicio de autenticación de dos factores usando TOTP (Time-based One-Time Password).
    Compatible con Google Authenticator, Authy, Microsoft Authenticator, etc.
    """
    
    # Configuración
    ISSUER_NAME = "Cantina Tita"
    NUM_BACKUP_CODES = 10
    CODIGO_VALIDO_VENTANA = 1  # Permite 1 código anterior/posterior (30 seg)
    MAX_INTENTOS_2FA = 3
    TIEMPO_BLOQUEO_2FA_MINUTOS = 15
    
    @staticmethod
    def _generar_secret_key() -> str:
        """
        Genera una secret key aleatoria para TOTP.
        
        Returns:
            Secret key en formato base32
        """
        return pyotp.random_base32()
    
    @staticmethod
    def _generar_backup_codes(cantidad: int = NUM_BACKUP_CODES) -> List[str]:
        """
        Genera códigos de respaldo para 2FA.
        
        Returns:
            Lista de códigos en formato XXXX-XXXX
        """
        codigos = []
        for _ in range(cantidad):
            # Generar código aleatorio de 8 caracteres
            codigo = secrets.token_hex(4).upper()
            # Formatear como XXXX-XXXX
            codigo_formateado = f"{codigo[:4]}-{codigo[4:]}"
            codigos.append(codigo_formateado)
        return codigos
    
    @staticmethod
    @transaction.atomic
    def habilitar_2fa_empleado(empleado: Empleados, ip_address: str) -> Dict:
        """
        Habilita 2FA para un empleado.
        
        Returns:
            {
                'success': bool,
                'secret_key': str,
                'qr_code': str (base64),
                'backup_codes': List[str],
                'provisioning_uri': str
            }
        """
        try:
            # Verificar si ya tiene 2FA habilitado
            auth_2fa_existente = Autenticacion2Fa.objects.filter(
                id_empleado=empleado,
                tipo_usuario='empleado',
                habilitado=True
            ).first()
            
            if auth_2fa_existente:
                return {
                    'success': False,
                    'mensaje': '2FA ya está habilitado para este usuario'
                }
            
            # Generar secret key
            secret_key = TwoFactorAuthService._generar_secret_key()
            
            # Generar códigos de respaldo
            backup_codes = TwoFactorAuthService._generar_backup_codes()
            
            # Crear registro 2FA
            auth_2fa = Autenticacion2Fa.objects.create(
                id_empleado=empleado,
                tipo_usuario='empleado',
                secret_key=secret_key,
                backup_codes=json.dumps(backup_codes),
                habilitado=True,
                fecha_activacion=timezone.now()
            )
            
            # Generar URI de provisioning para QR
            totp = pyotp.TOTP(secret_key)
            provisioning_uri = totp.provisioning_uri(
                name=empleado.email or empleado.usuario,
                issuer_name=TwoFactorAuthService.ISSUER_NAME
            )
            
            # Generar código QR
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir imagen a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='HABILITAR_2FA',
                tabla_afectada='Autenticacion2Fa',
                ip_origen=ip_address,
                datos_nuevos={
                    'id_auth_2fa': auth_2fa.id,
                    'tipo_usuario': 'empleado',
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'secret_key': secret_key,
                'qr_code': f"data:image/png;base64,{img_base64}",
                'backup_codes': backup_codes,
                'provisioning_uri': provisioning_uri,
                'mensaje': '2FA habilitado exitosamente. Guarde los códigos de respaldo en un lugar seguro.'
            }
            
        except Exception as e:
            print(f"Error al habilitar 2FA: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al habilitar 2FA: {str(e)}'
            }
    
    @staticmethod
    @transaction.atomic
    def verificar_codigo_2fa(empleado: Empleados, codigo: str, ip_address: str,
                            ciudad: str = None, pais: str = None) -> Dict:
        """
        Verifica un código 2FA (TOTP o código de respaldo).
        
        Args:
            empleado: Instancia del empleado
            codigo: Código de 6 dígitos o código de respaldo
            ip_address: IP del cliente
            ciudad: Ciudad detectada (opcional)
            pais: País detectado (opcional)
            
        Returns:
            {'success': bool, 'mensaje': str, 'tipo_codigo': str}
        """
        try:
            # Buscar configuración 2FA
            auth_2fa = Autenticacion2Fa.objects.filter(
                id_empleado=empleado,
                tipo_usuario='empleado',
                habilitado=True
            ).first()
            
            if not auth_2fa:
                return {
                    'success': False,
                    'mensaje': '2FA no está habilitado para este usuario'
                }
            
            # Verificar si está bloqueado temporalmente
            intentos_recientes = TwoFactorAuthService._contar_intentos_fallidos_recientes(
                empleado, TwoFactorAuthService.TIEMPO_BLOQUEO_2FA_MINUTOS
            )
            
            if intentos_recientes >= TwoFactorAuthService.MAX_INTENTOS_2FA:
                TwoFactorAuthService._registrar_intento_2fa(
                    empleado, ip_address, False, 
                    "Bloqueado por múltiples intentos fallidos",
                    ciudad, pais
                )
                return {
                    'success': False,
                    'mensaje': f'Demasiados intentos fallidos. Intente nuevamente en {TwoFactorAuthService.TIEMPO_BLOQUEO_2FA_MINUTOS} minutos.'
                }
            
            # Intentar verificar como código TOTP
            totp = pyotp.TOTP(auth_2fa.secret_key)
            
            # Limpiar código (remover espacios, guiones)
            codigo_limpio = codigo.replace(' ', '').replace('-', '')
            
            if totp.verify(codigo_limpio, valid_window=TwoFactorAuthService.CODIGO_VALIDO_VENTANA):
                # Código TOTP válido
                TwoFactorAuthService._registrar_intento_2fa(
                    empleado, ip_address, True, None, ciudad, pais
                )
                
                return {
                    'success': True,
                    'mensaje': 'Código 2FA verificado correctamente',
                    'tipo_codigo': 'totp'
                }
            
            # Intentar verificar como código de respaldo
            if TwoFactorAuthService._verificar_backup_code(auth_2fa, codigo_limpio, ip_address):
                TwoFactorAuthService._registrar_intento_2fa(
                    empleado, ip_address, True, None, ciudad, pais
                )
                
                return {
                    'success': True,
                    'mensaje': 'Código de respaldo verificado. ADVERTENCIA: Este código ya no puede usarse nuevamente.',
                    'tipo_codigo': 'backup'
                }
            
            # Código inválido
            TwoFactorAuthService._registrar_intento_2fa(
                empleado, ip_address, False, "Código inválido", ciudad, pais
            )
            
            intentos_restantes = TwoFactorAuthService.MAX_INTENTOS_2FA - intentos_recientes - 1
            
            return {
                'success': False,
                'mensaje': f'Código 2FA inválido. Intentos restantes: {intentos_restantes}',
                'intentos_restantes': intentos_restantes
            }
            
        except Exception as e:
            print(f"Error al verificar código 2FA: {str(e)}")
            return {
                'success': False,
                'mensaje': 'Error al verificar código 2FA'
            }
    
    @staticmethod
    def _verificar_backup_code(auth_2fa: Autenticacion2Fa, codigo: str, 
                               ip_address: str) -> bool:
        """
        Verifica un código de respaldo y lo marca como usado.
        
        Returns:
            True si el código es válido, False caso contrario
        """
        try:
            backup_codes = json.loads(auth_2fa.backup_codes)
            
            # Buscar código en la lista
            if codigo in backup_codes:
                # Remover código usado
                backup_codes.remove(codigo)
                auth_2fa.backup_codes = json.dumps(backup_codes)
                auth_2fa.save()
                
                return True
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def _registrar_intento_2fa(empleado: Empleados, ip_address: str,
                               exitoso: bool, motivo_fallo: str = None,
                               ciudad: str = None, pais: str = None) -> Intentos2Fa:
        """
        Registra un intento de verificación 2FA.
        """
        return Intentos2Fa.objects.create(
            id_empleado=empleado,
            tipo_usuario='empleado',
            ip_address=ip_address,
            ciudad=ciudad,
            pais=pais,
            exitoso=exitoso,
            motivo_fallo=motivo_fallo,
            fecha_intento=timezone.now()
        )
    
    @staticmethod
    def _contar_intentos_fallidos_recientes(empleado: Empleados, minutos: int) -> int:
        """
        Cuenta intentos 2FA fallidos recientes.
        """
        tiempo_limite = timezone.now() - timedelta(minutes=minutos)
        return Intentos2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado',
            exitoso=False,
            fecha_intento__gte=tiempo_limite
        ).count()
    
    @staticmethod
    @transaction.atomic
    def deshabilitar_2fa_empleado(empleado: Empleados, ip_address: str) -> Dict:
        """
        Deshabilita 2FA para un empleado.
        
        Returns:
            {'success': bool, 'mensaje': str}
        """
        try:
            auth_2fa = Autenticacion2Fa.objects.filter(
                id_empleado=empleado,
                tipo_usuario='empleado',
                habilitado=True
            ).first()
            
            if not auth_2fa:
                return {
                    'success': False,
                    'mensaje': '2FA no está habilitado'
                }
            
            auth_2fa.habilitado = False
            auth_2fa.save()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='DESHABILITAR_2FA',
                tabla_afectada='Autenticacion2Fa',
                ip_origen=ip_address,
                datos_anteriores={
                    'habilitado': True
                },
                datos_nuevos={
                    'habilitado': False,
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'mensaje': '2FA deshabilitado exitosamente'
            }
            
        except Exception as e:
            print(f"Error al deshabilitar 2FA: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al deshabilitar 2FA: {str(e)}'
            }
    
    @staticmethod
    @transaction.atomic
    def regenerar_backup_codes(empleado: Empleados, ip_address: str) -> Dict:
        """
        Regenera códigos de respaldo para un empleado.
        
        Returns:
            {'success': bool, 'backup_codes': List[str], 'mensaje': str}
        """
        try:
            auth_2fa = Autenticacion2Fa.objects.filter(
                id_empleado=empleado,
                tipo_usuario='empleado',
                habilitado=True
            ).first()
            
            if not auth_2fa:
                return {
                    'success': False,
                    'mensaje': '2FA no está habilitado'
                }
            
            # Generar nuevos códigos
            nuevos_backup_codes = TwoFactorAuthService._generar_backup_codes()
            
            auth_2fa.backup_codes = json.dumps(nuevos_backup_codes)
            auth_2fa.save()
            
            # Registrar en auditoría
            AuditoriaOperaciones.objects.create(
                id_empleado=empleado,
                operacion='REGENERAR_BACKUP_CODES',
                tabla_afectada='Autenticacion2Fa',
                ip_origen=ip_address,
                datos_nuevos={
                    'num_codigos': len(nuevos_backup_codes),
                    'timestamp': str(timezone.now())
                }
            )
            
            return {
                'success': True,
                'backup_codes': nuevos_backup_codes,
                'mensaje': 'Códigos de respaldo regenerados exitosamente. Los códigos anteriores ya no son válidos.'
            }
            
        except Exception as e:
            print(f"Error al regenerar códigos: {str(e)}")
            return {
                'success': False,
                'mensaje': f'Error al regenerar códigos: {str(e)}'
            }
    
    @staticmethod
    def verificar_2fa_habilitado(empleado: Empleados) -> bool:
        """
        Verifica si un empleado tiene 2FA habilitado.
        
        Returns:
            True si tiene 2FA habilitado, False caso contrario
        """
        return Autenticacion2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado',
            habilitado=True
        ).exists()
    
    @staticmethod
    def obtener_estadisticas_2fa(empleado: Empleados) -> Dict:
        """
        Obtiene estadísticas de uso de 2FA para un empleado.
        
        Returns:
            {
                'habilitado': bool,
                'fecha_activacion': datetime,
                'total_intentos': int,
                'intentos_exitosos': int,
                'intentos_fallidos': int,
                'backup_codes_restantes': int,
                'ultimo_uso': datetime
            }
        """
        auth_2fa = Autenticacion2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado'
        ).first()
        
        if not auth_2fa:
            return {
                'habilitado': False
            }
        
        # Contar códigos de respaldo restantes
        backup_codes_restantes = 0
        if auth_2fa.backup_codes:
            try:
                backup_codes = json.loads(auth_2fa.backup_codes)
                backup_codes_restantes = len(backup_codes)
            except:
                pass
        
        # Obtener estadísticas de intentos
        total_intentos = Intentos2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado'
        ).count()
        
        intentos_exitosos = Intentos2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado',
            exitoso=True
        ).count()
        
        ultimo_intento = Intentos2Fa.objects.filter(
            id_empleado=empleado,
            tipo_usuario='empleado'
        ).order_by('-fecha_intento').first()
        
        return {
            'habilitado': auth_2fa.habilitado,
            'fecha_activacion': auth_2fa.fecha_activacion,
            'total_intentos': total_intentos,
            'intentos_exitosos': intentos_exitosos,
            'intentos_fallidos': total_intentos - intentos_exitosos,
            'backup_codes_restantes': backup_codes_restantes,
            'ultimo_uso': ultimo_intento.fecha_intento if ultimo_intento else None
        }
