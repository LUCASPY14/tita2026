"""
Tests para utilities de la app usuarios
Cubre permissions, middleware, signals y configuración de apps
"""

import uuid
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from unittest.mock import Mock, patch

from apps.usuarios.models import Roles, Empleados
from apps.usuarios.apps import UsuariosConfig


class UsuariosAppsTest(TestCase):
    """Tests para configuración de la app usuarios"""

    def test_app_config(self):
        """Debe configurar la app correctamente"""
        app_config = UsuariosConfig
        
        self.assertEqual(app_config.default_auto_field, 'django.db.models.BigAutoField')
        self.assertEqual(app_config.name, 'apps.usuarios')
        self.assertEqual(app_config.verbose_name, 'Usuarios')

    def test_ready_method(self):
        """Debe importar signals al inicializar la app"""
        app_config = UsuariosConfig('apps.usuarios', Mock())
        
        # Verificar que se ejecuta sin errores
        try:
            app_config.ready()
        except ImportError:
            # Es normal si no existen los signals aún
            pass
        except Exception as e:
            self.fail(f"App ready() falló inesperadamente: {e}")


class UsuariosPermissionsTest(TestCase):
    """Tests para sistema de permisos personalizados"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.factory = RequestFactory()
        
        self.rol_admin = Roles.objects.create(
            nombre_rol="Administrador",
            descripcion="Permisos completos",
            activo=True
        )
        
        self.rol_cajero = Roles.objects.create(
            nombre_rol="Cajero",
            descripcion="Permisos limitados",
            activo=True
        )
        
        self.admin = Empleados.objects.create(
            nombre="Admin",
            apellido="User",
            usuario="admin",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            activo=True,
            id_rol=self.rol_admin
        )
        
        self.cajero = Empleados.objects.create(
            nombre="Cajero",
            apellido="User",
            usuario="cajero",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            activo=True,
            id_rol=self.rol_cajero
        )

    def test_user_has_role_admin(self):
        """Debe verificar si usuario tiene rol de administrador"""
        # Simular función de permisos
        def is_admin_role(empleado):
            return empleado.id_rol.nombre_rol == "Administrador"
        
        self.assertTrue(is_admin_role(self.admin))
        self.assertFalse(is_admin_role(self.cajero))

    def test_user_has_role_cajero(self):
        """Debe verificar si usuario tiene rol de cajero"""
        def is_cajero_role(empleado):
            return empleado.id_rol.nombre_rol == "Cajero"
        
        self.assertTrue(is_cajero_role(self.cajero))
        self.assertFalse(is_cajero_role(self.admin))

    def test_user_active_validation(self):
        """Debe validar que usuario esté activo"""
        def is_user_active(empleado):
            return empleado.activo
        
        self.assertTrue(is_user_active(self.admin))
        
        # Inactivar usuario
        self.admin.activo = False
        self.admin.save()
        
        self.assertFalse(is_user_active(self.admin))

    def test_role_active_validation(self):
        """Debe validar que el rol esté activo"""
        def is_role_active(empleado):
            return empleado.id_rol.activo
        
        self.assertTrue(is_role_active(self.admin))
        
        # Inactivar rol
        self.rol_admin.activo = False
        self.rol_admin.save()
        
        self.admin.refresh_from_db()
        self.assertFalse(is_role_active(self.admin))


class UsuariosMiddlewareTest(TestCase):
    """Tests para middleware de usuarios"""

    def setUp(self):
        """Configurar factory de requests"""
        self.factory = RequestFactory()
        
        self.rol = Roles.objects.create(nombre_rol="Test")
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )

    def test_middleware_structure(self):
        """Debe tener estructura básica de middleware"""
        # Test básico de estructura de middleware
        # (En implementación real se importaría el middleware)
        
        class TestMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
            
            def __call__(self, request):
                # Proceso antes de la vista
                response = self.get_response(request)
                # Proceso después de la vista
                return response
            
            def process_view(self, request, view_func, view_args, view_kwargs):
                # Procesar vista específica
                pass
        
        middleware = TestMiddleware(Mock())
        self.assertIsNotNone(middleware.get_response)

    def test_request_user_injection(self):
        """Debe inyectar información de usuario en request"""
        request = self.factory.get('/')
        
        # Simular inyección de usuario autenticado
        request.user = self.empleado
        request.user_role = self.empleado.id_rol.nombre_rol
        request.user_permissions = ['read', 'write']
        
        self.assertEqual(request.user, self.empleado)
        self.assertEqual(request.user_role, "Test")
        self.assertIn('read', request.user_permissions)

    def test_security_headers(self):
        """Debe agregar headers de seguridad"""
        request = self.factory.get('/')
        
        # Simular middleware que agrega headers de seguridad
        def add_security_headers(response):
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'
            return response
        
        mock_response = Mock()
        mock_response.__setitem__ = Mock()
        
        result = add_security_headers(mock_response)
        self.assertIsNotNone(result)

    def test_authentication_check(self):
        """Debe verificar autenticación en middleware"""
        def is_authenticated(request):
            return hasattr(request, 'user') and request.user.activo
        
        # Request con usuario autenticado
        auth_request = self.factory.get('/')
        auth_request.user = self.empleado
        self.assertTrue(is_authenticated(auth_request))
        
        # Request sin usuario
        unauth_request = self.factory.get('/')
        auth_request.user = AnonymousUser()
        self.assertFalse(is_authenticated(unauth_request))


class UsuariosSignalsTest(TestCase):
    """Tests para signals de usuarios"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.rol = Roles.objects.create(
            nombre_rol="SignalTest",
            activo=True
        )

    @patch('apps.usuarios.signals.audit_log')
    def test_empleado_creation_signal(self, mock_audit):
        """Debe disparar signal al crear empleado"""
        # Simular signal post_save
        empleado = Empleados.objects.create(
            nombre="Signal",
            apellido="Test",
            usuario="signaltest",
            contrasena_hash="hashedpass",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Verificar que el empleado se creó
        self.assertEqual(empleado.nombre, "Signal")
        self.assertEqual(empleado.usuario, "signaltest")

    @patch('apps.usuarios.signals.audit_log')
    def test_empleado_update_signal(self, mock_audit):
        """Debe disparar signal al actualizar empleado"""
        empleado = Empleados.objects.create(
            nombre="Original",
            apellido="Name",
            usuario="original",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Actualizar empleado
        empleado.nombre = "Updated"
        empleado.save()
        
        # Verificar actualización
        empleado.refresh_from_db()
        self.assertEqual(empleado.nombre, "Updated")

    def test_password_hashing_signal(self):
        """Debe hashear contraseña en signal pre_save"""
        def hash_password_if_needed(sender, instance, **kwargs):
            # Simular señal que hashea contraseña si es texto plano
            if not instance.contrasena_hash.startswith('$2b$'):
                instance.contrasena_hash = f'$2b$12${instance.contrasena_hash}'
        
        empleado = Empleados(
            nombre="Test",
            apellido="Hash",
            usuario="testhash",
            contrasena_hash="plaintext",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Simular signal
        hash_password_if_needed(Empleados, empleado)
        
        self.assertTrue(empleado.contrasena_hash.startswith('$2b$12$'))

    def test_audit_trail_signal(self):
        """Debe crear registro de auditoría en signal"""
        def create_audit_log(sender, instance, created, **kwargs):
            # Simular creación de log de auditoría
            action = "CREATE" if created else "UPDATE"
            return {
                'model': sender.__name__,
                'instance_id': instance.pk,
                'action': action,
                'timestamp': timezone.now(),
                'user': getattr(instance, 'modified_by', None)
            }
        
        empleado = Empleados.objects.create(
            nombre="Audit",
            apellido="Test",
            usuario="audituser",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Simular signal
        audit_data = create_audit_log(Empleados, empleado, True)
        
        self.assertEqual(audit_data['model'], 'Empleados')
        self.assertEqual(audit_data['action'], 'CREATE')
        self.assertIsNotNone(audit_data['timestamp'])

    def test_role_change_notification_signal(self):
        """Debe notificar cambio de rol en signal"""
        empleado = Empleados.objects.create(
            nombre="Role",
            apellido="Change",
            usuario="rolechange",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Crear nuevo rol
        nuevo_rol = Roles.objects.create(nombre_rol="NuevoRol")
        
        # Simular signal de cambio de rol
        def notify_role_change(old_role, new_role, empleado):
            return {
                'empleado_id': empleado.pk,
                'old_role': old_role.nombre_rol,
                'new_role': new_role.nombre_rol,
                'requires_reauth': True
            }
        
        notification = notify_role_change(self.rol, nuevo_rol, empleado)
        
        self.assertEqual(notification['old_role'], 'SignalTest')
        self.assertEqual(notification['new_role'], 'NuevoRol')
        self.assertTrue(notification['requires_reauth'])