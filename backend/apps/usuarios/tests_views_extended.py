"""
Tests extendidos para apps/usuarios/views.py
Cubre: AuthViewSet, TwoFactorViewSet, SesionesViewSet, PasswordRecoveryViewSet,
       PermisosViewSet, RolesViewSet.permisos/destroy, EmpleadosViewSet.create/cambiar_password,
       AuditoriaOperacionesViewSet custom actions
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from apps.usuarios.models import Roles, Empleados, AuditoriaOperaciones
from apps.usuarios.permissions import Permisos
from apps.usuarios.views import (
    AuthViewSet,
    TwoFactorViewSet,
    SesionesViewSet,
    PasswordRecoveryViewSet,
    PermisosViewSet,
    RolesViewSet,
    EmpleadosViewSet,
    AuditoriaOperacionesViewSet,
)


def make_user(username='testuser'):
    return User.objects.get_or_create(username=username, defaults={'password': 'x'})[0]


def make_rol(nombre='Cajero'):
    return Roles.objects.get_or_create(nombre_rol=nombre, defaults={'descripcion': '', 'estado': True})[0]


def make_empleado(usuario, rol=None):
    if rol is None:
        rol = make_rol()
    return Empleados.objects.get_or_create(
        usuario=usuario,
        defaults={
            'nombre': 'Test',
            'apellido': 'User',
            'contrasena_hash': 'x',
            'fecha_ingreso': timezone.now(),
            'estado': True,
            'id_rol': rol,
        }
    )[0]


# ==================== AuthViewSet ====================

@override_settings(RATELIMIT_ENABLE=False)
class AuthViewSetLoginTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AuthViewSet.as_view({'post': 'login'})

    def test_login_sin_credenciales(self):
        request = self.factory.post('/auth/login/', {}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_solo_usuario_sin_password(self):
        request = self.factory.post('/auth/login/', {'usuario': 'admin'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.AuthenticationService.login')
    def test_login_falla_credenciales(self, mock_login):
        mock_login.return_value = {
            'success': False,
            'codigo': 'CREDENCIALES_INVALIDAS',
            'mensaje': 'Credenciales incorrectas',
        }
        request = self.factory.post('/auth/login/', {'usuario': 'u', 'password': 'p'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.usuarios.views.AuthenticationService.login')
    def test_login_cuenta_bloqueada(self, mock_login):
        mock_login.return_value = {
            'success': False,
            'codigo': 'CUENTA_BLOQUEADA',
            'mensaje': 'Cuenta bloqueada',
        }
        request = self.factory.post('/auth/login/', {'usuario': 'u', 'password': 'p'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.usuarios.views.AuthenticationService.login')
    def test_login_cuenta_bloqueada_por_intentos(self, mock_login):
        mock_login.return_value = {
            'success': False,
            'codigo': 'CUENTA_BLOQUEADA_INTENTOS',
            'mensaje': 'Bloqueada por intentos',
        }
        request = self.factory.post('/auth/login/', {'usuario': 'u', 'password': 'p'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.usuarios.views.TwoFactorAuthService.verificar_2fa_habilitado')
    @patch('apps.usuarios.views.AuthenticationService.login')
    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_login_exitoso_sin_2fa(self, mock_get, mock_login, mock_2fa):
        mock_login.return_value = {
            'success': True,
            'tokens': {'access': 'tok', 'refresh': 'ref'},
            'empleado': {'nombre': 'Test'},
            'mensaje': 'OK',
        }
        mock_2fa.return_value = False
        mock_get.return_value = MagicMock()
        request = self.factory.post('/auth/login/', {'usuario': 'admin', 'password': 'pass'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['requiere_2fa'])

    @patch('apps.usuarios.views.TwoFactorAuthService.verificar_2fa_habilitado')
    @patch('apps.usuarios.views.AuthenticationService.login')
    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_login_exitoso_con_2fa(self, mock_get, mock_login, mock_2fa):
        mock_login.return_value = {
            'success': True,
            'tokens': {'access': 'tok', 'refresh': 'ref'},
            'empleado': {'nombre': 'Test'},
            'mensaje': 'OK',
        }
        mock_2fa.return_value = True
        mock_get.return_value = MagicMock()
        request = self.factory.post('/auth/login/', {'usuario': 'admin', 'password': 'pass'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requiere_2fa'])

    @patch('apps.usuarios.views.TwoFactorAuthService.verificar_2fa_habilitado')
    @patch('apps.usuarios.views.AuthenticationService.login')
    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_login_con_campo_username(self, mock_get, mock_login, mock_2fa):
        """También acepta 'username' como campo de usuario"""
        mock_login.return_value = {
            'success': True,
            'tokens': {'access': 'tok', 'refresh': 'ref'},
            'empleado': {},
            'mensaje': 'OK',
        }
        mock_2fa.return_value = False
        mock_get.return_value = MagicMock()
        request = self.factory.post('/auth/login/', {'username': 'admin', 'password': 'pass'}, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthViewSetLogoutTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AuthViewSet.as_view({'post': 'logout'})
        self.user = make_user('logoutuser')

    @patch('apps.usuarios.views.AuthenticationService.logout')
    def test_logout_exitoso(self, mock_logout):
        mock_logout.return_value = {'success': True, 'mensaje': 'Sesión cerrada'}
        request = self.factory.post('/auth/logout/', {'refresh_token': 'tok'}, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthViewSetCambiarPasswordTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AuthViewSet.as_view({'post': 'cambiar_password'})
        self.user = make_user('cpwduser')

    def test_cambiar_password_sin_campos(self):
        request = self.factory.post('/auth/cambiar_password/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_cambiar_password_empleado_no_encontrado(self, mock_get):
        from apps.usuarios.models import Empleados as Emp
        mock_get.side_effect = Emp.DoesNotExist
        request = self.factory.post('/auth/cambiar_password/',
                                    {'password_actual': 'old', 'password_nueva': 'new'},
                                    format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.usuarios.views.AuthenticationService.cambiar_password')
    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_cambiar_password_exitoso(self, mock_get, mock_cambiar):
        mock_empleado = MagicMock()
        mock_get.return_value = mock_empleado
        mock_cambiar.return_value = {'success': True, 'mensaje': 'OK'}
        request = self.factory.post('/auth/cambiar_password/',
                                    {'password_actual': 'old', 'password_nueva': 'new'},
                                    format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.AuthenticationService.cambiar_password')
    @patch('apps.usuarios.views.Empleados.objects.get')
    def test_cambiar_password_fallo(self, mock_get, mock_cambiar):
        mock_get.return_value = MagicMock()
        mock_cambiar.return_value = {'success': False, 'mensaje': 'Error'}
        request = self.factory.post('/auth/cambiar_password/',
                                    {'password_actual': 'old', 'password_nueva': 'new'},
                                    format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthViewSetPerfilTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AuthViewSet.as_view({'get': 'perfil'})
        self.user = make_user('perfiluser')

    @patch('apps.usuarios.views.Empleados.objects.select_related')
    def test_perfil_empleado_no_encontrado(self, mock_select):
        from apps.usuarios.models import Empleados as Emp
        mock_qs = MagicMock()
        mock_qs.get.side_effect = Emp.DoesNotExist
        mock_select.return_value = mock_qs
        request = self.factory.get('/auth/perfil/')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.usuarios.views.TwoFactorAuthService.obtener_estadisticas_2fa')
    @patch('apps.usuarios.views.PermissionService.obtener_permisos_empleado')
    @patch('apps.usuarios.views.EmpleadosSerializer')
    @patch('apps.usuarios.views.Empleados.objects.select_related')
    def test_perfil_exitoso(self, mock_select, mock_ser, mock_perms, mock_stats):
        mock_empleado = MagicMock()
        mock_qs = MagicMock()
        mock_qs.get.return_value = mock_empleado
        mock_select.return_value = mock_qs
        mock_ser.return_value.data = {'nombre': 'Test'}
        mock_perms.return_value = []
        mock_stats.return_value = {}
        request = self.factory.get('/auth/perfil/')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('empleado', response.data)


# ==================== TwoFactorViewSet ====================

class TwoFactorViewSetTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user('twofauser')

    @patch('apps.usuarios.views.TwoFactorAuthService.habilitar_2fa_empleado')
    def test_habilitar_2fa_exitoso(self, mock_habilitar):
        mock_habilitar.return_value = {'success': True, 'qr_code': 'abc'}
        view = TwoFactorViewSet.as_view({'post': 'habilitar'})
        request = self.factory.post('/2fa/habilitar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.TwoFactorAuthService.habilitar_2fa_empleado')
    def test_habilitar_2fa_fallo(self, mock_habilitar):
        mock_habilitar.return_value = {'success': False, 'mensaje': 'Ya habilitado'}
        view = TwoFactorViewSet.as_view({'post': 'habilitar'})
        request = self.factory.post('/2fa/habilitar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verificar_2fa_sin_codigo(self):
        view = TwoFactorViewSet.as_view({'post': 'verificar'})
        request = self.factory.post('/2fa/verificar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.TwoFactorAuthService.verificar_codigo_2fa')
    def test_verificar_2fa_exitoso(self, mock_verificar):
        mock_verificar.return_value = {'success': True, 'mensaje': 'OK'}
        view = TwoFactorViewSet.as_view({'post': 'verificar'})
        request = self.factory.post('/2fa/verificar/', {'codigo': '123456'}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.TwoFactorAuthService.verificar_codigo_2fa')
    def test_verificar_2fa_fallo(self, mock_verificar):
        mock_verificar.return_value = {'success': False, 'mensaje': 'Incorrecto'}
        view = TwoFactorViewSet.as_view({'post': 'verificar'})
        request = self.factory.post('/2fa/verificar/', {'codigo': '000000'}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.TwoFactorAuthService.deshabilitar_2fa_empleado')
    def test_deshabilitar_2fa(self, mock_des):
        mock_des.return_value = {'success': True}
        view = TwoFactorViewSet.as_view({'post': 'deshabilitar'})
        request = self.factory.post('/2fa/deshabilitar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.TwoFactorAuthService.regenerar_backup_codes')
    def test_regenerar_backup_codes_exitoso(self, mock_regen):
        mock_regen.return_value = {'success': True, 'codigos': []}
        view = TwoFactorViewSet.as_view({'post': 'regenerar_backup_codes'})
        request = self.factory.post('/2fa/regenerar_backup_codes/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.TwoFactorAuthService.regenerar_backup_codes')
    def test_regenerar_backup_codes_fallo(self, mock_regen):
        mock_regen.return_value = {'success': False, 'mensaje': 'Error'}
        view = TwoFactorViewSet.as_view({'post': 'regenerar_backup_codes'})
        request = self.factory.post('/2fa/regenerar_backup_codes/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.TwoFactorAuthService.obtener_estadisticas_2fa')
    def test_estadisticas_2fa(self, mock_stats):
        mock_stats.return_value = {'habilitado': False}
        view = TwoFactorViewSet.as_view({'get': 'estadisticas'})
        request = self.factory.get('/2fa/estadisticas/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ==================== SesionesViewSet ====================

class SesionesViewSetTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user('sesionuser')

    @patch('apps.usuarios.views.SessionService.listar_sesiones_activas')
    def test_sesiones_activas(self, mock_listar):
        mock_listar.return_value = [{'key': 'abc'}]
        view = SesionesViewSet.as_view({'get': 'activas'})
        request = self.factory.get('/sesiones/activas/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)

    def test_cerrar_sesion_sin_key(self):
        view = SesionesViewSet.as_view({'post': 'cerrar'})
        request = self.factory.post('/sesiones/cerrar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.SessionService.cerrar_sesion')
    def test_cerrar_sesion_exitoso(self, mock_cerrar):
        mock_cerrar.return_value = {'success': True}
        view = SesionesViewSet.as_view({'post': 'cerrar'})
        request = self.factory.post('/sesiones/cerrar/', {'session_key': 'abc123'}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.SessionService.cerrar_todas_sesiones')
    def test_cerrar_todas_sesiones(self, mock_cerrar):
        mock_cerrar.return_value = {'success': True, 'sesiones_cerradas': 2}
        view = SesionesViewSet.as_view({'post': 'cerrar_todas'})
        request = self.factory.post('/sesiones/cerrar_todas/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ==================== PasswordRecoveryViewSet ====================

class PasswordRecoveryViewSetTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_solicitar_sin_email(self):
        view = PasswordRecoveryViewSet.as_view({'post': 'solicitar'})
        request = self.factory.post('/password/solicitar/', {}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.PasswordRecoveryService.solicitar_recuperacion_empleado')
    def test_solicitar_exitoso(self, mock_solicitar):
        mock_solicitar.return_value = {'success': True, 'token': 'tok'}
        view = PasswordRecoveryViewSet.as_view({'post': 'solicitar'})
        request = self.factory.post('/password/solicitar/', {'email': 'test@test.com'}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_validar_token_sin_token(self):
        view = PasswordRecoveryViewSet.as_view({'post': 'validar_token'})
        request = self.factory.post('/password/validar_token/', {}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.PasswordRecoveryService.validar_token_recuperacion')
    def test_validar_token_valido(self, mock_validar):
        mock_validar.return_value = {'valido': True, 'mensaje': 'Token válido'}
        view = PasswordRecoveryViewSet.as_view({'post': 'validar_token'})
        request = self.factory.post('/password/validar_token/', {'token': 'abc'}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.PasswordRecoveryService.validar_token_recuperacion')
    def test_validar_token_invalido(self, mock_validar):
        mock_validar.return_value = {'valido': False, 'mensaje': 'Token expirado'}
        view = PasswordRecoveryViewSet.as_view({'post': 'validar_token'})
        request = self.factory.post('/password/validar_token/', {'token': 'bad'}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restablecer_sin_campos(self):
        view = PasswordRecoveryViewSet.as_view({'post': 'restablecer'})
        request = self.factory.post('/password/restablecer/', {}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.usuarios.views.PasswordRecoveryService.restablecer_password_con_token')
    def test_restablecer_exitoso(self, mock_reset):
        mock_reset.return_value = {'success': True, 'mensaje': 'OK'}
        view = PasswordRecoveryViewSet.as_view({'post': 'restablecer'})
        request = self.factory.post('/password/restablecer/',
                                    {'token': 'tok', 'nueva_password': 'NewPass123!'},
                                    format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.PasswordRecoveryService.restablecer_password_con_token')
    def test_restablecer_fallo(self, mock_reset):
        mock_reset.return_value = {'success': False, 'mensaje': 'Token inválido'}
        view = PasswordRecoveryViewSet.as_view({'post': 'restablecer'})
        request = self.factory.post('/password/restablecer/',
                                    {'token': 'tok', 'nueva_password': 'pass'},
                                    format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ==================== PermisosViewSet ====================

class PermisosViewSetTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.rol_admin = make_rol('Administrador')
        self.user = make_user('adminperm')
        make_empleado('adminperm', self.rol_admin)

    def test_listar_permisos(self):
        view = PermisosViewSet.as_view({'get': 'listar'})
        request = self.factory.get('/permisos/listar/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('permisos', response.data)

    @patch('apps.usuarios.views.PermissionService.inicializar_permisos')
    def test_inicializar_permisos(self, mock_init):
        mock_init.return_value = {'success': True, 'creados': 20}
        view = PermisosViewSet.as_view({'post': 'inicializar'})
        request = self.factory.post('/permisos/inicializar/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_asignar_a_rol_sin_campos(self):
        view = PermisosViewSet.as_view({'post': 'asignar_a_rol'})
        request = self.factory.post('/permisos/asignar_a_rol/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asignar_a_rol_not_found(self):
        view = PermisosViewSet.as_view({'post': 'asignar_a_rol'})
        with patch('apps.usuarios.views.Roles.objects.get') as mock_get:
            mock_get.side_effect = Roles.DoesNotExist
            request = self.factory.post('/permisos/asignar_a_rol/',
                                        {'id_rol': 99999, 'codigo_permiso': 'test.algo'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.usuarios.views.PermissionService.asignar_permiso_a_rol')
    def test_asignar_a_rol_exitoso(self, mock_asignar):
        mock_asignar.return_value = {'success': True}
        mock_rol = MagicMock()
        view = PermisosViewSet.as_view({'post': 'asignar_a_rol'})
        with patch('apps.usuarios.views.Roles.objects.get', return_value=mock_rol):
            request = self.factory.post('/permisos/asignar_a_rol/',
                                        {'id_rol': self.rol_admin.pk, 'codigo_permiso': 'ventas.crear'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.PermissionService.asignar_permiso_a_rol')
    def test_asignar_a_rol_fallo(self, mock_asignar):
        mock_asignar.return_value = {'success': False, 'mensaje': 'Error'}
        mock_rol = MagicMock()
        view = PermisosViewSet.as_view({'post': 'asignar_a_rol'})
        with patch('apps.usuarios.views.Roles.objects.get', return_value=mock_rol):
            request = self.factory.post('/permisos/asignar_a_rol/',
                                        {'id_rol': self.rol_admin.pk, 'codigo_permiso': 'x'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remover_de_rol_sin_campos(self):
        view = PermisosViewSet.as_view({'post': 'remover_de_rol'})
        request = self.factory.post('/permisos/remover_de_rol/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remover_de_rol_not_found(self):
        view = PermisosViewSet.as_view({'post': 'remover_de_rol'})
        with patch('apps.usuarios.views.Roles.objects.get') as mock_get:
            mock_get.side_effect = Roles.DoesNotExist
            request = self.factory.post('/permisos/remover_de_rol/',
                                        {'id_rol': 99999, 'codigo_permiso': 'x'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.usuarios.views.PermissionService.remover_permiso_de_rol')
    def test_remover_de_rol_exitoso(self, mock_remover):
        mock_remover.return_value = {'success': True}
        view = PermisosViewSet.as_view({'post': 'remover_de_rol'})
        with patch('apps.usuarios.views.Roles.objects.get', return_value=MagicMock()):
            request = self.factory.post('/permisos/remover_de_rol/',
                                        {'id_rol': self.rol_admin.pk, 'codigo_permiso': 'x'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('apps.usuarios.views.PermissionService.remover_permiso_de_rol')
    def test_remover_de_rol_fallo(self, mock_remover):
        mock_remover.return_value = {'success': False, 'mensaje': 'Error'}
        view = PermisosViewSet.as_view({'post': 'remover_de_rol'})
        with patch('apps.usuarios.views.Roles.objects.get', return_value=MagicMock()):
            request = self.factory.post('/permisos/remover_de_rol/',
                                        {'id_rol': self.rol_admin.pk, 'codigo_permiso': 'x'},
                                        format='json')
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ==================== RolesViewSet - acciones extra ====================

class RolesViewSetExtendedTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user('rolesuser')
        self.rol = make_rol('TestRol')

    def test_permisos_rol(self):
        view = RolesViewSet.as_view({'get': 'permisos'})
        request = self.factory.get(f'/roles/{self.rol.pk}/permisos/')
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.rol.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('permisos', response.data)

    def test_destroy_con_empleados(self):
        """No debe eliminar el rol si tiene empleados asignados"""
        emp = make_empleado('emprol', self.rol)
        view = RolesViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/roles/{self.rol.pk}/')
        force_authenticate(request, user=self.user)
        response = view(request, pk=self.rol.pk)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_sin_empleados(self):
        """Debe eliminar el rol si no tiene empleados"""
        rol_libre = Roles.objects.create(nombre_rol='RolSinEmpleados', descripcion='', estado=True)
        view = RolesViewSet.as_view({'delete': 'destroy'})
        request = self.factory.delete(f'/roles/{rol_libre.pk}/')
        force_authenticate(request, user=self.user)
        response = view(request, pk=rol_libre.pk)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Roles.objects.filter(pk=rol_libre.pk).exists())


# ==================== EmpleadosViewSet - acciones extra ====================

class EmpleadosViewSetCreateTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user('empcreateuser')
        self.rol = make_rol('Cajero')

    def test_create_sin_nombre(self):
        view = EmpleadosViewSet.as_view({'post': 'create'})
        data = {
            'apellido': 'Test', 'usuario': 'utest', 'password': 'TestPass1!',
            'fecha_ingreso': '2024-01-01', 'id_rol': self.rol.pk,
        }
        request = self.factory.post('/empleados/', data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', response.data)

    def test_create_sin_password(self):
        view = EmpleadosViewSet.as_view({'post': 'create'})
        data = {
            'nombre': 'J', 'apellido': 'T', 'usuario': 'jt',
            'fecha_ingreso': '2024-01-01', 'id_rol': self.rol.pk,
        }
        request = self.factory.post('/empleados/', data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_usuario_duplicado(self):
        make_empleado('duplicado', self.rol)
        view = EmpleadosViewSet.as_view({'post': 'create'})
        data = {
            'nombre': 'Juan', 'apellido': 'Test', 'usuario': 'duplicado',
            'password': 'TestPass1!', 'fecha_ingreso': '2024-01-01', 'id_rol': self.rol.pk,
        }
        request = self.factory.post('/empleados/', data, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('usuario', response.data)

    def test_create_multiple_missing_fields(self):
        """Debe reportar todos los campos requeridos faltantes"""
        view = EmpleadosViewSet.as_view({'post': 'create'})
        request = self.factory.post('/empleados/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verifica que reporta múltiples campos faltantes
        self.assertTrue(len(response.data) > 1)


class EmpleadosViewSetCambiarPasswordTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.rol_admin = make_rol('Administrador')
        self.rol_cajero = make_rol()
        self.admin_user = make_user('adminpwdtest')
        self.cajero_user = make_user('cajeropwdtest')
        self.admin_emp = make_empleado('adminpwdtest', self.rol_admin)
        self.cajero_emp = make_empleado('cajeropwdtest', self.rol_cajero)

    def test_cambiar_password_sin_password(self):
        view = EmpleadosViewSet.as_view({'post': 'cambiar_password'})
        request = self.factory.post(f'/empleados/{self.cajero_emp.pk}/cambiar_password/',
                                    {}, format='json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.cajero_emp.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_muy_corta(self):
        view = EmpleadosViewSet.as_view({'post': 'cambiar_password'})
        request = self.factory.post(f'/empleados/{self.cajero_emp.pk}/cambiar_password/',
                                    {'password': 'abc'}, format='json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.cajero_emp.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_no_es_admin(self):
        view = EmpleadosViewSet.as_view({'post': 'cambiar_password'})
        request = self.factory.post(f'/empleados/{self.cajero_emp.pk}/cambiar_password/',
                                    {'password': 'NewPass123!'}, format='json')
        force_authenticate(request, user=self.cajero_user)
        response = view(request, pk=self.cajero_emp.pk)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cambiar_password_exitoso_admin(self):
        view = EmpleadosViewSet.as_view({'post': 'cambiar_password'})
        request = self.factory.post(f'/empleados/{self.cajero_emp.pk}/cambiar_password/',
                                    {'password': 'NewPass123!'}, format='json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.cajero_emp.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


# ==================== AuditoriaOperacionesViewSet ====================

class AuditoriaOperacionesViewSetTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.rol_admin = make_rol('Administrador')
        self.user = make_user('audituser')
        make_empleado('audituser', self.rol_admin)
        # Create some audit records
        AuditoriaOperaciones.objects.create(
            usuario='audituser',
            tipo_usuario='EMPLEADO',
            operacion='LOGIN',
            tabla_afectada='empleados',
            resultado='EXITO',
            ip_address='127.0.0.1',
            fecha_operacion=timezone.now(),
        )
        AuditoriaOperaciones.objects.create(
            usuario='audituser',
            tipo_usuario='EMPLEADO',
            operacion='UPDATE',
            tabla_afectada='productos',
            resultado='ERROR',
            ip_address='127.0.0.1',
            fecha_operacion=timezone.now(),
        )

    def test_estadisticas(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'estadisticas'})
        request = self.factory.get('/auditoria/estadisticas/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_registros', response.data)

    def test_timeline(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'timeline'})
        request = self.factory.get('/auditoria/timeline/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_actividad_usuario_sin_parametro(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'actividad_usuario'})
        request = self.factory.get('/auditoria/actividad_usuario/')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actividad_usuario_con_id(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'actividad_usuario'})
        request = self.factory.get('/auditoria/actividad_usuario/', {'id_usuario': '1'})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_operaciones', response.data)

    def test_get_queryset_con_filtros_fecha(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'list'})
        request = self.factory.get('/auditoria/', {
            'fecha_desde': '2020-01-01',
            'fecha_hasta': '2099-12-31',
        })
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queryset_con_id_usuario(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'list'})
        request = self.factory.get('/auditoria/', {'id_usuario': '1'})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queryset_con_tabla(self):
        view = AuditoriaOperacionesViewSet.as_view({'get': 'list'})
        request = self.factory.get('/auditoria/', {'tabla': 'empleados'})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
