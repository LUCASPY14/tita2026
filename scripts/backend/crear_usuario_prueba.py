#!/usr/bin/env python
"""
Script para crear un usuario admin de prueba
Ejecutar: python crear_usuario_prueba.py
"""
import os
import django
import sys

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from apps.usuarios.models import Empleados, Roles
from django.contrib.auth.hashers import make_password
from datetime import datetime
import bcrypt

def crear_usuario_admin():
    """Crea un usuario admin de prueba"""
    
    # Verificar si existe rol de administrador
    try:
        rol_admin = Roles.objects.filter(nombre_rol__icontains='admin').first()
        if not rol_admin:
            print("⚠️  No se encontró rol de administrador, creando uno...")
            rol_admin = Roles.objects.create(
                nombre_rol='Administrador',
                descripcion='Acceso completo al sistema',
                activo=True
            )
            print(f"✅ Rol creado: {rol_admin.nombre_rol}")
    except Exception as e:
        print(f"❌ Error al buscar/crear rol: {e}")
        rol_admin = None
    
    # Verificar si ya existe el usuario
    if Empleados.objects.filter(usuario='admin').exists():
        print("⚠️  El usuario 'admin' ya existe")
        empleado = Empleados.objects.get(usuario='admin')
        print(f"   ID: {empleado.id_empleado}")
        print(f"   Nombre: {empleado.nombre} {empleado.apellido}")
        print(f"   Email: {empleado.email}")
        print(f"   Activo: {empleado.activo}")
        return empleado
    
    # Crear usuario admin
    try:
        # Usar bcrypt directamente para que el hash sea de 60 caracteres
        password_hash = bcrypt.hashpw('Admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        empleado = Empleados.objects.create(
            usuario='admin',
            contrasena_hash=password_hash,
            nombre='Administrador',
            apellido='del Sistema',
            email='admin@cantinatita.com',
            telefono='0981123456',
            id_rol=rol_admin,
            fecha_ingreso=datetime.now(),
            activo=True
        )
        
        print("✅ Usuario admin creado exitosamente!")
        print(f"   Usuario: admin")
        print(f"   Contraseña: Admin123")
        print(f"   Email: {empleado.email}")
        print(f"   ID: {empleado.id_empleado}")
        
        return empleado
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("🚀 Creando usuario administrador de prueba...")
    print("-" * 50)
    usuario = crear_usuario_admin()
    print("-" * 50)
    if usuario:
        print("\n🎉 ¡Listo! Ahora puedes hacer login con:")
        print("   Usuario: admin")
        print("   Contraseña: Admin123")
    else:
        print("\n❌ No se pudo crear el usuario")
