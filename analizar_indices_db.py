#!/usr/bin/env python3
"""
Script para verificar y sugerir índices de base de datos
Analiza los modelos Django y sugiere índices basados en campos consultados frecuentemente
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def analizar_indices_modelos(root_dir):
    """Analiza modelos y reporta índices existentes y sugerencias"""
    
    print("="*80)
    print("ANÁLISIS DE ÍNDICES DE BASE DE DATOS")
    print("="*80)
    
    backend_dir = Path(root_dir) / "backend" / "apps"
    
    indices_por_modelo = {}
    sugerencias = []
    
    for model_file in backend_dir.rglob("models.py"):
        app_name = model_file.parent.name
        
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar modelos
            model_pattern = r'class\s+(\w+)\(.*models\.Model.*?\):\s*(.*?)(?=\nclass\s|\Z)'
            
            for match in re.finditer(model_pattern, content, re.DOTALL):
                model_name = match.group(1)
                model_body = match.group(2)
                
                # Ignorar managers y clases auxiliares
                if 'Manager' in model_name or 'QuerySet' in model_name or 'Mixin' in model_name:
                    continue
                
                # Buscar Meta class con indexes
                meta_pattern = r'class\s+Meta:.*?indexes\s*=\s*\[(.*?)\]'
                meta_match = re.search(meta_pattern, model_body, re.DOTALL)
                
                indices_existentes = []
                if meta_match:
                    indices_str = meta_match.group(1)
                    # Extraer campos de los índices
                    field_pattern = r'fields=\[([^\]]+)\]'
                    for field_match in re.finditer(field_pattern, indices_str):
                        fields = field_match.group(1)
                        # Limpiar y extraer nombres de campos
                        field_names = re.findall(r'["\']([^"\']+)["\']', fields)
                        indices_existentes.append(field_names)
                
                # Buscar ForeignKeys
                fk_pattern = r'(\w+)\s*=\s*models\.ForeignKey'
                fks = [m.group(1) for m in re.finditer(fk_pattern, model_body)]
                
                # Buscar campos con unique=True
                unique_pattern = r'(\w+)\s*=\s*models\.\w+\([^)]*unique=True'
                uniques = [m.group(1) for m in re.finditer(unique_pattern, model_body)]
                
                # Buscar db_table
                table_pattern = r'db_table\s*=\s*["\'](\w+)["\']'
                table_match = re.search(table_pattern, model_body)
                db_table = table_match.group(1) if table_match else model_name.lower()
                
                model_info = {
                    'app': app_name,
                    'modelo': model_name,
                    'tabla': db_table,
                    'indices_existentes': indices_existentes,
                    'foreign_keys': fks,
                    'campos_unique': uniques
                }
                
                indices_por_modelo[f"{app_name}.{model_name}"] = model_info
                
                # Sugerencias de índices
                # FKs sin índice explícito (Django los crea automáticamente, pero verificamos)
                for fk in fks:
                    # Verificar si ya hay un índice que incluye este campo
                    tiene_indice = any(fk in idx for idx in indices_existentes)
                    if not tiene_indice:
                        sugerencias.append({
                            'modelo': f"{app_name}.{model_name}",
                            'tipo': 'FK automático',
                            'campos': [fk],
                            'razon': 'Django crea índice automático para FKs'
                        })
                
        except Exception as e:
            print(f"Error procesando {model_file}: {e}")
    
    # Reporte
    print(f"\n{'='*80}")
    print("MODELOS CON ÍNDICES DEFINIDOS")
    print(f"{'='*80}\n")
    
    modelos_con_indices = {k: v for k, v in indices_por_modelo.items() if v['indices_existentes']}
    modelos_sin_indices = {k: v for k, v in indices_por_modelo.items() if not v['indices_existentes']}
    
    print(f"✅ Modelos con índices explícitos: {len(modelos_con_indices)}")
    print(f"⚠️  Modelos sin índices explícitos: {len(modelos_sin_indices)}\n")
    
    for model_key, info in sorted(modelos_con_indices.items()):
        print(f"\n📊 {model_key} (tabla: {info['tabla']})")
        print(f"   Índices definidos: {len(info['indices_existentes'])}")
        for idx in info['indices_existentes']:
            print(f"     • {', '.join(idx)}")
        if info['foreign_keys']:
            print(f"   Foreign Keys: {', '.join(info['foreign_keys'])}")
        if info['campos_unique']:
            print(f"   Campos UNIQUE: {', '.join(info['campos_unique'])}")
    
    # Modelos sin índices
    if modelos_sin_indices:
        print(f"\n{'='*80}")
        print("⚠️  MODELOS SIN ÍNDICES EXPLÍCITOS")
        print(f"{'='*80}\n")
        
        for model_key, info in sorted(modelos_sin_indices.items()):
            print(f"\n{model_key} (tabla: {info['tabla']})")
            if info['foreign_keys']:
                print(f"   • Foreign Keys: {', '.join(info['foreign_keys'])} (índices automáticos)")
            if info['campos_unique']:
                print(f"   • Campos UNIQUE: {', '.join(info['campos_unique'])} (índices automáticos)")
            if not info['foreign_keys'] and not info['campos_unique']:
                print(f"   ⚠️  Sin índices (considerar agregar para campos de consulta frecuente)")
    
    # Sugerencias basadas en patrones comunes
    print(f"\n{'='*80}")
    print("💡 SUGERENCIAS DE ÍNDICES ADICIONALES")
    print(f"{'='*80}\n")
    
    print("Basadas en patrones comunes de consulta:\n")
    
    sugerencias_patrones = [
        {
            'modelo': 'ventas.Ventas',
            'campos': ['fecha', 'id_cliente'],
            'razon': 'Consultas frecuentes por fecha y cliente'
        },
        {
            'modelo': 'ventas.Ventas',
            'campos': ['estado_pago', 'fecha'],
            'razon': 'Filtrado por estado de pago y ordenamiento por fecha'
        },
        {
            'modelo': 'compras.Compras',
            'campos': ['fecha', 'id_proveedor'],
            'razon': 'Consultas frecuentes por fecha y proveedor'
        },
        {
            'modelo': 'cobros.Tarjetas',
            'campos': ['estado', 'id_hijo'],
            'razon': 'Búsqueda de tarjetas activas por hijo'
        },
        {
            'modelo': 'inventario.MovimientosStock',
            'campos': ['fecha_hora', 'id_producto'],
            'razon': 'Historial de movimientos por producto'
        },
        {
            'modelo': 'clientes.Clientes',
            'campos': ['estado', 'id_tipo_cliente'],
            'razon': 'Filtrado de clientes activos por tipo'
        }
    ]
    
    for sug in sugerencias_patrones:
        modelo_key = sug['modelo']
        if modelo_key in indices_por_modelo:
            info = indices_por_modelo[modelo_key]
            # Verificar si ya existe este índice
            campos_set = set(sug['campos'])
            ya_existe = any(set(idx) == campos_set for idx in info['indices_existentes'])
            
            if not ya_existe:
                print(f"📌 {sug['modelo']}")
                print(f"   Campos sugeridos: {', '.join(sug['campos'])}")
                print(f"   Razón: {sug['razon']}")
                print(f"   Código sugerido:")
                print(f"   models.Index(fields={sug['campos']}, name='idx_{info['tabla']}_{'_'.join(sug['campos'][:2])}')")
                print()
    
    # Resumen final
    print(f"\n{'='*80}")
    print("📈 RESUMEN")
    print(f"{'='*80}\n")
    
    total_modelos = len(indices_por_modelo)
    total_con_indices = len(modelos_con_indices)
    total_indices = sum(len(info['indices_existentes']) for info in indices_por_modelo.values())
    
    print(f"Total de modelos analizados: {total_modelos}")
    print(f"Modelos con índices explícitos: {total_con_indices} ({total_con_indices/total_modelos*100:.1f}%)")
    print(f"Total de índices definidos: {total_indices}")
    print(f"\n✅ Estado general: {'Excelente' if total_con_indices/total_modelos > 0.6 else 'Bueno' if total_con_indices/total_modelos > 0.4 else 'Mejorable'}")
    
    print(f"\n{'='*80}")


if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    root_dir = Path(__file__).parent
    
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    
    analizar_indices_modelos(root_dir)
