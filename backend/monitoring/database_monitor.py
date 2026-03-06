"""
====================================
Database Monitoring Configuration - Cantina Tita
Production database performance monitoring and alerting
====================================

Monitoring configuration for:
- Database connection pool
- Query performance
- Lock monitoring
- Index usage
- Storage monitoring
- Automated alerts
"""

import logging
import time
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import connections, connection
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

import psycopg2
from psycopg2.extras import RealDictCursor


logger = logging.getLogger(__name__)


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    timestamp: datetime
    active_connections: int
    idle_connections: int
    query_count: int
    avg_query_time: float
    slow_queries: int
    lock_waits: int
    cache_hit_ratio: float
    disk_usage_gb: float
    cpu_usage_percent: float
    memory_usage_gb: float


class DatabaseMonitor:
    """Production database monitoring system"""
    
    def __init__(self, db_alias='default'):
        self.db_alias = db_alias
        self.connection = connections[db_alias]
        self.thresholds = {
            'max_active_connections': 80,
            'max_avg_query_time': 0.1,  # 100ms
            'max_slow_queries': 10,
            'min_cache_hit_ratio': 0.95,  # 95%
            'max_disk_usage_gb': 50,
            'max_cpu_usage': 80,
            'max_memory_usage_gb': 4
        }
        
        # Cache keys for storing metrics
        self.cache_prefix = 'db_monitor'
        self.metrics_cache_timeout = 300  # 5 minutes
    
    def get_connection_pool_stats(self) -> Dict:
        """Get database connection pool statistics"""
        try:
            with self.connection.cursor() as cursor:
                # PostgreSQL connection stats
                cursor.execute("""
                    SELECT 
                        state,
                        COUNT(*) as count
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                    GROUP BY state;
                """)
                
                results = cursor.fetchall()
                
                connection_stats = {
                    'active': 0,
                    'idle': 0,
                    'idle_in_transaction': 0,
                    'total': 0
                }
                
                for state, count in results:
                    if state == 'active':
                        connection_stats['active'] = count
                    elif state == 'idle':
                        connection_stats['idle'] = count
                    elif state == 'idle in transaction':
                        connection_stats['idle_in_transaction'] = count
                    
                    connection_stats['total'] += count
                
                return connection_stats
                
        except Exception as e:
            logger.error(f"Error getting connection pool stats: {e}")
            return {}
    
    def get_query_performance_stats(self) -> Dict:
        """Get query performance statistics"""
        try:
            with self.connection.cursor() as cursor:
                # Query performance stats (requires pg_stat_statements extension)
                cursor.execute("""
                    SELECT 
                        COUNT(*) as query_count,
                        AVG(mean_time) as avg_time,
                        COUNT(*) FILTER (WHERE mean_time > 100) as slow_queries,
                        MAX(mean_time) as max_time
                    FROM pg_stat_statements 
                    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
                    AND calls > 0;
                """)
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'query_count': result[0] or 0,
                        'avg_query_time': result[1] or 0,
                        'slow_queries': result[2] or 0,
                        'max_query_time': result[3] or 0
                    }
                
        except Exception as e:
            logger.warning(f"pg_stat_statements not available: {e}")
            
        # Fallback to Django query log
        return self._get_django_query_stats()
    
    def _get_django_query_stats(self) -> Dict:
        """Fallback query stats from Django connection"""
        queries = getattr(connection, 'queries', [])
        
        if not queries:
            return {
                'query_count': 0,
                'avg_query_time': 0,
                'slow_queries': 0,
                'max_query_time': 0
            }
        
        query_times = [float(q.get('time', 0)) for q in queries]
        avg_time = sum(query_times) / len(query_times) if query_times else 0
        slow_queries = len([t for t in query_times if t > 0.1])
        max_time = max(query_times) if query_times else 0
        
        return {
            'query_count': len(queries),
            'avg_query_time': avg_time,
            'slow_queries': slow_queries,
            'max_query_time': max_time
        }
    
    def get_lock_stats(self) -> Dict:
        """Get database lock statistics"""
        try:
            with self.connection.cursor() as cursor:
                # Lock waits and conflicts
                cursor.execute("""
                    SELECT 
                        mode,
                        COUNT(*) as count
                    FROM pg_locks 
                    WHERE NOT granted
                    GROUP BY mode;
                """)
                
                results = cursor.fetchall()
                
                lock_stats = {
                    'total_lock_waits': sum(count for _, count in results),
                    'lock_types': dict(results)
                }
                
                # Blocking queries
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM pg_stat_activity
                    WHERE state = 'active' 
                    AND wait_event_type = 'Lock';
                """)
                
                blocked_queries = cursor.fetchone()[0] or 0
                lock_stats['blocked_queries'] = blocked_queries
                
                return lock_stats
                
        except Exception as e:
            logger.error(f"Error getting lock stats: {e}")
            return {'total_lock_waits': 0, 'blocked_queries': 0}
    
    def get_cache_hit_ratio(self) -> float:
        """Get database cache hit ratio"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        SUM(heap_blks_hit) / (SUM(heap_blks_hit) + SUM(heap_blks_read)) as hit_ratio
                    FROM pg_statio_user_tables
                    WHERE heap_blks_hit + heap_blks_read > 0;
                """)
                
                result = cursor.fetchone()
                return float(result[0]) if result and result[0] else 0.0
                
        except Exception as e:
            logger.error(f"Error getting cache hit ratio: {e}")
            return 0.0
    
    def get_disk_usage(self) -> float:
        """Get database disk usage in GB"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes;
                """)
                
                result = cursor.fetchone()
                if result:
                    size_bytes = result[1]
                    return size_bytes / (1024**3)  # Convert to GB
                
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            
        return 0.0
    
    def get_system_resources(self) -> Dict:
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_gb': memory_used_gb,
                'memory_available_gb': memory.available / (1024**3)
            }
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {
                'cpu_usage_percent': 0,
                'memory_usage_gb': 0,
                'memory_available_gb': 0
            }
    
    def collect_metrics(self) -> DatabaseMetrics:
        """Collect all database metrics"""
        timestamp = datetime.now()
        
        # Get all metrics
        connection_stats = self.get_connection_pool_stats()
        query_stats = self.get_query_performance_stats()
        lock_stats = self.get_lock_stats()
        cache_hit_ratio = self.get_cache_hit_ratio()
        disk_usage = self.get_disk_usage()
        system_stats = self.get_system_resources()
        
        metrics = DatabaseMetrics(
            timestamp=timestamp,
            active_connections=connection_stats.get('active', 0),
            idle_connections=connection_stats.get('idle', 0),
            query_count=query_stats.get('query_count', 0),
            avg_query_time=query_stats.get('avg_query_time', 0),
            slow_queries=query_stats.get('slow_queries', 0),
            lock_waits=lock_stats.get('total_lock_waits', 0),
            cache_hit_ratio=cache_hit_ratio,
            disk_usage_gb=disk_usage,
            cpu_usage_percent=system_stats.get('cpu_usage_percent', 0),
            memory_usage_gb=system_stats.get('memory_usage_gb', 0)
        )
        
        # Cache metrics
        cache_key = f"{self.cache_prefix}:latest_metrics"
        cache.set(cache_key, metrics, self.metrics_cache_timeout)
        
        return metrics
    
    def check_thresholds(self, metrics: DatabaseMetrics) -> List[str]:
        """Check metrics against thresholds and return alerts"""
        alerts = []
        
        if metrics.active_connections > self.thresholds['max_active_connections']:
            alerts.append(
                f"High active connections: {metrics.active_connections} "
                f"(threshold: {self.thresholds['max_active_connections']})"
            )
        
        if metrics.avg_query_time > self.thresholds['max_avg_query_time']:
            alerts.append(
                f"High average query time: {metrics.avg_query_time:.3f}s "
                f"(threshold: {self.thresholds['max_avg_query_time']}s)"
            )
        
        if metrics.slow_queries > self.thresholds['max_slow_queries']:
            alerts.append(
                f"Too many slow queries: {metrics.slow_queries} "
                f"(threshold: {self.thresholds['max_slow_queries']})"
            )
        
        if metrics.cache_hit_ratio < self.thresholds['min_cache_hit_ratio']:
            alerts.append(
                f"Low cache hit ratio: {metrics.cache_hit_ratio:.2%} "
                f"(threshold: {self.thresholds['min_cache_hit_ratio']:.2%})"
            )
        
        if metrics.disk_usage_gb > self.thresholds['max_disk_usage_gb']:
            alerts.append(
                f"High disk usage: {metrics.disk_usage_gb:.1f}GB "
                f"(threshold: {self.thresholds['max_disk_usage_gb']}GB)"
            )
        
        if metrics.cpu_usage_percent > self.thresholds['max_cpu_usage']:
            alerts.append(
                f"High CPU usage: {metrics.cpu_usage_percent:.1f}% "
                f"(threshold: {self.thresholds['max_cpu_usage']}%)"
            )
        
        if metrics.memory_usage_gb > self.thresholds['max_memory_usage_gb']:
            alerts.append(
                f"High memory usage: {metrics.memory_usage_gb:.1f}GB "
                f"(threshold: {self.thresholds['max_memory_usage_gb']}GB)"
            )
        
        return alerts
    
    def send_alert_email(self, alerts: List[str], metrics: DatabaseMetrics):
        """Send alert email for threshold violations"""
        if not alerts:
            return
        
        subject = f"Database Alert - Cantina Tita {settings.ENVIRONMENT}"
        
        message = f"""
Database performance alert detected at {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

ALERTS:
{chr(10).join(f'- {alert}' for alert in alerts)}

CURRENT METRICS:
- Active connections: {metrics.active_connections}
- Average query time: {metrics.avg_query_time:.3f}s
- Slow queries: {metrics.slow_queries}
- Cache hit ratio: {metrics.cache_hit_ratio:.2%}
- Disk usage: {metrics.disk_usage_gb:.1f}GB
- CPU usage: {metrics.cpu_usage_percent:.1f}%
- Memory usage: {metrics.memory_usage_gb:.1f}GB

Please investigate and take appropriate action.

Cantina Tita Monitoring System
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=getattr(settings, 'MONITORING_EMAIL_RECIPIENTS', []),
                fail_silently=False
            )
            logger.info(f"Alert email sent for {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def get_metrics_history(self, hours: int = 24) -> List[DatabaseMetrics]:
        """Get historical metrics from cache"""
        history_key = f"{self.cache_prefix}:history"
        history = cache.get(history_key, [])
        
        # Filter to requested time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_history = [
            m for m in history 
            if isinstance(m, DatabaseMetrics) and m.timestamp >= cutoff_time
        ]
        
        return filtered_history
    
    def store_metrics_history(self, metrics: DatabaseMetrics):
        """Store metrics in history cache"""
        history_key = f"{self.cache_prefix}:history"
        history = cache.get(history_key, [])
        
        # Add new metrics
        history.append(metrics)
        
        # Keep only last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        history = [
            m for m in history 
            if isinstance(m, DatabaseMetrics) and m.timestamp >= cutoff_time
        ]
        
        # Store back in cache (1 day timeout)
        cache.set(history_key, history, timeout=86400)
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        current_metrics = self.collect_metrics()
        history = self.get_metrics_history(hours=24)
        
        if not history:
            history = [current_metrics]
        
        # Calculate averages
        avg_connections = sum(m.active_connections for m in history) / len(history)
        avg_query_time = sum(m.avg_query_time for m in history) / len(history)
        avg_cache_hit = sum(m.cache_hit_ratio for m in history) / len(history)
        
        report = f"""
DATABASE PERFORMANCE REPORT
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Time Range: Last {len(history)} measurements (24h max)

CURRENT STATUS:
- Active connections: {current_metrics.active_connections}
- Idle connections: {current_metrics.idle_connections}
- Query count: {current_metrics.query_count}
- Avg query time: {current_metrics.avg_query_time:.3f}s
- Slow queries: {current_metrics.slow_queries}
- Lock waits: {current_metrics.lock_waits}
- Cache hit ratio: {current_metrics.cache_hit_ratio:.2%}
- Disk usage: {current_metrics.disk_usage_gb:.1f}GB
- CPU usage: {current_metrics.cpu_usage_percent:.1f}%
- Memory usage: {current_metrics.memory_usage_gb:.1f}GB

24-HOUR AVERAGES:
- Avg active connections: {avg_connections:.1f}
- Avg query time: {avg_query_time:.3f}s
- Avg cache hit ratio: {avg_cache_hit:.2%}

THRESHOLD STATUS:
"""
        
        alerts = self.check_thresholds(current_metrics)
        if alerts:
            report += "⚠️  ALERTS:\n"
            for alert in alerts:
                report += f"   - {alert}\n"
        else:
            report += "✅ All metrics within thresholds\n"
        
        report += f"\nNext check: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}\n"
        
        return report


class Command(BaseCommand):
    """Django management command for database monitoring"""
    
    help = "Monitor database performance and send alerts"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run in daemon mode with continuous monitoring'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,
            help='Monitoring interval in seconds (default: 300)'
        )
        parser.add_argument(
            '--report',
            action='store_true',
            help='Generate and display performance report'
        )
    
    def handle(self, *args, **options):
        monitor = DatabaseMonitor()
        
        if options['report']:
            report = monitor.generate_performance_report()
            self.stdout.write(report)
            return
        
        if options['daemon']:
            self.stdout.write("Starting database monitoring daemon...")
            self.run_daemon(monitor, options['interval'])
        else:
            self.run_single_check(monitor)
    
    def run_single_check(self, monitor: DatabaseMonitor):
        """Run a single monitoring check"""
        metrics = monitor.collect_metrics()
        monitor.store_metrics_history(metrics)
        
        alerts = monitor.check_thresholds(metrics)
        
        if alerts:
            self.stdout.write(
                self.style.WARNING(f"Database alerts detected: {len(alerts)}")
            )
            for alert in alerts:
                self.stdout.write(f"  - {alert}")
            
            monitor.send_alert_email(alerts, metrics)
        else:
            self.stdout.write(
                self.style.SUCCESS("Database performance normal")
            )
        
        report = monitor.generate_performance_report()
        self.stdout.write(report)
    
    def run_daemon(self, monitor: DatabaseMonitor, interval: int):
        """Run continuous monitoring daemon"""
        self.stdout.write(f"Monitoring database every {interval} seconds...")
        
        try:
            while True:
                try:
                    self.run_single_check(monitor)
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.stdout.write("\nStopping monitoring...")
                    break
                except Exception as e:
                    self.stderr.write(f"Monitoring error: {e}")
                    time.sleep(interval)
                    
        except Exception as e:
            self.stderr.write(f"Fatal monitoring error: {e}")


# Performance monitoring utility functions
def get_current_database_metrics() -> Optional[DatabaseMetrics]:
    """Get current database metrics"""
    monitor = DatabaseMonitor()
    return monitor.collect_metrics()


def check_database_health() -> tuple[bool, List[str]]:
    """Quick database health check"""
    monitor = DatabaseMonitor()
    metrics = monitor.collect_metrics()
    alerts = monitor.check_thresholds(metrics)
    
    is_healthy = len(alerts) == 0
    return is_healthy, alerts


def get_database_performance_summary() -> Dict:
    """Get performance summary for API endpoints"""
    cache_key = "db_monitor:latest_metrics"
    metrics = cache.get(cache_key)
    
    if not metrics:
        monitor = DatabaseMonitor()
        metrics = monitor.collect_metrics()
    
    return {
        'timestamp': metrics.timestamp.isoformat(),
        'active_connections': metrics.active_connections,
        'avg_query_time_ms': metrics.avg_query_time * 1000,
        'cache_hit_ratio': metrics.cache_hit_ratio,
        'disk_usage_gb': metrics.disk_usage_gb,
        'status': 'healthy' if metrics.avg_query_time < 0.1 else 'degraded'
    }