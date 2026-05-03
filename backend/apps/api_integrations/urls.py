"""
URLs de la app api_integrations
Webhooks de servicios externos
"""

from django.urls import path

from .views import bancard_webhook, webhook_test

urlpatterns = [
    path("", bancard_webhook, name="bancard_webhook"),
    path("test/", webhook_test, name="webhook_test"),
]
