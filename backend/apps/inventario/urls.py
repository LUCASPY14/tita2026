from django.urls import include, path  # pragma: no cover

from rest_framework.routers import DefaultRouter  # pragma: no cover

router = DefaultRouter()  # pragma: no cover

urlpatterns = [  # pragma: no cover
    path("", include(router.urls)),
]
