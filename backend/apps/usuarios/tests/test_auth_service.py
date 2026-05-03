"""
Tests para AuthenticationService
Cobertura completa de funcionalidades de autenticación y seguridad
"""

from datetime import timedelta

from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.usuarios.models import (
    AuditoriaOperaciones,
    BloqueosCuenta,
    Empleados,
    IntentosLogin,
    Roles,
    SesionesActivas,
)
from apps.usuarios.services.auth_service import AuthenticationService


class AuthenticationServiceTest(TransactionTestCase):
    """Tests para el servicio de autenticación"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear rol de prueba
        self.rol_test = Roles.objects.create(nombre_rol="Test Role", descripcion="Rol para testing", estado=True)

        # Crear empleado de prueba
        self.password = "TestPassword123!@#"
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="Usuario",
            usuario="testusuario",
            email="test@cantinatita.com",
            contrasena_hash=AuthenticationService._hash_password(self.password),
            id_rol=self.rol_test,
            fecha_ingreso=timezone.now(),
            estado=True,
        )

        self.ip_address = "127.0.0.1"
        self.user_agent = "Mozilla/5.0 Test Browser"

    def tearDown(self):
        """Limpieza después de cada test"""
        SesionesActivas.objects.all().delete()
        BloqueosCuenta.objects.all().delete()
        IntentosLogin.objects.all().delete()
        AuditoriaOperaciones.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


class PasswordHashingTest(AuthenticationServiceTest):
    """Tests para hashing y verificación de contraseñas"""

    def test_hash_password_genera_hash_bcrypt(self):
        """Verificar que se genera un hash bcrypt válido"""
        password = "MiPassword123!@#"
        hash_generado = AuthenticationService._hash_password(password)

        # Verificar que es un hash bcrypt (comienza con $2b$)
        self.assertTrue(hash_generado.startswith("$2b$"))
        # Verificar longitud típica de bcrypt
        self.assertEqual(len(hash_generado), 60)

    def test_hash_password_es_determinista(self):
        """Verificar que el mismo password genera hashes diferentes (salt)"""
        password = "MiPassword123!@#"
        hash1 = AuthenticationService._hash_password(password)
        hash2 = AuthenticationService._hash_password(password)

        # Los hashes deben ser diferentes debido al salt
        self.assertNotEqual(hash1, hash2)

    def test_verify_password_correcto(self):
        """Verificar que la contraseña correcta se valida"""
        password = "MiPassword123!@#"
        hash_pw = AuthenticationService._hash_password(password)

        resultado = AuthenticationService._verify_password(password, hash_pw)
        self.assertTrue(resultado)

    def test_verify_password_incorrecto(self):
        """Verificar que una contraseña incorrecta no se valida"""
        password = "MiPassword123!@#"
        password_incorrecta = "OtraPassword456$%^"
        hash_pw = AuthenticationService._hash_password(password)

        resultado = AuthenticationService._verify_password(password_incorrecta, hash_pw)
        self.assertFalse(resultado)

    def test_verify_password_case_sensitive(self):
        """Verificar que la validación es sensible a mayúsculas"""
        password = "MiPassword123!@#"
        password_diferente = "mipassword123!@#"
        hash_pw = AuthenticationService._hash_password(password)

        resultado = AuthenticationService._verify_password(password_diferente, hash_pw)
        self.assertFalse(resultado)


class PasswordStrengthTest(AuthenticationServiceTest):
    """Tests para validación de fortaleza de contraseña"""

    def test_password_cumple_requisitos(self):
        """Password que cumple todos los requisitos"""
        passwords_validas = [
            "Password123!",
            "Test1234@abc",
            "Secure#Pass1",
            "MyP@ssw0rd",
        ]

        for password in passwords_validas:
            valido, mensaje = AuthenticationService.validar_fortaleza_password(password)
            self.assertTrue(valido, f"Password '{password}' debería ser válida: {mensaje}")

    def test_password_muy_corta(self):
        """Password menor a 8 caracteres"""
        password = "Pass1!"
        valido, mensaje = AuthenticationService.validar_fortaleza_password(password)

        self.assertFalse(valido)
        self.assertIn("8 caracteres", mensaje)

    def test_password_sin_mayuscula(self):
        """Password sin letra mayúscula"""
        password = "password123!"
        valido, mensaje = AuthenticationService.validar_fortaleza_password(password)

        self.assertFalse(valido)
        self.assertIn("mayúscula", mensaje)

    def test_password_sin_minuscula(self):
        """Password sin letra minúscula"""
        password = "PASSWORD123!"
        valido, mensaje = AuthenticationService.validar_fortaleza_password(password)

        self.assertFalse(valido)
        self.assertIn("minúscula", mensaje)

    def test_password_sin_numero(self):
        """Password sin número"""
        password = "Password!@#"
        valido, mensaje = AuthenticationService.validar_fortaleza_password(password)

        self.assertFalse(valido)
        self.assertIn("número", mensaje)

    def test_password_sin_caracter_especial(self):
        """Password sin carácter especial"""
        password = "Password123"
        valido, mensaje = AuthenticationService.validar_fortaleza_password(password)

        self.assertFalse(valido)
        self.assertIn("especial", mensaje)


class LoginTest(AuthenticationServiceTest):
    """Tests para funcionalidad de login"""

    def test_login_exitoso(self):
        """Login con credenciales correctas"""
        resultado = AuthenticationService.login(
            usuario="testusuario",
            password=self.password,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertTrue(resultado["success"])
        self.assertIn("access", resultado)
        self.assertIn("refresh", resultado)
        self.assertIn("empleado", resultado)
        self.assertEqual(resultado["empleado"]["usuario"], "testusuario")

        # Verificar que se creó una sesión activa
        self.assertTrue(SesionesActivas.objects.filter(id_empleado=self.empleado).exists())

    def test_login_usuario_inexistente(self):
        """Login con usuario que no existe"""
        resultado = AuthenticationService.login(
            usuario="noexiste",
            password="cualquierpassword",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("Credenciales", resultado["mensaje"])

    def test_login_password_incorrecta(self):
        """Login con password incorrecta"""
        resultado = AuthenticationService.login(
            usuario="testusuario",
            password="PasswordIncorrecta123!",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("Credenciales", resultado["mensaje"])

        # Verificar que se registró el intento fallido
        self.assertTrue(IntentosLogin.objects.filter(id_empleado=self.empleado, exitoso=False).exists())

    def test_login_empleado_inactivo(self):
        """Login con empleado inactivo"""
        self.empleado.estado = False
        self.empleado.save()

        resultado = AuthenticationService.login(
            usuario="testusuario",
            password=self.password,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("inactiva", resultado["mensaje"])

    def test_login_cuenta_bloqueada(self):
        """Login con cuenta bloqueada"""
        # Crear bloqueo estado
        BloqueosCuenta.objects.create(
            id_empleado=self.empleado,
            fecha_bloqueo=timezone.now(),
            fecha_desbloqueo=timezone.now() + timedelta(minutes=30),
            motivo="Test bloqueo",
            estado=True,
        )

        resultado = AuthenticationService.login(
            usuario="testusuario",
            password=self.password,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("bloqueada", resultado["mensaje"])

    def test_bloqueo_automatico_tras_5_intentos(self):
        """Cuenta se bloquea automáticamente tras 5 intentos fallidos"""
        # Realizar 5 intentos fallidos
        for i in range(5):
            AuthenticationService.login(
                usuario="testusuario",
                password="PasswordIncorrecta123!",
                ip_address=self.ip_address,
                user_agent=self.user_agent,
            )

        # Verificar que la cuenta está bloqueada
        bloqueo = BloqueosCuenta.objects.filter(id_empleado=self.empleado, estado=True).first()

        self.assertIsNotNone(bloqueo)
        self.assertIn("intentos fallidos", bloqueo.motivo.lower())

        # Intentar login con password correcta (debe fallar por bloqueo)
        resultado = AuthenticationService.login(
            usuario="testusuario",
            password=self.password,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("bloqueada", resultado["mensaje"])


class LogoutTest(AuthenticationServiceTest):
    """Tests para funcionalidad de logout"""

    def test_logout_exitoso(self):
        """Logout cierra la sesión correctamente"""
        # Primero hacer login
        login_result = AuthenticationService.login(
            usuario="testusuario",
            password=self.password,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # Obtener session_key
        sesion = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).first()

        # Hacer logout
        resultado = AuthenticationService.logout(
            empleado=self.empleado, session_key=sesion.session_key, ip_address=self.ip_address
        )

        self.assertTrue(resultado["success"])

        # Verificar que la sesión se marcó como inactiva
        sesion.refresh_from_db()
        self.assertFalse(sesion.activa)
        self.assertIsNotNone(sesion.fecha_cierre)

    def test_logout_sin_sesion(self):
        """Logout cuando no hay sesión activa"""
        resultado = AuthenticationService.logout(
            empleado=self.empleado, session_key="session_inexistente", ip_address=self.ip_address
        )

        self.assertFalse(resultado["success"])


class ChangePasswordTest(AuthenticationServiceTest):
    """Tests para cambio de contraseña"""

    def test_cambiar_password_exitoso(self):
        """Cambio de contraseña con password actual correcta"""
        nueva_password = "NuevaPassword123!@#"

        resultado = AuthenticationService.cambiar_password(
            empleado=self.empleado,
            password_actual=self.password,
            password_nueva=nueva_password,
            ip_address=self.ip_address,
        )

        self.assertTrue(resultado["success"])

        # Verificar que la nueva password funciona
        self.empleado.refresh_from_db()
        self.assertTrue(AuthenticationService._verify_password(nueva_password, self.empleado.contrasena_hash))

    def test_cambiar_password_actual_incorrecta(self):
        """Cambio de contraseña con password actual incorrecta"""
        resultado = AuthenticationService.cambiar_password(
            empleado=self.empleado,
            password_actual="PasswordIncorrecta123!",
            password_nueva="NuevaPassword123!@#",
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("actual", resultado["mensaje"].lower())

    def test_cambiar_password_nueva_debil(self):
        """Cambio de contraseña con nueva password débil"""
        resultado = AuthenticationService.cambiar_password(
            empleado=self.empleado,
            password_actual=self.password,
            password_nueva="debil",
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])

    def test_cambiar_password_invalida_sesiones(self):
        """Cambio de contraseña invalida todas las sesiones activas"""
        # Crear múltiples sesiones
        for i in range(3):
            SesionesActivas.objects.create(
                id_empleado=self.empleado,
                session_key=f"session_{i}",
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                fecha_inicio=timezone.now(),
                ultima_actividad=timezone.now(),
                activa=True,
            )

        # Cambiar password
        AuthenticationService.cambiar_password(
            empleado=self.empleado,
            password_actual=self.password,
            password_nueva="NuevaPassword123!@#",
            ip_address=self.ip_address,
        )

        # Verificar que todas las sesiones están inactivas
        sesiones_activas = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).count()

        self.assertEqual(sesiones_activas, 0)


class CreateEmpleadoTest(AuthenticationServiceTest):
    """Tests para creación de empleados"""

    def test_crear_empleado_exitoso(self):
        """Creación exitosa de un nuevo empleado"""
        resultado = AuthenticationService.crear_empleado(
            nombre="Nuevo",
            apellido="Empleado",
            usuario="nuevoempleado",
            email="nuevo@cantinatita.com",
            password="Password123!@#",
            id_rol=self.rol_test.id_rol,
            creado_por=self.empleado,
            ip_address=self.ip_address,
        )

        self.assertTrue(resultado["success"])
        self.assertIn("empleado", resultado)
        self.assertEqual(resultado["empleado"].usuario, "nuevoempleado")

        # Verificar que se creó en la base de datos
        self.assertTrue(Empleados.objects.filter(usuario="nuevoempleado").exists())

    def test_crear_empleado_usuario_duplicado(self):
        """No permite crear empleado con usuario duplicado"""
        resultado = AuthenticationService.crear_empleado(
            nombre="Otro",
            apellido="Usuario",
            usuario="testusuario",  # Usuario que ya existe
            email="otro@cantinatita.com",
            password="Password123!@#",
            id_rol=self.rol_test.id_rol,
            creado_por=self.empleado,
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("existe", resultado["mensaje"].lower())

    def test_crear_empleado_email_duplicado(self):
        """No permite crear empleado con email duplicado"""
        resultado = AuthenticationService.crear_empleado(
            nombre="Otro",
            apellido="Usuario",
            usuario="otrousuario",
            email="test@cantinatita.com",  # Email que ya existe
            password="Password123!@#",
            id_rol=self.rol_test.id_rol,
            creado_por=self.empleado,
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])
        self.assertIn("email", resultado["mensaje"].lower())

    def test_crear_empleado_password_debil(self):
        """No permite crear empleado con password débil"""
        resultado = AuthenticationService.crear_empleado(
            nombre="Nuevo",
            apellido="Empleado",
            usuario="nuevoempleado",
            email="nuevo@cantinatita.com",
            password="debil",
            id_rol=self.rol_test.id_rol,
            creado_por=self.empleado,
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])

    def test_crear_empleado_rol_inexistente(self):
        """No permite crear empleado con rol inexistente"""
        resultado = AuthenticationService.crear_empleado(
            nombre="Nuevo",
            apellido="Empleado",
            usuario="nuevoempleado",
            email="nuevo@cantinatita.com",
            password="Password123!@#",
            id_rol=99999,  # ID que no existe
            creado_por=self.empleado,
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])


class AccountLockingTest(AuthenticationServiceTest):
    """Tests para sistema de bloqueo de cuentas"""

    def test_verificar_cuenta_no_bloqueada(self):
        """Cuenta sin bloqueos activos"""
        bloqueada, mensaje = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)

        self.assertFalse(bloqueada)
        self.assertIsNone(mensaje)

    def test_verificar_cuenta_bloqueada_activa(self):
        """Cuenta con bloqueo estado y vigente"""
        BloqueosCuenta.objects.create(
            id_empleado=self.empleado,
            fecha_bloqueo=timezone.now(),
            fecha_desbloqueo=timezone.now() + timedelta(minutes=30),
            motivo="Test",
            estado=True,
        )

        bloqueada, mensaje = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)

        self.assertTrue(bloqueada)
        self.assertIn("bloqueada", mensaje.lower())

    def test_verificar_cuenta_bloqueo_expirado(self):
        """Cuenta con bloqueo expirado se desbloquea automáticamente"""
        # Crear bloqueo expirado (fecha_desbloqueo en el pasado)
        BloqueosCuenta.objects.create(
            id_empleado=self.empleado,
            fecha_bloqueo=timezone.now() - timedelta(hours=1),
            fecha_desbloqueo=timezone.now() - timedelta(minutes=1),
            motivo="Test",
            estado=True,
        )

        bloqueada, mensaje = AuthenticationService.verificar_cuenta_bloqueada(self.empleado)

        self.assertFalse(bloqueada)

        # Verificar que el bloqueo se marcó como inactivo
        bloqueo = BloqueosCuenta.objects.get(id_empleado=self.empleado)
        self.assertFalse(bloqueo.estado)
