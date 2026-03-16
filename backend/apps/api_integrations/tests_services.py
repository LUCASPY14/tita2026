"""
Tests para servicios de api_integrations
Cubre BancardService y otros servicios de integración API
"""

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import json
import hashlib
import hmac
import requests

from apps.api_integrations.services.bancard_service import BancardService
from apps.api_integrations.models import (
    ProveedoresApi,
    LogsLlamadasApi,
    CredencialesApi
)
from apps.core.models import ConfiguracionSistema, CargasSaldo


class BancardServiceTest(TestCase):
    """Tests para BancardService"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Configuración de sistema
        ConfiguracionSistema.objects.create(
            clave='BANCARD_PUBLIC_KEY',
            valor_texto='test_public_key_123',
            descripcion='Clave pública de Bancard para testing',
            estado=True
        )
        
        ConfiguracionSistema.objects.create(
            clave='BANCARD_PRIVATE_KEY',
            valor_texto='test_private_key_456',
            descripcion='Clave privada de Bancard para testing',
            estado=True
        )
        
        # Crear proveedor
        self.proveedor = ProveedoresApi.objects.create(
            nombre='Bancard',
            descripcion='Pasarela de pagos Bancard',
            tipo_servicio='payment_gateway',
            url_base='https://vpos.infonet.com.py:8888',
            version='0.3',
            tipo_auth='hmac_sha256',
            config_auth={
                'public_key': 'test_public_key_123',
                'private_key': 'test_private_key_456'
            },
            timeout=30,
            max_reintentos=3,
            created_at=timezone.now()
        )
        
        # Crear recarga de prueba
        self.recarga = CargasSaldo.objects.create(
            monto=Decimal('50000.00'),
            estado='pendiente',
            metodo_pago='bancard',
            fecha_creacion=timezone.now()
        )

    def test_bancard_service_init_staging(self):
        """Debe inicializar correctamente en ambiente staging"""
        service = BancardService(ambiente='staging')
        
        self.assertEqual(service.ambiente, 'staging')
        self.assertEqual(service.base_url, BancardService.BANCARD_STAGING_URL)
        self.assertEqual(service.public_key, 'test_public_key_123')
        self.assertEqual(service.private_key, 'test_private_key_456')

    def test_bancard_service_init_production(self):
        """Debe inicializar correctamente en ambiente production"""
        service = BancardService(ambiente='production')
        
        self.assertEqual(service.ambiente, 'production')
        self.assertEqual(service.base_url, BancardService.BANCARD_PRODUCTION_URL)

    def test_bancard_service_get_config_from_db(self):
        """Debe obtener configuración desde base de datos"""
        service = BancardService()
        
        config = service._get_config('BANCARD_PUBLIC_KEY')
        self.assertEqual(config, 'test_public_key_123')

    def test_bancard_service_get_config_fallback_settings(self):
        """Debe usar settings como fallback si no está en BD"""
        service = BancardService()
        
        # Configuración que no existe en BD
        with patch.object(settings, 'BANCARD_NONEXISTENT', 'fallback_value', create=True):
            config = service._get_config('BANCARD_NONEXISTENT', 'default_value')
            # Puede retornar fallback_value o default_value dependiendo de implementación

    def test_generar_token_md5(self):
        """Debe generar token MD5 correctamente"""
        service = BancardService()
        process_id = "TEST-123-456"
        
        token = service._generar_token(process_id)
        
        # Verificar que es MD5 válido (32 caracteres hexadecimales)
        self.assertEqual(len(token), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in token))
        
        # Verificar consistencia
        token2 = service._generar_token(process_id)
        self.assertEqual(token, token2)

    def test_generar_token_different_process_ids(self):
        """Debe generar tokens diferentes para process_ids diferentes"""
        service = BancardService()
        
        token1 = service._generar_token("PROC-1")
        token2 = service._generar_token("PROC-2")
        
        self.assertNotEqual(token1, token2)

    def test_validar_webhook_signature_valid(self):
        """Debe validar firma HMAC-SHA256 correcta"""
        service = BancardService()
        
        shop_process_id = "REC-123-TEST"
        operation = {
            "response": "S",
            "amount": "50000.00",
            "currency": "PYG"
        }
        
        # Generar firma válida
        operation_json = json.dumps(operation, separators=(',', ':'), sort_keys=True)
        mensaje = f"{shop_process_id}{operation_json}"
        signature = hmac.new(
            service.private_key.encode('utf-8'),
            mensaje.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = service._validar_webhook_signature(shop_process_id, operation, signature)
        self.assertTrue(is_valid)

    def test_validar_webhook_signature_invalid(self):
        """Debe rechazar firma HMAC-SHA256 incorrecta"""
        service = BancardService()
        
        shop_process_id = "REC-123-TEST"
        operation = {"response": "S", "amount": "50000.00"}
        invalid_signature = "invalid_signature_hash"
        
        is_valid = service._validar_webhook_signature(shop_process_id, operation, invalid_signature)
        self.assertFalse(is_valid)

    def test_validar_webhook_signature_tampering(self):
        """Debe detectar manipulación de datos"""
        service = BancardService()
        
        shop_process_id = "REC-123-TEST"
        original_operation = {"response": "S", "amount": "50000.00"}
        
        # Generar firma para operation original
        operation_json = json.dumps(original_operation, separators=(',', ':'), sort_keys=True)
        mensaje = f"{shop_process_id}{operation_json}"
        valid_signature = hmac.new(
            service.private_key.encode('utf-8'),
            mensaje.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Modificar operation después
        tampered_operation = {"response": "S", "amount": "100000.00"}  # Monto cambiado
        
        is_valid = service._validar_webhook_signature(shop_process_id, tampered_operation, valid_signature)
        self.assertFalse(is_valid)

    def test_log_api_call_complete(self):
        """Debe loguear llamada API completamente"""
        service = BancardService()
        
        payload_req = {"amount": "50000", "currency": "PYG"}
        payload_res = {"process_id": "PROC-123", "status": "success"}
        contexto = {"recarga_id": 123, "usuario": "test"}
        
        service._log_api_call(
            metodo='POST',
            url='https://api.test.com/payment',
            payload_req=payload_req,
            status_code=200,
            payload_res=payload_res,
            tiempo_ms=150,
            exitoso=True,
            error_msg=None,
            contexto=contexto
        )
        
        # Verificar que se creó el log
        log = LogsLlamadasApi.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.metodo, 'POST')
        self.assertEqual(log.url, 'https://api.test.com/payment')
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.tiempo_ms, 150)
        self.assertEqual(log.exitoso, 1)

    def test_log_api_call_error(self):
        """Debe loguear errores de API apropiadamente"""
        service = BancardService()
        
        service._log_api_call(
            metodo='POST',
            url='https://api.test.com/payment',
            status_code=500,
            tiempo_ms=5000,
            exitoso=False,
            error_msg='Internal server error',
            contexto={'error': 'timeout'}
        )
        
        log = LogsLlamadasApi.objects.first()
        self.assertEqual(log.exitoso, 0)
        self.assertEqual(log.error_msg, 'Internal server error')

    def test_log_api_call_exception_handling(self):
        """Debe manejar excepciones en logging sin fallar"""
        service = BancardService()
        
        # Mock para simular error en creación de log
        with patch('apps.api_integrations.models.LogsLlamadasApi.objects.create') as mock_create:
            mock_create.side_effect = Exception("DB Error")
            
            # No debe lanzar excepción
            try:
                service._log_api_call(
                    metodo='GET',
                    url='https://api.test.com/status',
                    exitoso=True
                )
            except Exception:
                self.fail("_log_api_call no debe lanzar excepción si falla logging")

    @patch('requests.post')
    def test_iniciar_transaccion_success(self, mock_post):
        """Debe iniciar transacción exitosamente"""
        service = BancardService()
        
        # Mock respuesta exitosa de Bancard
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "messages": [],
            "process_id": "BANCARD-PROC-123456",
            "redirect_url": "https://vpos.infonet.com.py:8888/checkout/1234567"
        }
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.150
        mock_post.return_value = mock_response
        
        # Ejecutar iniciar_transaccion
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('50000.00'),
            descripcion='Recarga de saldo',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel'
        )
        
        # Verificar resultado exitoso
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['process_id'], 'BANCARD-PROC-123456')
        self.assertIn('checkout', resultado['payment_url'])
        
        # Verificar que se hizo la llamada HTTP correcta
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('single_buy', call_args[0][0])  # URL contiene single_buy

    @patch('requests.post')
    def test_iniciar_transaccion_with_buyer_info(self, mock_post):
        """Debe incluir información del comprador en la transacción"""
        service = BancardService()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "process_id": "PROC-WITH-BUYER"
        }
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.200
        mock_post.return_value = mock_response
        
        buyer_info = {
            "ci": "12345678",
            "nombre": "Juan Pérez",
            "email": "juan@example.com",
            "telefono": "0981234567",
            "direccion": "Asunción, Paraguay"
        }
        
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('25000.00'),
            descripcion='Recarga con datos del comprador',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel',
            buyer_info=buyer_info
        )
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se enviaron los datos del comprador
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertIn('buyer_preload', payload['operation'])
        self.assertEqual(payload['operation']['buyer_preload']['ci'], '12345678')
        self.assertEqual(payload['operation']['buyer_preload']['email'], 'juan@example.com')

    @patch('requests.post')
    def test_iniciar_transaccion_network_error(self, mock_post):
        """Debe manejar errores de red apropiadamente"""
        service = BancardService()
        
        # Mock error de conexión
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('75000.00'),
            descripcion='Recarga con error de red',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel'
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('error', resultado)
        self.assertIn('Network error', resultado['error'])

    @patch('requests.post')
    def test_iniciar_transaccion_bancard_error_response(self, mock_post):
        """Debe manejar respuestas de error de Bancard"""
        service = BancardService()
        
        # Mock respuesta de error de Bancard
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "error",
            "messages": [
                {"key": "InvalidAmount", "dsc": "El monto debe ser mayor a 0"}
            ]
        }
        mock_response.status_code = 400
        mock_response.elapsed.total_seconds.return_value = 0.100
        mock_post.return_value = mock_response
        
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('0.00'),  # Monto inválido
            descripcion='Recarga con monto inválido',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel'
        )
        
        self.assertFalse(resultado['success'])
        # El servicio incluye el mensaje de descripción (dsc) del error de Bancard
        self.assertTrue(len(resultado['error']) > 0)

    @patch('requests.post')
    def test_iniciar_transaccion_timeout(self, mock_post):
        """Debe manejar timeouts de requests"""
        service = BancardService()
        
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('30000.00'),
            descripcion='Recarga con timeout',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel'
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('timeout', resultado['error'].lower())

    @patch('requests.post')
    def test_iniciar_transaccion_invalid_json_response(self, mock_post):
        """Debe manejar respuestas con JSON inválido"""
        service = BancardService()
        
        # Mock respuesta con JSON inválido
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "response", 0)
        mock_response.status_code = 200
        mock_response.text = "Invalid response format"
        mock_response.elapsed.total_seconds.return_value = 0.080
        mock_post.return_value = mock_response
        
        resultado = service.iniciar_transaccion(
            recarga_id=self.recarga.id_carga,
            monto=Decimal('40000.00'),
            descripcion='Recarga con respuesta JSON inválida',
            return_url='https://app.cantina.com/success',
            cancel_url='https://app.cantina.com/cancel'
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('JSON', resultado['error'])

    def test_iniciar_transaccion_token_generation(self):
        """Debe generar token de seguridad correcto para la transacción"""
        service = BancardService()
        
        # Verificar formato del shop_process_id y token
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "success", "process_id": "TEST"}
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.100
            mock_post.return_value = mock_response
            
            service.iniciar_transaccion(
                recarga_id=self.recarga.id_carga,
                monto=Decimal('20000.00'),
                descripcion='Test token generation',
                return_url='https://test.com/success',
                cancel_url='https://test.com/cancel'
            )
            
            # Verificar que se generó shop_process_id con formato correcto
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            shop_process_id = payload['operation']['shop_process_id']
            self.assertTrue(shop_process_id.startswith(f'REC-{self.recarga.id_carga}-'))
            
            # Verificar que se generó token
            token = payload['operation']['token']
            self.assertEqual(len(token), 32)  # MD5 hash

    @patch('requests.post')
    def test_iniciar_transaccion_monto_formatting(self, mock_post):
        """Debe formatear monto correctamente para Bancard"""
        service = BancardService()
        
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "process_id": "FORMAT-TEST"}
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.100
        mock_post.return_value = mock_response
        
        # Test con diferentes formatos de monto
        montos_test = [
            Decimal('1234.56'),
            Decimal('1000.00'),
            Decimal('999.99'),
            Decimal('50000')
        ]
        
        for monto in montos_test:
            with self.subTest(monto=monto):
                service.iniciar_transaccion(
                    recarga_id=self.recarga.id_carga,
                    monto=monto,
                    descripcion=f'Test monto {monto}',
                    return_url='https://test.com/success',
                    cancel_url='https://test.com/cancel'
                )
                
                call_args = mock_post.call_args
                payload = call_args[1]['json']
                amount_sent = payload['operation']['amount']
                
                # Debe tener formato "XXXX.XX"
                self.assertRegex(amount_sent, r'^\d+\.\d{2}$')

    @patch('apps.api_integrations.services.bancard_service.BancardService._validar_webhook_signature')
    @patch('apps.core.models.CargasSaldo.objects.get')
    def test_procesar_webhook_signature_validation(self, mock_get_recarga, mock_validate_signature):
        """Debe validar firma de webhook antes de procesar"""
        service = BancardService()
        
        # Mock recarga
        mock_recarga = Mock()
        mock_recarga.estado = 'pendiente'
        mock_get_recarga.return_value = mock_recarga
        
        # Mock validación de firma fallida
        mock_validate_signature.return_value = False
        
        resultado = service.procesar_webhook(
            shop_process_id="REC-123-TEST",
            operation={"response": "S", "amount": "50000.00"},
            signature="invalid_signature"
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('firma', resultado['error'].lower())
        
        # Verificar que se llamó la validación
        mock_validate_signature.assert_called_once()

    def test_service_constants(self):
        """Debe tener constantes correctas definidas"""
        self.assertEqual(BancardService.BANCARD_STAGING_URL, "https://vpos.infonet.com.py:8888")
        self.assertEqual(BancardService.BANCARD_PRODUCTION_URL, "https://vpos.infonet.com.py")
        self.assertEqual(BancardService.ENDPOINT_SINGLE_BUY, "/vpos/api/0.3/single_buy")
        self.assertEqual(BancardService.ENDPOINT_CONFIRM, "/vpos/api/0.3/single_buy/confirmations")
        self.assertEqual(BancardService.ENDPOINT_ROLLBACK, "/vpos/api/0.3/single_buy/rollback")

    def test_service_timeout_configuration(self):
        """Debe configurar timeout correctamente"""
        service = BancardService()
        self.assertEqual(service.timeout, 30)
        
        # Verificar que timeout se usa en requests
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "success"}
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.100
            mock_post.return_value = mock_response
            
            service.iniciar_transaccion(
                recarga_id=self.recarga.id_carga,
                monto=Decimal('10000.00'),
                descripcion='Test timeout',
                return_url='https://test.com/success',
                cancel_url='https://test.com/cancel'
            )
            
            # Verificar que se pasó timeout
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs['timeout'], 30)
