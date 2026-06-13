"""Tests for apps.notificaciones.routing — WebSocket URL configuration."""


def test_websocket_urlpatterns_has_one_entry():
    from apps.notificaciones.routing import websocket_urlpatterns
    assert len(websocket_urlpatterns) == 1


def test_websocket_urlpattern_callback_is_callable():
    from apps.notificaciones.routing import websocket_urlpatterns
    pattern = websocket_urlpatterns[0]
    assert callable(pattern.callback)
