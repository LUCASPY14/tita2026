#!/usr/bin/env python
"""Script para listar todos los usuarios activos en el sistema"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.usuarios.models import Empleados

print("\n" + "="*60)
print("USUARIOS ACTIVOS EN EL SISTEMA")
print("="*60 + "\n")

usuarios = Empleados.objects.all().order_by('usuario')

if not usuarios.exists():
    print("⚠️  No hay usuarios registrados en el sistema.\n")
else:
    for u in usuarios:
        print(f"📋 Usuario: {u.usuario}")
        print(f"   Email: {u.email or '(sin email)'}")
        print(f"   Nombre completo: {u.nombre} {u.apellido}")
        
        # Mostrar rol
        try:
            print(f"   Rol: {u.id_rol.nombre_rol if u.id_rol else 'Sin rol'}")
        except:
            print(f"   Rol: Sin rol")
        
        # Estado
        estado = "✅ Activo" if u.estado else "❌ Inactivo"
        print(f"   Estado: {estado}")
        
        print(f"   Teléfono: {u.telefono or 'Sin teléfono'}")
        print(f"   Fecha ingreso: {u.fecha_ingreso.strftime('%Y-%m-%d %H:%M')}")
        
        if u.fecha_baja:
            print(f"   Fecha baja: {u.fecha_baja.strftime('%Y-%m-%d %H:%M')}")
        
        print("-" * 60)

print(f"\n📊 Total de usuarios: {usuarios.count()}\n")
