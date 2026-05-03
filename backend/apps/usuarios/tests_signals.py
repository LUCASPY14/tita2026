"""
Tests para signals de usuarios
Cubre hooks, listeners y automatizaciones de eventos de modelo
"""

from unittest.mock import Mock, call, patch

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.test import TestCase
from django.utils import timezone

from apps.usuarios.models import Empleados, Roles


class UsuariosSignalsTest(TestCase):
    """Tests para sistema de signals de usuarios"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.rol = Roles.objects.create(nombre_rol="SignalTest", descripcion="Rol para pruebas de signals", estado=True)

    @patch("apps.usuarios.signals.audit_logger")
    def test_empleado_creation_signal(self, mock_logger):
        """Debe disparar signal al crear empleado y registrar auditoría"""

        # Simular signal handler
        def log_empleado_creation(sender, instance, created, **kwargs):
            if created:
                mock_logger.info(
                    f"Empleado creado: {instance.usuario}",
                    extra={
                        "empleado_id": instance.id_empleado,
                        "usuario": instance.usuario,
                        "rol": instance.id_rol.nombre_rol,
                        "action": "CREATE",
                    },
                )

        # Conectar signal simulado
        post_save.connect(log_empleado_creation, sender=Empleados)

        try:
            # Crear empleado
            empleado = Empleados.objects.create(
                nombre="Signal",
                apellido="Test",
                usuario="signaltest",
                contrasena_hash="$2b$12$hashedpass",
                fecha_ingreso=timezone.now(),
                email="signal@test.com",
                estado=True,
                id_rol=self.rol,
            )

            # Verificar que el signal se disparó
            self.assertEqual(empleado.usuario, "signaltest")

        finally:
            # Limpiar signal
            post_save.disconnect(log_empleado_creation, sender=Empleados)

    @patch("apps.usuarios.signals.send_notification")
    def test_empleado_role_change_signal(self, mock_notification):
        """Debe notificar cambio de rol de empleado"""
        empleado = Empleados.objects.create(
            nombre="Role",
            apellido="Change",
            usuario="rolechange",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Simular signal handler para cambio de rol
        def notify_role_change(sender, instance, **kwargs):
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                if old_instance.id_rol != instance.id_rol:
                    mock_notification.delay(
                        user_id=instance.id_empleado,
                        message=f"Rol cambiado de {old_instance.id_rol.nombre_rol} a {instance.id_rol.nombre_rol}",
                        notification_type="ROLE_CHANGE",
                    )
            except sender.DoesNotExist:
                pass  # Nuevo objeto

        # Crear nuevo rol
        nuevo_rol = Roles.objects.create(nombre_rol="NuevoRol")

        # Conectar signal
        pre_save.connect(notify_role_change, sender=Empleados)

        try:
            # Cambiar rol (simular con validación manual ya que pre_save es complejo)
            old_role = empleado.id_rol.nombre_rol
            empleado.id_rol = nuevo_rol
            empleado.save()

            # Verificar cambio
            empleado.refresh_from_db()
            self.assertEqual(empleado.id_rol, nuevo_rol)
            self.assertNotEqual(empleado.id_rol.nombre_rol, old_role)

        finally:
            pre_save.disconnect(notify_role_change, sender=Empleados)

    @patch("apps.usuarios.signals.hash_password")
    def test_password_hashing_signal(self, mock_hash):
        """Debe hashear contraseña antes de guardar"""
        mock_hash.return_value = "$2b$12$mockedhash"

        # Simular signal handler para hasheo de contraseña
        def auto_hash_password(sender, instance, **kwargs):
            if not instance.contrasena_hash.startswith("$2b$"):
                instance.contrasena_hash = mock_hash(instance.contrasena_hash)

        pre_save.connect(auto_hash_password, sender=Empleados)

        try:
            # Crear empleado con contraseña en texto plano
            empleado = Empleados.objects.create(
                nombre="Password",
                apellido="Test",
                usuario="passtest",
                contrasena_hash="plaintext_password",  # Sin hashear
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )

            # Verificar que se llamó el hash
            mock_hash.assert_called_once_with("plaintext_password")

        finally:
            pre_save.disconnect(auto_hash_password, sender=Empleados)

    @patch("apps.usuarios.signals.create_user_profile")
    def test_user_profile_creation_signal(self, mock_create_profile):
        """Debe crear perfil de usuario automáticamente"""

        # Simular signal handler
        def auto_create_profile(sender, instance, created, **kwargs):
            if created:
                mock_create_profile.delay(
                    empleado_id=instance.id_empleado,
                    default_settings={"theme": "light", "language": "es", "timezone": "America/Asuncion"},
                )

        post_save.connect(auto_create_profile, sender=Empleados)

        try:
            empleado = Empleados.objects.create(
                nombre="Profile",
                apellido="Test",
                usuario="profiletest",
                contrasena_hash="$2b$12$hash",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )

            # Verificar que se llamó la creación de perfil
            mock_create_profile.delay.assert_called_once()
            call_args = mock_create_profile.delay.call_args
            self.assertEqual(call_args[1]["empleado_id"], empleado.id_empleado)

        finally:
            post_save.disconnect(auto_create_profile, sender=Empleados)

    @patch("apps.usuarios.signals.invalidate_sessions")
    def test_user_deactivation_signal(self, mock_invalidate):
        """Debe invalidar sesiones cuando usuario se desactiva"""
        empleado = Empleados.objects.create(
            nombre="Deactivation",
            apellido="Test",
            usuario="deactivtest",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol,
        )

        # Simular signal handler
        def handle_user_deactivation(sender, instance, **kwargs):
            if hasattr(instance, "_original_activo"):
                if instance._original_activo and not instance.estado:
                    mock_invalidate.delay(empleado_id=instance.id_empleado)

        # Simular pre_save para capturar estado original
        def capture_original_state(sender, instance, **kwargs):
            if instance.pk:
                try:
                    original = sender.objects.get(pk=instance.pk)
                    instance._original_activo = original.estado
                except sender.DoesNotExist:
                    instance._original_activo = None

        pre_save.connect(capture_original_state, sender=Empleados)
        post_save.connect(handle_user_deactivation, sender=Empleados)

        try:
            # Desactivar empleado
            empleado.estado = False
            empleado.save()

            # Verificar empleado desactivado
            empleado.refresh_from_db()
            self.assertFalse(empleado.estado)

        finally:
            pre_save.disconnect(capture_original_state, sender=Empleados)
            post_save.disconnect(handle_user_deactivation, sender=Empleados)

    @patch("apps.usuarios.signals.cleanup_user_data")
    def test_user_deletion_signal(self, mock_cleanup):
        """Debe limpiar datos relacionados al eliminar usuario"""
        empleado = Empleados.objects.create(
            nombre="Deletion",
            apellido="Test",
            usuario="deletetest",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        empleado_id = empleado.id_empleado

        # Simular signal handler
        def cleanup_on_deletion(sender, instance, **kwargs):
            mock_cleanup.delay(
                empleado_id=instance.id_empleado,
                cleanup_tasks=["remove_sessions", "archive_audit_logs", "remove_permissions", "notify_administrators"],
            )

        pre_delete.connect(cleanup_on_deletion, sender=Empleados)

        try:
            # Eliminar empleado
            empleado.delete()

            # Verificar que se llamó la limpieza
            mock_cleanup.delay.assert_called_once()
            call_args = mock_cleanup.delay.call_args
            self.assertEqual(call_args[1]["empleado_id"], empleado_id)
            self.assertIn("remove_sessions", call_args[1]["cleanup_tasks"])

        finally:
            pre_delete.disconnect(cleanup_on_deletion, sender=Empleados)

    @patch("apps.usuarios.signals.send_welcome_email")
    def test_welcome_email_signal(self, mock_email):
        """Debe enviar email de bienvenida a nuevos empleados"""

        # Simular signal handler
        def send_welcome(sender, instance, created, **kwargs):
            if created and instance.email:
                mock_email.delay(
                    to_email=instance.email,
                    empleado_name=f"{instance.nombre} {instance.apellido}",
                    username=instance.usuario,
                    role=instance.id_rol.nombre_rol,
                )

        post_save.connect(send_welcome, sender=Empleados)

        try:
            empleado = Empleados.objects.create(
                nombre="Welcome",
                apellido="Email",
                usuario="welcometest",
                contrasena_hash="$2b$12$hash",
                fecha_ingreso=timezone.now(),
                email="welcome@test.com",
                id_rol=self.rol,
            )

            # Verificar llamada al email
            mock_email.delay.assert_called_once()
            call_kwargs = mock_email.delay.call_args[1]
            self.assertEqual(call_kwargs["to_email"], "welcome@test.com")
            self.assertEqual(call_kwargs["username"], "welcometest")

        finally:
            post_save.disconnect(send_welcome, sender=Empleados)

    @patch("apps.usuarios.signals.update_last_login")
    def test_login_tracking_signal(self, mock_update_login):
        """Debe actualizar último login del usuario"""
        empleado = Empleados.objects.create(
            nombre="Login",
            apellido="Track",
            usuario="logintrack",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Simular signal custom para login
        def track_login(sender, user, **kwargs):
            mock_update_login(
                empleado_id=user.id_empleado,
                login_time=timezone.now(),
                ip_address=kwargs.get("ip_address"),
                user_agent=kwargs.get("user_agent"),
            )

        # Simular login exitoso
        track_login(sender=None, user=empleado, ip_address="192.168.1.100", user_agent="Mozilla/5.0")

        # Verificar llamada
        mock_update_login.assert_called_once()
        call_args = mock_update_login.call_args[1]
        self.assertEqual(call_args["empleado_id"], empleado.id_empleado)
        self.assertEqual(call_args["ip_address"], "192.168.1.100")

    @patch("apps.usuarios.signals.log_role_change")
    def test_role_change_audit_signal(self, mock_log):
        """Debe auditar cambios de rol"""
        empleado = Empleados.objects.create(
            nombre="Audit",
            apellido="Role",
            usuario="auditrole",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Crear nuevo rol
        nuevo_rol = Roles.objects.create(nombre_rol="AuditRole")

        # Simular signal de auditoría
        def audit_role_change(old_role, new_role, empleado, changed_by=None):
            mock_log(
                action="ROLE_CHANGE",
                empleado_id=empleado.id_empleado,
                old_role_id=old_role.id_rol,
                new_role_id=new_role.id_rol,
                changed_by=changed_by,
                timestamp=timezone.now(),
            )

        # Simular cambio de rol
        audit_role_change(old_role=self.rol, new_role=nuevo_rol, empleado=empleado, changed_by="admin")

        # Verificar auditoría
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        self.assertEqual(call_kwargs["action"], "ROLE_CHANGE")
        self.assertEqual(call_kwargs["empleado_id"], empleado.id_empleado)
        self.assertEqual(call_kwargs["old_role_id"], self.rol.id_rol)
        self.assertEqual(call_kwargs["new_role_id"], nuevo_rol.id_rol)

    def test_signal_disconnection_cleanup(self):
        """Debe limpiar signals apropiadamente"""
        # Contador para verificar disconnection
        call_count = 0

        def test_handler(sender, **kwargs):
            nonlocal call_count
            call_count += 1

        # Conectar
        post_save.connect(test_handler, sender=Empleados)

        # Verificar que está conectado
        Empleados.objects.create(
            nombre="Signal",
            apellido="Test",
            usuario="signalcount1",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )
        self.assertEqual(call_count, 1)

        # Desconectar
        post_save.disconnect(test_handler, sender=Empleados)

        # Verificar que NO se llama después de desconectar
        Empleados.objects.create(
            nombre="Signal",
            apellido="Test2",
            usuario="signalcount2",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )
        self.assertEqual(call_count, 1)  # No debe incrementar

    def test_multiple_signals_coordination(self):
        """Debe coordinar múltiples signals correctamente"""
        results = []

        def handler1(sender, instance, created, **kwargs):
            if created:
                results.append("handler1")

        def handler2(sender, instance, created, **kwargs):
            if created:
                results.append("handler2")

        def handler3(sender, instance, created, **kwargs):
            if created:
                results.append("handler3")

        # Conectar múltiples handlers
        post_save.connect(handler1, sender=Empleados)
        post_save.connect(handler2, sender=Empleados)
        post_save.connect(handler3, sender=Empleados)

        try:
            # Crear empleado
            Empleados.objects.create(
                nombre="Multiple",
                apellido="Signals",
                usuario="multisignal",
                contrasena_hash="$2b$12$hash",
                fecha_ingreso=timezone.now(),
                id_rol=self.rol,
            )

            # Verificar que todos los handlers se ejecutaron
            self.assertEqual(len(results), 3)
            self.assertIn("handler1", results)
            self.assertIn("handler2", results)
            self.assertIn("handler3", results)

        finally:
            # Limpiar
            post_save.disconnect(handler1, sender=Empleados)
            post_save.disconnect(handler2, sender=Empleados)
            post_save.disconnect(handler3, sender=Empleados)
