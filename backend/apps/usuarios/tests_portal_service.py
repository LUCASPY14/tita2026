"""
Tests para servicio de autenticación del portal (PortalAuthService)

NOTA: La medición de cobertura con pytest-cov puede fallar en Python 3.14
debido a incompatibilidad de bcrypt (PyO3). Los tests funcionan correctamente
sin cobertura. Para medir cobertura, usar Python 3.11 o ejecutar en CI/CD.
"""
import jwt
import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings
from django.utils import timezone

from apps.usuarios.services.portal_service import (
    PortalAuthService,
    PORTAL_TOKEN_LIFETIME,
    PORTAL_TOKEN_TYPE,
)
from apps.usuarios.models import UsuariosPortal
from apps.clientes.models import Clientes


@pytest.fixture
def mock_cliente():
    """Mock de Clientes"""
    cliente = Mock(spec=Clientes)
    cliente.id_cliente = 100
    cliente.nombre_completo = "Juan Pérez"
    cliente.ruc_ci = "1234567-8"
    return cliente


@pytest.fixture
def mock_portal_user(mock_cliente):
    """Mock de UsuariosPortal"""
    user = Mock(spec=UsuariosPortal)
    user.id_usuario_portal = 50
    user.email = "cliente@example.com"
    user.email_verificado = True
    user.estado = True
    user.id_cliente = mock_cliente
    user.id_cliente_id = mock_cliente.id_cliente
    user.check_password = Mock(return_value=True)
    user.save = Mock()
    return user


class TestPortalAuthServiceLogin:
    """Tests para PortalAuthService.login()"""

    @patch("apps.usuarios.services.portal_service.PortalAuthService._generar_token")
    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    @patch("apps.usuarios.services.portal_service.timezone.now")
    def test_login_exitoso(
        self,
        mock_now,
        mock_select_related,
        mock_generar_token,
        mock_portal_user,
    ):
        """Login exitoso debe retornar token y datos del usuario"""
        mock_now.return_value = timezone.now()
        mock_select_related.return_value.get.return_value = mock_portal_user
        mock_generar_token.return_value = "token_generado_123"

        result = PortalAuthService.login("cliente@example.com", "password123")

        assert result["token"] == "token_generado_123"
        assert result["portal_user"]["id_usuario_portal"] == 50
        assert result["portal_user"]["email"] == "cliente@example.com"
        assert result["portal_user"]["email_verificado"] is True
        assert result["portal_user"]["id_cliente"] == 100
        assert result["portal_user"]["nombre_completo"] == "Juan Pérez"
        assert result["portal_user"]["ruc_ci"] == "1234567-8"
        
        mock_portal_user.save.assert_called_once_with(update_fields=["ultimo_acceso"])
        mock_portal_user.check_password.assert_called_once_with("password123")

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_usuario_no_existe(self, mock_select_related):
        """Login con usuario inexistente debe levantar ValueError"""
        mock_select_related.return_value.get.side_effect = (
            UsuariosPortal.DoesNotExist
        )

        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.login("noexiste@example.com", "password")

        assert "Credenciales incorrectas" in str(excinfo.value)

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_cuenta_desactivada(self, mock_select_related, mock_portal_user):
        """Login con cuenta desactivada debe levantar ValueError"""
        mock_portal_user.estado = False
        mock_select_related.return_value.get.return_value = mock_portal_user

        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.login("cliente@example.com", "password")

        assert "Cuenta desactivada" in str(excinfo.value)

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_password_incorrecto(self, mock_select_related, mock_portal_user):
        """Login con password incorrecto debe levantar ValueError"""
        mock_portal_user.check_password.return_value = False
        mock_select_related.return_value.get.return_value = mock_portal_user

        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.login("cliente@example.com", "password_malo")

        assert "Credenciales incorrectas" in str(excinfo.value)

    @patch("apps.usuarios.services.portal_service.PortalAuthService._generar_token")
    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_actualiza_ultimo_acceso(
        self, mock_select_related, mock_generar_token, mock_portal_user
    ):
        """Login debe actualizar ultimo_acceso del usuario"""
        mock_select_related.return_value.get.return_value = mock_portal_user
        mock_generar_token.return_value = "token123"

        PortalAuthService.login("cliente@example.com", "password")

        assert mock_portal_user.ultimo_acceso is not None
        mock_portal_user.save.assert_called_once_with(update_fields=["ultimo_acceso"])

    @patch("apps.usuarios.services.portal_service.PortalAuthService._generar_token")
    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_normaliza_email_case_insensitive(
        self, mock_select_related, mock_generar_token, mock_portal_user
    ):
        """Login debe buscar email con case insensitive"""
        mock_select_related.return_value.get.return_value = mock_portal_user
        mock_generar_token.return_value = "token"

        PortalAuthService.login("CLIENTE@EXAMPLE.COM", "password")

        # Verificar que se usó email__iexact
        mock_select_related.return_value.get.assert_called_once()
        call_kwargs = mock_select_related.return_value.get.call_args[1]
        assert "email__iexact" in call_kwargs

    @patch("apps.usuarios.services.portal_service.PortalAuthService._generar_token")
    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_login_elimina_espacios_del_email(
        self, mock_select_related, mock_generar_token, mock_portal_user
    ):
        """Login debe eliminar espacios del email"""
        mock_select_related.return_value.get.return_value = mock_portal_user
        mock_generar_token.return_value = "token"

        PortalAuthService.login("  cliente@example.com  ", "password")

        # Verificar que se usó strip()
        call_kwargs = mock_select_related.return_value.get.call_args[1]
        email_buscado = call_kwargs["email__iexact"]
        assert email_buscado == "cliente@example.com"


class TestPortalAuthServiceGenerarToken:
    """Tests para PortalAuthService._generar_token()"""

    @patch("time.time")
    def test_generar_token_estructura_correcta(self, mock_time, mock_portal_user):
        """Token generado debe tener estructura correcta"""
        import time
        current_time = int(time.time())
        mock_time.return_value = current_time  # Usar tiempo actual
        
        token = PortalAuthService._generar_token(mock_portal_user)
        
        # Decodificar sin verificar expiración para testing
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        assert payload["token_type"] == PORTAL_TOKEN_TYPE
        assert payload["id_usuario_portal"] == 50
        assert payload["id_cliente"] == 100
        assert payload["email"] == "cliente@example.com"
        assert payload["iat"] == current_time
        assert payload["exp"] == current_time + int(PORTAL_TOKEN_LIFETIME.total_seconds())

    @patch("time.time")
    def test_generar_token_tiempo_expiracion(self, mock_time, mock_portal_user):
        """Token debe expirar en PORTAL_TOKEN_LIFETIME (8 horas)"""
        import time
        current_time = int(time.time())
        mock_time.return_value = current_time
        
        token = PortalAuthService._generar_token(mock_portal_user)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        expected_exp = current_time + int(timedelta(hours=8).total_seconds())
        assert payload["exp"] == expected_exp

    def test_generar_token_es_valido(self, mock_portal_user):
        """Token generado debe ser válido para jwt.decode"""
        token = PortalAuthService._generar_token(mock_portal_user)
        
        # No debe levantar excepción
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload is not None


class TestPortalAuthServiceVerificarToken:
    """Tests para PortalAuthService.verificar_token()"""

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_verificar_token_exitoso(self, mock_select_related, mock_portal_user):
        """Verificación exitosa debe retornar UsuariosPortal"""
        mock_select_related.return_value.get.return_value = mock_portal_user
        
        # Crear token válido
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": 50,
            "id_cliente": 100,
            "email": "cliente@example.com",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        result = PortalAuthService.verificar_token(token)
        
        assert result == mock_portal_user
        mock_select_related.return_value.get.assert_called_once_with(
            id_usuario_portal=50,
            estado=True,
        )

    def test_verificar_token_expirado(self):
        """Token expirado debe levantar ValueError"""
        import time
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": 50,
            "exp": int(time.time()) - 3600,  # Expirado hace 1 hora
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Token expirado" in str(excinfo.value)

    def test_verificar_token_invalido(self):
        """Token mal formado debe levantar ValueError"""
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token("token_invalido")
        
        assert "Token inválido" in str(excinfo.value)

    def test_verificar_token_firma_incorrecta(self):
        """Token con firma incorrecta debe levantar ValueError"""
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": 50,
        }
        token = jwt.encode(payload, "clave_incorrecta", algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Token inválido" in str(excinfo.value)

    def test_verificar_token_tipo_incorrecto(self):
        """Token con tipo != 'portal' debe levantar ValueError"""
        payload = {
            "token_type": "empleado",  # Tipo incorrecto
            "id_usuario_portal": 50,
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Token inválido" in str(excinfo.value)

    def test_verificar_token_sin_tipo(self):
        """Token sin claim token_type debe levantar ValueError"""
        payload = {"id_usuario_portal": 50}  # Sin token_type
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Token inválido" in str(excinfo.value)

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_verificar_token_usuario_no_existe(self, mock_select_related):
        """Usuario no encontrado debe levantar ValueError"""
        mock_select_related.return_value.get.side_effect = UsuariosPortal.DoesNotExist
        
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": 999,  # No existe
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Usuario de portal no encontrado o inactivo" in str(excinfo.value)

    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_verificar_token_usuario_inactivo(self, mock_select_related):
        """Usuario inactivo debe levantar ValueError (filtrado por estado=True)"""
        mock_select_related.return_value.get.side_effect = UsuariosPortal.DoesNotExist
        
        payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "id_usuario_portal": 50,
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(ValueError) as excinfo:
            PortalAuthService.verificar_token(token)
        
        assert "Usuario de portal no encontrado o inactivo" in str(excinfo.value)


class TestPortalAuthServiceIntegracion:
    """Tests de integración para flujo completo login → verificar_token"""

    @patch("apps.usuarios.services.portal_service.timezone.now")
    @patch("apps.usuarios.models.UsuariosPortal.objects.select_related")
    def test_flujo_completo_login_y_verificacion(
        self, mock_select_related, mock_now, mock_portal_user
    ):
        """Test de integración: login genera token válido que puede verificarse"""
        mock_now.return_value = timezone.now()
        mock_select_related.return_value.get.return_value = mock_portal_user
        
        # Login
        login_result = PortalAuthService.login("cliente@example.com", "password123")
        token = login_result["token"]
        
        # Verificar token generado
        verified_user = PortalAuthService.verificar_token(token)
        
        assert verified_user == mock_portal_user
        assert login_result["portal_user"]["id_usuario_portal"] == 50
        assert login_result["portal_user"]["email"] == "cliente@example.com"
