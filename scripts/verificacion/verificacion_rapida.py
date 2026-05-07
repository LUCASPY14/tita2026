"""
Verificación rápida de consistencia - Solo genera JSON
"""

import os
import re
import json
from pathlib import Path


def main():
    root_dir = Path("d:/tita2026")
    frontend_types = root_dir / "frontend" / "src" / "types" / "index.ts"
    
    # Mapeo de modelos a interfaces
    model_to_interface = {
        'TiposCliente': 'TipoCliente',
        'DetallesVenta': 'DetalleVenta',
        'DetallesCompra': 'DetalleCompra',
        'MovimientosStock': 'MovimientoStock',
        'CierresCaja': 'CierreCaja',
        'MediosPago': 'MedioPago',
        'PlanesAlmuerzo': 'PlanAlmuerzo',
        'SuscripcionesAlmuerzo': 'SuscripcionAlmuerzo',
        'PagosClientes': 'PagoCliente',
        'StockUnico': 'StockUnico',
        'PreciosPorLista': 'PrecioPorLista',
        'Clientes': 'Cliente',
        'Hijos': 'Hijo',
        'Empleados': 'Empleado',
        'Roles': 'Rol',
        'Ventas': 'Venta',
        'Productos': 'Producto',
        'Categorias': 'Categoria',
        'Compras': 'Compra',
        'Proveedores': 'Proveedor',
        'Impuestos': 'Impuesto',
    }
    
    # Leer archivo de tipos
    with open(frontend_types, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar interfaces
    resultados = {}
    interfaces_encontradas = 0
    interfaces_faltantes = 0
    
    for modelo, interface in model_to_interface.items():
        pattern = rf'export\s+interface\s+{interface}\s*\{{'
        if re.search(pattern, content):
            interfaces_encontradas += 1
        else:
            interfaces_faltantes += 1
            resultados[modelo] = f"Interface {interface} NO encontrada"
    
    # Resumen
    total = len(model_to_interface)
    consistencia = (interfaces_encontradas / total) * 100
    
    print(f"\n{'='*80}")
    print(f"VERIFICACION RAPIDA DE CONSISTENCIA")
    print(f"{'='*80}\n")
    print(f"Total de modelos verificados: {total}")
    print(f"Interfaces encontradas: {interfaces_encontradas}")
    print(f"Interfaces faltantes: {interfaces_faltantes}")
    print(f"\nConsistencia: {consistencia:.1f}%")
    
    if interfaces_faltantes > 0:
        print(f"\nInterfaces faltantes:")
        for modelo, msg in resultados.items():
            print(f"  - {modelo}: {msg}")
    else:
        print(f"\n[OK] Todas las interfaces estan presentes!")
    
    # Guardar JSON
    output = {
        'total': total,
        'encontradas': interfaces_encontradas,
        'faltantes': interfaces_faltantes,
        'consistencia': consistencia,
        'problemas': resultados
    }
    
    with open(root_dir / 'verificacion_rapida.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados guardados en: verificacion_rapida.json")


if __name__ == '__main__':
    main()
