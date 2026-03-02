"""
Tests para TwoFactorAuthService
Cobertura completa de autenticación de dos factores (2FA/TOTP)
"""
from django.test import TransactionTestCase
from django.utils import timezone
from datetime import timedelta
import pyotp
import base64
from apps.usuarios.services.two_factor_service import TwoFactorAuthService
from apps.usuarios.models import (
    Empleados, Roles, Autenticacion2Fa, Intentos2Fa
)


class TwoFactorAuthServiceTest(TransactionTestCase):
    """Tests para el servicio de autenticación 2FA"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol de prueba
        self.rol_test = Roles.objects.create(
            nombre_rol='Test Role',
            descripcion='Rol para testing',
            activo=True
        )
        
        # Crear empleado de prueba
        self.empleado = Empleados.objects.create(
            nombre='Test',
            apellido='Usuario',
            usuario='testusuario',
            email='test@cantinatita.com',
            contrasena_hash='hash_test',
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            activo=True
        )
        
        self.ip_address = '127.0.0.1'
        self.ciudad = 'Test City'
        self.pais = 'Test Country'
    
    def tearDown(self):
        """Limpieza después de cada test"""
        Intentos2Fa.objects.all().delete()
        Autenticacion2Fa.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


class SecretKeyGenerationTest(TwoFactorAuthServiceTest):
    """Tests para generación de secret keys"""
    
    def test_generar_secret_key_formato_valido(self):
        """Verificar que se genera una secret key válida"""
        secret = TwoFactorAuthService._generar_secret_key()
        
        # Verificar que es una cadena base32 válida
        self.assertIsInstance(secret, str)
        self.assertGreater(len(secret), 0)
        # Verificar que puede ser decodificada como base32
        try:
            base64.b32decode(secret)
            valida = True
        except:
            valida = False
        self.assertTrue(valida)
    
    def test_generar_secret_key_es_unica(self):
        """Cada secret key generada debe ser única"""
        secret1 = TwoFactorAuthService._generar_secret_key()
        secret2 = TwoFactorAuthService._generar_secret_key()
        
        self.assertNotEqual(secret1, secret2)


class BackupCodesGenerationTest(TwoFactorAuthServiceTest):
    """Tests para generación de códigos de respaldo"""
    
    def test_generar_backup_codes_cantidad(self):
        """Verificar que se generan 10 códigos de respaldo"""
        codes = TwoFactorAuthService._generar_backup_codes()
        
        self.assertEqual(len(codes), 10)
    
    def test_generar_backup_codes_formato(self):
        """Verificar formato XXXX-XXXX"""
        codes = TwoFactorAuthService._generar_backup_codes()
        
        for code in codes:
            # Formato: XXXX-XXXX (4 dígitos, guion, 4 dígitos)
            self.assertRegex(code, r'^\d{4}-\d{4}$')
    
    def test_generar_backup_codes_unicos(self):
        """Todos los códigos deben ser únicos"""
        codes = TwoFactorAuthService._generar_backup_codes()
        
        # Verificar que no hay duplicados
        self.assertEqual(len(codes), len(set(codes)))


class Enable2FATest(TwoFactorAuthServiceTest):
    """Tests para habilitación de 2FA"""
    
    def test_habilitar_2fa_exitoso(self):
        """Habilitar 2FA para un empleado"""
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        self.assertTrue(resultado['success'])
        self.assertIn('secret_key', resultado)
        self.assertIn('qr_code', resultado)
        self.assertIn('backup_codes', resultado)
        self.assertIn('provisioning_uri', resultado)
        
        # Verificar códigos de respaldo
        self.assertEqual(len(resultado['backup_codes']), 10)
        
        # Verificar QR code es base64
        qr_code = resultado['qr_code']
        self.assertTrue(qr_code.startswith('data:image/png;base64,'))
    
    def test_habilitar_2fa_crea_registro_db(self):
        """Verificar que se crea el registro en la base de datos"""
        TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        # Verificar registro en DB
        auth_2fa = Autenticacion2Fa.objects.filter(
            id_empleado=self.empleado
        ).first()
        
        self.assertIsNotNone(auth_2fa)
        self.assertTrue(auth_2fa.habilitado)
        self.assertIsNotNone(auth_2fa.secret_key)
        self.assertEqual(len(auth_2fa.backup_codes), 10)
    
    def test_habilitar_2fa_ya_habilitado(self):
        """Intentar habilitar 2FA cuando ya está habilitado"""
        # Primera habilitación
        TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        # Segunda habilitación
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('habilitado', resultado['mensaje'].lower())
    
    def test_provisioning_uri_formato_correcto(self):
        """Verificar formato del provisioning URI para apps TOTP"""
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        uri = resultado['provisioning_uri']
        
        # Debe empezar con otpauth://totp/
        self.assertTrue(uri.startswith('otpauth://totp/'))
        # Debe contener el usuario
        self.assertIn('testusuario', uri)
        # Debe contener el issuer
        self.assertIn('issuer=', uri)


class Verify2FATest(TwoFactorAuthServiceTest):
    """Tests para verificación de códigos 2FA"""
    
    def setUp(self):
        """Configuración adicional para tests de verificación"""
        super().setUp()
        
        # Habilitar 2FA para el empleado
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        self.secret_key = resultado['secret_key']
        self.backup_codes = resultado['backup_codes']
        
        # Crear TOTP generator para generar códigos válidos
        self.totp = pyotp.TOTP(self.secret_key)
    
    def test_verificar_codigo_totp_valido(self):
        """Verificar código TOTP válido"""
        # Generar código actual
        codigo_valido = self.totp.now()
        
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_valido,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['tipo_codigo'], 'totp')
    
    def test_verificar_codigo_totp_invalido(self):
        """Verificar código TOTP inválido"""
        codigo_invalido = '000000'
        
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_invalido,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertFalse(resultado['success'])
    
    def test_verificar_backup_code_valido(self):
        """Verificar código de respaldo válido"""
        codigo_backup = self.backup_codes[0]
        
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_backup,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['tipo_codigo'], 'backup')
    
    def test_verificar_backup_code_marca_usado(self):
        """Código de respaldo usado se marca como tal"""
        codigo_backup = self.backup_codes[0]
        
        # Primera verificación (debe funcionar)
        resultado1 = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_backup,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        self.assertTrue(resultado1['success'])
        
        # Segunda verificación con mismo código (debe fallar)
        resultado2 = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_backup,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        self.assertFalse(resultado2['success'])
    
    def test_verificar_codigo_2fa_no_habilitado(self):
        """Verificar código cuando 2FA no está habilitado"""
        # Crear empleado sin 2FA
        empleado_sin_2fa = Empleados.objects.create(
            nombre='Sin2FA',
            apellido='Usuario',
            usuario='sin2fa',
            email='sin2fa@cantinatita.com',
            contrasena_hash='hash_test',
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            activo=True
        )
        
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=empleado_sin_2fa,
            codigo='123456',
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('habilitado', resultado['mensaje'].lower())
    
    def test_limite_intentos_fallidos(self):
        """Bloquear tras 3 intentos fallidos en 15 minutos"""
        codigo_invalido = '000000'
        
        # Hacer 3 intentos fallidos
        for i in range(3):
            TwoFactorAuthService.verificar_codigo_2fa(
                empleado=self.empleado,
                codigo=codigo_invalido,
                ip_address=self.ip_address,
                ciudad=self.ciudad,
                pais=self.pais
            )
        
        # Cuarto intento debe ser bloqueado
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_invalido,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('intentos', resultado['mensaje'].lower())


class Disable2FATest(TwoFactorAuthServiceTest):
    """Tests para deshabilitación de 2FA"""
    
    def setUp(self):
        """Configuración adicional"""
        super().setUp()
        
        # Habilitar 2FA primero
        TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
    
    def test_deshabilitar_2fa_exitoso(self):
        """Deshabilitar 2FA correctamente"""
        resultado = TwoFactorAuthService.deshabilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        self.assertTrue(resultado['success'])
        
        # Verificar en DB
        auth_2fa = Autenticacion2Fa.objects.get(id_empleado=self.empleado)
        self.assertFalse(auth_2fa.habilitado)
        self.assertIsNotNone(auth_2fa.fecha_deshabilitado)
    
    def test_deshabilitar_2fa_no_habilitado(self):
        """Intentar deshabilitar cuando no está habilitado"""
        # Crear empleado sin 2FA
        empleado_sin_2fa = Empleados.objects.create(
            nombre='Sin2FA',
            apellido='Usuario',
            usuario='sin2fa',
            email='sin2fa@cantinatita.com',
            contrasena_hash='hash_test',
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            activo=True
        )
        
        resultado = TwoFactorAuthService.deshabilitar_2fa_empleado(
            empleado=empleado_sin_2fa,
            ip_address=self.ip_address
        )
        
        self.assertFalse(resultado['success'])


class RegenerateBackupCodesTest(TwoFactorAuthServiceTest):
    """Tests para regeneración de códigos de respaldo"""
    
    def setUp(self):
        """Configuración adicional"""
        super().setUp()
        
        # Habilitar 2FA
        resultado = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        self.codigos_originales = resultado['backup_codes']
    
    def test_regenerar_backup_codes_exitoso(self):
        """Regenerar códigos de respaldo"""
        resultado = TwoFactorAuthService.regenerar_backup_codes(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        self.assertTrue(resultado['success'])
        self.assertIn('backup_codes', resultado)
        self.assertEqual(len(resultado['backup_codes']), 10)
    
    def test_regenerar_backup_codes_diferentes(self):
        """Los nuevos códigos deben ser diferentes a los anteriores"""
        resultado = TwoFactorAuthService.regenerar_backup_codes(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        codigos_nuevos = resultado['backup_codes']
        
        # Verificar que son diferentes
        self.assertNotEqual(
            set(self.codigos_originales),
            set(codigos_nuevos)
        )
    
    def test_regenerar_backup_codes_invalidates_old(self):
        """Códigos antiguos no deben funcionar después de regenerar"""
        codigo_antiguo = self.codigos_originales[0]
        
        # Regenerar
        TwoFactorAuthService.regenerar_backup_codes(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        # Intentar usar código antiguo (debe fallar)
        resultado = TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_antiguo,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        self.assertFalse(resultado['success'])
    
    def test_regenerar_backup_codes_sin_2fa(self):
        """No permitir regenerar si 2FA no está habilitado"""
        empleado_sin_2fa = Empleados.objects.create(
            nombre='Sin2FA',
            apellido='Usuario',
            usuario='sin2fa',
            email='sin2fa@cantinatita.com',
            contrasena_hash='hash_test',
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            activo=True
        )
        
        resultado = TwoFactorAuthService.regenerar_backup_codes(
            empleado=empleado_sin_2fa,
            ip_address=self.ip_address
        )
        
        self.assertFalse(resultado['success'])


class Get2FAStatsTest(TwoFactorAuthServiceTest):
    """Tests para obtener estadísticas de 2FA"""
    
    def test_estadisticas_sin_2fa(self):
        """Estadísticas para empleado sin 2FA"""
        resultado = TwoFactorAuthService.obtener_estadisticas_2fa(
            empleado=self.empleado
        )
        
        self.assertTrue(resultado['success'])
        self.assertFalse(resultado['habilitado'])
        self.assertEqual(resultado['intentos_fallidos_recientes'], 0)
    
    def test_estadisticas_con_2fa_habilitado(self):
        """Estadísticas para empleado con 2FA habilitado"""
        # Habilitar 2FA
        TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        resultado = TwoFactorAuthService.obtener_estadisticas_2fa(
            empleado=self.empleado
        )
        
        self.assertTrue(resultado['success'])
        self.assertTrue(resultado['habilitado'])
        self.assertIn('backup_codes_restantes', resultado)
        self.assertEqual(resultado['backup_codes_restantes'], 10)
        self.assertIsNotNone(resultado['fecha_habilitado'])
    
    def test_estadisticas_backup_codes_usados(self):
        """Estadísticas reflejan códigos de respaldo usados"""
        # Habilitar 2FA
        resultado_habilitar = TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        # Usar un código de respaldo
        codigo_backup = resultado_habilitar['backup_codes'][0]
        TwoFactorAuthService.verificar_codigo_2fa(
            empleado=self.empleado,
            codigo=codigo_backup,
            ip_address=self.ip_address,
            ciudad=self.ciudad,
            pais=self.pais
        )
        
        # Obtener estadísticas
        resultado = TwoFactorAuthService.obtener_estadisticas_2fa(
            empleado=self.empleado
        )
        
        self.assertEqual(resultado['backup_codes_restantes'], 9)
    
    def test_estadisticas_intentos_fallidos(self):
        """Estadísticas muestran intentos fallidos recientes"""
        # Habilitar 2FA
        TwoFactorAuthService.habilitar_2fa_empleado(
            empleado=self.empleado,
            ip_address=self.ip_address
        )
        
        # Hacer 2 intentos fallidos
        for _ in range(2):
            TwoFactorAuthService.verificar_codigo_2fa(
                empleado=self.empleado,
                codigo='000000',
                ip_address=self.ip_address,
                ciudad=self.ciudad,
                pais=self.pais
            )
        
        # Obtener estadísticas
        resultado = TwoFactorAuthService.obtener_estadisticas_2fa(
            empleado=self.empleado
        )
        
        self.assertEqual(resultado['intentos_fallidos_recientes'], 2)
