"""
Tests para PasswordRecoveryService
Cobertura completa de recuperación de contraseñas y verificación de email
"""

import hashlib
from datetime import timedelta

from django.test import TransactionTestCase
from django.utils import timezone

from apps.usuarios.models import Empleados, Roles, SesionesActivas, TokensRecuperacion
from apps.usuarios.services.password_recovery_service import PasswordRecoveryService


class PasswordRecoveryServiceTest(TransactionTestCase):
    """Tests para el servicio de recuperación de contraseñas"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol de prueba
        self.rol_test = Roles.objects.create(nombre_rol="Test Role", descripcion="Rol para testing", estado=True)

        # Crear empleado de prueba
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="Usuario",
            usuario="testusuario",
            email="test@cantinatita.com",
            contrasena_hash="hash_test",
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            estado=True,
        )

        self.ip_address = "127.0.0.1"

    def tearDown(self):
        """Limpieza después de cada test"""
        TokensRecuperacion.objects.all().delete()
        SesionesActivas.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


class TokenGenerationTest(PasswordRecoveryServiceTest):
    """Tests para generación de tokens"""

    def test_generar_token_seguro_longitud(self):
        """Token generado tiene 64 caracteres (32 bytes hex)"""
        token = PasswordRecoveryService._generar_token_seguro()

        self.assertEqual(len(token), 64)

    def test_generar_token_seguro_unico(self):
        """Cada token generado es único"""
        token1 = PasswordRecoveryService._generar_token_seguro()
        token2 = PasswordRecoveryService._generar_token_seguro()

        self.assertNotEqual(token1, token2)

    def test_hash_token_sha256(self):
        """Hash de token usa SHA-256"""
        token = "test_token_123"
        hash_token = PasswordRecoveryService._hash_token(token)

        # SHA-256 produce 64 caracteres hex
        self.assertEqual(len(hash_token), 64)

        # Verificar que es consistente
        hash_token2 = PasswordRecoveryService._hash_token(token)
        self.assertEqual(hash_token, hash_token2)

    def test_hash_token_diferente_para_diferentes_tokens(self):
        """Diferentes tokens producen diferentes hashes"""
        hash1 = PasswordRecoveryService._hash_token("token1")
        hash2 = PasswordRecoveryService._hash_token("token2")

        self.assertNotEqual(hash1, hash2)


class RequestPasswordRecoveryTest(PasswordRecoveryServiceTest):
    """Tests para solicitud de recuperación de contraseña"""

    def test_solicitar_recuperacion_exitosa(self):
        """Solicitar recuperación de contraseña exitosamente"""
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )

        self.assertTrue(resultado["success"])

        # Verificar que se creó el token en DB
        token_db = TokensRecuperacion.objects.filter(
            id_empleado=self.empleado, tipo="password_recovery", usado=False
        ).first()

        self.assertIsNotNone(token_db)

    def test_solicitar_recuperacion_email_inexistente(self):
        """Intentar recuperar con email que no existe"""
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="noexiste@cantinatita.com", ip_address=self.ip_address
        )

        # Por seguridad, debe devolver success=True aunque no exista
        # (evitar enumeración de usuarios)
        self.assertTrue(resultado["success"])

        # Pero no debe crear token
        tokens = TokensRecuperacion.objects.filter(tipo="password_recovery").count()
        self.assertEqual(tokens, 0)

    def test_solicitar_recuperacion_cuenta_inactiva(self):
        """No permitir recuperación para cuenta inactiva"""
        self.empleado.estado = False
        self.empleado.save()

        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )

        # Por seguridad, success=True
        self.assertTrue(resultado["success"])

        # Pero no debe crear token
        tokens = TokensRecuperacion.objects.filter(id_empleado=self.empleado).count()
        self.assertEqual(tokens, 0)

    def test_solicitar_recuperacion_limite_diario(self):
        """Limitar a 5 solicitudes por día"""
        # Crear 5 solicitudes
        for _ in range(5):
            TokensRecuperacion.objects.create(
                id_empleado=self.empleado,
                tipo="password_recovery",
                token_hash="dummy_hash_" + str(_),
                fecha_creacion=timezone.now(),
                fecha_expiracion=timezone.now() + timedelta(hours=2),
                usado=False,
            )

        # Sexta solicitud debe fallar
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )

        self.assertFalse(resultado["success"])
        self.assertIn("límite", resultado["mensaje"].lower())

    def test_solicitar_recuperacion_expiracion_2_horas(self):
        """Token expira en 2 horas"""
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )

        token_db = TokensRecuperacion.objects.get(id_empleado=self.empleado, tipo="password_recovery")

        tiempo_expiracion = token_db.fecha_expiracion - token_db.fecha_creacion

        # Debe ser aproximadamente 2 horas
        self.assertAlmostEqual(tiempo_expiracion.total_seconds(), 2 * 3600, delta=60)  # +/- 1 minuto


class ValidateRecoveryTokenTest(PasswordRecoveryServiceTest):
    """Tests para validación de tokens"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear token válido
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )
        self.token_valido = resultado["token"]

    def test_validar_token_valido(self):
        """Validar token correcto"""
        resultado = PasswordRecoveryService.validar_token_recuperacion(token=self.token_valido, tipo_usuario="empleado")

        self.assertTrue(resultado["success"])
        self.assertIn("empleado", resultado)
        self.assertEqual(resultado["empleado"].email, "test@cantinatita.com")

    def test_validar_token_invalido(self):
        """Token incorrecto no valida"""
        resultado = PasswordRecoveryService.validar_token_recuperacion(
            token="token_invalido_123", tipo_usuario="empleado"
        )

        self.assertFalse(resultado["success"])

    def test_validar_token_expirado(self):
        """Token expirado no valida"""
        # Crear token expirado manualmente
        token_expirado = "token_expirado"
        hash_token = PasswordRecoveryService._hash_token(token_expirado)

        TokensRecuperacion.objects.create(
            id_empleado=self.empleado,
            tipo="password_recovery",
            token_hash=hash_token,
            fecha_creacion=timezone.now() - timedelta(hours=3),
            fecha_expiracion=timezone.now() - timedelta(hours=1),
            usado=False,
        )

        resultado = PasswordRecoveryService.validar_token_recuperacion(token=token_expirado, tipo_usuario="empleado")

        self.assertFalse(resultado["success"])
        self.assertIn("expirado", resultado["mensaje"].lower())

    def test_validar_token_ya_usado(self):
        """Token usado no puede reutilizarse"""
        # Marcar token como usado
        token_db = TokensRecuperacion.objects.get(token_hash=PasswordRecoveryService._hash_token(self.token_valido))
        token_db.usado = True
        token_db.save()

        resultado = PasswordRecoveryService.validar_token_recuperacion(token=self.token_valido, tipo_usuario="empleado")

        self.assertFalse(resultado["success"])
        self.assertIn("usado", resultado["mensaje"].lower())


class ResetPasswordWithTokenTest(PasswordRecoveryServiceTest):
    """Tests para restablecer contraseña con token"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear token válido
        resultado = PasswordRecoveryService.solicitar_recuperacion_empleado(
            email="test@cantinatita.com", ip_address=self.ip_address
        )
        self.token_valido = resultado["token"]

    def test_restablecer_password_exitoso(self):
        """Restablecer contraseña exitosamente"""
        nueva_password = "NuevaPassword123!@#"

        resultado = PasswordRecoveryService.restablecer_password_con_token(
            token=self.token_valido, nueva_password=nueva_password, ip_address=self.ip_address
        )

        self.assertTrue(resultado["success"])

        # Verificar que el token se marcó como usado
        token_db = TokensRecuperacion.objects.get(token_hash=PasswordRecoveryService._hash_token(self.token_valido))
        self.assertTrue(token_db.usado)
        self.assertIsNotNone(token_db.fecha_uso)

    def test_restablecer_password_invalida_sesiones(self):
        """Restablecer contraseña cierra todas las sesiones"""
        # Crear sesiones activas
        for i in range(2):
            SesionesActivas.objects.create(
                id_empleado=self.empleado,
                session_key=f"session_{i}",
                ip_address=self.ip_address,
                user_agent="Test",
                fecha_inicio=timezone.now(),
                ultima_actividad=timezone.now(),
                activa=True,
            )

        # Restablecer contraseña
        PasswordRecoveryService.restablecer_password_con_token(
            token=self.token_valido,
            nueva_password="NuevaPassword123!@#",
            ip_address=self.ip_address,
        )

        # Verificar que todas las sesiones están cerradas
        sesiones_activas = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).count()

        self.assertEqual(sesiones_activas, 0)

    def test_restablecer_password_debil(self):
        """No permitir restablecer con contraseña débil"""
        resultado = PasswordRecoveryService.restablecer_password_con_token(
            token=self.token_valido, nueva_password="debil", ip_address=self.ip_address
        )

        self.assertFalse(resultado["success"])

    def test_restablecer_password_token_invalido(self):
        """No permitir restablecer con token inválido"""
        resultado = PasswordRecoveryService.restablecer_password_con_token(
            token="token_invalido", nueva_password="Password123!@#", ip_address=self.ip_address
        )

        self.assertFalse(resultado["success"])


class EmailVerificationTest(PasswordRecoveryServiceTest):
    """Tests para verificación de email"""

    def test_solicitar_verificacion_email_exitoso(self):
        """Solicitar verificación de email"""
        resultado = PasswordRecoveryService.solicitar_verificacion_email(
            empleado=self.empleado, ip_address=self.ip_address
        )

        self.assertTrue(resultado["success"])

        # Verificar token en DB
        token_db = TokensRecuperacion.objects.filter(
            id_empleado=self.empleado, tipo="email_verification", usado=False
        ).first()

        self.assertIsNotNone(token_db)

    def test_solicitar_verificacion_expiracion_24_horas(self):
        """Token de verificación expira en 24 horas"""
        resultado = PasswordRecoveryService.solicitar_verificacion_email(
            empleado=self.empleado, ip_address=self.ip_address
        )

        token_db = TokensRecuperacion.objects.get(id_empleado=self.empleado, tipo="email_verification")

        tiempo_expiracion = token_db.fecha_expiracion - token_db.fecha_creacion

        # Debe ser aproximadamente 24 horas
        self.assertAlmostEqual(tiempo_expiracion.total_seconds(), 24 * 3600, delta=60)

    def test_verificar_email_exitoso(self):
        """Verificar email con token válido"""
        # Solicitar verificación
        resultado_solicitud = PasswordRecoveryService.solicitar_verificacion_email(
            empleado=self.empleado, ip_address=self.ip_address
        )

        token = resultado_solicitud["token"]

        # Verificar email
        resultado = PasswordRecoveryService.verificar_email(token=token, ip_address=self.ip_address)

        self.assertTrue(resultado["success"])

        # Verificar que el token se marcó como usado
        token_db = TokensRecuperacion.objects.get(token_hash=PasswordRecoveryService._hash_token(token))
        self.assertTrue(token_db.usado)

    def test_verificar_email_token_invalido(self):
        """Verificar email con token inválido"""
        resultado = PasswordRecoveryService.verificar_email(token="token_invalido", ip_address=self.ip_address)

        self.assertFalse(resultado["success"])


class CleanupExpiredTokensTest(PasswordRecoveryServiceTest):
    """Tests para limpieza de tokens expirados"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear tokens con diferentes estados
        # Token expirado hace 8 días (debe eliminarse)
        TokensRecuperacion.objects.create(
            id_empleado=self.empleado,
            tipo="password_recovery",
            token_hash="token_viejo",
            fecha_creacion=timezone.now() - timedelta(days=8),
            fecha_expiracion=timezone.now() - timedelta(days=8),
            usado=False,
        )

        # Token expirado hace 3 días (aún no se elimina)
        TokensRecuperacion.objects.create(
            id_empleado=self.empleado,
            tipo="password_recovery",
            token_hash="token_reciente",
            fecha_creacion=timezone.now() - timedelta(days=3),
            fecha_expiracion=timezone.now() - timedelta(days=3),
            usado=False,
        )

        # Token válido
        TokensRecuperacion.objects.create(
            id_empleado=self.empleado,
            tipo="password_recovery",
            token_hash="token_valido",
            fecha_creacion=timezone.now(),
            fecha_expiracion=timezone.now() + timedelta(hours=2),
            usado=False,
        )

    def test_limpiar_tokens_expirados(self):
        """Limpiar tokens expirados hace más de 7 días"""
        resultado = PasswordRecoveryService.limpiar_tokens_expirados()

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["tokens_eliminados"], 1)

        # Verificar que solo se eliminó el muy viejo
        self.assertFalse(TokensRecuperacion.objects.filter(token_hash="token_viejo").exists())
        self.assertTrue(TokensRecuperacion.objects.filter(token_hash="token_reciente").exists())
        self.assertTrue(TokensRecuperacion.objects.filter(token_hash="token_valido").exists())
