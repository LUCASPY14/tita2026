#!/usr/bin/env python
"""Script para crear medios de pago predeterminados"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.core.models import MediosPago

print("\n" + "="*60)
print("CREANDO MEDIOS DE PAGO PREDETERMINADOS")
print("="*60 + "\n")

medios_pago = [
    {
        'descripcion': 'Efectivo',
        'genera_comision': False,
        'requiere_validacion': False,
        'estado': True
    },
    {
        'descripcion': 'Transferencia Bancaria',
        'genera_comision': False,
        'requiere_validacion': True,
        'estado': True
    },
    {
        'descripcion': 'Tarjeta de Crédito',
        'genera_comision': True,
        'requiere_validacion': True,
        'estado': True
    },
    {
        'descripcion': 'Tarjeta de Débito',
        'genera_comision': True,
        'requiere_validacion': True,
        'estado': True
    },
    {
        'descripcion': 'Cheque',
        'genera_comision': False,
        'requiere_validacion': True,
        'estado': True
    },
]

for medio_data in medios_pago:
    medio, created = MediosPago.objects.get_or_create(
        descripcion=medio_data['descripcion'],
        defaults={
            'genera_comision': medio_data['genera_comision'],
            'requiere_validacion': medio_data['requiere_validacion'],
            'estado': medio_data['estado']
        }
    )
    
    if created:
        print(f"✅ Medio de pago creado: {medio.descripcion}")
    else:
        print(f"⚠️  Ya existe: {medio.descripcion}")

print("\n" + "="*60)
print("MEDIOS DE PAGO DISPONIBLES")
print("="*60 + "\n")

medios = MediosPago.objects.filter(estado=True).order_by('id_medio_pago')
for m in medios:
    comision = "✓" if m.genera_comision else "✗"
    validacion = "✓" if m.requiere_validacion else "✗"
    print(f"ID: {m.id_medio_pago} - {m.descripcion}")
    print(f"   Comisión: {comision} | Requiere validación: {validacion}")
    print("-" * 60)

print(f"\n📊 Total de medios de pago activos: {medios.count()}\n")
