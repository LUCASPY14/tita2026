"""
Core decorators for Cantina Tita
Authentication and permission decorators
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


def admin_required(view_func):
    """
    Decorator that requires user to be authenticated and have admin privileges
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        if not request.user.is_staff:
            return JsonResponse({"error": "Admin privileges required"}, status=403)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def api_admin_required(view_func):
    """
    Decorator for DRF API views that requires admin privileges
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_staff:
            return Response({"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def staff_required(view_func):
    """
    Decorator that requires user to be staff member
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({"error": "Staff privileges required"}, status=403)

        return view_func(request, *args, **kwargs)

    return _wrapped_view
