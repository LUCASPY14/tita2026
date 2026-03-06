"""
====================================
API Performance Tests - Cantina Tita
Specific performance tests for critical API endpoints
====================================

Test individual API endpoints for performance characteristics:
- Response time
- Throughput
- Error rates
- Resource utilization
"""

import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

import requests
from locust import HttpUser, task, between
from locust.contrib.fasthttp import FastHttpUser


class APIPerformanceTestUser(FastHttpUser):
    """
    Dedicated user for API performance testing
    Tests individual endpoints systematically
    """
    
    wait_time = between(0.1, 0.3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.test_data = {}

    def on_start(self):
        """Setup for API testing"""
        self.authenticate()
        self.prepare_test_data()

    def authenticate(self):
        """Get authentication token"""
        login_data = {
            "email": "performance@test.com",
            "password": "testpass123"
        }
        
        response = self.client.post("/api/auth/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access")
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

    def prepare_test_data(self):
        """Prepare test data for operations"""
        # Get sample client data
        response = self.client.get("/api/clientes/?page_size=5")
        if response.status_code == 200:
            clients = response.json().get("results", [])
            if clients:
                self.test_data["client_id"] = clients[0]["id_cliente"]
        
        # Get sample product data
        response = self.client.get("/api/productos/?page_size=5")
        if response.status_code == 200:
            products = response.json().get("results", [])
            if products:
                self.test_data["product_id"] = products[0]["id_producto"]

    # ====================================
    # Authentication API Performance Tests
    # ====================================
    
    @task(5)
    def test_auth_performance(self):
        """Test authentication endpoint performance"""
        login_data = {
            "email": "testuser@test.com",
            "password": "testpass123"
        }
        
        # Measure login performance
        start_time = time.time()
        response = self.client.post("/api/auth/login/", json=login_data, name="Auth Login Performance")
        end_time = time.time()
        
        if response.status_code == 200:
            # Test token refresh performance
            token_data = response.json()
            refresh_token = token_data.get("refresh")
            
            if refresh_token:
                refresh_data = {"refresh": refresh_token}
                self.client.post("/api/auth/refresh/", json=refresh_data, name="Auth Refresh Performance")

    # ====================================
    # Client API Performance Tests
    # ====================================
    
    @task(10)
    def test_clients_list_performance(self):
        """Test clients listing with various parameters"""
        # Test basic listing
        self.client.get("/api/clientes/", name="Clients List - Basic")
        
        # Test with pagination
        self.client.get("/api/clientes/?page=1&page_size=50", name="Clients List - Paginated")
        
        # Test with search
        self.client.get("/api/clientes/?search=test", name="Clients List - Search")
        
        # Test with filters
        self.client.get("/api/clientes/?activo=true", name="Clients List - Filtered")

    @task(8)
    def test_client_detail_performance(self):
        """Test individual client retrieval performance"""
        if "client_id" in self.test_data:
            client_id = self.test_data["client_id"]
            self.client.get(f"/api/clientes/{client_id}/", name="Client Detail - Performance")

    @task(3)
    def test_client_create_performance(self):
        """Test client creation performance"""
        import random
        
        client_data = {
            "nombres": f"Test User {random.randint(1000, 9999)}",
            "apellidos": "Performance Test",
            "ruc_ci": str(random.randint(10000000, 99999999)),
            "email": f"perf{random.randint(1000, 9999)}@test.com",
            "activo": True,
            "id_tipo_cliente": 1
        }
        
        self.client.post("/api/clientes/", json=client_data, name="Client Create - Performance")

    # ====================================
    # Product API Performance Tests
    # ====================================
    
    @task(12)
    def test_products_list_performance(self):
        """Test products listing performance"""
        # Basic listing
        self.client.get("/api/productos/", name="Products List - Basic")
        
        # With category filter
        self.client.get("/api/productos/?categoria=1", name="Products List - Category Filter")
        
        # With price range
        self.client.get("/api/productos/?precio_min=10&precio_max=100", name="Products List - Price Filter")
        
        # With search
        self.client.get("/api/productos/?search=almuerzo", name="Products List - Search")

    @task(7)
    def test_product_detail_performance(self):
        """Test product detail retrieval"""
        if "product_id" in self.test_data:
            product_id = self.test_data["product_id"]
            self.client.get(f"/api/productos/{product_id}/", name="Product Detail - Performance")

    # ====================================
    # Sales API Performance Tests
    # ====================================
    
    @task(6)
    def test_sales_list_performance(self):
        """Test sales listing performance"""
        # Recent sales
        self.client.get("/api/ventas/?ordering=-fecha_venta", name="Sales List - Recent")
        
        # Date filtered sales
        self.client.get("/api/ventas/?fecha_venta__gte=2026-03-01", name="Sales List - Date Filter")
        
        # Client sales
        if "client_id" in self.test_data:
            client_id = self.test_data["client_id"]
            self.client.get(f"/api/ventas/?id_cliente={client_id}", name="Sales List - Client Filter")

    @task(4)
    def test_sales_statistics_performance(self):
        """Test sales statistics endpoints"""
        # Daily stats
        self.client.get("/api/reportes/ventas/daily/", name="Sales Stats - Daily")
        
        # Monthly stats
        self.client.get("/api/reportes/ventas/monthly/", name="Sales Stats - Monthly")
        
        # Top products
        self.client.get("/api/reportes/productos/top/", name="Sales Stats - Top Products")

    # ====================================
    # Inventory API Performance Tests
    # ====================================
    
    @task(8)
    def test_inventory_performance(self):
        """Test inventory operations performance"""
        # List inventory
        self.client.get("/api/inventario/", name="Inventory List - Performance")
        
        # Low stock alerts
        self.client.get("/api/inventario/?stock_bajo=true", name="Inventory List - Low Stock")
        
        # Category inventory
        self.client.get("/api/inventario/?categoria=1", name="Inventory List - Category")

    # ====================================
    # Reports API Performance Tests
    # ====================================
    
    @task(2)
    def test_reports_performance(self):
        """Test report generation performance"""
        params = {
            "date_from": "2026-03-01",
            "date_to": "2026-03-06"
        }
        
        # Sales report
        self.client.get("/api/reportes/ventas/", params=params, name="Reports - Sales Performance")
        
        # Inventory report
        self.client.get("/api/reportes/inventario/", params=params, name="Reports - Inventory Performance")

    # ====================================
    # Bulk Operations Performance Tests
    # ====================================
    
    @task(1)
    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        # Bulk price update simulation
        bulk_data = [
            {"id": i, "precio": 25.0 + i} 
            for i in range(1, 21)  # 20 products
        ]
        
        self.client.patch(
            "/api/productos/bulk-update/",
            json={"products": bulk_data},
            name="Bulk Operations - Products Performance"
        )


class DatabaseIntensiveUser(FastHttpUser):
    """
    User that performs database-intensive operations
    Tests complex queries and aggregations
    """
    
    wait_time = between(1, 3)
    weight = 1  # Lower frequency
    
    def on_start(self):
        """Setup authentication"""
        login_data = {
            "email": "dbtest@test.com",
            "password": "testpass123"
        }
        
        response = self.client.post("/api/auth/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access")
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

    @task(1)
    def test_complex_aggregation_queries(self):
        """Test complex database aggregation queries"""
        # Monthly sales aggregation
        self.client.get(
            "/api/reportes/ventas/aggregated/?group_by=month&year=2026",
            name="DB Intensive - Monthly Aggregation"
        )
        
        # Product popularity analysis
        self.client.get(
            "/api/reportes/productos/analytics/",
            name="DB Intensive - Product Analytics"
        )
        
        # Client spending analysis
        self.client.get(
            "/api/reportes/clientes/spending/",
            name="DB Intensive - Client Spending"
        )

    @task(1)
    def test_large_dataset_queries(self):
        """Test queries that return large datasets"""
        # Large date range
        params = {
            "date_from": "2025-01-01",
            "date_to": "2026-03-06",
            "include_details": True
        }
        
        self.client.get(
            "/api/reportes/comprehensive/",
            params=params,
            name="DB Intensive - Large Dataset"
        )

    @task(1)
    def test_join_heavy_queries(self):
        """Test queries with multiple table joins"""
        # Sales with all related data
        self.client.get(
            "/api/ventas/?include=cliente,items,productos,usuario",
            name="DB Intensive - Multiple Joins"
        )
        
        # Inventory with supplier and category data
        self.client.get(
            "/api/inventario/?include=producto,categoria,proveedor",
            name="DB Intensive - Inventory Joins"
        )


# ====================================
# Performance Test Utilities
# ====================================

def benchmark_endpoint(url: str, method: str = "GET", data: dict = None, headers: dict = None, iterations: int = 100) -> Dict:
    """
    Benchmark a specific endpoint
    Returns performance statistics
    """
    
    response_times = []
    errors = 0
    
    for _ in range(iterations):
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code >= 400:
                errors += 1
            else:
                response_times.append(response_time)
                
        except Exception:
            errors += 1
    
    if response_times:
        return {
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            "total_requests": iterations,
            "successful_requests": len(response_times),
            "error_rate": (errors / iterations) * 100,
            "response_times": response_times
        }
    else:
        return {
            "error": "All requests failed",
            "total_requests": iterations,
            "errors": errors
        }


def stress_test_endpoint(url: str, concurrent_users: int = 10, duration_seconds: int = 60, headers: dict = None) -> Dict:
    """
    Stress test an endpoint with concurrent users
    """
    
    def make_request():
        response_times = []
        errors = 0
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            start_time = time.time()
            try:
                response = requests.get(url, headers=headers)
                request_time = (time.time() - start_time) * 1000
                
                if response.status_code >= 400:
                    errors += 1
                else:
                    response_times.append(request_time)
                    
            except Exception:
                errors += 1
        
        return {
            "response_times": response_times,
            "errors": errors,
            "requests": len(response_times) + errors
        }
    
    # Run concurrent stress test
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request) for _ in range(concurrent_users)]
        results = [future.result() for future in as_completed(futures)]
    
    # Aggregate results
    all_response_times = []
    total_errors = 0
    total_requests = 0
    
    for result in results:
        all_response_times.extend(result["response_times"])
        total_errors += result["errors"]
        total_requests += result["requests"]
    
    if all_response_times:
        return {
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "total_requests": total_requests,
            "successful_requests": len(all_response_times),
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests) * 100 if total_requests > 0 else 0,
            "avg_response_time": statistics.mean(all_response_times),
            "p95_response_time": statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times),
            "requests_per_second": total_requests / duration_seconds
        }
    else:
        return {
            "error": "No successful requests",
            "total_errors": total_errors
        }