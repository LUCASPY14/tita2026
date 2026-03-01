#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de prueba
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.clientes.models import Cliente
from apps.productos.models import Producto, Categoria

User = get_user_model()

def create_users():
    """Crear usuarios de prueba"""
    print("Creando usuarios...")
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@cantina.com',
            password='admin123'
        )
        print("✓ Usuario admin creado")
    
    if not User.objects.filter(username='vendedor').exists():
        User.objects.create_user(
            username='vendedor',
            email='vendedor@cantina.com',
            password='vendedor123'
        )
        print("✓ Usuario vendedor creado")

def create_categories():
    """Crear categorías de productos"""
    print("\nCreando categorías...")
    
    categorias = [
        'Bebidas',
        'Snacks',
        'Almuerzos',
        'Golosinas',
        'Útiles Escolares'
    ]
    
    for nombre in categorias:
        Categoria.objects.get_or_create(nombre=nombre)
        print(f"✓ Categoría {nombre} creada")

def create_products():
    """Crear productos de prueba"""
    print("\nCreando productos...")
    
    productos = [
        {'codigo': 'BEB-001', 'nombre': 'Coca Cola 500ml', 'precio': 8000, 'categoria': 'Bebidas', 'stock': 50},
        {'codigo': 'BEB-002', 'nombre': 'Agua Mineral 500ml', 'precio': 3000, 'categoria': 'Bebidas', 'stock': 100},
        {'codigo': 'SNK-001', 'nombre': 'Papas Lays', 'precio': 5000, 'categoria': 'Snacks', 'stock': 30},
        {'codigo': 'SNK-002', 'nombre': 'Galletas Oreo', 'precio': 6000, 'categoria': 'Snacks', 'stock': 40},
        {'codigo': 'ALM-001', 'nombre': 'Almuerzo Completo', 'precio': 15000, 'categoria': 'Almuerzos', 'stock': 20},
    ]
    
    for prod_data in productos:
        categoria = Categoria.objects.get(nombre=prod_data['categoria'])
        Producto.objects.get_or_create(
            codigo=prod_data['codigo'],
            defaults={
                'nombre': prod_data['nombre'],
                'precio': prod_data['precio'],
                'categoria': categoria,
                'stock': prod_data['stock'],
                'stock_minimo': 10
            }
        )
        print(f"✓ Producto {prod_data['nombre']} creado")

def create_clients():
    """Crear clientes de prueba"""
    print("\nCreando clientes...")
    
    clientes = [
        {
            'nombre': 'Juan Pérez',
            'ruc': '12345678-9',
            'telefono': '0981234567',
            'email': 'juan@example.com',
        },
        {
            'nombre': 'María González',
            'ruc': '87654321-0',
            'telefono': '0987654321',
            'email': 'maria@example.com',
        },
    ]
    
    for cliente_data in clientes:
        Cliente.objects.get_or_create(
            ruc=cliente_data['ruc'],
            defaults=cliente_data
        )
        print(f"✓ Cliente {cliente_data['nombre']} creado")

def main():
    """Función principal"""
    print("=" * 50)
    print("Poblando base de datos con datos de prueba")
    print("=" * 50)
    
    create_users()
    create_categories()
    create_products()
    create_clients()
    
    print("\n" + "=" * 50)
    print("✓ Base de datos poblada exitosamente!")
    print("=" * 50)
    print("\nCredenciales:")
    print("  Admin: admin / admin123")
    print("  Vendedor: vendedor / vendedor123")

if __name__ == '__main__':
    main()
