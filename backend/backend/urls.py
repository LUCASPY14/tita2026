from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection, OperationalError as DBError
from django.http import JsonResponse
from django.urls import include, path
from apps.usuarios.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def health_check(request):
    checks = {}
    ok = True

    # Database
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        checks["db"] = "ok"
    except DBError as exc:
        checks["db"] = str(exc)
        ok = False

    # Redis
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = str(exc)
        ok = False

    status = "ok" if ok else "degraded"
    return JsonResponse({"status": status, "version": "1.0", "checks": checks},
                        status=200 if ok else 503)


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('api/health/', health_check, name='health-check'),

    # Prometheus metrics (protegido por IP en producción via Nginx)
    path('', include('django_prometheus.urls')),

    # OpenAPI / Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT Auth
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Apps API v1
    path('api/v1/almuerzos/', include('apps.almuerzos.urls')),
    path('api/v1/ventas/', include('apps.ventas.urls')),
    path('api/v1/compras/', include('apps.compras.urls')),
    path('api/v1/clientes/', include('apps.clientes.urls')),
    path('api/v1/productos/', include('apps.productos.urls')),
    path('api/v1/inventario/', include('apps.inventario.urls')),
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/contabilidad/', include('apps.contabilidad.urls')),
    path('api/v1/usuarios/', include('apps.usuarios.urls')),
    path('api/v1/notificaciones/', include('apps.notificaciones.urls')),
    path('api/v1/integrations/', include('apps.api_integrations.urls')),
]

if settings.DEBUG:
    # Servir archivos estáticos desde STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir archivos media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)