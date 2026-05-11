"""
Tests extendidos para apps/core/views.py
Cubre las líneas faltantes en core/views.py:
244-245 (hijo not found), 263-265 (sin tarjeta),
335-336 (bancard falla), 389-390, 400, 407 (configuracion),
421-422 (actualizar_valor sin valor), 439-454 (integer validation),
457-473 (decimal validation), 476-477 (boolean), 480-483 (json),
487-489 (valores_permitidos), 507-508 (resetear_default exception)
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import ConfiguracionSistema
from apps.core.views import ConfiguracionSistemaViewSet

# =============================================================================
# TESTS iniciar_recarga_bancard - líneas faltantes 244-245, 263-265, 335-336
# =============================================================================


class IniciarRecargaBancardEdgeCasesTest(TestCase):
    """Cubre casos de borde en iniciar_recarga_bancard"""

    def setUp(self):
        from apps.clientes.models import Clientes, Hijos, TiposCliente
        from apps.core.models import Tarjetas
        from apps.productos.models import ListasPrecios

        self.client = APIClient()
        self.auth_user = User.objects.create_user(username="bancard_ext_user", password="testpass123", is_staff=True)
        self.client.force_authenticate(user=self.auth_user)

        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Standard Bancard", estado=True)
        self.lista_precios = ListasPrecios.objects.create(nombre_lista="Lista Bancard", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Ana",
            apellidos="Lopez",
            ruc_ci="12312312",
            email="ana@test.com",
            telefono="0981111111",
            id_lista=self.lista_precios,
            id_tipo_cliente=self.tipo_cliente,
        )
        # Hijo sin tarjeta asignada
        self.hijo_sin_tarjeta = Hijos.objects.create(
            nombre="Pedro",
            apellido="Lopez",
            fecha_nacimiento="2017-01-01",
            id_cliente_responsable=self.cliente,
        )
        # Hijo con tarjeta
        from datetime import datetime

        self.hijo_con_tarjeta = Hijos.objects.create(
            nombre="Maria",
            apellido="Lopez",
            fecha_nacimiento="2018-06-15",
            id_cliente_responsable=self.cliente,
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="TAR-BANC-EXT-001",
            saldo_actual=Decimal("5000.00"),
            estado="Activa",
            fecha_creacion=datetime.now(),
            limite_credito=Decimal("10000000.00"),
            id_hijo=self.hijo_con_tarjeta,
        )

    def test_hijo_no_encontrado_retorna_404(self):
        """Línea 244-245: Hijo no existe → 404"""
        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": 999999,
            "monto": 50000,
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("no encontrado", response.data["error"])

    def test_hijo_sin_tarjeta_retorna_400(self):
        """Líneas 263-265: Hijo existe pero sin tarjeta → 400"""
        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": self.hijo_sin_tarjeta.id_hijo,
            "monto": 50000,
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tarjeta", response.data["error"])

    def test_monto_invalido_retorna_400(self):
        """Líneas 270-273: Monto no numérico → 400"""
        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": self.hijo_con_tarjeta.id_hijo,
            "monto": "no_es_numero",
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_monto_cero_retorna_400(self):
        """Monto = 0 → 400 (falsy, faltan datos)"""
        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": self.hijo_con_tarjeta.id_hijo,
            "monto": 0,
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_monto_negativo_retorna_400(self):
        """Monto negativo → 400 (pasa all() pero falla validación)"""
        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": self.hijo_con_tarjeta.id_hijo,
            "monto": -100,
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.api_integrations.services.BancardService")
    def test_bancard_falla_cancela_recarga(self, mock_bancard_cls):
        """Líneas 335-336: Bancard retorna success=False → recarga rechazada, 400"""
        mock_bancard = MagicMock()
        mock_bancard_cls.return_value = mock_bancard
        mock_bancard.iniciar_transaccion.return_value = {
            "success": False,
            "error": "Bancard no disponible",
        }

        url = "/api/v1/cargas-saldo/init/"
        data = {
            "hijo_id": self.hijo_con_tarjeta.id_hijo,
            "monto": 50000,
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("error", response.data)


# =============================================================================
# TESTS ConfiguracionSistemaViewSet._validar_valor_config - líneas 421-489
# =============================================================================


class ValidarValorConfigTest(TestCase):
    """Cubre _validar_valor_config con distintos tipos"""

    def _make_config(self, tipo="string", valor_min=None, valor_max=None, valores_permitidos=None):
        config = MagicMock()
        config.tipo = tipo
        config.valor_min = valor_min
        config.valor_max = valor_max
        config.valores_permitidos = valores_permitidos
        return config

    # --- integer ---
    def test_integer_invalido_retorna_error(self):
        """Línea 439-441: int() raises → error mensaje"""
        config = self._make_config(tipo="integer")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "abc")
        self.assertIn("número entero", result)

    def test_integer_menor_que_min_retorna_error(self):
        """Línea 444-445: valor < valor_min → error"""
        config = self._make_config(tipo="integer", valor_min="10")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "5")
        self.assertIn("mínimo", result)

    def test_integer_mayor_que_max_retorna_error(self):
        """Línea 449-450: valor > valor_max → error"""
        config = self._make_config(tipo="integer", valor_max="100")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "200")
        self.assertIn("máximo", result)

    def test_integer_valido_retorna_none(self):
        """Integer válido y dentro de rango → None"""
        config = self._make_config(tipo="integer", valor_min="0", valor_max="100")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "50")
        self.assertIsNone(result)

    def test_integer_min_no_numerico_pasa(self):
        """valor_min no numérico → no falla (pasa except)"""
        config = self._make_config(tipo="integer", valor_min="abc")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "50")
        self.assertIsNone(result)

    def test_integer_max_no_numerico_pasa(self):
        """valor_max no numérico → no falla (pasa except)"""
        config = self._make_config(tipo="integer", valor_max="abc")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "50")
        self.assertIsNone(result)

    # --- decimal ---
    def test_decimal_invalido_retorna_error(self):
        """Línea 457-459: Decimal() raises → error mensaje"""
        config = self._make_config(tipo="decimal")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "no_decimal")
        self.assertIn("número decimal", result)

    def test_decimal_menor_que_min_retorna_error(self):
        """Línea 462-463: decimal < valor_min → error"""
        config = self._make_config(tipo="decimal", valor_min="10.00")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "5.00")
        self.assertIn("mínimo", result)

    def test_decimal_mayor_que_max_retorna_error(self):
        """Línea 467-468: decimal > valor_max → error"""
        config = self._make_config(tipo="decimal", valor_max="100.00")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "200.00")
        self.assertIn("máximo", result)

    def test_decimal_valido_retorna_none(self):
        """Decimal válido → None"""
        config = self._make_config(tipo="decimal", valor_min="0", valor_max="1000")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "500.50")
        self.assertIsNone(result)

    def test_decimal_min_invalido_pasa(self):
        """valor_min inválido para Decimal → pasa except"""
        config = self._make_config(tipo="decimal", valor_min="not_decimal")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "50.00")
        self.assertIsNone(result)

    def test_decimal_max_invalido_pasa(self):
        """valor_max inválido para Decimal → pasa except"""
        config = self._make_config(tipo="decimal", valor_max="not_decimal")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "50.00")
        self.assertIsNone(result)

    # --- boolean ---
    def test_boolean_invalido_retorna_error(self):
        """Línea 476-477: boolean inválido → error"""
        config = self._make_config(tipo="boolean")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "maybe")
        self.assertIn("true o false", result)

    def test_boolean_true_valido(self):
        """boolean 'true' → None"""
        config = self._make_config(tipo="boolean")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "true")
        self.assertIsNone(result)

    def test_boolean_false_valido(self):
        """boolean 'false' → None"""
        config = self._make_config(tipo="boolean")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "false")
        self.assertIsNone(result)

    def test_boolean_1_valido(self):
        """boolean '1' → None"""
        config = self._make_config(tipo="boolean")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "1")
        self.assertIsNone(result)

    def test_boolean_0_valido(self):
        """boolean '0' → None"""
        config = self._make_config(tipo="boolean")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "0")
        self.assertIsNone(result)

    # --- json ---
    def test_json_invalido_retorna_error(self):
        """Líneas 480-483: JSON inválido → error"""
        config = self._make_config(tipo="json")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "not json {")
        self.assertIn("JSON válido", result)

    def test_json_valido_retorna_none(self):
        """JSON válido → None"""
        config = self._make_config(tipo="json")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, '{"key": "value"}')
        self.assertIsNone(result)

    # --- valores_permitidos ---
    def test_valor_no_en_permitidos_retorna_error(self):
        """Línea 487-489: valor no está en lista de permitidos → error"""
        config = self._make_config(tipo="string", valores_permitidos=["opcion1", "opcion2"])
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "otro_valor")
        self.assertIn("no permitido", result)

    def test_valor_en_permitidos_retorna_none(self):
        """Valor en lista de permitidos → None"""
        config = self._make_config(tipo="string", valores_permitidos=["opcion1", "opcion2"])
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "opcion1")
        self.assertIsNone(result)

    def test_valores_permitidos_no_lista_pasa(self):
        """valores_permitidos no es lista (string) → lista vacía, pasa"""
        config = self._make_config(tipo="string", valores_permitidos="string_not_list")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "cualquiera")
        self.assertIsNone(result)

    def test_valores_permitidos_lista_vacia_pasa(self):
        """valores_permitidos lista vacía → pasa"""
        config = self._make_config(tipo="string", valores_permitidos=[])
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "cualquiera")
        self.assertIsNone(result)

    def test_tipo_string_sin_restricciones_retorna_none(self):
        """Tipo string sin restricciones → None"""
        config = self._make_config(tipo="string")
        result = ConfiguracionSistemaViewSet._validar_valor_config(config, "cualquier texto")
        self.assertIsNone(result)


# =============================================================================
# TESTS ConfiguracionSistemaViewSet endpoints - líneas 389-390, 400, 407
# =============================================================================


class ConfiguracionSistemaActualizarValorTest(TestCase):
    """Cubre actualizar_valor y resetear_default con DB real"""

    def setUp(self):
        self.client = APIClient()
        self.auth_user = User.objects.create_superuser(username="config_ext_user", password="testpass123")
        self.client.force_authenticate(user=self.auth_user)

        self.config = ConfiguracionSistema.objects.create(
            clave="test_config_ext_integer",
            valor="50",
            valor_defecto="10",
            tipo="integer",
            categoria="sistema",
            estado=True,
            valor_min="1",
            valor_max="100",
        )
        self.config_bool = ConfiguracionSistema.objects.create(
            clave="test_config_ext_bool",
            valor="true",
            valor_defecto="false",
            tipo="boolean",
            categoria="sistema",
            estado=True,
        )
        self.config_decimal = ConfiguracionSistema.objects.create(
            clave="test_config_ext_decimal",
            valor="50.00",
            valor_defecto="10.00",
            tipo="decimal",
            categoria="sistema",
            estado=True,
            valor_min="1.00",
            valor_max="100.00",
        )
        self.config_json = ConfiguracionSistema.objects.create(
            clave="test_config_ext_json",
            valor='{"key":"value"}',
            valor_defecto="{}",
            tipo="json",
            categoria="sistema",
            estado=True,
        )

    def test_actualizar_valor_sin_campo_valor_retorna_400(self):
        """Líneas 421-422: valor=None → 400"""
        url = f"/api/v1/configuracion/{self.config.pk}/actualizar_valor/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor es requerido", response.data["error"])

    def test_actualizar_valor_integer_invalido_retorna_400(self):
        """Integer inválido a través del endpoint → 400"""
        url = f"/api/v1/configuracion/{self.config.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "abc"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_valor_integer_menor_min_retorna_400(self):
        """Integer menor que valor_min → 400"""
        url = f"/api/v1/configuracion/{self.config.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "0"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_valor_integer_mayor_max_retorna_400(self):
        """Integer mayor que valor_max → 400"""
        url = f"/api/v1/configuracion/{self.config.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "200"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_valor_integer_valido_retorna_200(self):
        """Integer válido dentro de rango → 200"""
        url = f"/api/v1/configuracion/{self.config.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "75"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_actualizar_valor_boolean_invalido_retorna_400(self):
        """Boolean inválido → 400"""
        url = f"/api/v1/configuracion/{self.config_bool.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "maybe"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_valor_decimal_invalido_retorna_400(self):
        """Decimal inválido → 400"""
        url = f"/api/v1/configuracion/{self.config_decimal.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "not_decimal"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_valor_json_invalido_retorna_400(self):
        """JSON inválido → 400"""
        url = f"/api/v1/configuracion/{self.config_json.pk}/actualizar_valor/"
        response = self.client.post(url, {"valor": "not json {"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resetear_default_exitoso(self):
        """resetear_default funciona → 200"""
        url = f"/api/v1/configuracion/{self.config.pk}/resetear_default/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.config.refresh_from_db()
        self.assertEqual(self.config.valor, "10")

    def test_resetear_default_objeto_no_existe_retorna_400(self):
        """Líneas 507-508: pk no existe → 400 (raises exception)"""
        url = "/api/v1/configuracion/99999/resetear_default/"
        response = self.client.post(url, {}, format="json")
        # 404 from get_object or 400 from exception handler
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_por_categoria_retorna_agrupado(self):
        """por_categoria endpoint → 200 con dict"""
        url = "/api/v1/configuracion/por_categoria/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
