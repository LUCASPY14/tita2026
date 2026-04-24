"""
URL Configuration for Cantina Tita Backend
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Cantina Tita API",
        default_version='v1',
        description="""
        ## Sistema de Gestión de Cantina Escolar
        
        API REST completa para la gestión de cantina escolar con los siguientes módulos:
        
        ### 📦 Módulos Disponibles
        - **Ventas:** Gestión de ventas y transacciones
        - **Compras:** Gestión de compras a proveedores
        - **Inventario:** Control de stock y movimientos
        - **Almuerzos:** Planes y suscripciones de almuerzos
        - **Clientes:** Gestión de clientes e hijos
        - **Productos:** Catálogo de productos
        - **Usuarios:** Gestión de empleados y roles
        - **Reportes:** Generación de reportes y estadísticas
        - **Notificaciones:** Sistema de notificaciones
        - **Contabilidad:** Cajas, cierres y documentos tributarios
        
        ### 🔐 Autenticación
        Esta API usa JWT (JSON Web Tokens) para autenticación. 
        
        **Obtener token:**
        ```
        POST /api/auth/login/
        {
            "username": "tu_usuario",
            "password": "tu_contraseña"
        }
        ```
        
        **Usar token:** Incluir en headers: `Authorization: Bearer {token}`
        
        ### 📚 Documentación
        - **Swagger UI:** [/swagger/](/swagger/)
        - **ReDoc:** [/redoc/](/redoc/)
        - **OpenAPI Schema:** [/swagger.json](/swagger.json)
        
        ### 🔗 Links Útiles
        - [GitHub Repository](https://github.com/LUCASPY14/tita2026)
        - [Documentación Completa](https://github.com/LUCASPY14/tita2026/tree/main/docs)
        """,
        terms_of_service="https://www.cantinatita.com/terms/",
        contact=openapi.Contact(
            name="Equipo de Desarrollo",
            email="lucas@cantinatita.com",
            url="https://github.com/LUCASPY14/tita2026"
        ),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

def api_root(request):
    """Root endpoint for the API"""
    return JsonResponse({
        'message': 'Cantina Tita API v1',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/v1/',
            'docs': '/swagger/',
            'redoc': '/redoc/',
            'auth': {
                'login': '/api/auth/login/',
                'refresh': '/api/auth/refresh/',
                'verify': '/api/auth/verify/',
            }
        }
    })

def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include('api.v1.urls')),
    
    # Alias routes for usuarios (used by some tests)
    path('api/usuarios/', include('apps.usuarios.urls')),
    
    # Authentication (JWT)
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Webhooks (sin autenticación JWT)
    path('api/webhooks/bancard/', include('apps.api_integrations.urls'), name='webhook_bancard'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development/Docker
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
