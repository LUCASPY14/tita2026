#!/usr/bin/env python3
"""
Análisis Detallado de Consistencia de Base de Datos
Compara las columnas de las tablas principales con su uso en backend y frontend
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Modelos principales a analizar
MODELOS_PRINCIPALES = [
    ('clientes', 'Clientes'),
    ('clientes', 'Hijos'),
    ('clientes', 'TiposCliente'),
    ('ventas', 'Ventas'),
    ('ventas', 'DetallesVenta'),
    ('ventas', 'PagosVentas'),
    ('productos', 'Productos'),
    ('productos', 'Categorias'),
    ('productos', 'PreciosPorLista'),
    ('compras', 'Compras'),
    ('compras', 'DetallesCompra'),
    ('compras', 'Proveedores'),
    ('usuarios', 'Empleados'),
    ('usuarios', 'Roles'),
    ('cobros', 'Tarjetas'),
    ('cobros', 'CargasSaldo'),
    ('inventario', 'StockUnico'),
    ('inventario', 'MovimientosStock'),
    ('almuerzos', 'PlanesAlmuerzo'),
    ('almuerzos', 'SuscripcionesAlmuerzo'),
    ('contabilidad', 'Impuestos'),
    ('contabilidad', 'CierresCaja'),
    ('core', 'MediosPago'),
]


def extraer_campos_modelo(app_name, model_name, root_dir):
    """Extrae campos de un modelo específico"""
    model_file = Path(root_dir) / "backend" / "apps" / app_name / "models.py"
    
    if not model_file.exists():
        return None
    
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la clase del modelo
        pattern = rf'class\s+{model_name}\(.*models\.Model.*?\):\s*(.*?)(?=\nclass\s|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        model_body = match.group(1)
        
        # Extraer campos (models.XField)
        fields = {}
        field_pattern = r'(\w+)\s*=\s*models\.(\w+)\([^)]*\)'
        
        for field_match in re.finditer(field_pattern, model_body):
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            
            # Excluir propiedades y métodos
            if field_name not in ['objects', 'Meta', 'DoesNotExist']:
                # Extraer información adicional del campo
                field_def = field_match.group(0)
                
                # Verificar si es nullable
                is_null = 'null=True' in field_def
                is_blank = 'blank=True' in field_def
                is_unique = 'unique=True' in field_def
                
                # Verificar si es ForeignKey
                is_fk = field_type in ['ForeignKey', 'OneToOneField']
                
                # Extraer help_text si existe
                help_match = re.search(r'help_text=["\']([^"\']+)["\']', field_def)
                help_text = help_match.group(1) if help_match else ''
                
                fields[field_name] = {
                    'type': field_type,
                    'nullable': is_null,
                    'blank': is_blank,
                    'unique': is_unique,
                    'is_fk': is_fk,
                    'help_text': help_text
                }
        
        return fields
        
    except Exception as e:
        print(f"Error leyendo {model_file}: {e}")
        return None


def extraer_campos_serializer(app_name, model_name, root_dir):
    """Extrae campos de un serializer específico"""
    serializer_file = Path(root_dir) / "backend" / "apps" / app_name / "serializers.py"
    
    if not serializer_file.exists():
        return None
    
    try:
        with open(serializer_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar serializer correspondiente
        serializer_name = f'{model_name}Serializer'
        pattern = rf'class\s+{serializer_name}\(.*?Serializer.*?\):\s*(.*?)(?=\nclass\s|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            # Intentar variantes
            for variant in [f'{model_name}ListSerializer', f'{model_name}DetailSerializer', 
                          f'{model_name}BaseSerializer']:
                pattern = rf'class\s+{variant}\(.*?Serializer.*?\):\s*(.*?)(?=\nclass\s|\Z)'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    serializer_name = variant
                    break
        
        if not match:
            return None
        
        serializer_body = match.group(1)
        
        # Extraer campos de Meta.fields
        meta_fields_pattern = r'class\s+Meta:.*?fields\s*=\s*(\[.*?\]|\'__all__\'|"__all__"|\(.*?\))'
        meta_match = re.search(meta_fields_pattern, serializer_body, re.DOTALL)
        
        if meta_match:
            fields_str = meta_match.group(1)
            
            if '__all__' in fields_str:
                return {'__all__': True, 'serializer_name': serializer_name}
            
            # Extraer nombres de campos
            field_names = re.findall(r'["\'](\w+)["\']', fields_str)
            return {'fields': field_names, 'serializer_name': serializer_name}
        
        return None
        
    except Exception as e:
        print(f"Error leyendo {serializer_file}: {e}")
        return None


def buscar_uso_frontend(model_name, root_dir):
    """Busca interfaces TypeScript relacionadas con el modelo"""
    frontend_dir = Path(root_dir) / "frontend" / "src"
    
    if not frontend_dir.exists():
        return []
    
    interfaces_encontradas = []
    
    # Buscar en types/index.ts
    types_file = frontend_dir / "types" / "index.ts"
    if types_file.exists():
        try:
            with open(types_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar interface con nombre similar al modelo
            # Normalizar nombre: Clientes → Cliente, Empleados → Empleado, etc.
            singular_name = model_name.rstrip('s')
            
            for name_variant in [model_name, singular_name, model_name.lower(), singular_name.lower()]:
                pattern = rf'(?:export\s+)?interface\s+{name_variant}\s*\{{([^}}]+)\}}'
                match = re.search(pattern, content, re.IGNORECASE)
                
                if match:
                    interface_body = match.group(1)
                    
                    # Extraer propiedades
                    prop_pattern = r'(\w+)\??:\s*([^;]+);'
                    fields = {}
                    
                    for prop_match in re.finditer(prop_pattern, interface_body):
                        prop_name = prop_match.group(1)
                        prop_type = prop_match.group(2).strip()
                        fields[prop_name] = prop_type
                    
                    interfaces_encontradas.append({
                        'interface_name': name_variant,
                        'file': 'types/index.ts',
                        'fields': fields
                    })
                    break
        
        except Exception as e:
            pass
    
    return interfaces_encontradas


def generar_reporte_detallado(root_dir):
    """Genera reporte detallado de consistencia"""
    print("="*100)
    print("REPORTE DETALLADO DE VERIFICACIÓN DE CONSISTENCIA - BASE DE DATOS TITADB")
    print("="*100)
    
    reporte = {
        'modelos_analizados': [],
        'resumen': {
            'total_modelos': len(MODELOS_PRINCIPALES),
            'con_serializer': 0,
            'sin_serializer': 0,
            'con_interface_frontend': 0,
            'sin_interface_frontend': 0,
            'inconsistencias_totales': 0
        },
        'inconsistencias': []
    }
    
    for app_name, model_name in MODELOS_PRINCIPALES:
        print(f"\n{'='*100}")
        print(f"MODELO: {app_name}.{model_name}")
        print(f"{'='*100}")
        
        modelo_info = {
            'app': app_name,
            'modelo': model_name,
            'campos_modelo': {},
            'serializer': None,
            'frontend': [],
            'problemas': []
        }
        
        # 1. Extraer campos del modelo
        campos_modelo = extraer_campos_modelo(app_name, model_name, root_dir)
        
        if not campos_modelo:
            print(f"⚠️  ADVERTENCIA: No se pudo leer el modelo {model_name}")
            modelo_info['problemas'].append(f"Modelo no encontrado o no pudo ser leído")
            reporte['modelos_analizados'].append(modelo_info)
            continue
        
        modelo_info['campos_modelo'] = campos_modelo
        
        print(f"\n📋 CAMPOS DEL MODELO ({len(campos_modelo)} campos):")
        for campo, info in sorted(campos_modelo.items()):
            nullable_str = " [NULL]" if info['nullable'] else ""
            unique_str = " [UNIQUE]" if info['unique'] else ""
            fk_str = " [FK]" if info['is_fk'] else ""
            print(f"  • {campo}: {info['type']}{nullable_str}{unique_str}{fk_str}")
            if info['help_text']:
                print(f"    └─ {info['help_text']}")
        
        # 2. Extraer campos del serializer
        campos_serializer = extraer_campos_serializer(app_name, model_name, root_dir)
        
        if not campos_serializer:
            print(f"\n❌ SERIALIZER: No encontrado")
            modelo_info['problemas'].append(f"No hay serializer para {model_name}")
            reporte['resumen']['sin_serializer'] += 1
        else:
            reporte['resumen']['con_serializer'] += 1
            modelo_info['serializer'] = campos_serializer
            
            if campos_serializer.get('__all__'):
                print(f"\n✅ SERIALIZER: {campos_serializer['serializer_name']} (usa '__all__' - todos los campos)")
            else:
                campos_ser = campos_serializer.get('fields', [])
                print(f"\n📝 SERIALIZER: {campos_serializer['serializer_name']} ({len(campos_ser)} campos)")
                
                # Comparar campos
                campos_modelo_set = set(campos_modelo.keys())
                campos_serializer_set = set(campos_ser)
                
                faltantes = campos_modelo_set - campos_serializer_set
                extras = campos_serializer_set - campos_modelo_set
                
                if faltantes:
                    print(f"\n  ⚠️  Campos del modelo NO en serializer:")
                    for campo in sorted(faltantes):
                        print(f"    • {campo}")
                    modelo_info['problemas'].append(f"Campos faltantes en serializer: {', '.join(faltantes)}")
                    reporte['resumen']['inconsistencias_totales'] += len(faltantes)
                
                if extras:
                    print(f"\n  ℹ️  Campos adicionales en serializer (computed/extra):")
                    for campo in sorted(extras):
                        print(f"    • {campo}")
        
        # 3. Buscar uso en frontend
        interfaces_frontend = buscar_uso_frontend(model_name, root_dir)
        
        if not interfaces_frontend:
            print(f"\n❌ FRONTEND: No se encontró interface para {model_name}")
            reporte['resumen']['sin_interface_frontend'] += 1
        else:
            reporte['resumen']['con_interface_frontend'] += 1
            modelo_info['frontend'] = interfaces_frontend
            
            for interface in interfaces_frontend:
                print(f"\n🎨 FRONTEND: {interface['interface_name']} en {interface['file']} ({len(interface['fields'])} campos)")
                
                campos_frontend = set(interface['fields'].keys())
                campos_modelo_comparar = set(campos_modelo.keys())
                
                # En frontend a veces se usa id_modelo como 'id' solamente
                # o se usan nombres más amigables
                print(f"\n  Campos en interface:")
                for campo, tipo in sorted(interface['fields'].items()):
                    print(f"    • {campo}: {tipo}")
        
        reporte['modelos_analizados'].append(modelo_info)
    
    # Resumen final
    print(f"\n{'='*100}")
    print("RESUMEN FINAL")
    print(f"{'='*100}")
    print(f"\n📊 Estadísticas:")
    print(f"  • Total de modelos analizados: {reporte['resumen']['total_modelos']}")
    print(f"  • Con serializer: {reporte['resumen']['con_serializer']}")
    print(f"  • Sin serializer: {reporte['resumen']['sin_serializer']}")
    print(f"  • Con interface frontend: {reporte['resumen']['con_interface_frontend']}")
    print(f"  • Sin interface frontend: {reporte['resumen']['sin_interface_frontend']}")
    print(f"  • Inconsistencias detectadas: {reporte['resumen']['inconsistencias_totales']}")
    
    # Guardar reporte en JSON
    report_file = Path(root_dir) / "REPORTE_CONSISTENCIA_DB_DETALLADO.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Reporte detallado guardado en: {report_file}")
    
    # Crear reporte Markdown
    crear_reporte_markdown(reporte, root_dir)


def crear_reporte_markdown(reporte, root_dir):
    """Crea un reporte en formato Markdown"""
    md_file = Path(root_dir) / "VERIFICACION_CONSISTENCIA_DB.md"
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Verificación de Consistencia - Base de Datos TITADB\n\n")
        f.write(f"**Fecha:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Resumen Ejecutivo\n\n")
        f.write(f"- **Total de modelos analizados:** {reporte['resumen']['total_modelos']}\n")
        f.write(f"- **Modelos con serializer:** {reporte['resumen']['con_serializer']}\n")
        f.write(f"- **Modelos sin serializer:** {reporte['resumen']['sin_serializer']}\n")
        f.write(f"- **Modelos con interface frontend:** {reporte['resumen']['con_interface_frontend']}\n")
        f.write(f"- **Modelos sin interface frontend:** {reporte['resumen']['sin_interface_frontend']}\n")
        f.write(f"- **Inconsistencias detectadas:** {reporte['resumen']['inconsistencias_totales']}\n\n")
        
        f.write("## Análisis Detallado por Modelo\n\n")
        
        for modelo in reporte['modelos_analizados']:
            f.write(f"### {modelo['app']}.{modelo['modelo']}\n\n")
            
            # Campos del modelo
            if modelo['campos_modelo']:
                f.write("#### Campos del Modelo\n\n")
                f.write("| Campo | Tipo | Características |\n")
                f.write("|-------|------|----------------|\n")
                
                for campo, info in sorted(modelo['campos_modelo'].items()):
                    caracteristicas = []
                    if info.get('nullable'):
                        caracteristicas.append('NULL')
                    if info.get('unique'):
                        caracteristicas.append('UNIQUE')
                    if info.get('is_fk'):
                        caracteristicas.append('FK')
                    
                    caract_str = ', '.join(caracteristicas) if caracteristicas else '-'
                    f.write(f"| `{campo}` | {info['type']} | {caract_str} |\n")
                
                f.write("\n")
            
            # Serializer
            if modelo['serializer']:
                ser = modelo['serializer']
                f.write(f"#### Serializer: `{ser.get('serializer_name', 'N/A')}`\n\n")
                
                if ser.get('__all__'):
                    f.write("✅ Usa `'__all__'` - incluye todos los campos del modelo\n\n")
                elif 'fields' in ser:
                    f.write(f"Campos incluidos: {', '.join(f'`{c}`' for c in ser['fields'])}\n\n")
            else:
                f.write("#### Serializer\n\n")
                f.write("❌ No se encontró serializer para este modelo\n\n")
            
            # Frontend
            if modelo['frontend']:
                for interface in modelo['frontend']:
                    f.write(f"#### Frontend Interface: `{interface['interface_name']}`\n\n")
                    f.write(f"**Archivo:** `{interface['file']}`\n\n")
                    f.write("| Campo | Tipo TypeScript |\n")
                    f.write("|-------|----------------|\n")
                    
                    for campo, tipo in sorted(interface['fields'].items()):
                        f.write(f"| `{campo}` | `{tipo}` |\n")
                    
                    f.write("\n")
            else:
                f.write("#### Frontend\n\n")
                f.write("❌ No se encontró interface TypeScript para este modelo\n\n")
            
            # Problemas
            if modelo['problemas']:
                f.write("#### ⚠️ Problemas Detectados\n\n")
                for problema in modelo['problemas']:
                    f.write(f"- {problema}\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        f.write("## Recomendaciones\n\n")
        f.write("1. **Serializers faltantes:** Crear serializers para los modelos que no los tienen\n")
        f.write("2. **Interfaces TypeScript:** Definir interfaces para los modelos sin representación en frontend\n")
        f.write("3. **Campos faltantes en serializers:** Agregar campos del modelo o usar `'__all__'`\n")
        f.write("4. **Documentación:** Agregar help_text a todos los campos para mejor comprensión\n")
    
    print(f"✅ Reporte Markdown guardado en: {md_file}")


if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    root_dir = Path(__file__).parent
    
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    
    generar_reporte_detallado(root_dir)
