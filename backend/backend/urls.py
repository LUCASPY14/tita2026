from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


# Health check
def health_check(request):
    return JsonResponse({"status": "ok", "version": "1.0"})


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('api/health/', health_check, name='health-check'),

    # JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

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
    path('api/reportes/', include('apps.reportes.urls')),
]

if settings.DEBUG:
    # Servir archivos estáticos desde STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir archivos media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)