#!/usr/bin/env python3
"""
Verificación Exhaustiva de Consistencia Base de Datos TITADB
Análisis detallado campo por campo entre DB, Backend y Frontend
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class VerificadorExhaustivo:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        
        self.modelos_db = {}
        self.serializers = {}
        self.interfaces_ts = {}
        self.problemas = []
        
    def extraer_campos_modelo_completo(self, app_name, model_name):
        """Extrae todos los campos de un modelo Django con información detallada"""
        model_file = self.backend_dir / "apps" / app_name / "models.py"
        
        if not model_file.exists():
            return None
        
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar la clase del modelo exacto - asegurar que sea el modelo correcto
            # Primero, dividir el contenido en clases
            class_pattern = r'class\s+(\w+)\((.*?)\):(.*?)(?=\nclass\s|\Z)'
            classes = re.finditer(class_pattern, content, re.DOTALL)
            
            model_body = None
            for class_match in classes:
                class_name = class_match.group(1)
                class_inheritance = class_match.group(2)
                class_content = class_match.group(3)
                
                # Verificar que sea exactamente el modelo que buscamos
                if class_name == model_name and 'models.Model' in class_inheritance:
                    model_body = class_content
                    break
            
            if not model_body:
                return None
            
            # Extraer campos con toda la información
            campos = {}
            
            # Patrón para campos de modelos
            field_pattern = r'(\w+)\s*=\s*models\.(\w+)\((.*?)\)(?:\s*#.*)?$'
            
            for line in model_body.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('"""') or line.startswith('class ') or line.startswith('def ') or line.startswith('@'):
                    continue
                
                match = re.match(field_pattern, line)
                if match:
                    field_name = match.group(1)
                    field_type = match.group(2)
                    field_args = match.group(3)
                    
                    # Excluir objetos y Meta
                    if field_name in ['objects', 'Meta', 'DoesNotExist']:
                        continue
                    
                    # Parsear argumentos del campo
                    is_null = 'null=True' in field_args or 'null = True' in field_args
                    is_blank = 'blank=True' in field_args or 'blank = True' in field_args
                    is_unique = 'unique=True' in field_args or 'unique = True' in field_args
                    is_pk = 'primary_key=True' in field_args or 'primary_key = True' in field_args
                    
                    # Extraer max_length
                    max_length_match = re.search(r'max_length\s*=\s*(\d+)', field_args)
                    max_length = int(max_length_match.group(1)) if max_length_match else None
                    
                    # Extraer max_digits y decimal_places
                    max_digits_match = re.search(r'max_digits\s*=\s*(\d+)', field_args)
                    decimal_places_match = re.search(r'decimal_places\s*=\s*(\d+)', field_args)
                    max_digits = int(max_digits_match.group(1)) if max_digits_match else None
                    decimal_places = int(decimal_places_match.group(1)) if decimal_places_match else None
                    
                    # Extraer default
                    default_match = re.search(r'default\s*=\s*([^,)]+)', field_args)
                    default = default_match.group(1).strip() if default_match else None
                    
                    # Extraer help_text
                    help_text_match = re.search(r'help_text\s*=\s*["\']([^"\']+)["\']', field_args)
                    help_text = help_text_match.group(1) if help_text_match else None
                    
                    # Extraer db_column
                    db_column_match = re.search(r'db_column\s*=\s*["\']([^"\']+)["\']', field_args)
                    db_column = db_column_match.group(1) if db_column_match else field_name
                    
                    # Determinar si es relación
                    is_fk = field_type in ['ForeignKey', 'OneToOneField', 'ManyToManyField']
                    
                    # Extraer modelo relacionado si es FK
                    related_model = None
                    if is_fk:
                        related_match = re.search(r'["\']([^"\']+)["\']', field_args)
                        if related_match:
                            related_model = related_match.group(1)
                    
                    campos[field_name] = {
                        'type': field_type,
                        'db_column': db_column,
                        'nullable': is_null,
                        'blank': is_blank,
                        'unique': is_unique,
                        'primary_key': is_pk,
                        'max_length': max_length,
                        'max_digits': max_digits,
                        'decimal_places': decimal_places,
                        'default': default,
                        'help_text': help_text,
                        'is_relation': is_fk,
                        'related_model': related_model,
                    }
            
            # Buscar db_table
            table_pattern = r'db_table\s*=\s*["\'](\w+)["\']'
            table_match = re.search(table_pattern, model_body)
            db_table = table_match.group(1) if table_match else model_name.lower()
            
            return {
                'campos': campos,
                'db_table': db_table,
                'total_campos': len(campos)
            }
            
        except Exception as e:
            print(f"{Colors.FAIL}Error procesando {model_file}: {e}{Colors.ENDC}")
            return None
    
    def extraer_serializer_completo(self, app_name, model_name):
        """Extrae información completa del serializer"""
        serializer_file = self.backend_dir / "apps" / app_name / "serializers.py"
        
        if not serializer_file.exists():
            return None
        
        try:
            with open(serializer_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar serializer
            serializer_variants = [
                f'{model_name}Serializer',
                f'{model_name}ListSerializer',
                f'{model_name}DetailSerializer',
                f'{model_name}BaseSerializer',
            ]
            
            for variant in serializer_variants:
                pattern = rf'class\s+{variant}\(.*?\):\s*(.*?)(?=\nclass\s|\Z)'
                match = re.search(pattern, content, re.DOTALL)
                
                if match:
                    serializer_body = match.group(1)
                    
                    # Extraer Meta.fields
                    meta_pattern = r'class\s+Meta:.*?fields\s*=\s*(\[.*?\]|\'__all__\'|"__all__"|\(.*?\))'
                    meta_match = re.search(meta_pattern, serializer_body, re.DOTALL)
                    
                    if meta_match:
                        fields_str = meta_match.group(1)
                        
                        if '__all__' in fields_str:
                            return {
                                'serializer_name': variant,
                                'usa_all': True,
                                'campos': None,
                                'campos_extra': [],
                                'read_only': [],
                            }
                        
                        # Extraer campos
                        field_names = re.findall(r'["\'](\w+)["\']', fields_str)
                        
                        # Buscar campos extra (SerializerMethodField, etc.)
                        extra_fields = []
                        extra_pattern = r'(\w+)\s*=\s*serializers\.(\w+Field)\('
                        for extra_match in re.finditer(extra_pattern, serializer_body):
                            extra_name = extra_match.group(1)
                            extra_type = extra_match.group(2)
                            if extra_name not in field_names:
                                extra_fields.append({
                                    'name': extra_name,
                                    'type': extra_type
                                })
                        
                        # Buscar campos read_only en Meta
                        read_only_pattern = r'read_only_fields\s*=\s*\((.*?)\)'
                        read_only_match = re.search(read_only_pattern, serializer_body)
                        read_only = []
                        if read_only_match:
                            read_only = re.findall(r'["\'](\w+)["\']', read_only_match.group(1))
                        
                        return {
                            'serializer_name': variant,
                            'usa_all': False,
                            'campos': field_names,
                            'campos_extra': extra_fields,
                            'read_only': read_only,
                        }
            
            return None
            
        except Exception as e:
            print(f"{Colors.FAIL}Error procesando serializer: {e}{Colors.ENDC}")
            return None
    
    def extraer_interface_typescript(self, model_name):
        """Extrae interface TypeScript del frontend"""
        types_file = self.frontend_dir / "src" / "types" / "index.ts"
        
        if not types_file.exists():
            return None
        
        try:
            with open(types_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mapeo manual de nombres de modelos Django a interfaces TypeScript
            manual_mappings = {
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
            }
            
            # Normalizar nombre usando mapeo manual o reglas automáticas
            interface_variants = []
            
            # Primero intentar mapeo manual
            if model_name in manual_mappings:
                interface_variants.append(manual_mappings[model_name])
            
            # Luego intentar nombre exacto y variantes comunes
            interface_variants.extend([
                model_name,
                model_name.rstrip('s'),  # Eliminar 's' final
                model_name[:-2] if model_name.endswith('es') else model_name,  # Naciones -> Nacion
            ])
            
            for variant in interface_variants:
                pattern = rf'export\s+interface\s+{variant}\s*\{{([^}}]+)\}}'
                match = re.search(pattern, content, re.IGNORECASE)
                
                if match:
                    interface_body = match.group(1)
                    
                    # Extraer propiedades
                    campos = {}
                    prop_pattern = r'(\w+)\??:\s*([^;]+);'
                    
                    for prop_match in re.finditer(prop_pattern, interface_body):
                        prop_name = prop_match.group(1)
                        prop_type = prop_match.group(2).strip()
                        
                        # Determinar si es opcional
                        is_optional = '?' in prop_match.group(0)
                        
                        campos[prop_name] = {
                            'type': prop_type,
                            'optional': is_optional
                        }
                    
                    return {
                        'interface_name': variant,
                        'campos': campos,
                        'total_campos': len(campos)
                    }
            
            return None
            
        except Exception as e:
            print(f"{Colors.FAIL}Error procesando interface: {e}{Colors.ENDC}")
            return None
    
    def verificar_modelo(self, app_name, model_name):
        """Verificación exhaustiva de un modelo específico"""
        print(f"\n{Colors.HEADER}{'='*100}{Colors.ENDC}")
        print(f"{Colors.HEADER}VERIFICACIÓN: {app_name}.{model_name}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*100}{Colors.ENDC}")
        
        problemas_modelo = []
        
        # 1. Extraer información del modelo
        print(f"\n{Colors.OKBLUE}1. Analizando modelo Django...{Colors.ENDC}")
        modelo_info = self.extraer_campos_modelo_completo(app_name, model_name)
        
        if not modelo_info:
            print(f"{Colors.FAIL}   [X] No se pudo leer el modelo{Colors.ENDC}")
            problemas_modelo.append({
                'tipo': 'modelo_no_encontrado',
                'mensaje': f'No se encontró el modelo {model_name} en {app_name}'
            })
            return problemas_modelo
        
        campos_modelo = modelo_info['campos']
        print(f"{Colors.OKGREEN}   [OK] Modelo encontrado: {len(campos_modelo)} campos{Colors.ENDC}")
        print(f"   [INFO] Tabla en BD: {modelo_info['db_table']}")
        
        # Mostrar campos del modelo
        print(f"\n   {Colors.BOLD}Campos del modelo:{Colors.ENDC}")
        for campo, info in sorted(campos_modelo.items()):
            caracteristicas = []
            if info['primary_key']:
                caracteristicas.append('PK')
            if info['unique']:
                caracteristicas.append('UNIQUE')
            if info['nullable']:
                caracteristicas.append('NULL')
            if info['is_relation']:
                caracteristicas.append(f"FK→{info['related_model']}")
            
            caract_str = f" [{', '.join(caracteristicas)}]" if caracteristicas else ""
            help_str = f"\n      💬 {info['help_text']}" if info['help_text'] else ""
            
            print(f"      • {campo}: {info['type']}{caract_str}{help_str}")
        
        # 2. Verificar serializer
        print(f"\n{Colors.OKBLUE}2. Analizando serializer...{Colors.ENDC}")
        serializer_info = self.extraer_serializer_completo(app_name, model_name)
        
        if not serializer_info:
            print(f"{Colors.WARNING}   ⚠️  No se encontró serializer{Colors.ENDC}")
            problemas_modelo.append({
                'tipo': 'serializer_no_encontrado',
                'mensaje': f'No hay serializer para {model_name}'
            })
        else:
            print(f"{Colors.OKGREEN}   ✅ Serializer: {serializer_info['serializer_name']}{Colors.ENDC}")
            
            if serializer_info['usa_all']:
                print(f"   📝 Usa '__all__' - todos los campos del modelo incluidos")
            else:
                campos_ser = set(serializer_info['campos'])
                campos_mod = set(campos_modelo.keys())
                
                print(f"   📝 Campos explícitos: {len(campos_ser)}")
                
                # Comparar
                faltantes = campos_mod - campos_ser
                extras = campos_ser - campos_mod
                
                if faltantes:
                    print(f"\n   {Colors.WARNING}⚠️  Campos del modelo NO en serializer:{Colors.ENDC}")
                    for campo in sorted(faltantes):
                        print(f"      • {campo}")
                    problemas_modelo.append({
                        'tipo': 'campos_faltantes_serializer',
                        'campos': list(faltantes)
                    })
                
                if extras:
                    print(f"\n   {Colors.OKCYAN}ℹ️  Campos adicionales en serializer:{Colors.ENDC}")
                    for campo in sorted(extras):
                        print(f"      • {campo}")
                
                if serializer_info['campos_extra']:
                    print(f"\n   {Colors.OKCYAN}ℹ️  Campos calculados/extra:{Colors.ENDC}")
                    for extra in serializer_info['campos_extra']:
                        print(f"      • {extra['name']}: {extra['type']}")
        
        # 3. Verificar interface TypeScript
        print(f"\n{Colors.OKBLUE}3. Analizando interface TypeScript...{Colors.ENDC}")
        interface_info = self.extraer_interface_typescript(model_name)
        
        if not interface_info:
            print(f"{Colors.WARNING}   ⚠️  No se encontró interface TypeScript{Colors.ENDC}")
            problemas_modelo.append({
                'tipo': 'interface_no_encontrada',
                'mensaje': f'No hay interface TypeScript para {model_name}'
            })
        else:
            print(f"{Colors.OKGREEN}   ✅ Interface: {interface_info['interface_name']}{Colors.ENDC}")
            print(f"   📝 Campos: {interface_info['total_campos']}")
            
            campos_ts = set(interface_info['campos'].keys())
            campos_mod = set(campos_modelo.keys())
            
            # Ajustar nombres de campos (id_campo → id, etc.)
            # Los campos en frontend a veces tienen nombres diferentes
            print(f"\n   {Colors.BOLD}Campos en interface:{Colors.ENDC}")
            for campo, info in sorted(interface_info['campos'].items()):
                opcional = " (opcional)" if info['optional'] else ""
                print(f"      • {campo}: {info['type']}{opcional}")
            
            # Comparación básica
            campos_comunes = campos_ts & campos_mod
            if campos_comunes:
                print(f"\n   {Colors.OKGREEN}✅ Campos coincidentes: {len(campos_comunes)}{Colors.ENDC}")
            
            # Campos que están en interface pero no en modelo (pueden ser calculados)
            extras_ts = campos_ts - campos_mod
            if extras_ts:
                print(f"\n   {Colors.OKCYAN}ℹ️  Campos adicionales/calculados en frontend:{Colors.ENDC}")
                for campo in sorted(extras_ts):
                    print(f"      • {campo}")
        
        # 4. Resumen
        print(f"\n{Colors.BOLD}📊 RESUMEN:{Colors.ENDC}")
        if not problemas_modelo:
            print(f"{Colors.OKGREEN}   ✅ Modelo completamente consistente{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}   ⚠️  {len(problemas_modelo)} problema(s) detectado(s){Colors.ENDC}")
        
        return problemas_modelo
    
    def ejecutar_verificacion(self):
        """Ejecuta la verificación exhaustiva en modelos principales"""
        print(f"{Colors.BOLD}{'='*100}{Colors.ENDC}")
        print(f"{Colors.BOLD}VERIFICACIÓN EXHAUSTIVA DE CONSISTENCIA - BASE DE DATOS TITADB{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*100}{Colors.ENDC}")
        
        # Modelos principales a verificar
        modelos_principales = [
            ('clientes', 'Clientes'),
            ('clientes', 'Hijos'),
            ('clientes', 'TiposCliente'),
            ('ventas', 'Ventas'),
            ('ventas', 'DetallesVenta'),
            ('productos', 'Productos'),
            ('productos', 'Categorias'),
            ('productos', 'PreciosPorLista'),
            ('compras', 'Compras'),
            ('compras', 'DetallesCompra'),
            ('compras', 'Proveedores'),
            ('usuarios', 'Empleados'),
            ('usuarios', 'Roles'),
            ('cobros', 'PagosClientes'),
            ('inventario', 'StockUnico'),
            ('inventario', 'MovimientosStock'),
            ('contabilidad', 'Impuestos'),
            ('contabilidad', 'CierresCaja'),
            ('core', 'MediosPago'),
            ('almuerzos', 'PlanesAlmuerzo'),
            ('almuerzos', 'SuscripcionesAlmuerzo'),
        ]
        
        todos_los_problemas = {}
        
        for app_name, model_name in modelos_principales:
            problemas = self.verificar_modelo(app_name, model_name)
            if problemas:
                todos_los_problemas[f"{app_name}.{model_name}"] = problemas
        
        # Reporte final
        print(f"\n{Colors.BOLD}{'='*100}{Colors.ENDC}")
        print(f"{Colors.BOLD}REPORTE FINAL{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*100}{Colors.ENDC}")
        
        print(f"\n📊 Estadísticas:")
        print(f"   • Total de modelos verificados: {len(modelos_principales)}")
        print(f"   • Modelos con problemas: {len(todos_los_problemas)}")
        print(f"   • Modelos sin problemas: {len(modelos_principales) - len(todos_los_problemas)}")
        
        if todos_los_problemas:
            print(f"\n{Colors.WARNING}⚠️  PROBLEMAS DETECTADOS:{Colors.ENDC}\n")
            
            for modelo, problemas in todos_los_problemas.items():
                print(f"   {Colors.WARNING}{modelo}:{Colors.ENDC}")
                for problema in problemas:
                    if problema['tipo'] == 'modelo_no_encontrado':
                        print(f"      • {problema['mensaje']}")
                    elif problema['tipo'] == 'serializer_no_encontrado':
                        print(f"      • {problema['mensaje']}")
                    elif problema['tipo'] == 'interface_no_encontrada':
                        print(f"      • {problema['mensaje']}")
                    elif problema['tipo'] == 'campos_faltantes_serializer':
                        print(f"      • Campos faltantes en serializer: {', '.join(problema['campos'])}")
                print()
        else:
            print(f"\n{Colors.OKGREEN}✅ ¡EXCELENTE! No se detectaron problemas de consistencia{Colors.ENDC}")
        
        # Guardar reporte JSON
        report_file = self.root_dir / "verificacion_exhaustiva_resultado.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(todos_los_problemas, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Colors.OKGREEN}✅ Reporte JSON guardado en: {report_file}{Colors.ENDC}")
        
        return len(todos_los_problemas) == 0


if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    root_dir = Path(__file__).parent
    
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    
    verificador = VerificadorExhaustivo(root_dir)
    exito = verificador.ejecutar_verificacion()
    
    sys.exit(0 if exito else 1)
