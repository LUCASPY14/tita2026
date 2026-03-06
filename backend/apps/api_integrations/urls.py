"""
URLs de la app api_integrations
Webhooks de servicios externos
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import bancard_webhook, webhook_test

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("", bancard_webhook, name="bancard_webhook"),
    path("test/", webhook_test, name="webhook_test"),
]
