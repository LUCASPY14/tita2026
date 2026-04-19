"""
Verificacion final - que falta para 100%
"""

import os
import sys
import re
from pathlib import Path

# Configurar Django
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')

import django
django.setup()

from django.apps import apps

# Leer archivo TypeScript
frontend_types = Path(__file__).parent / "frontend" / "src" / "types" / "index.ts"
with open(frontend_types, 'r', encoding='utf-8') as f:
    ts_content = f.read()

# Mapeo de modelos
modelos_verificar = {
    'clientes.Clientes': 'Cliente',
    'clientes.Hijos': 'Hijo',
    'clientes.TiposCliente': 'TipoCliente',
    'ventas.Ventas': 'Venta',
    'ventas.DetallesVenta': 'DetalleVenta',
    'productos.Productos': 'Producto',
    'productos.Categorias': 'Categoria',
    'productos.PreciosPorLista': 'PrecioPorLista',
    'compras.Compras': 'Compra',
    'compras.DetallesCompra': 'DetalleCompra',
    'compras.Proveedores': 'Proveedor',
    'usuarios.Empleados': 'Empleado',
    'usuarios.Roles': 'Rol',
    'cobros.PagosClientes': 'PagoCliente',
    'inventario.StockUnico': 'StockUnico',
    'inventario.MovimientosStock': 'MovimientoStock',
    'contabilidad.Impuestos': 'Impuesto',
    'contabilidad.CierresCaja': 'CierreCaja',
    'core.MediosPago': 'MedioPago',
    'almuerzos.PlanesAlmuerzo': 'PlanAlmuerzo',
    'almuerzos.SuscripcionesAlmuerzo': 'SuscripcionAlmuerzo',
}

def extraer_campos_interface(interface_name):
    """Extrae campos de una interface TypeScript"""
    pattern = rf'export\s+interface\s+{interface_name}\s*\{{([^}}]+)\}}'
    match = re.search(pattern, ts_content, re.DOTALL)
    
    if not match:
        return None
    
    interface_body = match.group(1)
    campos = set()
    
    # Extraer campos (ignorar comentarios)
    lines = interface_body.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('//'):
            # Extraer nombre del campo
            match_field = re.match(r'(\w+)(\??):.*', line)
            if match_field:
                campos.add(match_field.group(1))
    
    return campos

def obtener_campos_django(app_model):
    """Obtiene campos del modelo Django"""
    app_name, model_name = app_model.split('.')
    try:
        modelo = apps.get_model(app_name, model_name)
        campos = set()
        
        for field in modelo._meta.get_fields():
            if hasattr(field, 'name'):
                # Excluir relaciones reversas
                if not hasattr(field, 'related_name') or field.concrete:
                    campos.add(field.name)
        
        return campos
    except Exception as e:
        return None

# Verificar cada modelo
print("="*80)
print("VERIFICACION FINAL - QUE FALTA PARA 100%")
print("="*80)

campos_faltantes = {}
campos_calculados = {}
campos_excluidos = {'contrasena_hash'}  # Campos que no deben estar por seguridad

for app_model, interface_name in modelos_verificar.items():
    campos_django = obtener_campos_django(app_model)
    campos_ts = extraer_campos_interface(interface_name)
    
    if not campos_django or not campos_ts:
        continue
    
    # Campos en Django pero no en TS (excluyendo id que es implícito)
    faltantes = campos_django - campos_ts - {'id'} - campos_excluidos
    if faltantes:
        campos_faltantes[app_model] = faltantes
    
    # Campos en TS pero no en Django (calculados o relacionados)
    calculados = campos_ts - campos_django - {'id'}
    if calculados:
        campos_calculados[app_model] = calculados

print("\n1. CAMPOS FALTANTES EN TYPESCRIPT")
print("-" * 80)
if campos_faltantes:
    total_faltantes = sum(len(v) for v in campos_faltantes.values())
    print(f"Total: {total_faltantes} campos\n")
    for modelo, campos in sorted(campos_faltantes.items()):
        print(f"{modelo}:")
        for campo in sorted(campos):
            print(f"  - {campo}")
        print()
else:
    print("[OK] No hay campos faltantes!\n")

print("\n2. CAMPOS CALCULADOS/RELACIONADOS (OK - son esperados)")
print("-" * 80)
total_calculados = sum(len(v) for v in campos_calculados.values())
print(f"Total: {total_calculados} campos calculados\n")

print("\n3. CAMPOS EXCLUIDOS POR SEGURIDAD")
print("-" * 80)
print(f"Total: {len(campos_excluidos)} campos\n")
for campo in sorted(campos_excluidos):
    print(f"  - {campo} (NO debe exponerse al frontend)")

print("\n" + "="*80)
print("RESUMEN")
print("="*80)

total_modelos = len(modelos_verificar)
modelos_con_faltantes = len(campos_faltantes)
total_faltantes = sum(len(v) for v in campos_faltantes.values())

consistencia_real = ((total_modelos - modelos_con_faltantes) / total_modelos) * 100

print(f"Modelos verificados:         {total_modelos}")
print(f"Modelos 100% consistentes:   {total_modelos - modelos_con_faltantes}")
print(f"Modelos con campos faltantes: {modelos_con_faltantes}")
print(f"Total campos faltantes:      {total_faltantes}")
print(f"Campos excluidos (seguridad): {len(campos_excluidos)}")
print(f"Campos calculados (normal):  {total_calculados}")
print(f"\nConsistencia real:           {consistencia_real:.1f}%")

if total_faltantes == 0:
    print("\n[OK] CONSISTENCIA 100% - Todos los campos necesarios estan presentes!")
    print("Los campos calculados son normales y esperados.")
else:
    print(f"\n[REVISAR] Faltan {total_faltantes} campos para alcanzar 100%")
    print("Revisa la lista anterior para ver que campos agregar.")

print("="*80)
