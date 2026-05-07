#!/usr/bin/env python
"""Script para listar todos los roles disponibles"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.usuarios.models import Roles

print("\n" + "="*60)
print("ROLES DISPONIBLES EN EL SISTEMA")
print("="*60 + "\n")

roles = Roles.objects.all().order_by('id_rol')

if not roles.exists():
    print("⚠️  No hay roles registrados en el sistema.\n")
else:
    for r in roles:
        print(f"ID: {r.id_rol} - Nombre: {r.nombre_rol}")
        if hasattr(r, 'descripcion') and r.descripcion:
            print(f"   Descripción: {r.descripcion}")
        print("-" * 60)

print(f"\n📊 Total de roles: {roles.count()}\n")
