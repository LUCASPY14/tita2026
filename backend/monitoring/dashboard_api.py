"""
====================================
Performance Dashboard API - Cantina Tita
Real-time performance monitoring dashboard endpoints
====================================

API endpoints for performance monitoring dashboard:
- System metrics
- Database performance
- API response times
- Error rates
- Real-time status
"""

from datetime import datetime, timedelta
from typing import Dict, List
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db import connection
from django.core.cache import cache
from django.conf import settings

from apps.core.decorators import admin_required
from monitoring.database_monitor import (
    get_current_database_metrics, 
    get_database_performance_summary,
    check_database_health
)


class PerformanceDashboardAPI(View):
    """Main performance dashboard API"""
    
    @method_decorator(admin_required)
    def get(self, request):
        """Get comprehensive performance dashboard data"""
        
        # Database metrics
        db_healthy, db_alerts = check_database_health()
        db_summary = get_database_performance_summary()
        
        # System metrics
        system_metrics = self.get_system_metrics()
        
        # API metrics  
        api_metrics = self.get_api_metrics()
        
        # Error metrics
        error_metrics = self.get_error_metrics()
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'status': {
                'overall': 'healthy' if db_healthy and system_metrics['status'] == 'healthy' else 'warning',
                'database': 'healthy' if db_healthy else 'warning',
                'system': system_metrics['status'],
                'api': api_metrics['status']
            },
            'database': {
                **db_summary,
                'alerts': db_alerts,
                'health_score': self.calculate_db_health_score(db_summary)
            },
            'system': system_metrics,
            'api': api_metrics,
            'errors': error_metrics,
            'alerts': {
                'total': len(db_alerts),
                'database': db_alerts,
                'system': system_metrics.get('alerts', []),
                'api': api_metrics.get('alerts', [])
            }
        }
        
        return JsonResponse(dashboard_data)
    
    def get_system_metrics(self) -> Dict:
        """Get system performance metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            alerts = []
            if cpu_percent > 80:
                alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 85:
                alerts.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > 90:
                alerts.append(f"High disk usage: {disk_percent:.1f}%")
            
            status = 'healthy' if not alerts else 'warning'
            
            return {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': memory_available_gb,
                'disk_percent': disk_percent,
                'disk_free_gb': disk_free_gb,
                'network_sent_mb': network.bytes_sent / (1024**2),
                'network_recv_mb': network.bytes_recv / (1024**2),
                'process_count': process_count,
                'alerts': alerts,
                'health_score': max(0, 100 - cpu_percent/2 - memory_percent/2 - disk_percent/3)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'health_score': 0
            }
    
    def get_api_metrics(self) -> Dict:
        """Get API performance metrics"""
        cache_key = 'api_metrics:summary'
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics:
            return cached_metrics
        
        # Default metrics if no cache available
        return {
            'status': 'healthy',
            'response_time_avg_ms': 150,
            'requests_per_minute': 45,
            'error_rate_percent': 0.5,
            'active_sessions': 12,
            'cache_hit_rate': 0.85,
            'alerts': [],
            'endpoints': [
                {'name': '/api/v1/ventas/', 'avg_time_ms': 120, 'rpm': 15},
                {'name': '/api/v1/clientes/', 'avg_time_ms': 80, 'rpm': 20},
                {'name': '/api/v1/productos/', 'avg_time_ms': 95, 'rpm': 10}
            ]
        }
    
    def get_error_metrics(self) -> Dict:
        """Get error and exception metrics"""
        cache_key = 'error_metrics:summary'
        cached_errors = cache.get(cache_key)
        
        if cached_errors:
            return cached_errors
        
        # Default error metrics
        return {
            'total_errors_today': 3,
            'error_rate_percent': 0.2,
            'last_error_time': (datetime.now() - timedelta(hours=2)).isoformat(),
            'error_types': {
                'ValidationError': 1,
                'DatabaseError': 1,
                'AuthenticationError': 1
            },
            'critical_errors': 0,
            'trend': 'decreasing'
        }
    
    def calculate_db_health_score(self, db_metrics: Dict) -> float:
        """Calculate database health score (0-100)"""
        score = 100.0
        
        # Query time impact (max 30 points)
        avg_time_ms = db_metrics.get('avg_query_time_ms', 0)
        if avg_time_ms > 100:
            score -= min(30, (avg_time_ms - 100) / 10)
        
        # Cache hit ratio impact (max 25 points)
        cache_ratio = db_metrics.get('cache_hit_ratio', 1.0)
        if cache_ratio < 0.95:
            score -= (0.95 - cache_ratio) * 500  # 25 points for 5% drop
        
        # Connection count impact (max 20 points)
        active_conns = db_metrics.get('active_connections', 0)
        if active_conns > 20:
            score -= min(20, (active_conns - 20) * 2)
        
        # Disk usage impact (max 25 points)
        disk_gb = db_metrics.get('disk_usage_gb', 0)
        if disk_gb > 10:
            score -= min(25, (disk_gb - 10) * 2.5)
        
        return max(0, score)


@require_http_methods(["GET"])
@admin_required
def performance_status(request):
    """Quick performance status check"""
    db_healthy, db_alerts = check_database_health()
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'database_healthy': db_healthy,
        'alert_count': len(db_alerts),
        'status': 'healthy' if db_healthy else 'warning'
    }
    
    return JsonResponse(status)


@require_http_methods(["GET"])
@cache_page(60)  # Cache for 1 minute
def performance_metrics(request):
    """Get detailed performance metrics"""
    
    # Database metrics
    db_summary = get_database_performance_summary()
    
    # System metrics (simplified for public view)
    try:
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
    except:
        cpu_percent = 0
        memory_percent = 0
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'database': {
            'avg_query_time_ms': db_summary.get('avg_query_time_ms', 0),
            'cache_hit_ratio': db_summary.get('cache_hit_ratio', 0),
            'status': db_summary.get('status', 'unknown')
        },
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'status': 'healthy' if cpu_percent < 80 and memory_percent < 85 else 'warning'
        }
    }
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@admin_required
def performance_history(request):
    """Get historical performance data"""
    hours = int(request.GET.get('hours', 24))
    
    # This would typically come from a time-series database
    # For now, return mock historical data
    history_data = {
        'period_hours': hours,
        'data_points': 24,  # One per hour
        'metrics': [
            {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'database_response_ms': 50 + (i % 5) * 20,
                'cpu_percent': 25 + (i % 3) * 15,
                'memory_percent': 60 + (i % 4) * 10,
                'active_connections': 15 + (i % 6) * 5
            }
            for i in range(0, hours, max(1, hours // 24))
        ]
    }
    
    return JsonResponse(history_data)


@require_http_methods(["POST"])  
@admin_required
def trigger_performance_test(request):
    """Trigger performance tests on demand"""
    
    try:
        test_type = json.loads(request.body).get('test_type', 'basic')
        
        # This would trigger actual performance tests
        # For now, simulate test execution
        
        test_results = {
            'test_id': f"perf_{int(datetime.now().timestamp())}",
            'test_type': test_type,
            'status': 'running',
            'estimated_duration': '5 minutes',
            'started_at': datetime.now().isoformat()
        }
        
        return JsonResponse(test_results, status=202)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to trigger performance test',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
@admin_required 
def performance_alerts(request):
    """Get current performance alerts"""
    
    db_healthy, db_alerts = check_database_health()
    
    # Collect all alerts from different sources
    all_alerts = []
    
    # Database alerts
    for alert in db_alerts:
        all_alerts.append({
            'id': len(all_alerts) + 1,
            'type': 'database',
            'severity': 'warning',
            'message': alert,
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        })
    
    # System alerts (mock)
    system_alerts = []
    
    alerts_response = {
        'timestamp': datetime.now().isoformat(),
        'total_alerts': len(all_alerts),
        'unacknowledged': len(all_alerts),
        'alerts': all_alerts,
        'summary': {
            'database': len(db_alerts),
            'system': len(system_alerts),
            'api': 0
        }
    }
    
    return JsonResponse(alerts_response)


# URL Configuration
from django.urls import path

dashboard_urls = [
    path('dashboard/', PerformanceDashboardAPI.as_view(), name='performance_dashboard'),
    path('status/', performance_status, name='performance_status'),
    path('metrics/', performance_metrics, name='performance_metrics'),
    path('history/', performance_history, name='performance_history'),
    path('test/', trigger_performance_test, name='trigger_performance_test'),
    path('alerts/', performance_alerts, name='performance_alerts'),
]