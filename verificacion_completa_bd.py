"""
Verificacion Exhaustiva de Consistencia: Base de Datos -> Django -> TypeScript
Compara la estructura real de la base de datos titadb con modelos Django y frontend
"""

import os
import sys
import django
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set

# Configurar Django
sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')
django.setup()

from django.db import connection
from django.apps import apps

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


class VerificadorConsistenciaDB:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent
        self.backend_dir = self.root_dir / 'backend'
        self.frontend_types = self.root_dir / 'frontend' / 'src' / 'types' / 'index.ts'
        self.resultados = {
            'tablas_bd': {},
            'modelos_django': {},
            'interfaces_typescript': {},
            'comparaciones': [],
            'resumen': {}
        }
        
        # Mapeo de nombres de tabla a modelo Django
        self.tabla_a_modelo = {}
        
        # Mapeo de modelos Django a interfaces TypeScript
        self.modelo_a_interface = {
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
            'AplicacionesPagoCliente': 'AplicacionPagoCliente',
        }

    def obtener_tablas_bd(self) -> Dict[str, List[Dict]]:
        """Obtiene todas las tablas y sus columnas directamente de la base de datos"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}PASO 1: INSPECCIONANDO BASE DE DATOS TITADB{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        tablas = {}
        
        with connection.cursor() as cursor:
            # Obtener todas las tablas del usuario (excluyendo tablas del sistema)
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' 
                AND TABLE_SCHEMA = 'dbo'
                ORDER BY TABLE_NAME
            """)
            
            nombres_tablas = [row[0] for row in cursor.fetchall()]
            print(f"[INFO] Tablas encontradas en BD: {len(nombres_tablas)}\n")
            
            for tabla in nombres_tablas:
                # Saltar tablas de Django
                if tabla.startswith('django_') or tabla == 'auth_' or tabla in ['auth_group', 'auth_group_permissions', 'auth_permission', 'auth_user', 'auth_user_groups', 'auth_user_user_permissions']:
                    continue
                
                print(f"  Analizando tabla: {tabla}")
                
                # Obtener información de columnas
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE,
                        COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, [tabla])
                
                columnas = []
                for row in cursor.fetchall():
                    col_name, data_type, max_length, is_nullable, default = row
                    columnas.append({
                        'nombre': col_name,
                        'tipo': data_type,
                        'max_length': max_length,
                        'nullable': is_nullable == 'YES',
                        'default': default
                    })
                
                tablas[tabla] = columnas
                print(f"    Columnas: {len(columnas)}")
        
        self.resultados['tablas_bd'] = tablas
        print(f"\n{Colors.OKGREEN}[OK] Total de tablas analizadas: {len(tablas)}{Colors.ENDC}")
        return tablas

    def obtener_modelos_django(self) -> Dict[str, Dict]:
        """Obtiene información de todos los modelos Django"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}PASO 2: ANALIZANDO MODELOS DJANGO{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        modelos = {}
        apps_principales = ['clientes', 'ventas', 'productos', 'compras', 'usuarios', 
                           'cobros', 'inventario', 'almuerzos', 'contabilidad', 'core']
        
        for app_name in apps_principales:
            try:
                app_config = apps.get_app_config(app_name)
                print(f"\n  App: {app_name}")
                
                for model in app_config.get_models():
                    model_name = model.__name__
                    db_table = model._meta.db_table
                    
                    # Construir mapa tabla -> modelo
                    self.tabla_a_modelo[db_table] = f"{app_name}.{model_name}"
                    
                    campos = []
                    for field in model._meta.get_fields():
                        if hasattr(field, 'column'):
                            campo_info = {
                                'nombre': field.name,
                                'columna': field.column,
                                'tipo': field.get_internal_type(),
                                'null': field.null if hasattr(field, 'null') else None,
                                'blank': field.blank if hasattr(field, 'blank') else None,
                                'primary_key': field.primary_key if hasattr(field, 'primary_key') else False,
                            }
                            
                            # Agregar max_length si existe
                            if hasattr(field, 'max_length'):
                                campo_info['max_length'] = field.max_length
                            
                            # Agregar choices si existen
                            if hasattr(field, 'choices') and field.choices:
                                campo_info['choices'] = [c[0] for c in field.choices]
                            
                            campos.append(campo_info)
                    
                    modelos[f"{app_name}.{model_name}"] = {
                        'db_table': db_table,
                        'campos': campos
                    }
                    
                    print(f"    Modelo: {model_name} -> Tabla: {db_table} ({len(campos)} campos)")
            
            except LookupError:
                print(f"  [!] App '{app_name}' no encontrada")
                continue
        
        self.resultados['modelos_django'] = modelos
        print(f"\n{Colors.OKGREEN}[OK] Total de modelos analizados: {len(modelos)}{Colors.ENDC}")
        return modelos

    def obtener_interfaces_typescript(self) -> Dict[str, List[str]]:
        """Extrae interfaces TypeScript del archivo de tipos"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}PASO 3: ANALIZANDO INTERFACES TYPESCRIPT{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        interfaces = {}
        
        if not self.frontend_types.exists():
            print(f"{Colors.FAIL}[X] No se encontró el archivo de tipos: {self.frontend_types}{Colors.ENDC}")
            return interfaces
        
        with open(self.frontend_types, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patrón para capturar interfaces completas
        pattern = r'export\s+interface\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            interface_name = match.group(1)
            interface_body = match.group(2)
            
            # Extraer campos
            campos = []
            field_pattern = r'(\w+)(\?)?:\s*([^;]+);'
            for field_match in re.finditer(field_pattern, interface_body):
                field_name = field_match.group(1)
                is_optional = field_match.group(2) == '?'
                field_type = field_match.group(3).strip()
                
                campos.append({
                    'nombre': field_name,
                    'tipo': field_type,
                    'opcional': is_optional
                })
            
            interfaces[interface_name] = campos
            print(f"  Interface: {interface_name} ({len(campos)} campos)")
        
        self.resultados['interfaces_typescript'] = interfaces
        print(f"\n{Colors.OKGREEN}[OK] Total de interfaces encontradas: {len(interfaces)}{Colors.ENDC}")
        return interfaces

    def comparar_bd_con_django(self, tablas_bd: Dict, modelos_django: Dict) -> List[Dict]:
        """Compara estructura de BD con modelos Django"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}PASO 4: COMPARANDO BASE DE DATOS vs DJANGO{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        problemas = []
        
        # Verificar tablas en BD que no tienen modelo Django
        tablas_bd_set = set(tablas_bd.keys())
        tablas_django_set = set(self.tabla_a_modelo.keys())
        
        tablas_sin_modelo = tablas_bd_set - tablas_django_set
        if tablas_sin_modelo:
            print(f"{Colors.WARNING}[!] Tablas en BD sin modelo Django ({len(tablas_sin_modelo)}):{Colors.ENDC}")
            for tabla in sorted(tablas_sin_modelo):
                print(f"    - {tabla}")
                problemas.append({
                    'tipo': 'tabla_sin_modelo',
                    'tabla': tabla,
                    'severidad': 'media'
                })
        
        # Verificar modelos Django sin tabla en BD
        modelos_sin_tabla = tablas_django_set - tablas_bd_set
        if modelos_sin_tabla:
            print(f"\n{Colors.WARNING}[!] Modelos Django sin tabla en BD ({len(modelos_sin_tabla)}):{Colors.ENDC}")
            for tabla in sorted(modelos_sin_tabla):
                modelo = self.tabla_a_modelo.get(tabla, 'Unknown')
                print(f"    - {tabla} (modelo: {modelo})")
                problemas.append({
                    'tipo': 'modelo_sin_tabla',
                    'tabla': tabla,
                    'modelo': modelo,
                    'severidad': 'alta'
                })
        
        # Comparar columnas para tablas que existen en ambos
        tablas_comunes = tablas_bd_set & tablas_django_set
        print(f"\n{Colors.OKBLUE}[INFO] Comparando {len(tablas_comunes)} tablas comunes...{Colors.ENDC}\n")
        
        for tabla in sorted(tablas_comunes):
            modelo_path = self.tabla_a_modelo[tabla]
            modelo_info = modelos_django.get(modelo_path)
            
            if not modelo_info:
                continue
            
            print(f"  Tabla: {tabla} -> Modelo: {modelo_path}")
            
            # Obtener conjuntos de columnas (filtrar None para campos sin columna DB)
            columnas_bd = {col['nombre'] for col in tablas_bd[tabla]}
            columnas_modelo = {campo['columna'] for campo in modelo_info['campos'] if campo['columna'] is not None}
            
            # Columnas en BD que no están en modelo
            cols_bd_extra = columnas_bd - columnas_modelo
            if cols_bd_extra:
                print(f"    {Colors.WARNING}[!] Columnas en BD no definidas en modelo: {', '.join(sorted(cols_bd_extra))}{Colors.ENDC}")
                problemas.append({
                    'tipo': 'columnas_bd_extra',
                    'tabla': tabla,
                    'modelo': modelo_path,
                    'columnas': list(cols_bd_extra),
                    'severidad': 'media'
                })
            
            # Columnas en modelo que no están en BD
            cols_modelo_extra = columnas_modelo - columnas_bd
            if cols_modelo_extra:
                print(f"    {Colors.FAIL}[X] Columnas en modelo no existen en BD: {', '.join(sorted(cols_modelo_extra))}{Colors.ENDC}")
                problemas.append({
                    'tipo': 'columnas_modelo_extra',
                    'tabla': tabla,
                    'modelo': modelo_path,
                    'columnas': list(cols_modelo_extra),
                    'severidad': 'alta'
                })
            
            if not cols_bd_extra and not cols_modelo_extra:
                print(f"    {Colors.OKGREEN}[OK] Sincronizado ({len(columnas_bd)} columnas){Colors.ENDC}")
        
        return problemas

    def comparar_django_con_typescript(self, modelos_django: Dict, interfaces_ts: Dict) -> List[Dict]:
        """Compara modelos Django con interfaces TypeScript"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}PASO 5: COMPARANDO DJANGO vs TYPESCRIPT{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        problemas = []
        
        for modelo_path, modelo_info in modelos_django.items():
            # Obtener nombre del modelo
            modelo_nombre = modelo_path.split('.')[-1]
            
            # Buscar interfaz correspondiente
            interface_nombre = self.modelo_a_interface.get(modelo_nombre)
            
            if not interface_nombre:
                print(f"  {Colors.WARNING}[!] Modelo {modelo_nombre}: Sin mapeo a interface{Colors.ENDC}")
                continue
            
            if interface_nombre not in interfaces_ts:
                print(f"  {Colors.FAIL}[X] Modelo {modelo_nombre}: Interface {interface_nombre} no encontrada{Colors.ENDC}")
                problemas.append({
                    'tipo': 'interface_no_encontrada',
                    'modelo': modelo_path,
                    'interface_esperada': interface_nombre,
                    'severidad': 'alta'
                })
                continue
            
            # Comparar campos
            print(f"  Modelo: {modelo_nombre} -> Interface: {interface_nombre}")
            
            campos_modelo = {campo['nombre'] for campo in modelo_info['campos'] if not campo.get('primary_key')}
            campos_interface = {campo['nombre'] for campo in interfaces_ts[interface_nombre]}
            
            # Campos en modelo que no están en interface
            campos_modelo_extra = campos_modelo - campos_interface
            if campos_modelo_extra:
                # Filtrar campos calculados comunes
                campos_calculados = {'total', 'subtotal', 'saldo', 'nombre_completo'}
                campos_modelo_extra = campos_modelo_extra - campos_calculados
                
                if campos_modelo_extra:
                    print(f"    {Colors.WARNING}[!] Campos en modelo no en interface: {', '.join(sorted(campos_modelo_extra))}{Colors.ENDC}")
                    problemas.append({
                        'tipo': 'campos_modelo_extra_ts',
                        'modelo': modelo_path,
                        'interface': interface_nombre,
                        'campos': list(campos_modelo_extra),
                        'severidad': 'media'
                    })
            
            # Campos en interface que no están en modelo
            campos_interface_extra = campos_interface - campos_modelo
            if campos_interface_extra:
                print(f"    {Colors.WARNING}[!] Campos en interface no en modelo: {', '.join(sorted(campos_interface_extra))}{Colors.ENDC}")
                problemas.append({
                    'tipo': 'campos_interface_extra',
                    'modelo': modelo_path,
                    'interface': interface_nombre,
                    'campos': list(campos_interface_extra),
                    'severidad': 'baja'
                })
            
            if not campos_modelo_extra and not campos_interface_extra:
                print(f"    {Colors.OKGREEN}[OK] Sincronizado ({len(campos_modelo)} campos){Colors.ENDC}")
        
        return problemas

    def generar_reporte(self, problemas_bd_django: List[Dict], problemas_django_ts: List[Dict]):
        """Genera reporte final de consistencia"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}REPORTE FINAL DE CONSISTENCIA{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        total_problemas = len(problemas_bd_django) + len(problemas_django_ts)
        
        # Contar por severidad
        problemas_alta = sum(1 for p in problemas_bd_django + problemas_django_ts if p.get('severidad') == 'alta')
        problemas_media = sum(1 for p in problemas_bd_django + problemas_django_ts if p.get('severidad') == 'media')
        problemas_baja = sum(1 for p in problemas_bd_django + problemas_django_ts if p.get('severidad') == 'baja')
        
        print(f"Total de tablas en BD: {len(self.resultados['tablas_bd'])}")
        print(f"Total de modelos Django: {len(self.resultados['modelos_django'])}")
        print(f"Total de interfaces TypeScript: {len(self.resultados['interfaces_typescript'])}")
        print(f"\nProblemas detectados: {total_problemas}")
        print(f"  - Alta severidad: {problemas_alta}")
        print(f"  - Media severidad: {problemas_media}")
        print(f"  - Baja severidad: {problemas_baja}")
        
        # Calcular consistencia
        total_elementos = len(self.resultados['tablas_bd']) + len(self.resultados['modelos_django'])
        if total_elementos > 0:
            consistencia = ((total_elementos - total_problemas) / total_elementos) * 100
            print(f"\nConsistencia general: {consistencia:.1f}%")
            
            if consistencia >= 95:
                print(f"{Colors.OKGREEN}[OK] Excelente consistencia{Colors.ENDC}")
            elif consistencia >= 85:
                print(f"{Colors.WARNING}[!] Buena consistencia, mejorar algunos aspectos{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[X] Consistencia baja, requiere atención{Colors.ENDC}")
        
        # Guardar resultados
        self.resultados['comparaciones'] = problemas_bd_django + problemas_django_ts
        self.resultados['resumen'] = {
            'total_tablas_bd': len(self.resultados['tablas_bd']),
            'total_modelos_django': len(self.resultados['modelos_django']),
            'total_interfaces_ts': len(self.resultados['interfaces_typescript']),
            'total_problemas': total_problemas,
            'problemas_alta': problemas_alta,
            'problemas_media': problemas_media,
            'problemas_baja': problemas_baja,
            'consistencia': consistencia if total_elementos > 0 else 0
        }
        
        output_file = self.root_dir / 'verificacion_completa_bd_resultado.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Colors.OKGREEN}[OK] Resultados guardados en: {output_file.name}{Colors.ENDC}")

    def ejecutar_verificacion(self):
        """Ejecuta la verificación completa"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("="*80)
        print("VERIFICACION EXHAUSTIVA DE CONSISTENCIA")
        print("Base de Datos TITADB -> Django -> TypeScript")
        print("="*80)
        print(f"{Colors.ENDC}\n")
        
        try:
            # Paso 1: Inspeccionar base de datos
            tablas_bd = self.obtener_tablas_bd()
            
            # Paso 2: Analizar modelos Django
            modelos_django = self.obtener_modelos_django()
            
            # Paso 3: Analizar interfaces TypeScript
            interfaces_ts = self.obtener_interfaces_typescript()
            
            # Paso 4: Comparar BD con Django
            problemas_bd_django = self.comparar_bd_con_django(tablas_bd, modelos_django)
            
            # Paso 5: Comparar Django con TypeScript
            problemas_django_ts = self.comparar_django_con_typescript(modelos_django, interfaces_ts)
            
            # Paso 6: Generar reporte
            self.generar_reporte(problemas_bd_django, problemas_django_ts)
            
            return True
            
        except Exception as e:
            print(f"\n{Colors.FAIL}[ERROR] {str(e)}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    verificador = VerificadorConsistenciaDB()
    exito = verificador.ejecutar_verificacion()
    sys.exit(0 if exito else 1)
