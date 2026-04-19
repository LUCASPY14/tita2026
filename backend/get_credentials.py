"""Script temporal para obtener credenciales de usuarios"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from apps.usuarios.models import UsuariosPortal, Empleados
from apps.ventas.models import Ventas
from decimal import Decimal

print("\n" + "="*80)
print(" REPORTE DE CREDENCIALES - CANTINA TITA")
print("="*80)

# Portal Users
print("\n📱 PORTAL DE CLIENTES - http://localhost:3002/portal/login")
print("-"*80)
print("Contraseña por defecto para todos: Portal123!")
print("-"*80)

usuarios_portal = UsuariosPortal.objects.select_related('id_cliente').all()[:10]

for u in usuarios_portal:
    facturas_pendientes = Ventas.objects.filter(
        id_cliente=u.id_cliente, 
        estado__in=['Pendiente', 'Parcial']
    )
    deuda_total = sum([v.saldo_pendiente for v in facturas_pendientes])
    
    print(f"\n✓ Email:    {u.email}")
    print(f"  Password: Portal123!")
    print(f"  Cliente:  {u.id_cliente.nombre_completo}")
    print(f"  RUC/CI:   {u.id_cliente.ruc_ci}")
    print(f"  Hijos:    {u.id_cliente.hijos.count()}")
    print(f"  Facturas: {facturas_pendientes.count()} pendientes")
    print(f"  Deuda:    Gs. {deuda_total:,.0f}")

# Admin System Users
print("\n\n💼 SISTEMA ADMINISTRATIVO - http://localhost:3002/login")
print("-"*80)

empleados = Empleados.objects.select_related('id_rol').filter(estado=True).order_by('id_rol__nombre_rol', 'usuario')

roles_info = {
    'Administrador': 'Admin123!@#',
    'Cajero': 'cajero123',
    'Gestor de Compras': 'cajero123',
    'Supervisor': 'supervisor123'
}

for e in empleados:
    password = roles_info.get(e.id_rol.nombre_rol, 'desconocida')
    print(f"\n✓ Usuario:  {e.usuario}")
    print(f"  Password: {password}")
    print(f"  Nombre:   {e.nombre} {e.apellido}")
    print(f"  Rol:      {e.id_rol.nombre_rol}")
    print(f"  Email:    {e.email}")

# Django Admin
print("\n\n⚙️  DJANGO ADMIN - http://127.0.0.1:8000/admin/")
print("-"*80)
print("\n✓ Usuario:  admin")
print("  Password: Admin123!@#")
print("  Acceso:   Superusuario Django")

print("\n" + "="*80)
print(" RESUMEN DE SISTEMAS")
print("="*80)
print("\n1. Portal de Clientes:  http://localhost:3002/portal/login")
print("   - Contraseña estándar: Portal123!")
print(f"   - {usuarios_portal.count()} usuarios disponibles")
print("\n2. Sistema Admin:       http://localhost:3002/login")
print("   - admin / Admin123!@#")
print(f"   - {empleados.count()} usuarios activos")
print("\n3. Django Admin:        http://127.0.0.1:8000/admin/")
print("   - admin / Admin123!@#")
print("\n" + "="*80 + "\n")
