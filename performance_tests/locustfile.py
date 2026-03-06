"""
====================================
Load Testing Framework - Cantina Tita
Comprehensive performance testing using Locust
====================================

Main entry point for load testing scenarios.
Run with: locust -f locustfile.py --host=http://localhost:8000
"""

import json
import random
import time
from itertools import cycle
from typing import Dict, List, Optional

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


class CantinaTitaUser(FastHttpUser):
    """
    Simulates a typical user of the Cantina Tita system
    Includes authentication, browsing, and transaction flows
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.user_data = None
        self.client_id = None

    def on_start(self):
        """Called when a user starts. Sets up authentication."""
        self.authenticate()
        self.load_user_data()

    def authenticate(self):
        """Authenticate user and get access token"""
        login_data = {
            "email": f"testuser{random.randint(1, 100)}@test.com",
            "password": "testpass123"
        }
        
        with self.client.post(
            "/api/auth/login/",
            json=login_data,
            name="Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access")
                self.user_data = data.get("user")
                
                # Set authorization header for subsequent requests
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
            else:
                print(f"Login failed: {response.status_code}")

    def load_user_data(self):
        """Load user-specific data for realistic testing"""
        if self.auth_token:
            # Get user profile
            self.client.get("/api/auth/profile/", name="Load Profile")
            
            # Get user's clients
            response = self.client.get("/api/clientes/", name="Load Clients")
            if response.status_code == 200:
                clients = response.json().get("results", [])
                if clients:
                    self.client_id = clients[0]["id_cliente"]

    @task(10)
    def browse_dashboard(self):
        """Simulate browsing the main dashboard"""
        self.client.get("/api/dashboard/stats/", name="Dashboard Stats")
        self.client.get("/api/dashboard/recent/", name="Recent Activity")

    @task(20)
    def browse_clients(self):
        """Simulate browsing clients"""
        # List clients
        self.client.get("/api/clientes/", name="List Clients")
        
        # Get specific client details
        if self.client_id:
            self.client.get(
                f"/api/clientes/{self.client_id}/",
                name="Client Detail"
            )

    @task(15)
    def browse_products(self):
        """Simulate browsing products and inventory"""
        params = {
            "page": random.randint(1, 3),
            "page_size": 20
        }
        
        self.client.get("/api/productos/", params=params, name="List Products")
        self.client.get("/api/inventario/", params=params, name="List Inventory")

    @task(8)
    def create_sale(self):
        """Simulate creating a sale transaction"""
        if not self.client_id:
            return
            
        sale_data = {
            "id_cliente": self.client_id,
            "items": [
                {
                    "id_producto": random.randint(1, 50),
                    "cantidad": random.randint(1, 3),
                    "precio_unitario": round(random.uniform(5.0, 25.0), 2)
                }
            ],
            "metodo_pago": random.choice(["efectivo", "tarjeta", "transferencia"]),
            "observaciones": "Test transaction from load test"
        }
        
        self.client.post(
            "/api/ventas/",
            json=sale_data,
            name="Create Sale"
        )

    @task(5)
    def search_functionality(self):
        """Test search performance"""
        search_terms = [
            "almuerzo", "bebida", "hamburguesa", 
            "jugo", "ensalada", "pollo"
        ]
        
        term = random.choice(search_terms)
        params = {"search": term}
        
        self.client.get("/api/productos/", params=params, name="Search Products")
        self.client.get("/api/clientes/", params=params, name="Search Clients")

    @task(3)
    def generate_reports(self):
        """Test report generation performance"""
        date_from = "2026-03-01"
        date_to = "2026-03-06"
        
        params = {
            "date_from": date_from,
            "date_to": date_to
        }
        
        self.client.get("/api/reportes/ventas/", params=params, name="Sales Report")
        self.client.get("/api/reportes/inventario/", params=params, name="Inventory Report")

    def on_stop(self):
        """Called when user stops. Cleanup resources."""
        if self.auth_token:
            self.client.post("/api/auth/logout/", name="Logout")


class AdminUser(FastHttpUser):
    """
    Simulates administrative user with heavier operations
    """
    
    wait_time = between(2, 8)
    weight = 1  # Less frequent than regular users
    
    def on_start(self):
        """Admin authentication"""
        login_data = {
            "email": "admin@cantina-tita.com",
            "password": "admin123"
        }
        
        with self.client.post("/api/auth/login/", json=login_data) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access")
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })

    @task(5)
    def admin_dashboard(self):
        """Access admin-specific endpoints"""
        self.client.get("/api/admin/stats/", name="Admin Stats")
        self.client.get("/api/admin/users/", name="Admin Users")

    @task(3)
    def bulk_operations(self):
        """Simulate bulk operations"""
        # Bulk product updates
        bulk_data = [
            {
                "id": i,
                "precio": round(random.uniform(10.0, 50.0), 2)
            }
            for i in range(1, 11)
        ]
        
        self.client.patch(
            "/api/productos/bulk-update/",
            json={"products": bulk_data},
            name="Bulk Update Products"
        )

    @task(2)
    def generate_complex_reports(self):
        """Generate complex administrative reports"""
        params = {
            "date_from": "2026-01-01",
            "date_to": "2026-03-06",
            "detail_level": "full",
            "include_analytics": True
        }
        
        self.client.get("/api/reportes/comprehensive/", params=params, name="Complex Report")


class StressTestUser(HttpUser):
    """
    User for stress testing - performs rapid operations
    """
    
    wait_time = between(0.1, 0.5)  # Very fast operations
    weight = 1  # Use sparingly
    
    @task
    def rapid_api_calls(self):
        """Rapid API calls for stress testing"""
        endpoints = [
            "/api/productos/",
            "/api/clientes/",
            "/api/inventario/",
            "/health/"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=f"Stress {endpoint}")


# ====================================
# Test Scenarios and Event Handlers
# ====================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("🚀 Starting Cantina Tita Load Test")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("🏁 Load test completed")
    
    # Print summary statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Monitor individual requests"""
    if exception:
        print(f"❌ Request failed: {name} - {exception}")
    elif response_time > 2000:  # Log slow requests
        print(f"⚠️  Slow request: {name} - {response_time:.0f}ms")


# ====================================
# Custom Test Scenarios
# ====================================

def create_peak_hours_scenario():
    """Simulate peak lunch hours traffic"""
    return [
        {"user_class": CantinaTitaUser, "weight": 80},
        {"user_class": AdminUser, "weight": 5},
        {"user_class": StressTestUser, "weight": 15},
    ]


def create_normal_traffic_scenario():
    """Simulate normal business hours"""
    return [
        {"user_class": CantinaTitaUser, "weight": 90},
        {"user_class": AdminUser, "weight": 10},
    ]


# Default user classes for basic load testing
user_classes = [CantinaTitaUser, AdminUser]