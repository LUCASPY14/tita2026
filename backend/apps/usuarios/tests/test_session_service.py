"""
Tests para SessionService
Cobertura completa de gestión de sesiones y detección de patrones
"""

from django.test import TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from apps.usuarios.services.session_service import SessionService
from apps.usuarios.models import Empleados, Roles, SesionesActivas, PatronesAcceso


class SessionServiceTest(TransactionTestCase):
    """Tests para el servicio de sesiones"""

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

        self.ip_address = "192.168.1.100"
        self.user_agent = "Mozilla/5.0 Test Browser"

    def tearDown(self):
        """Limpieza después de cada test"""
        PatronesAcceso.objects.all().delete()
        SesionesActivas.objects.all().delete()
        Empleados.objects.all().delete()
        Roles.objects.all().delete()


class CreateSessionTest(SessionServiceTest):
    """Tests para creación de sesiones"""

    def test_crear_sesion_exitosa(self):
        """Crear una sesión nueva"""
        resultado = SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="test_session_key_1",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertTrue(resultado["success"])
        self.assertIn("sesion", resultado)

        # Verificar en DB
        sesion = SesionesActivas.objects.filter(id_empleado=self.empleado, session_key="test_session_key_1").first()

        self.assertIsNotNone(sesion)
        self.assertTrue(sesion.activa)

    def test_crear_sesion_limite_maximo(self):
        """No permitir más de 3 sesiones simultáneas"""
        # Crear 3 sesiones
        for i in range(3):
            SessionService.crear_sesion(
                empleado=self.empleado,
                session_key=f"session_{i}",
                ip_address=self.ip_address,
                user_agent=self.user_agent,
            )

        # Intentar crear una cuarta (debe cerrar la más antigua)
        resultado = SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="session_nueva",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        self.assertTrue(resultado["success"])

        # Verificar que solo hay 3 sesiones activas
        sesiones_activas = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).count()

        self.assertEqual(sesiones_activas, 3)

        # Verificar que la primera sesión fue cerrada
        primera_sesion = SesionesActivas.objects.get(id_empleado=self.empleado, session_key="session_0")
        self.assertFalse(primera_sesion.activa)

    def test_crear_sesion_analiza_patron(self):
        """Crear sesión analiza patrón de acceso"""
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="test_session",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

        # Verificar que se creó un patrón
        patron = PatronesAcceso.objects.filter(id_empleado=self.empleado).first()

        self.assertIsNotNone(patron)


class RenewSessionTest(SessionServiceTest):
    """Tests para renovación de sesiones"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear sesión inicial
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="old_session",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

    def test_renovar_sesion_exitosa(self):
        """Renovar sesión correctamente"""
        resultado = SessionService.renovar_sesion(
            empleado=self.empleado,
            session_key_actual="old_session",
            nuevo_session_key="new_session",
            ip_address=self.ip_address,
        )

        self.assertTrue(resultado["success"])

        # Verificar que la sesión antigua está inactiva
        sesion_antigua = SesionesActivas.objects.get(session_key="old_session")
        self.assertFalse(sesion_antigua.activa)

        # Verificar que existe la nueva sesión
        sesion_nueva = SesionesActivas.objects.filter(session_key="new_session", activa=True).first()
        self.assertIsNotNone(sesion_nueva)

    def test_renovar_sesion_muy_reciente(self):
        """No permitir renovación antes de 5 minutos"""
        # Primera renovación
        resultado1 = SessionService.renovar_sesion(
            empleado=self.empleado,
            session_key_actual="old_session",
            nuevo_session_key="new_session_1",
            ip_address=self.ip_address,
        )
        self.assertTrue(resultado1["success"])

        # Intentar renovar inmediatamente (debe fallar)
        resultado2 = SessionService.renovar_sesion(
            empleado=self.empleado,
            session_key_actual="new_session_1",
            nuevo_session_key="new_session_2",
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado2["success"])
        self.assertIn("minutos", resultado2["mensaje"].lower())

    def test_renovar_sesion_inexistente(self):
        """Intentar renovar sesión que no existe"""
        resultado = SessionService.renovar_sesion(
            empleado=self.empleado,
            session_key_actual="sesion_inexistente",
            nuevo_session_key="nueva",
            ip_address=self.ip_address,
        )

        self.assertFalse(resultado["success"])


class UpdateActivityTest(SessionServiceTest):
    """Tests para actualización de actividad"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear sesión inicial
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="test_session",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

    def test_actualizar_actividad_exitosa(self):
        """Actualizar última actividad de sesión"""
        # Esperar un momento
        import time

        time.sleep(1)

        resultado = SessionService.actualizar_actividad_sesion(empleado=self.empleado, session_key="test_session")

        self.assertTrue(resultado["success"])

        # Verificar que ultima_actividad se actualizó
        sesion = SesionesActivas.objects.get(session_key="test_session")
        tiempo_desde_actualizacion = timezone.now() - sesion.ultima_actividad

        # Debe ser muy reciente (menos de 5 segundos)
        self.assertLess(tiempo_desde_actualizacion.total_seconds(), 5)

    def test_actualizar_actividad_sesion_inexistente(self):
        """Actualizar sesión que no existe"""
        resultado = SessionService.actualizar_actividad_sesion(empleado=self.empleado, session_key="sesion_inexistente")

        self.assertFalse(resultado["success"])


class CloseSessionTest(SessionServiceTest):
    """Tests para cierre de sesiones"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear sesión
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="test_session",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )

    def test_cerrar_sesion_exitosa(self):
        """Cerrar sesión correctamente"""
        resultado = SessionService.cerrar_sesion(
            empleado=self.empleado, session_key="test_session", ip_address=self.ip_address
        )

        self.assertTrue(resultado["success"])

        # Verificar que está inactiva
        sesion = SesionesActivas.objects.get(session_key="test_session")
        self.assertFalse(sesion.activa)
        self.assertIsNotNone(sesion.fecha_cierre)

    def test_cerrar_sesion_inexistente(self):
        """Intentar cerrar sesión que no existe"""
        resultado = SessionService.cerrar_sesion(
            empleado=self.empleado, session_key="sesion_inexistente", ip_address=self.ip_address
        )

        self.assertFalse(resultado["success"])


class CloseAllSessionsTest(SessionServiceTest):
    """Tests para cierre de todas las sesiones"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear múltiples sesiones
        for i in range(3):
            SessionService.crear_sesion(
                empleado=self.empleado,
                session_key=f"session_{i}",
                ip_address=self.ip_address,
                user_agent=self.user_agent,
            )

    def test_cerrar_todas_sesiones(self):
        """Cerrar todas las sesiones del empleado"""
        resultado = SessionService.cerrar_todas_sesiones(empleado=self.empleado, ip_address=self.ip_address)

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["sesiones_cerradas"], 3)

        # Verificar que todas están inactivas
        sesiones_activas = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).count()

        self.assertEqual(sesiones_activas, 0)

    def test_cerrar_todas_excepto_actual(self):
        """Cerrar todas las sesiones excepto la actual"""
        resultado = SessionService.cerrar_todas_sesiones(
            empleado=self.empleado, ip_address=self.ip_address, excepto_session_key="session_1"
        )

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["sesiones_cerradas"], 2)

        # Verificar que solo queda una activa
        sesiones_activas = SesionesActivas.objects.filter(id_empleado=self.empleado, activa=True).count()

        self.assertEqual(sesiones_activas, 1)

        # Verificar que es la correcta
        sesion_activa = SesionesActivas.objects.get(id_empleado=self.empleado, activa=True)
        self.assertEqual(sesion_activa.session_key, "session_1")


class ListActiveSessionsTest(SessionServiceTest):
    """Tests para listar sesiones activas"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear sesiones activas e inactivas
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="active_1",
            ip_address="192.168.1.100",
            user_agent="Browser 1",
        )
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="active_2",
            ip_address="192.168.1.101",
            user_agent="Browser 2",
        )

        # Crear sesión y cerrarla
        SessionService.crear_sesion(
            empleado=self.empleado,
            session_key="inactive",
            ip_address="192.168.1.102",
            user_agent="Browser 3",
        )
        SessionService.cerrar_sesion(empleado=self.empleado, session_key="inactive", ip_address="192.168.1.102")

    def test_listar_sesiones_activas(self):
        """Listar solo sesiones activas"""
        sesiones = SessionService.listar_sesiones_activas(empleado=self.empleado)

        self.assertEqual(len(sesiones), 2)

        # Verificar que contienen información esperada
        for sesion in sesiones:
            self.assertIn("ip_address", sesion)
            self.assertIn("user_agent", sesion)
            self.assertIn("fecha_inicio", sesion)
            self.assertIn("ultima_actividad", sesion)
            self.assertIn("tiempo_inactivo_minutos", sesion)


class DetectUnusualAccessTest(SessionServiceTest):
    """Tests para detección de accesos inusuales"""

    def test_detectar_nueva_ip_es_inusual(self):
        """Nueva IP se detecta como inusual"""
        # Crear patrón de acceso desde IP habitual
        PatronesAcceso.objects.create(
            id_empleado=self.empleado,
            ip_habitual="192.168.1.100",
            horario_habitual="09:00:00",
            dias_semana_habituales="1,2,3,4,5",
            es_habitual=True,
        )

        # Intentar acceso desde IP nueva
        resultado = SessionService.detectar_acceso_inusual(
            empleado=self.empleado, ip_address="10.0.0.1"  # IP diferente
        )

        self.assertTrue(resultado["es_inusual"])
        self.assertIn("Nueva IP", resultado["razones"])
        self.assertIn(resultado["nivel_riesgo"], ["bajo", "medio", "alto"])

    def test_detectar_ip_habitual_no_es_inusual(self):
        """IP habitual no se detecta como inusual"""
        # Crear patrón de acceso
        PatronesAcceso.objects.create(
            id_empleado=self.empleado,
            ip_habitual="192.168.1.100",
            horario_habitual="09:00:00",
            dias_semana_habituales="1,2,3,4,5",
            es_habitual=True,
        )

        # Acceso desde IP habitual
        resultado = SessionService.detectar_acceso_inusual(empleado=self.empleado, ip_address="192.168.1.100")

        self.assertFalse(resultado["es_inusual"])

    def test_detectar_primer_acceso_no_es_inusual(self):
        """Primer acceso sin patrón no es inusual"""
        resultado = SessionService.detectar_acceso_inusual(empleado=self.empleado, ip_address="192.168.1.100")

        self.assertFalse(resultado["es_inusual"])


class CleanupExpiredSessionsTest(SessionServiceTest):
    """Tests para limpieza de sesiones expiradas"""

    def setUp(self):
        """Configuración adicional"""
        super().setUp()

        # Crear sesiones con diferentes estados
        # Sesión expirada (>24 horas)
        sesion_expirada = SesionesActivas.objects.create(
            id_empleado=self.empleado,
            session_key="expired",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            fecha_inicio=timezone.now() - timedelta(hours=25),
            ultima_actividad=timezone.now() - timedelta(hours=25),
            activa=True,
        )

        # Sesión inactiva (>30 minutos sin actividad)
        sesion_inactiva = SesionesActivas.objects.create(
            id_empleado=self.empleado,
            session_key="inactive",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            fecha_inicio=timezone.now() - timedelta(hours=1),
            ultima_actividad=timezone.now() - timedelta(minutes=35),
            activa=True,
        )

        # Sesión activa reciente
        sesion_activa = SesionesActivas.objects.create(
            id_empleado=self.empleado,
            session_key="active",
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            fecha_inicio=timezone.now() - timedelta(minutes=10),
            ultima_actividad=timezone.now() - timedelta(minutes=5),
            activa=True,
        )

    def test_limpiar_sesiones_expiradas(self):
        """Limpia sesiones expiradas e inactivas"""
        resultado = SessionService.limpiar_sesiones_expiradas()

        self.assertTrue(resultado["success"])
        self.assertGreater(resultado["sesiones_cerradas"], 0)

        # Verificar que las expiradas están cerradas
        sesion_expirada = SesionesActivas.objects.get(session_key="expired")
        self.assertFalse(sesion_expirada.activa)

        sesion_inactiva = SesionesActivas.objects.get(session_key="inactive")
        self.assertFalse(sesion_inactiva.activa)

        # Verificar que la activa sigue activa
        sesion_activa = SesionesActivas.objects.get(session_key="active")
        self.assertTrue(sesion_activa.activa)
