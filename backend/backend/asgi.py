import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")

django_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402 (must come after Django setup)
import apps.notificaciones.routing as notif_routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": URLRouter(notif_routing.websocket_urlpatterns),
})
