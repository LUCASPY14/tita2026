#!/usr/bin/env python
"""Script para crear usuarios de prueba con diferentes roles"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import bcrypt
from apps.usuarios.models import Empleados, Roles

def crear_usuario(usuario, nombre, apellido, password, id_rol, email, telefono=None):
    """Crea un usuario con contraseña hasheada"""
    
    # Verificar si el usuario ya existe
    if Empleados.objects.filter(usuario=usuario).exists():
        print(f"⚠️  El usuario '{usuario}' ya existe. Actualizando contraseña...")
        emp = Empleados.objects.get(usuario=usuario)
        emp.contrasena_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        emp.estado = True
        emp.save()
        print(f"✅ Contraseña actualizada para '{usuario}'")
        return emp
    
    # Obtener el rol
    try:
        rol = Roles.objects.get(id_rol=id_rol)
    except Roles.DoesNotExist:
        print(f"❌ Error: No existe el rol con ID {id_rol}")
        return None
    
    # Hashear la contraseña
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Crear el empleado
    empleado = Empleados.objects.create(
        usuario=usuario,
        nombre=nombre,
        apellido=apellido,
        contrasena_hash=password_hash,
        email=email,
        telefono=telefono,
        fecha_ingreso=datetime.now(),
        estado=True,
        id_rol=rol
    )
    
    print(f"✅ Usuario '{usuario}' creado exitosamente con rol {rol.nombre_rol}")
    return empleado


print("\n" + "="*60)
print("CREANDO USUARIOS DE PRUEBA")
print("="*60 + "\n")

# Crear usuarios para cada rol
usuarios_crear = [
    {
        'usuario': 'admin',
        'nombre': 'Administrador',
        'apellido': 'Sistema',
        'password': 'Admin123',
        'id_rol': 1,  # ADMINISTRADOR
        'email': 'admin@cantina.com',
        'telefono': '0981-111111'
    },
    {
        'usuario': 'cajero',
        'nombre': 'Juan',
        'apellido': 'Pérez',
        'password': 'Cajero123',
        'id_rol': 2,  # CAJERO
        'email': 'cajero@cantina.com',
        'telefono': '0981-222222'
    },
    {
        'usuario': 'supervisor',
        'nombre': 'María',
        'apellido': 'González',
        'password': 'Supervisor123',
        'id_rol': 3,  # SUPERVISOR
        'email': 'supervisor@cantina.com',
        'telefono': '0981-333333'
    },
    {
        'usuario': 'cobrador',
        'nombre': 'Carlos',
        'apellido': 'Ramírez',
        'password': 'Cobrador123',
        'id_rol': 4,  # Cobrador
        'email': 'cobrador@cantina.com',
        'telefono': '0981-444444'
    },
    {
        'usuario': 'vendedor',
        'nombre': 'Ana',
        'apellido': 'Martínez',
        'password': 'Vendedor123',
        'id_rol': 2,  # CAJERO (vendedor es similar a cajero)
        'email': 'vendedor@cantina.com',
        'telefono': '0981-555555'
    },
]

# Crear cada usuario
for datos in usuarios_crear:
    crear_usuario(**datos)

print("\n" + "="*60)
print("RESUMEN DE CREDENCIALES CREADAS")
print("="*60 + "\n")

for datos in usuarios_crear:
    rol = Roles.objects.get(id_rol=datos['id_rol'])
    print(f"👤 Usuario: {datos['usuario']}")
    print(f"   Contraseña: {datos['password']}")
    print(f"   Rol: {rol.nombre_rol}")
    print(f"   Email: {datos['email']}")
    print("-" * 60)

print("\n✅ Todos los usuarios han sido creados exitosamente!\n")
