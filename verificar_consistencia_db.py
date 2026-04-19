#!/usr/bin/env python3
"""
Script para verificar la consistencia entre:
- Esquema de base de datos (modelos Django)
- Serializers (backend)
- Frontend (TypeScript interfaces y servicios)

Genera un reporte detallado de campos faltantes o inconsistentes
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ConsistencyChecker:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        
        self.models_data = {}
        self.serializers_data = {}
        self.frontend_interfaces = {}
        self.issues = []
        
    def extract_model_fields(self, model_file):
        """Extrae campos de un archivo models.py"""
        fields_by_model = {}
        
        try:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar clases que hereden de models.Model
            model_pattern = r'class\s+(\w+)\(.*models\.Model.*?\):\s*(.*?)(?=\n\s*class\s|\n\s*def\s+\w+\s*\(.*?\)\s*:\s*"""|\Z)'
            
            for match in re.finditer(model_pattern, content, re.DOTALL):
                model_name = match.group(1)
                model_body = match.group(2)
                
                # Extraer campos (models.XField)
                field_pattern = r'(\w+)\s*=\s*models\.(\w+)\('
                fields = {}
                
                for field_match in re.finditer(field_pattern, model_body):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    
                    # Verificar si es un campo de modelo y no otro tipo de definición
                    if field_name not in ['objects', 'Meta', 'DoesNotExist']:
                        fields[field_name] = field_type
                        
                if fields:
                    fields_by_model[model_name] = fields
                    
        except Exception as e:
            print(f"{Colors.FAIL}Error leyendo {model_file}: {e}{Colors.ENDC}")
            
        return fields_by_model
    
    def extract_serializer_fields(self, serializer_file):
        """Extrae campos de un archivo serializers.py"""
        fields_by_serializer = {}
        
        try:
            with open(serializer_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar clases que hereden de serializers
            serializer_pattern = r'class\s+(\w+)\(.*Serializer.*?\):\s*(.*?)(?=\n\s*class\s|\Z)'
            
            for match in re.finditer(serializer_pattern, content, re.DOTALL):
                serializer_name = match.group(1)
                serializer_body = match.group(2)
                
                # Extraer campos de Meta.fields
                meta_fields_pattern = r'class\s+Meta:.*?fields\s*=\s*(\[.*?\]|\'__all__\'|"__all__"|\(.*?\))'
                meta_match = re.search(meta_fields_pattern, serializer_body, re.DOTALL)
                
                if meta_match:
                    fields_str = meta_match.group(1)
                    
                    if '__all__' in fields_str:
                        fields_by_serializer[serializer_name] = ['__all__']
                    else:
                        # Extraer nombres de campos
                        field_names = re.findall(r'["\'](\w+)["\']', fields_str)
                        fields_by_serializer[serializer_name] = field_names
                        
                # También extraer campos definidos explícitamente
                explicit_fields = {}
                field_pattern = r'(\w+)\s*=\s*serializers\.(\w+)\('
                
                for field_match in re.finditer(field_pattern, serializer_body):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    explicit_fields[field_name] = field_type
                    
                if explicit_fields:
                    if serializer_name not in fields_by_serializer:
                        fields_by_serializer[serializer_name] = []
                    fields_by_serializer[serializer_name].extend(explicit_fields.keys())
                    
        except Exception as e:
            print(f"{Colors.FAIL}Error leyendo {serializer_file}: {e}{Colors.ENDC}")
            
        return fields_by_serializer
    
    def extract_frontend_interfaces(self, ts_file):
        """Extrae interfaces y tipos de archivos TypeScript"""
        interfaces = {}
        
        try:
            with open(ts_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar interfaces
            interface_pattern = r'(?:export\s+)?interface\s+(\w+)\s*\{([^}]+)\}'
            
            for match in re.finditer(interface_pattern, content, re.DOTALL):
                interface_name = match.group(1)
                interface_body = match.group(2)
                
                # Extraer propiedades
                prop_pattern = r'(\w+)\??:\s*([^;]+);'
                fields = {}
                
                for prop_match in re.finditer(prop_pattern, interface_body):
                    prop_name = prop_match.group(1)
                    prop_type = prop_match.group(2).strip()
                    fields[prop_name] = prop_type
                    
                if fields:
                    interfaces[interface_name] = fields
                    
        except Exception as e:
            print(f"{Colors.FAIL}Error leyendo {ts_file}: {e}{Colors.ENDC}")
            
        return interfaces
    
    def scan_backend_models(self):
        """Escanea todos los archivos models.py en el backend"""
        print(f"\n{Colors.HEADER}=== Escaneando Modelos del Backend ==={Colors.ENDC}")
        
        apps_dir = self.backend_dir / "apps"
        if not apps_dir.exists():
            print(f"{Colors.FAIL}No se encuentra el directorio apps: {apps_dir}{Colors.ENDC}")
            return
            
        for model_file in apps_dir.rglob("models.py"):
            app_name = model_file.parent.name
            print(f"{Colors.OKCYAN}Escaneando: {app_name}/models.py{Colors.ENDC}")
            
            fields = self.extract_model_fields(model_file)
            for model_name, model_fields in fields.items():
                full_name = f"{app_name}.{model_name}"
                self.models_data[full_name] = model_fields
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {model_name}: {len(model_fields)} campos")
                
    def scan_backend_serializers(self):
        """Escanea todos los archivos serializers.py en el backend"""
        print(f"\n{Colors.HEADER}=== Escaneando Serializers del Backend ==={Colors.ENDC}")
        
        apps_dir = self.backend_dir / "apps"
        if not apps_dir.exists():
            return
            
        for serializer_file in apps_dir.rglob("serializers.py"):
            app_name = serializer_file.parent.name
            print(f"{Colors.OKCYAN}Escaneando: {app_name}/serializers.py{Colors.ENDC}")
            
            fields = self.extract_serializer_fields(serializer_file)
            for serializer_name, serializer_fields in fields.items():
                full_name = f"{app_name}.{serializer_name}"
                self.serializers_data[full_name] = serializer_fields
                field_count = len(serializer_fields) if isinstance(serializer_fields, list) else '?'
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {serializer_name}: {field_count} campos")
                
    def scan_frontend_interfaces(self):
        """Escanea interfaces TypeScript en el frontend"""
        print(f"\n{Colors.HEADER}=== Escaneando Interfaces del Frontend ==={Colors.ENDC}")
        
        src_dir = self.frontend_dir / "src"
        if not src_dir.exists():
            print(f"{Colors.WARNING}No se encuentra el directorio src del frontend{Colors.ENDC}")
            return
            
        for ts_file in src_dir.rglob("*.ts"):
            # Ignorar archivos de test
            if '.spec.ts' in ts_file.name or '.test.ts' in ts_file.name:
                continue
                
            interfaces = self.extract_frontend_interfaces(ts_file)
            if interfaces:
                rel_path = ts_file.relative_to(src_dir)
                print(f"{Colors.OKCYAN}Escaneando: {rel_path}{Colors.ENDC}")
                
                for interface_name, interface_fields in interfaces.items():
                    full_name = f"{rel_path}:{interface_name}"
                    self.frontend_interfaces[full_name] = interface_fields
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {interface_name}: {len(interface_fields)} campos")
                    
    def compare_model_to_serializer(self):
        """Compara modelos con sus serializers correspondientes"""
        print(f"\n{Colors.HEADER}=== Comparando Modelos con Serializers ==={Colors.ENDC}")
        
        for model_full_name, model_fields in self.models_data.items():
            app_name, model_name = model_full_name.split('.')
            
            # Buscar serializer correspondiente
            serializer_name = f"{model_name}Serializer"
            serializer_full_name = f"{app_name}.{serializer_name}"
            
            if serializer_full_name not in self.serializers_data:
                # Intentar otras variantes
                alt_names = [
                    f"{app_name}.{model_name}BaseSerializer",
                    f"{app_name}.{model_name}ListSerializer",
                    f"{app_name}.{model_name}DetailSerializer",
                ]
                
                for alt_name in alt_names:
                    if alt_name in self.serializers_data:
                        serializer_full_name = alt_name
                        break
                else:
                    print(f"{Colors.WARNING}⚠ No se encontró serializer para {model_name}{Colors.ENDC}")
                    self.issues.append({
                        'type': 'missing_serializer',
                        'model': model_full_name,
                        'message': f'No hay serializer para {model_name}'
                    })
                    continue
                    
            serializer_fields = self.serializers_data[serializer_full_name]
            
            # Si el serializer usa __all__, no hay que verificar
            if '__all__' in serializer_fields:
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} {model_name} ↔ {serializer_name} (usa __all__)")
                continue
                
            # Comparar campos
            model_field_names = set(model_fields.keys())
            serializer_field_names = set(serializer_fields) if isinstance(serializer_fields, list) else set()
            
            # Campos del modelo que NO están en el serializer
            missing_in_serializer = model_field_names - serializer_field_names
            
            # Campos del serializer que NO están en el modelo
            extra_in_serializer = serializer_field_names - model_field_names
            
            if missing_in_serializer:
                print(f"{Colors.WARNING}⚠ {model_name}: Campos faltantes en serializer: {missing_in_serializer}{Colors.ENDC}")
                self.issues.append({
                    'type': 'fields_missing_in_serializer',
                    'model': model_full_name,
                    'serializer': serializer_full_name,
                    'fields': list(missing_in_serializer)
                })
                
            if extra_in_serializer:
                print(f"{Colors.OKCYAN}ℹ {model_name}: Campos adicionales en serializer: {extra_in_serializer}{Colors.ENDC}")
                
            if not missing_in_serializer and not extra_in_serializer:
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} {model_name} ↔ {serializer_name} (consistente)")
                
    def generate_report(self):
        """Genera un reporte final con todas las inconsistencias"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}REPORTE DE VERIFICACIÓN DE CONSISTENCIA{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Resumen:{Colors.ENDC}")
        print(f"  • Modelos encontrados: {Colors.OKBLUE}{len(self.models_data)}{Colors.ENDC}")
        print(f"  • Serializers encontrados: {Colors.OKBLUE}{len(self.serializers_data)}{Colors.ENDC}")
        print(f"  • Interfaces de frontend: {Colors.OKBLUE}{len(self.frontend_interfaces)}{Colors.ENDC}")
        print(f"  • Problemas detectados: {Colors.WARNING if self.issues else Colors.OKGREEN}{len(self.issues)}{Colors.ENDC}")
        
        if self.issues:
            print(f"\n{Colors.BOLD}Problemas Detectados:{Colors.ENDC}")
            
            issues_by_type = defaultdict(list)
            for issue in self.issues:
                issues_by_type[issue['type']].append(issue)
                
            for issue_type, issues in issues_by_type.items():
                print(f"\n  {Colors.WARNING}{issue_type.replace('_', ' ').title()}:{Colors.ENDC}")
                for issue in issues:
                    if issue_type == 'missing_serializer':
                        print(f"    - {issue['model']}: {issue['message']}")
                    elif issue_type == 'fields_missing_in_serializer':
                        print(f"    - {issue['model']} → {issue['serializer']}")
                        print(f"      Campos: {', '.join(issue['fields'])}")
        else:
            print(f"\n{Colors.OKGREEN}✓ No se detectaron problemas de consistencia{Colors.ENDC}")
            
        # Detalles de modelos principales
        print(f"\n{Colors.BOLD}Detalles de Modelos Principales:{Colors.ENDC}")
        
        main_models = ['clientes.Clientes', 'ventas.Ventas', 'productos.Productos', 
                      'compras.Compras', 'usuarios.Empleados']
        
        for model_name in main_models:
            if model_name in self.models_data:
                fields = self.models_data[model_name]
                print(f"\n  {Colors.OKBLUE}{model_name}{Colors.ENDC} ({len(fields)} campos):")
                for field_name, field_type in sorted(fields.items()):
                    print(f"    - {field_name}: {field_type}")
            else:
                print(f"\n  {Colors.WARNING}{model_name}: No encontrado{Colors.ENDC}")
                
    def run(self):
        """Ejecuta el análisis completo"""
        print(f"{Colors.BOLD}Iniciando verificación de consistencia de base de datos...{Colors.ENDC}")
        print(f"Directorio raíz: {self.root_dir}")
        
        self.scan_backend_models()
        self.scan_backend_serializers()
        self.scan_frontend_interfaces()
        self.compare_model_to_serializer()
        self.generate_report()
        
        # Guardar reporte en archivo JSON
        report_file = self.root_dir / "verificacion_consistencia_db.json"
        report_data = {
            'models': {k: list(v.keys()) for k, v in self.models_data.items()},
            'serializers': {k: v for k, v in self.serializers_data.items()},
            'frontend_interfaces': {k: list(v.keys()) for k, v in self.frontend_interfaces.items()},
            'issues': self.issues
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n{Colors.OKGREEN}✓ Reporte guardado en: {report_file}{Colors.ENDC}")


if __name__ == '__main__':
    import sys
    
    # Obtener el directorio raíz del proyecto
    root_dir = Path(__file__).parent
    
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
        
    checker = ConsistencyChecker(root_dir)
    checker.run()
