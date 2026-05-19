from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from apps.usuarios.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


# Health check
def health_check(request):
    return JsonResponse({"status": "ok", "version": "1.0"})


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('api/health/', health_check, name='health-check'),

    # OpenAPI / Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT Auth
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Apps API
    path('api/almuerzos/', include('apps.almuerzos.urls')),
    path('api/ventas/', include('apps.ventas.urls')),
    path('api/compras/', include('apps.compras.urls')),
    path('api/clientes/', include('apps.clientes.urls')),
    path('api/productos/', include('apps.productos.urls')),
    path('api/inventario/', include('apps.inventario.urls')),
    path('api/core/', include('apps.core.urls')),
    path('api/contabilidad/', include('apps.contabilidad.urls')),
    path('api/usuarios/', include('apps.usuarios.urls')),
    path('api/notificaciones/', include('apps.notificaciones.urls')),
    path('api/integrations/', include('apps.api_integrations.urls')),
]

if settings.DEBUG:
    # Servir archivos estáticos desde STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir archivos media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)