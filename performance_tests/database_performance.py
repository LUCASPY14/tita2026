"""
====================================
Database Performance Tests - Cantina Tita
Tests for database query performance and optimization
====================================

Tests various database scenarios:
- Query optimization
- Index effectiveness
- Connection pooling
- Transaction performance
"""

import os
import sys
import time
import statistics
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the backend directory to Python path for Django imports
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')

import django
django.setup()

import pytest
from django.test import TestCase, TransactionTestCase
from django.db import transaction, connection, connections
from django.test.utils import override_settings
from django.core.management import call_command
from django.contrib.auth import get_user_model

from apps.clientes.models import Clientes, TiposCliente, Hijos, Grados
from apps.productos.models import Productos, Categorias
from apps.ventas.models import Ventas, DetalleVentas
from apps.inventario.models import Inventario

User = get_user_model()


class DatabasePerformanceTestCase(TransactionTestCase):
    """Base class for database performance tests"""
    
    def setUp(self):
        self.setup_test_data()
        self.performance_thresholds = {
            "simple_query": 0.01,  # 10ms
            "complex_query": 0.1,   # 100ms
            "bulk_insert": 0.5,     # 500ms
            "aggregation": 0.2,     # 200ms
        }

    def setup_test_data(self):
        """Create test data for performance testing"""
        # Create test types and categories
        self.tipo_cliente = TiposCliente.objects.create(
            nombre_tipo="Cliente Test",
            activo=True
        )
        
        self.categoria = Categorias.objects.create(
            nombre_categoria="Categoria Test",
            activo=True
        )
        
        self.grado = Grados.objects.create(
            nombre_grado="Grado Test",
            nivel=1,
            activo=True
        )

    def measure_query_time(self, query_func, *args, **kwargs):
        """Measure the execution time of a query function"""
        start_time = time.time()
        result = query_func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time

    def benchmark_query(self, query_func, iterations=10, *args, **kwargs):
        """Benchmark a query function multiple times"""
        execution_times = []
        
        for _ in range(iterations):
            _, execution_time = self.measure_query_time(query_func, *args, **kwargs)
            execution_times.append(execution_time)
        
        return {
            "min": min(execution_times),
            "max": max(execution_times),
            "avg": statistics.mean(execution_times),
            "median": statistics.median(execution_times),
            "times": execution_times
        }


@pytest.mark.performance
@pytest.mark.database
class ModelQueryPerformanceTest(DatabasePerformanceTestCase):
    """Test query performance for individual models"""

    def test_client_query_performance(self):
        """Test client model query performance"""
        # Create test clients
        clients_data = [
            Clientes(
                nombres=f"Cliente {i}",
                apellidos=f"Apellido {i}",
                ruc_ci=f"{1000000 + i}",
                email=f"cliente{i}@test.com",
                activo=True,
                id_tipo_cliente=self.tipo_cliente
            )
            for i in range(100)
        ]
        
        # Test bulk creation
        def bulk_create_clients():
            return Clientes.objects.bulk_create(clients_data)
        
        _, bulk_time = self.measure_query_time(bulk_create_clients)
        
        # Should create 100 clients in reasonable time
        self.assertLess(bulk_time, self.performance_thresholds["bulk_insert"])
        
        # Test query performance
        def query_active_clients():
            return list(Clientes.objects.filter(activo=True))
        
        stats = self.benchmark_query(query_active_clients, iterations=10)
        
        # Average query time should be acceptable
        self.assertLess(stats["avg"], self.performance_thresholds["simple_query"])

    def test_client_search_performance(self):
        """Test client search query performance"""
        # Create clients with searchable data
        Clientes.objects.bulk_create([
            Clientes(
                nombres=f"Juan {i}",
                apellidos=f"Pérez {i}",
                ruc_ci=f"{2000000 + i}",
                email=f"juan{i}@test.com",
                activo=True,
                id_tipo_cliente=self.tipo_cliente
            )
            for i in range(50)
        ])
        
        def search_clients_by_name():
            return list(Clientes.objects.filter(nombres__icontains="Juan"))
        
        stats = self.benchmark_query(search_clients_by_name, iterations=10)
        
        # Search should be fast
        self.assertLess(stats["avg"], self.performance_thresholds["simple_query"])

    def test_product_query_performance(self):
        """Test product model query performance"""
        # Create test products
        products_data = [
            Productos(
                nombre_producto=f"Producto {i}",
                precio=10.0 + i,
                activo=True,
                id_categoria=self.categoria
            )
            for i in range(100)
        ]
        
        # Test bulk creation
        def bulk_create_products():
            return Productos.objects.bulk_create(products_data)
        
        _, bulk_time = self.measure_query_time(bulk_create_products)
        self.assertLess(bulk_time, self.performance_thresholds["bulk_insert"])
        
        # Test filtering by category
        def filter_by_category():
            return list(Productos.objects.filter(id_categoria=self.categoria))
        
        stats = self.benchmark_query(filter_by_category, iterations=10)
        self.assertLess(stats["avg"], self.performance_thresholds["simple_query"])

    def test_sales_query_performance(self):
        """Test sales query performance with joins"""
        # Create test data
        cliente = Clientes.objects.create(
            nombres="Cliente Test",
            apellidos="Performance",
            ruc_ci="12345678",
            email="perf@test.com",
            activo=True,
            id_tipo_cliente=self.tipo_cliente
        )
        
        producto = Productos.objects.create(
            nombre_producto="Producto Test",
            precio=25.0,
            activo=True,
            id_categoria=self.categoria
        )
        
        # Create sales with details
        for i in range(20):
            venta = Ventas.objects.create(
                id_cliente=cliente,
                total=25.0,
                metodo_pago="efectivo"
            )
            
            DetalleVentas.objects.create(
                id_venta=venta,
                id_producto=producto,
                cantidad=1,
                precio_unitario=25.0,
                subtotal=25.0
            )
        
        # Test querying sales with related data
        def query_sales_with_details():
            return list(
                Ventas.objects
                .select_related('id_cliente')
                .prefetch_related('detalleventas_set__id_producto')
            )
        
        stats = self.benchmark_query(query_sales_with_details, iterations=5)
        self.assertLess(stats["avg"], self.performance_thresholds["complex_query"])


@pytest.mark.performance
@pytest.mark.database
class AggregationPerformanceTest(DatabasePerformanceTestCase):
    """Test aggregation query performance"""

    def setUp(self):
        super().setUp()
        self.create_sales_data()

    def create_sales_data(self):
        """Create substantial sales data for aggregation tests"""
        # Create clients
        clientes = Clientes.objects.bulk_create([
            Clientes(
                nombres=f"Cliente {i}",
                apellidos=f"Test {i}",
                ruc_ci=f"{3000000 + i}",
                email=f"agg{i}@test.com",
                activo=True,
                id_tipo_cliente=self.tipo_cliente
            )
            for i in range(20)
        ])
        
        # Create products
        productos = Productos.objects.bulk_create([
            Productos(
                nombre_producto=f"Producto {i}",
                precio=15.0 + i,
                activo=True,
                id_categoria=self.categoria
            )
            for i in range(10)
        ])
        
        # Create sales
        for i in range(50):
            venta = Ventas.objects.create(
                id_cliente=clientes[i % len(clientes)],
                total=100.0,
                metodo_pago="efectivo"
            )
            
            # Add details
            for j in range(3):  # 3 items per sale
                DetalleVentas.objects.create(
                    id_venta=venta,
                    id_producto=productos[j % len(productos)],
                    cantidad=2,
                    precio_unitario=15.0 + j,
                    subtotal=30.0 + j * 2
                )

    def test_sales_aggregation_performance(self):
        """Test sales aggregation performance"""
        from django.db.models import Sum, Count, Avg
        
        def aggregate_sales():
            return Ventas.objects.aggregate(
                total_sales=Sum('total'),
                total_count=Count('id_venta'),
                avg_sale=Avg('total')
            )
        
        stats = self.benchmark_query(aggregate_sales, iterations=10)
        self.assertLess(stats["avg"], self.performance_thresholds["aggregation"])

    def test_product_sales_aggregation(self):
        """Test product sales aggregation with joins"""
        from django.db.models import Sum, Count
        
        def product_sales_summary():
            return (
                Productos.objects
                .annotate(
                    total_sold=Sum('detalleventas__cantidad'),
                    sales_count=Count('detalleventas')
                )
                .values('nombre_producto', 'total_sold', 'sales_count')
            )
        
        stats = self.benchmark_query(list, product_sales_summary, iterations=5)
        self.assertLess(stats["avg"], self.performance_thresholds["aggregation"])

    def test_client_spending_aggregation(self):
        """Test client spending aggregation"""
        from django.db.models import Sum
        
        def client_spending():
            return (
                Clientes.objects
                .annotate(total_spent=Sum('ventas__total'))
                .filter(total_spent__gt=0)
                .order_by('-total_spent')
            )
        
        stats = self.benchmark_query(list, client_spending, iterations=5)
        self.assertLess(stats["avg"], self.performance_thresholds["aggregation"])


@pytest.mark.performance
@pytest.mark.database
class DatabaseConnectionPerformanceTest(TestCase):
    """Test database connection and transaction performance"""

    def test_connection_pooling_performance(self):
        """Test connection pooling performance"""
        def get_connection():
            conn = connections['default']
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result
        
        # Test multiple connections
        start_time = time.time()
        for _ in range(100):
            get_connection()
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        # Each connection should be fast
        self.assertLess(avg_time, 0.01)  # 10ms per connection

    def test_transaction_performance(self):
        """Test transaction performance"""
        def create_client_with_transaction():
            with transaction.atomic():
                return Clientes.objects.create(
                    nombres="Transaction Test",
                    apellidos="Performance",
                    ruc_ci="99999999",
                    email="trans@test.com",
                    activo=True,
                    id_tipo_cliente=TiposCliente.objects.first()
                )
        
        # Create tipo_cliente if not exists
        if not TiposCliente.objects.exists():
            TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        
        start_time = time.time()
        for i in range(10):
            create_client_with_transaction()
        end_time = time.time()
        
        avg_transaction_time = (end_time - start_time) / 10
        self.assertLess(avg_transaction_time, 0.05)  # 50ms per transaction

    @override_settings(DEBUG=True)
    def test_query_count_optimization(self):
        """Test that queries are optimized (N+1 problem detection)"""
        # Create test data
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        
        clientes = [
            Clientes(
                nombres=f"Cliente {i}",
                apellidos="Test",
                ruc_ci=f"{4000000 + i}",
                email=f"query{i}@test.com",
                activo=True,
                id_tipo_cliente=tipo_cliente
            )
            for i in range(10)
        ]
        Clientes.objects.bulk_create(clientes)
        
        # Test that accessing related data doesn't cause N+1 queries
        from django.test.utils import override_settings
        from django.db import reset_queries
        
        reset_queries()
        
        # Query with select_related to avoid N+1
        clientes_with_type = list(
            Clientes.objects.select_related('id_tipo_cliente').all()
        )
        
        # Access related data
        for cliente in clientes_with_type:
            _ = cliente.id_tipo_cliente.nombre_tipo
        
        query_count = len(connection.queries)
        
        # Should be only 1 query (not 11 due to N+1)
        self.assertLessEqual(query_count, 2)


@pytest.mark.performance
@pytest.mark.database
class IndexPerformanceTest(DatabasePerformanceTestCase):
    """Test database index effectiveness"""

    def test_email_index_performance(self):
        """Test that email lookups are fast (assuming index exists)"""
        # Create clients
        Clientes.objects.bulk_create([
            Clientes(
                nombres=f"Cliente {i}",
                apellidos="Index Test",
                ruc_ci=f"{5000000 + i}",
                email=f"index{i}@test.com",
                activo=True,
                id_tipo_cliente=self.tipo_cliente
            )
            for i in range(1000)
        ])
        
        def lookup_by_email():
            return Clientes.objects.get(email="index500@test.com")
        
        stats = self.benchmark_query(lookup_by_email, iterations=10)
        
        # Email lookup should be very fast with index
        self.assertLess(stats["avg"], 0.005)  # 5ms

    def test_ruc_index_performance(self):
        """Test RUC/CI lookup performance"""
        # Create clients
        Clientes.objects.bulk_create([
            Clientes(
                nombres=f"Cliente {i}",
                apellidos="RUC Test",
                ruc_ci=f"{6000000 + i}",
                email=f"ruc{i}@test.com",
                activo=True,
                id_tipo_cliente=self.tipo_cliente
            )
            for i in range(1000)
        ])
        
        def lookup_by_ruc():
            return Clientes.objects.get(ruc_ci="6000500")
        
        stats = self.benchmark_query(lookup_by_ruc, iterations=10)
        
        # RUC lookup should be fast
        self.assertLess(stats["avg"], 0.005)  # 5ms


def run_performance_tests():
    """
    Run all database performance tests and generate report
    """
    import subprocess
    import json
    
    # Run tests
    result = subprocess.run([
        'pytest', 
        'performance_tests/database_performance.py',
        '-m', 'performance',
        '--tb=short',
        '-v',
        '--json-report',
        '--json-report-file=performance_report.json'
    ], capture_output=True, text=True)
    
    print("Database Performance Test Results:")
    print("=" * 50)
    print(result.stdout)
    
    if result.returncode != 0:
        print("Errors:")
        print(result.stderr)
    
    # Load and display JSON report if available
    try:
        with open('performance_report.json', 'r') as f:
            report = json.load(f)
            
        print(f"Total tests: {report['summary']['total']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Duration: {report['duration']:.2f}s")
        
    except FileNotFoundError:
        print("No JSON report generated")


if __name__ == "__main__":
    run_performance_tests()