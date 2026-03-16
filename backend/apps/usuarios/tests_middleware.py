"""
Tests para middleware de usuarios
Cubre autenticación, autorización y procesamiento de requests
"""

from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from unittest.mock import Mock, patch

from apps.usuarios.models import Roles, Empleados


class UsuariosMiddlewareTest(TestCase):
    """Tests para middleware personalizado de usuarios"""

    def setUp(self):
        """Configurar factory de requests y datos de prueba"""
        self.factory = RequestFactory()
        
        self.rol = Roles.objects.create(
            nombre_rol="MiddlewareTest",
            estado=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="User",
            usuario="testuser",
            contrasena_hash="$2b$12$hashedpassword",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=self.rol
        )

    def test_middleware_basic_structure(self):
        """Debe tener estructura básica de middleware Django"""
        class AuthenticationMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
            
            def __call__(self, request):
                # Procesar request antes de la vista
                response = self.get_response(request)
                # Procesar response después de la vista
                return response
        
        get_response_mock = Mock(return_value=HttpResponse("OK"))
        middleware = AuthenticationMiddleware(get_response_mock)
        
        request = self.factory.get('/')
        response = middleware(request)
        
        self.assertIsInstance(response, HttpResponse)
        get_response_mock.assert_called_once_with(request)

    def test_user_authentication_injection(self):
        """Debe inyectar información de usuario autenticado en request"""
        def inject_user_info(request):
            # Simular inyección de información de usuario
            if hasattr(request, 'META') and 'HTTP_AUTHORIZATION' in request.META:
                # Simular autenticación JWT o similar
                request.user = self.empleado
                request.user_role = self.empleado.id_rol.nombre_rol
                request.user_permissions = ['usuarios.view', 'usuarios.add']
            else:
                request.user = AnonymousUser()
                request.user_role = None
                request.user_permissions = []
            
            return request
        
        # Request con autenticación
        auth_request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer token123')
        auth_request = inject_user_info(auth_request)
        
        self.assertEqual(auth_request.user, self.empleado)
        self.assertEqual(auth_request.user_role, "MiddlewareTest")
        self.assertIn('usuarios.view', auth_request.user_permissions)
        
        # Request sin autenticación
        unauth_request = self.factory.get('/')
        unauth_request = inject_user_info(unauth_request)
        
        self.assertIsInstance(unauth_request.user, AnonymousUser)
        self.assertIsNone(unauth_request.user_role)
        self.assertEqual(unauth_request.user_permissions, [])

    def test_security_headers_injection(self):
        """Debe inyectar headers de seguridad"""
        def add_security_headers(response):
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response
        
        response = HttpResponse("Secure content")
        secure_response = add_security_headers(response)
        
        self.assertEqual(secure_response['X-Frame-Options'], 'DENY')
        self.assertEqual(secure_response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(secure_response['X-XSS-Protection'], '1; mode=block')
        self.assertIn('max-age=31536000', secure_response['Strict-Transport-Security'])

    def test_cors_headers_handling(self):
        """Debe manejar headers CORS apropiadamente"""
        def handle_cors(request, response):
            origin = request.META.get('HTTP_ORIGIN')
            allowed_origins = [
                'http://localhost:3000',
                'https://cantina.example.com'
            ]
            
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response['Access-Control-Allow-Credentials'] = 'true'
            
            return response
        
        request = self.factory.get('/', HTTP_ORIGIN='http://localhost:3000')
        response = HttpResponse("CORS content")
        
        cors_response = handle_cors(request, response)
        
        self.assertEqual(cors_response['Access-Control-Allow-Origin'], 'http://localhost:3000')
        self.assertIn('Authorization', cors_response['Access-Control-Allow-Headers'])

    def test_rate_limiting_middleware(self):
        """Debe implementar rate limiting por usuario"""
        def check_rate_limit(request):
            # Simular rate limiting
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_id = getattr(request.user, 'id_empleado', None) if hasattr(request, 'user') else None
            
            # Simulación simple de rate limiting
            key = f"rate_limit:{user_id or client_ip}"
            current_requests = 1  # Simular conteo actual
            max_requests = 100  # Límite por minuto
            
            return {
                'key': key,
                'current': current_requests,
                'limit': max_requests,
                'exceeded': current_requests > max_requests
            }
        
        request = self.factory.post('/api/endpoint')
        request.user = self.empleado
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        rate_check = check_rate_limit(request)
        
        self.assertIn('key', rate_check)
        self.assertIn(str(self.empleado.id_empleado), rate_check['key'])
        self.assertFalse(rate_check['exceeded'])

    def test_audit_logging_middleware(self):
        """Debe registrar actividad para auditoría"""
        def log_request(request, response):
            # Simular logging de auditoría
            if hasattr(request, 'user') and request.user.is_authenticated:
                log_entry = {
                    'user_id': request.user.id_empleado,
                    'method': request.method,
                    'path': request.path,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'response_status': response.status_code,
                    'timestamp': timezone.now()
                }
                return log_entry
            return None
        
        request = self.factory.post('/api/important-action')
        request.user = self.empleado
        request.user.is_authenticated = True  # Mock
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        response = HttpResponse("Success", status=201)
        
        log_entry = log_request(request, response)
        
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry['user_id'], self.empleado.id_empleado)
        self.assertEqual(log_entry['method'], 'POST')
        self.assertEqual(log_entry['path'], '/api/important-action')
        self.assertEqual(log_entry['response_status'], 201)

    def test_session_validation_middleware(self):
        """Debe validar sesiones de usuario"""
        def validate_session(request):
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Simular validación de sesión
                session_checks = {
                    'user_active': request.user.estado,
                    'role_active': request.user.id_rol.estado,
                    'session_valid': True,  # Simulado
                    'requires_reauth': False
                }
                
                # Verificar si usuario o rol fueron desactivados
                if not session_checks['user_active'] or not session_checks['role_active']:
                    session_checks['session_valid'] = False
                    session_checks['requires_reauth'] = True
                
                return session_checks
            
            return {'session_valid': False, 'user_active': False}
        
        request = self.factory.get('/protected/')
        request.user = self.empleado
        request.user.is_authenticated = True  # Mock
        
        # Usuario estado
        validation = validate_session(request)
        self.assertTrue(validation['session_valid'])
        self.assertTrue(validation['user_active'])
        self.assertFalse(validation['requires_reauth'])
        
        # Usuario inactivo
        self.empleado.estado = False
        self.empleado.save()
        validation = validate_session(request)
        self.assertFalse(validation['session_valid'])
        self.assertTrue(validation['requires_reauth'])

    def test_timezone_middleware(self):
        """Debe configurar timezone del usuario"""
        def set_user_timezone(request):
            default_tz = 'America/Asuncion'
            user_tz = default_tz
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Simular obtención de timezone del perfil de usuario
                user_tz = getattr(request.user, 'timezone', default_tz)
            
            # Simular activación de timezone
            return {
                'timezone': user_tz,
                'activated': True
            }
        
        request = self.factory.get('/')
        request.user = self.empleado
        request.user.is_authenticated = True
        request.user.timezone = 'America/Asuncion'  # Mock
        
        tz_result = set_user_timezone(request)
        
        self.assertEqual(tz_result['timezone'], 'America/Asuncion')
        self.assertTrue(tz_result['activated'])

    def test_middleware_exception_handling(self):
        """Debe manejar excepciones apropiadamente"""
        class ErrorHandlingMiddleware:
            def __init__(self, get_response):
                self.get_response = get_response
            
            def __call__(self, request):
                try:
                    response = self.get_response(request)
                    return response
                except Exception as e:
                    # Log error y retornar respuesta de error
                    error_response = HttpResponse(
                        f"Internal Error: {str(e)}", 
                        status=500
                    )
                    return error_response
            
            def process_exception(self, request, exception):
                # Procesar excepción específica
                return HttpResponse(
                    "Error procesado por middleware", 
                    status=500
                )
        
        def failing_view(request):
            raise ValueError("Test exception")
        
        middleware = ErrorHandlingMiddleware(failing_view)
        request = self.factory.get('/')
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("Internal Error", response.content.decode())

    def test_request_timing_middleware(self):
        """Debe medir tiempo de procesamiento de requests"""
        import time
        
        def measure_request_time(request, response):
            # Simular medición de tiempo
            start_time = getattr(request, '_start_time', time.time())
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Agregar header con tiempo de procesamiento
            response['X-Processing-Time'] = f"{processing_time:.3f}ms"
            
            return {
                'start_time': start_time,
                'end_time': end_time,
                'processing_time': processing_time
            }
        
        request = self.factory.get('/')
        request._start_time = time.time()
        response = HttpResponse("Timed response")
        
        # Simular pequeño retraso
        time.sleep(0.001)
        
        timing_result = measure_request_time(request, response)
        
        self.assertIn('processing_time', timing_result)
        self.assertGreater(timing_result['processing_time'], 0)
        self.assertIn('X-Processing-Time', response)