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
        description="API REST para el sistema de gestión de cantina escolar",
        terms_of_service="https://www.cantinatita.com/terms/",
        contact=openapi.Contact(email="lucas@cantinatita.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
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

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include('api.v1.urls')),
    
    # Authentication (JWT)
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
