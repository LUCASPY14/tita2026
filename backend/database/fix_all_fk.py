"""
Script final para corregir TODAS las referencias FK/OneToOne/M2M en los modelos
"""
import re
from pathlib import Path

BASE_DIR = Path(r'D:\tita2026\cantina_tita\backend')

# Mapeo completo modelo -> app
MODEL_TO_APP = {
    'Empleados': 'usuarios', 'Roles': 'usuarios', 'PerfilesUsuario': 'usuarios',
    'Autenticacion2Fa': 'usuarios', 'Intentos2Fa': 'usuarios', 'IntentosLogin': 'usuarios',
    'SesionesActivas': 'usuarios', 'RenovacionesSesion': 'usuarios',
    'TokensRecuperacion': 'usuarios', 'TokensVerificacion': 'usuarios',
    'PatronesAcceso': 'usuarios', 'BloqueosCuenta': 'usuarios',
    'UsuariosPortal': 'usuarios', 'UsuariosWebClientes': 'usuarios',
    'AuditoriaEmpleados': 'usuarios', 'AuditoriaOperaciones': 'usuarios', 'AuditoriaUsuariosWeb': 'usuarios',
    'Clientes': 'clientes', 'TiposCliente': 'clientes',
    'Hijos': 'clientes', 'Grados': 'clientes', 'HistorialGradosHijos': 'clientes',
    'RestriccionesHijos': 'clientes',
    'AutorizacionesSaldoNegativo': 'clientes', 'LogsAutorizaciones': 'clientes',
    'Productos': 'productos', 'Categorias': 'productos',
    'UnidadesMedida': 'productos',
    'ListasPrecios': 'productos', 'PreciosPorLista': 'productos',
    'HistoricoPrecios': 'productos',
    'StockUnico': 'inventario', 'MovimientosStock': 'inventario',
    'AjustesInventario': 'inventario', 'DetallesAjuste': 'inventario',
    'CostosHistoricos': 'inventario',
    'Ventas': 'ventas', 'DetallesVenta': 'ventas',
    'PagosVenta': 'ventas', 'AplicacionPagosVentas': 'ventas',
    'NotasCreditoCliente': 'ventas', 'DetallesNotaCredito': 'ventas',
    'Promociones': 'ventas', 'CategoriasPromocion': 'ventas', 
    'ProductosPromocion': 'ventas', 'PromocionesAplicadas': 'ventas',
    'Proveedores': 'compras', 'Compras': 'compras', 'DetallesCompra': 'compras',
    'PagosProveedores': 'compras', 'AplicacionPagosCompras': 'compras',
    'NotasCreditoProveedor': 'compras', 'DetallesNotaCreditoProveedor': 'compras',
    'PlanesAlmuerzo': 'almuerzos', 'TiposAlmuerzo': 'almuerzos',
    'SuscripcionesAlmuerzo': 'almuerzos', 'RegistrosConsumoAlmuerzo': 'almuerzos',
    'CuentasAlmuerzoMensual': 'almuerzos', 'PagosAlmuerzoMensual': 'almuerzos', 
    'PagosCuentasAlmuerzo': 'almuerzos',
    'Alergenos': 'almuerzos', 'ProductosAlergenos': 'almuerzos',
    'Tarjetas': 'core', 'TarjetasAutorizacion': 'core',
    'CargasSaldo': 'core', 'ConsumosTarjeta': 'core',
    'TransaccionesOnline': 'core',
    'MediosPago': 'core',
    'ConfiguracionSistema': 'core', 'CacheConfiguracion': 'core',
    'Cajas': 'contabilidad', 'CierresCaja': 'contabilidad', 'MovimientosCaja': 'contabilidad',
    'TarifasComision': 'contabilidad', 'AuditoriaComisiones': 'contabilidad',
    'ConciliacionPagos': 'contabilidad',
    'DocumentosTributarios': 'contabilidad', 'DocumentoImpuestos': 'contabilidad',
    'Timbrados': 'contabilidad', 'PuntosExpedicion': 'contabilidad',
    'DatosEmpresa': 'contabilidad', 'Impuestos': 'contabilidad',
    'NotificacionesPortal': 'notificaciones', 'NotificacionesSaldo': 'notificaciones',
    'SolicitudesNotificacion': 'notificaciones', 'PreferenciasNotificacion': 'notificaciones',
    'EmailsEnviados': 'notificaciones', 'SmsEnviados': 'notificaciones',
    'PlantillasEmail': 'notificaciones', 'PlantillasSms': 'notificaciones',
    'CampanasComunicacion': 'notificaciones',
    'AlertasAutomaticas': 'notificaciones', 'AlertaDestinatarios': 'notificaciones',
    'AlertasSistema': 'notificaciones', 'HistorialAlertas': 'notificaciones',
    'AnomaliasDetectadas': 'notificaciones', 'RestriccionesHorarias': 'notificaciones',
    'ProveedoresApi': 'api_integrations', 'EndpointsApi': 'api_integrations',
    'LogsLlamadasApi': 'api_integrations', 'CredencialesApi': 'api_integrations',
    'LogsWebhooks': 'api_integrations', 'WebhookEndpoints': 'api_integrations',
    'PlantillasReporte': 'reportes', 'Dashboards': 'reportes',
    'KpiMetricas': 'reportes', 'ValoresKpi': 'reportes',
    'PlantillasTarea': 'reportes', 'EjecucionesTarea': 'reportes', 
    'DestinatariosTarea': 'reportes',
}

def fix_all_fk_references(app_name, content):
    """Arregla TODAS las referencias FK incluyendo las que ya están en formato string"""
    
    # Paso 1: Arreglar referencias directas (sin comillas):
    # ForeignKey(ModeloNombre, ...) -> ForeignKey('app.ModelName', ...)
    patterns_direct = [
        (r"models\.ForeignKey\(([A-Z]\w+),", 'ForeignKey'),
        (r"models\.OneToOneField\(([A-Z]\w+),", 'OneToOneField'),
        (r"models\.ManyToManyField\(([A-Z]\w+),", 'ManyToManyField'),
    ]
    
    for pattern, field_type in patterns_direct:
        def replace_direct(match):
            model_name = match.group(1)
            if model_name in MODEL_TO_APP:
                target_app = MODEL_TO_APP[model_name]
                if target_app != app_name:
                    return f"models.{field_type}('{target_app}.{model_name}',"
                else:
                    return f"models.{field_type}('{model_name}',"
            return match.group(0)
        content = re.sub(pattern, replace_direct, content)
    
    # Paso 2: Arreglar referencias en string con app incorrecta:
    # ForeignKey('wrongapp.Model', ...) -> ForeignKey('correctapp.Model', ...)
    # O ForeignKey('Model', ...) donde Model está en otra app
    patterns_string = [
        (r"models\.ForeignKey\('([^']+)',", 'ForeignKey'),
        (r"models\.OneToOneField\('([^']+)',", 'OneToOneField'),
        (r"models\.ManyToManyField\('([^']+)',", 'ManyToManyField'),
    ]
    
    for pattern, field_type in patterns_string:
        def replace_string(match):
            ref = match.group(1)
            
            # Si es 'self' o tiene un punto y no es el app correcto, dejarlo como está
            if ref == 'self':
                return match.group(0)
            
            # Extraer el nombre del modelo
            if '.' in ref:
                parts = ref.split('.')
                if len(parts) == 2:
                    old_app, model_name = parts
                else:
                    return match.group(0)
            else:
                model_name = ref
            
            # Buscar el app correcto para este modelo
            if model_name in MODEL_TO_APP:
                correct_app = MODEL_TO_APP[model_name]
                if correct_app != app_name:
                    return f"models.{field_type}('{correct_app}.{model_name}',"
                else:
                    return f"models.{field_type}('{model_name}',"
            
            # Si no se encuentra en el mapeo, dejarlo como está
            return match.group(0)
        
        content = re.sub(pattern, replace_string, content)
    
    return content

def process_all_models():
    """Procesa TODOS los archivos models.py"""
    apps = ['usuarios', 'clientes', 'productos', 'inventario', 'ventas', 'compras',
            'almuerzos', 'core', 'contabilidad', 'notificaciones', 'api_integrations', 'reportes']
    
    print("Corrigiendo TODAS las referencias FK/OneToOne/M2M en los modelos...")
    total_fixed = 0
    
    for app_name in apps:
        models_file = BASE_DIR / 'apps' / app_name / 'models.py'
        
        if not models_file.exists():
            continue
        
        # Leer contenido
        with open(models_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Corregir referencias
        fixed_content = fix_all_fk_references(app_name, original_content)
        
        # Contar cambios
        if original_content != fixed_content:
            total_fixed += 1
            
            # Escribir de  vuelta
            with open(models_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"  ✓ {app_name}")
        else:
            print(f"  - {app_name} (sin cambios)")
    
    print(f"\n¡Corrección completada! {total_fixed} archivos modificados")

if __name__ == '__main__':
    process_all_models()
