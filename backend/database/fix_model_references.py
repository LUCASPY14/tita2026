"""
Script para corregir referencias entre modelos en diferentes apps
Convierte referencias directas a formato string: 'app.Model'
"""
import re
from pathlib import Path

# Ruta base
BASE_DIR = Path(r'D:\tita2026\cantina_tita\backend')

# Mapeo de modelos a apps
MODEL_TO_APP = {
    # usuarios
    'Empleados': 'usuarios', 'Roles': 'usuarios', 'PerfilesUsuario': 'usuarios',
    'Autenticacion2Fa': 'usuarios', 'Intentos2Fa': 'usuarios', 'IntentosLogin': 'usuarios',
    'SesionesActivas': 'usuarios', 'RenovacionesSesion': 'usuarios',
    'TokensRecuperacion': 'usuarios', 'TokensVerificacion': 'usuarios',
    'PatronesAcceso': 'usuarios', 'BloqueosCuenta': 'usuarios',
    'UsuariosPortal': 'usuarios', 'UsuariosWebClientes': 'usuarios',
    'AuditoriaEmpleados': 'usuarios', 'AuditoriaOperaciones': 'usuarios', 'AuditoriaUsuariosWeb': 'usuarios',
    
    # clientes
    'Clientes': 'clientes', 'TiposCliente': 'clientes',
    'Hijos': 'clientes', 'Grados': 'clientes', 'HistorialGradosHijos': 'clientes',
    'RestriccionesHijos': 'clientes',
    'AutorizacionesSaldoNegativo': 'clientes', 'LogsAutorizaciones': 'clientes',
    
    # productos
    'Productos': 'productos', 'Categorias': 'productos',
    'UnidadesMedida': 'productos',
    'ListasPrecios': 'productos', 'PreciosPorLista': 'productos',
    'HistoricoPrecios': 'productos',
    
    # inventario
    'StockUnico': 'inventario', 'MovimientosStock': 'inventario',
    'AjustesInventario': 'inventario', 'DetallesAjuste': 'inventario',
    'CostosHistoricos': 'inventario',
    
    # ventas
    'Ventas': 'ventas', 'DetallesVenta': 'ventas',
    'PagosVenta': 'ventas', 'AplicacionPagosVentas': 'ventas',
    'NotasCreditoCliente': 'ventas', 'DetallesNotaCredito': 'ventas',
    'Promociones': 'ventas', 'CategoriasPromocion': 'ventas', 'ProductosPromocion': 'ventas', 'PromocionesAplicadas': 'ventas',
    
    # compras
    'Proveedores': 'compras', 'Compras': 'compras', 'DetallesCompra': 'compras',
    'PagosProveedores': 'compras', 'AplicacionPagosCompras': 'compras',
    'NotasCreditoProveedor': 'compras', 'DetallesNotaCreditoProveedor': 'compras',
    
    # almuerzos
    'PlanesAlmuerzo': 'almuerzos', 'TiposAlmuerzo': 'almuerzos',
    'SuscripcionesAlmuerzo': 'almuerzos', 'RegistrosConsumoAlmuerzo': 'almuerzos',
    'CuentasAlmuerzoMensual': 'almuerzos', 'PagosAlmuerzoMensual': 'almuerzos', 'PagosCuentasAlmuerzo': 'almuerzos',
    'Alergenos': 'almuerzos', 'ProductosAlergenos': 'almuerzos',
    
    # core
    'Tarjetas': 'core', 'TarjetasAutorizacion': 'core',
    'CargasSaldo': 'core', 'ConsumosTarjeta': 'core',
    'TransaccionesOnline': 'core',
    'MediosPago': 'core',
    'ConfiguracionSistema': 'core', 'CacheConfiguracion': 'core',
    
    # contabilidad
    'Cajas': 'contabilidad', 'CierresCaja': 'contabilidad', 'MovimientosCaja': 'contabilidad',
    'TarifasComision': 'contabilidad', 'AuditoriaComisiones': 'contabilidad',
    'ConciliacionPagos': 'contabilidad',
    'DocumentosTributarios': 'contabilidad', 'DocumentoImpuestos': 'contabilidad',
    'Timbrados': 'contabilidad', 'PuntosExpedicion': 'contabilidad',
    'DatosEmpresa': 'contabilidad', 'Impuestos': 'contabilidad',
    
    # notificaciones
    'NotificacionesPortal': 'notificaciones', 'NotificacionesSaldo': 'notificaciones',
    'SolicitudesNotificacion': 'notificaciones', 'PreferenciasNotificacion': 'notificaciones',
    'EmailsEnviados': 'notificaciones', 'SmsEnviados': 'notificaciones',
    'PlantillasEmail': 'notificaciones', 'PlantillasSms': 'notificaciones',
    'CampanasComunicacion': 'notificaciones',
    'AlertasAutomaticas': 'notificaciones', 'AlertaDestinatarios': 'notificaciones', 
    'AlertasSistema': 'notificaciones', 'HistorialAlertas': 'notificaciones',
    'AnomaliasDetectadas': 'notificaciones', 'RestriccionesHorarias': 'notificaciones',
    
    # api_integrations
    'ProveedoresApi': 'api_integrations', 'EndpointsApi': 'api_integrations',
    'LogsLlamadasApi': 'api_integrations', 'CredencialesApi': 'api_integrations',
    'LogsWebhooks': 'api_integrations', 'WebhookEndpoints': 'api_integrations',
    
    # reportes
    'PlantillasReporte': 'reportes', 'Dashboards': 'reportes',
    'KpiMetricas': 'reportes', 'ValoresKpi': 'reportes',
    'PlantillasTarea': 'reportes', 'EjecucionesTarea': 'reportes', 'DestinatariosTarea': 'reportes',
}

def fix_model_references(app_name, content):
    """Corrige las referencias a modelos en un archivo models.py"""
    
    # Patrón para encontrar ForeignKey, OneToOneField, ManyToManyField
    patterns = [
        (r'models\.ForeignKey\((\w+),', 'ForeignKey'),
        (r'models\.OneToOneField\((\w+),', 'OneToOneField'),
        (r'models\.ManyToManyField\((\w+),', 'ManyToManyField'),
    ]
    
    for pattern, field_type in patterns:
        def replace_reference(match):
            model_name = match.group(1)
            
            # Si el modelo está en el mapeo y no es de la misma app
            if model_name in MODEL_TO_APP:
                target_app = MODEL_TO_APP[model_name]
                
                # Si es de otra app, usar 'app.Model'
                if target_app != app_name:
                    return f"models.{field_type}('{target_app}.{model_name}',"
                else:
                    # Si es de la misma app, usar 'Model'
                    return f"models.{field_type}('{model_name}',"
            
            # Si no está en el mapeo, dejarlo como está (podría ser un string ya)
            return match.group(0)
        
        content = re.sub(pattern, replace_reference, content)
    
    return content

def process_all_apps():
    """Procesa todos los archivos models.py de las apps"""
    apps = ['usuarios', 'clientes', 'productos', 'inventario', 'ventas', 'compras', 
            'almuerzos', 'core', 'contabilidad', 'notificaciones', 'api_integrations', 'reportes']
    
    print("Corrigiendo referencias entre modelos...")
    
    for app_name in apps:
        models_file = BASE_DIR / 'apps' / app_name / 'models.py'
        
        if not models_file.exists():
            continue
        
        # Leer contenido
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corregir referencias
        fixed_content = fix_model_references(app_name, content)
        
        # Escribir de vuelta
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"  ✓ {app_name}")
    
    print("\n¡Corrección completada!")

if __name__ == '__main__':
    process_all_apps()
