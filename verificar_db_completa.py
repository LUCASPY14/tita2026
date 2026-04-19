"""
Verificación exhaustiva de consistencia: Base de Datos Real → Django → TypeScript
Conecta a SQL Server titadb y compara estructura real con modelos y frontend
"""

import os
import sys
import json
import pyodbc
from pathlib import Path
from collections import defaultdict

# Configurar Django
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')

import django
django.setup()

from django.apps import apps
from django.db import connection


class VerificadorDBCompleto:
    """Verificador de consistencia entre BD real, Django y TypeScript"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.frontend_types = self.root_dir / "frontend" / "src" / "types" / "index.ts"
        self.problemas = defaultdict(list)
        self.estadisticas = {
            'tablas_verificadas': 0,
            'columnas_verificadas': 0,
            'problemas_encontrados': 0,
            'consistencia_db_django': 0,
            'consistencia_django_ts': 0,
        }
        
        # Mapeo de tablas a verificar
        self.tablas_a_verificar = {
            'clientes': ('clientes', 'Clientes', 'Cliente'),
            'hijos': ('clientes', 'Hijos', 'Hijo'),
            'tipos_cliente': ('clientes', 'TiposCliente', 'TipoCliente'),
            'ventas': ('ventas', 'Ventas', 'Venta'),
            'detalles_venta': ('ventas', 'DetallesVenta', 'DetalleVenta'),
            'productos': ('productos', 'Productos', 'Producto'),
            'categorias': ('productos', 'Categorias', 'Categoria'),
            'precios_por_lista': ('productos', 'PreciosPorLista', 'PrecioPorLista'),
            'compras': ('compras', 'Compras', 'Compra'),
            'detalles_compra': ('compras', 'DetallesCompra', 'DetalleCompra'),
            'proveedores': ('compras', 'Proveedores', 'Proveedor'),
            'empleados': ('usuarios', 'Empleados', 'Empleado'),
            'roles': ('usuarios', 'Roles', 'Rol'),
            'pagos_clientes': ('cobros', 'PagosClientes', 'PagoCliente'),
            'stock_unico': ('inventario', 'StockUnico', 'StockUnico'),
            'movimientos_stock': ('inventario', 'MovimientosStock', 'MovimientoStock'),
            'impuestos': ('contabilidad', 'Impuestos', 'Impuesto'),
            'cierres_caja': ('contabilidad', 'CierresCaja', 'CierreCaja'),
            'medios_pago': ('core', 'MediosPago', 'MedioPago'),
            'planes_almuerzo': ('almuerzos', 'PlanesAlmuerzo', 'PlanAlmuerzo'),
            'suscripciones_almuerzo': ('almuerzos', 'SuscripcionesAlmuerzo', 'SuscripcionAlmuerzo'),
        }

    def obtener_estructura_bd(self):
        """Obtiene la estructura real de las tablas desde SQL Server"""
        print("\n[1/4] Obteniendo estructura de la base de datos SQL Server 'titadb'...")
        
        estructura = {}
        
        with connection.cursor() as cursor:
            for tabla, (app, modelo, interface) in self.tablas_a_verificar.items():
                try:
                    # Query para obtener columnas de la tabla
                    query = """
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.IS_NULLABLE,
                        c.CHARACTER_MAXIMUM_LENGTH,
                        c.NUMERIC_PRECISION,
                        c.NUMERIC_SCALE,
                        c.COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    WHERE c.TABLE_NAME = %s
                    ORDER BY c.ORDINAL_POSITION
                    """
                    
                    cursor.execute(query, [tabla])
                    columnas = cursor.fetchall()
                    
                    if columnas:
                        estructura[tabla] = []
                        for col in columnas:
                            estructura[tabla].append({
                                'nombre': col[0],
                                'tipo': col[1],
                                'nullable': col[2] == 'YES',
                                'max_length': col[3],
                                'precision': col[4],
                                'scale': col[5],
                                'default': col[6]
                            })
                        print(f"  [OK] {tabla}: {len(columnas)} columnas")
                    else:
                        print(f"  [X] {tabla}: No encontrada en BD")
                        self.problemas[tabla].append({
                            'tipo': 'tabla_no_existe',
                            'mensaje': f'Tabla {tabla} no existe en la base de datos'
                        })
                        
                except Exception as e:
                    print(f"  [X] {tabla}: Error - {str(e)}")
                    self.problemas[tabla].append({
                        'tipo': 'error_consulta',
                        'mensaje': str(e)
                    })
        
        self.estadisticas['tablas_verificadas'] = len(estructura)
        return estructura

    def obtener_campos_modelo(self, app_name, model_name):
        """Obtiene los campos del modelo Django"""
        try:
            modelo = apps.get_model(app_name, model_name)
            campos = {}
            
            for field in modelo._meta.get_fields():
                if hasattr(field, 'column'):
                    campos[field.column] = {
                        'nombre': field.name,
                        'tipo': field.get_internal_type(),
                        'nullable': field.null,
                        'blank': field.blank if hasattr(field, 'blank') else False,
                        'max_length': getattr(field, 'max_length', None),
                        'primary_key': field.primary_key if hasattr(field, 'primary_key') else False,
                    }
            
            return campos
        except Exception as e:
            return None

    def extraer_interface_typescript(self, interface_name):
        """Extrae campos de una interface TypeScript"""
        try:
            with open(self.frontend_types, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            # Buscar la interface
            pattern = rf'export\s+interface\s+{interface_name}\s*\{{([^}}]+)\}}'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                return None
            
            interface_body = match.group(1)
            campos = {}
            
            # Extraer campos
            field_pattern = r'(\w+)(\??):\s*([^;]+);'
            for field_match in re.finditer(field_pattern, interface_body):
                campo = field_match.group(1)
                opcional = field_match.group(2) == '?'
                tipo = field_match.group(3).strip()
                
                campos[campo] = {
                    'opcional': opcional,
                    'tipo': tipo
                }
            
            return campos
        except Exception as e:
            return None

    def comparar_db_con_django(self, tabla, estructura_bd, app_name, model_name):
        """Compara estructura de BD con modelo Django"""
        problemas = []
        
        campos_modelo = self.obtener_campos_modelo(app_name, model_name)
        if not campos_modelo:
            problemas.append({
                'tipo': 'modelo_no_encontrado',
                'mensaje': f'Modelo {app_name}.{model_name} no encontrado'
            })
            return problemas
        
        # Columnas en BD pero no en modelo
        for col_bd in estructura_bd:
            nombre_col = col_bd['nombre']
            if nombre_col not in campos_modelo:
                problemas.append({
                    'tipo': 'columna_sin_campo',
                    'columna': nombre_col,
                    'mensaje': f"Columna '{nombre_col}' existe en BD pero no en modelo Django"
                })
        
        # Campos en modelo pero no en BD
        for col_modelo in campos_modelo:
            if not any(c['nombre'] == col_modelo for c in estructura_bd):
                problemas.append({
                    'tipo': 'campo_sin_columna',
                    'campo': col_modelo,
                    'mensaje': f"Campo '{col_modelo}' existe en modelo Django pero no en BD"
                })
        
        self.estadisticas['columnas_verificadas'] += len(estructura_bd)
        return problemas

    def comparar_django_con_typescript(self, app_name, model_name, interface_name):
        """Compara modelo Django con interface TypeScript"""
        problemas = []
        
        campos_modelo = self.obtener_campos_modelo(app_name, model_name)
        if not campos_modelo:
            return problemas
        
        campos_interface = self.extraer_interface_typescript(interface_name)
        if not campos_interface:
            problemas.append({
                'tipo': 'interface_no_encontrada',
                'interface': interface_name,
                'mensaje': f"Interface '{interface_name}' no encontrada en TypeScript"
            })
            return problemas
        
        # Campos en Django pero no en TypeScript
        for col_name, field_info in campos_modelo.items():
            field_name = field_info['nombre']
            if field_name not in campos_interface and not field_info['primary_key']:
                if field_name != 'id':  # Ignorar id, suele ser implícito
                    problemas.append({
                        'tipo': 'campo_sin_interface',
                        'campo': field_name,
                        'mensaje': f"Campo '{field_name}' en Django no está en interface TypeScript"
                    })
        
        # Campos en TypeScript pero no en Django (posibles calculados)
        campos_django = {f['nombre'] for f in campos_modelo.values()}
        for campo_ts in campos_interface:
            if campo_ts not in campos_django and campo_ts != 'id':
                # Solo advertencia, pueden ser campos calculados
                problemas.append({
                    'tipo': 'campo_calculado_posible',
                    'campo': campo_ts,
                    'mensaje': f"Campo '{campo_ts}' en TypeScript no está en Django (¿campo calculado?)"
                })
        
        return problemas

    def ejecutar_verificacion(self):
        """Ejecuta la verificación completa"""
        print("\n" + "="*80)
        print("VERIFICACION COMPLETA: BASE DE DATOS → DJANGO → TYPESCRIPT")
        print("="*80)
        
        # Paso 1: Obtener estructura de BD
        estructura_bd = self.obtener_estructura_bd()
        
        # Paso 2: Verificar cada tabla
        print("\n[2/4] Comparando BD con modelos Django...")
        for tabla, (app, modelo, interface) in self.tablas_a_verificar.items():
            if tabla not in estructura_bd:
                continue
            
            print(f"\n  Verificando: {tabla} -> {app}.{modelo}")
            
            # Comparar BD con Django
            problemas_bd_django = self.comparar_db_con_django(
                tabla, estructura_bd[tabla], app, modelo
            )
            
            if problemas_bd_django:
                self.problemas[tabla].extend(problemas_bd_django)
                print(f"    [!] {len(problemas_bd_django)} problemas BD-Django")
            else:
                print(f"    [OK] BD-Django consistente")
        
        # Paso 3: Verificar Django con TypeScript
        print("\n[3/4] Comparando Django con TypeScript...")
        for tabla, (app, modelo, interface) in self.tablas_a_verificar.items():
            if tabla not in estructura_bd:
                continue
            
            print(f"\n  Verificando: {app}.{modelo} -> {interface}")
            
            problemas_django_ts = self.comparar_django_con_typescript(app, modelo, interface)
            
            if problemas_django_ts:
                self.problemas[tabla].extend(problemas_django_ts)
                print(f"    [!] {len(problemas_django_ts)} problemas Django-TS")
            else:
                print(f"    [OK] Django-TS consistente")
        
        # Paso 4: Generar reporte
        self.generar_reporte()

    def generar_reporte(self):
        """Genera reporte de resultados"""
        print("\n[4/4] Generando reporte...")
        
        total_problemas = sum(len(p) for p in self.problemas.values())
        self.estadisticas['problemas_encontrados'] = total_problemas
        
        # Calcular consistencias
        tablas_con_problemas = len([t for t in self.problemas if self.problemas[t]])
        tablas_ok = self.estadisticas['tablas_verificadas'] - tablas_con_problemas
        
        if self.estadisticas['tablas_verificadas'] > 0:
            consistencia = (tablas_ok / self.estadisticas['tablas_verificadas']) * 100
            self.estadisticas['consistencia_general'] = round(consistencia, 1)
        
        # Guardar resultados
        resultados = {
            'estadisticas': self.estadisticas,
            'problemas': dict(self.problemas),
            'tablas_verificadas': list(self.tablas_a_verificar.keys())
        }
        
        output_file = self.root_dir / 'verificacion_db_completa.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        print("\n" + "="*80)
        print("RESUMEN DE VERIFICACION")
        print("="*80)
        print(f"Tablas verificadas:        {self.estadisticas['tablas_verificadas']}")
        print(f"Columnas verificadas:      {self.estadisticas['columnas_verificadas']}")
        print(f"Problemas encontrados:     {total_problemas}")
        print(f"Consistencia general:      {self.estadisticas.get('consistencia_general', 0)}%")
        
        if total_problemas > 0:
            print(f"\nTablas con problemas:")
            for tabla, problemas in self.problemas.items():
                if problemas:
                    print(f"  - {tabla}: {len(problemas)} problemas")
        else:
            print(f"\n[OK] No se encontraron problemas de consistencia!")
        
        print(f"\nResultados guardados en: verificacion_db_completa.json")
        
        return total_problemas == 0


if __name__ == '__main__':
    verificador = VerificadorDBCompleto()
    exito = verificador.ejecutar_verificacion()
    sys.exit(0 if exito else 1)
