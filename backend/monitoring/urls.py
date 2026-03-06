"""
====================================
Performance Monitoring URLs - Cantina Tita
URL configuration for performance monitoring system
====================================
"""

from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from .dashboard_api import (
    PerformanceDashboardAPI,
    performance_status,
    performance_metrics,
    performance_history,
    trigger_performance_test,
    performance_alerts
)

app_name = 'monitoring'

urlpatterns = [
    # Dashboard view
    path(
        '', 
        login_required(TemplateView.as_view(template_name='monitoring/dashboard.html')),
        name='dashboard_view'
    ),
    
    # API endpoints
    path('dashboard/', PerformanceDashboardAPI.as_view(), name='dashboard_api'),
    path('status/', performance_status, name='status'),
    path('metrics/', performance_metrics, name='metrics'),
    path('history/', performance_history, name='history'),
    path('test/', trigger_performance_test, name='trigger_test'),
    path('alerts/', performance_alerts, name='alerts'),
]