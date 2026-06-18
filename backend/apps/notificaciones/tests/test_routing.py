"""Tests for apps.notificaciones.routing — WebSocket URL configuration."""


def test_websocket_urlpatterns_count():
    from apps.notificaciones.routing import websocket_urlpatterns
    # notificaciones + dashboard
    assert len(websocket_urlpatterns) == 2


def test_websocket_urlpattern_callbacks_are_callable():
    from apps.notificaciones.routing import websocket_urlpatterns
    for pattern in websocket_urlpatterns:
        assert callable(pattern.callback)
