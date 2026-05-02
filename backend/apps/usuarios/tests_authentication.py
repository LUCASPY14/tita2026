"""
Tests para autenticación de usuarios del portal (clientes)
"""

import jwt
import pytest
from unittest.mock import Mock, patch, MagicMock
from rest_framework.exceptions import AuthenticationFailed

from apps.usuarios.authentication import (
    PortalUserProxy,
    PortalJWTAuthentication,
)
from apps.usuarios.services.portal_service import PORTAL_TOKEN_TYPE


@pytest.fixture
def mock_portal_user():
    """Mock de UsuariosPortal"""
    mock_user = Mock()
    mock_user.id_usuario_portal = 123
    mock_user.email = "cliente@example.com"
    return mock_user


@pytest.fixture
def portal_jwt_auth():
    """Instancia de PortalJWTAuthentication"""
    return PortalJWTAuthentication()


class TestPortalUserProxy:
    """Tests para PortalUserProxy wrapper"""

    def test_inicializa_correctamente(self, mock_portal_user):
        """Debe inicializar con portal_user y establecer atributos"""
        proxy = PortalUserProxy(mock_portal_user)

        assert proxy.portal_user == mock_portal_user
        assert proxy.is_authenticated is True
        assert proxy.pk == 123

    def test_str_retorna_email(self, mock_portal_user):
        """__str__ debe retornar el email del usuario"""
        proxy = PortalUserProxy(mock_portal_user)

        assert str(proxy) == "cliente@example.com"

    def test_pk_corresponde_a_id_usuario_portal(self, mock_portal_user):
        """pk debe ser el id_usuario_portal del usuario"""
        mock_portal_user.id_usuario_portal = 456
        proxy = PortalUserProxy(mock_portal_user)

        assert proxy.pk == 456

    def test_is_authenticated_siempre_true(self, mock_portal_user):
        """is_authenticated debe ser siempre True"""
        proxy = PortalUserProxy(mock_portal_user)

        assert proxy.is_authenticated is True


class TestPortalJWTAuthentication:
    """Tests para PortalJWTAuthentication"""

    # === Tests de autenticación exitosa ===

    @patch("apps.usuarios.authentication.PortalAuthService.verificar_token")
    def test_autenticacion_exitosa_con_token_portal(self, mock_verificar_token, portal_jwt_auth, mock_portal_user):
        """Debe autenticar correctamente con token de tipo portal"""
        mock_verificar_token.return_value = mock_portal_user

        # Crear token con tipo portal
        token_payload = {"token_type": PORTAL_TOKEN_TYPE, "user_id": 123}
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        result = portal_jwt_auth.authenticate(request)

        assert result is not None
        proxy, returned_token = result
        assert isinstance(proxy, PortalUserProxy)
        assert proxy.portal_user == mock_portal_user
        assert returned_token == token
        mock_verificar_token.assert_called_once_with(token)

    # === Tests de skip (retorna None) ===

    def test_sin_header_authorization_retorna_none(self, portal_jwt_auth):
        """Sin header Authorization debe retornar None"""
        request = Mock()
        request.META = {}

        result = portal_jwt_auth.authenticate(request)

        assert result is None

    def test_header_no_bearer_retorna_none(self, portal_jwt_auth):
        """Header sin 'Bearer ' debe retornar None"""
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Token abc123"}

        result = portal_jwt_auth.authenticate(request)

        assert result is None

    def test_token_sin_tipo_retorna_none(self, portal_jwt_auth):
        """Token sin claim token_type debe retornar None"""
        token_payload = {"user_id": 123}  # Sin token_type
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        result = portal_jwt_auth.authenticate(request)

        assert result is None

    def test_token_tipo_no_portal_retorna_none(self, portal_jwt_auth):
        """Token con token_type != 'portal' debe retornar None"""
        token_payload = {"token_type": "empleado", "user_id": 123}
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        result = portal_jwt_auth.authenticate(request)

        assert result is None

    def test_token_invalido_en_peek_retorna_none(self, portal_jwt_auth):
        """Token mal formado en peek debe retornar None"""
        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer token_invalido"}

        result = portal_jwt_auth.authenticate(request)

        assert result is None

    # === Tests de errores de autenticación ===

    @patch("apps.usuarios.authentication.PortalAuthService.verificar_token")
    def test_verificar_token_lanza_value_error(self, mock_verificar_token, portal_jwt_auth):
        """ValueError de verificar_token debe convertirse en AuthenticationFailed"""
        mock_verificar_token.side_effect = ValueError("Token expirado")

        token_payload = {"token_type": PORTAL_TOKEN_TYPE, "user_id": 123}
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        with pytest.raises(AuthenticationFailed) as excinfo:
            portal_jwt_auth.authenticate(request)

        assert "Token expirado" in str(excinfo.value)

    @patch("apps.usuarios.authentication.PortalAuthService.verificar_token")
    def test_verificar_token_token_invalido(self, mock_verificar_token, portal_jwt_auth):
        """Debe levantar AuthenticationFailed con mensaje correcto"""
        mock_verificar_token.side_effect = ValueError("Token inválido")

        token_payload = {"token_type": PORTAL_TOKEN_TYPE, "user_id": 123}
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        with pytest.raises(AuthenticationFailed) as excinfo:
            portal_jwt_auth.authenticate(request)

        assert "Token inválido" in str(excinfo.value)

    # === Test de authenticate_header ===

    def test_authenticate_header_retorna_bearer(self, portal_jwt_auth):
        """authenticate_header debe retornar 'Bearer'"""
        request = Mock()

        result = portal_jwt_auth.authenticate_header(request)

        assert result == "Bearer"

    # === Tests de extracción de token ===

    @patch("apps.usuarios.authentication.PortalAuthService.verificar_token")
    def test_extrae_token_correctamente_de_header(self, mock_verificar_token, portal_jwt_auth, mock_portal_user):
        """Debe extraer token después de 'Bearer '"""
        mock_verificar_token.return_value = mock_portal_user

        token_payload = {"token_type": PORTAL_TOKEN_TYPE}
        expected_token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {expected_token}"}

        proxy, returned_token = portal_jwt_auth.authenticate(request)

        assert returned_token == expected_token

    def test_header_bearer_con_espacios_extras(self, portal_jwt_auth):
        """Debe manejar espacios extras en header Bearer"""
        token_payload = {"token_type": "other"}
        token = jwt.encode(token_payload, "secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer  {token}"}  # 2 espacios

        # Nota: split(" ", 1) tomará todo después del primer espacio
        result = portal_jwt_auth.authenticate(request)

        # Token con espacio extra al inicio no será válido
        assert result is None

    # === Test de integración del flujo completo ===

    @patch("apps.usuarios.authentication.PortalAuthService.verificar_token")
    def test_flujo_completo_autenticacion_portal(self, mock_verificar_token, portal_jwt_auth, mock_portal_user):
        """Test de integración del flujo completo"""
        # Arrange
        mock_portal_user.id_usuario_portal = 789
        mock_portal_user.email = "test@portal.com"
        mock_verificar_token.return_value = mock_portal_user

        token_payload = {
            "token_type": PORTAL_TOKEN_TYPE,
            "user_id": 789,
            "email": "test@portal.com",
        }
        token = jwt.encode(token_payload, "test_secret", algorithm="HS256")

        request = Mock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # Act
        proxy, returned_token = portal_jwt_auth.authenticate(request)

        # Assert
        assert proxy.is_authenticated is True
        assert proxy.pk == 789
        assert str(proxy) == "test@portal.com"
        assert returned_token == token
        assert proxy.portal_user == mock_portal_user
