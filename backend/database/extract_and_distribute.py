"""
Script para extraer modelos desde generated_models.py y distribuirlos a las apps
"""
import re
import os
from pathlib import Path

# Ruta base
BASE_DIR = Path(r'D:\tita2026\cantina_tita\backend')
GENERATED_FILE = BASE_DIR / 'database' / 'generated_models.py'

# Distribución de modelos por app
MODEL_DISTRIBUTION = {
    'usuarios': [
        'Empleados', 'Roles', 'PerfilesUsuario',
        'Autenticacion2Fa', 'Intentos2Fa', 'IntentosLogin',
        'SesionesActivas', 'RenovacionesSesion',
        'TokensRecuperacion', 'TokensVerificacion',
        'PatronesAcceso', 'BloqueosCuenta',
        'UsuariosPortal', 'UsuariosWebClientes',
        'AuditoriaEmpleados', 'AuditoriaOperaciones', 'AuditoriaUsuariosWeb'
    ],
    'clientes': [
        'Clientes', 'TiposCliente',
        'Hijos', 'Grados', 'HistorialGradosHijos',
        'RestriccionesHijos',
        'AutorizacionesSaldoNegativo', 'LogsAutorizaciones'
    ],
    'productos': [
        'Productos', 'Categorias',
        'UnidadesMedida',
        'ListasPrecios', 'PreciosPorLista',
        'HistoricoPrecios'
    ],
    'inventario': [
        'StockUnico', 'MovimientosStock',
        'AjustesInventario', 'DetallesAjuste',
        'CostosHistoricos'
    ],
    'ventas': [
        'Ventas', 'DetallesVenta',
        'PagosVenta', 'AplicacionPagosVentas',
        'NotasCreditoCliente', 'DetallesNotaCredito',
        'Promociones', 'CategoriasPromocion', 'ProductosPromocion', 'PromocionesAplicadas'
    ],
    'compras': [
        'Proveedores', 'Compras', 'DetallesCompra',
        'PagosProveedores', 'AplicacionPagosCompras',
        'NotasCreditoProveedor', 'DetallesNotaCreditoProveedor'
    ],
    'almuerzos': [
        'PlanesAlmuerzo', 'TiposAlmuerzo',
        'SuscripcionesAlmuerzo', 'RegistrosConsumoAlmuerzo',
        'CuentasAlmuerzoMensual', 'PagosAlmuerzoMensual', 'PagosCuentasAlmuerzo',
        'Alergenos', 'ProductosAlergenos'
    ],
    'core': [
        'Tarjetas', 'TarjetasAutorizacion',
        'CargasSaldo', 'ConsumosTarjeta',
        'TransaccionesOnline',
        'MediosPago',
        'ConfiguracionSistema', 'CacheConfiguracion'
    ],
    'contabilidad': [
        'Cajas', 'CierresCaja', 'MovimientosCaja',
        'TarifasComision', 'AuditoriaComisiones',
        'ConciliacionPagos',
        'DocumentosTributarios', 'DocumentoImpuestos',
        'Timbrados', 'PuntosExpedicion',
        'DatosEmpresa', 'Impuestos'
    ],
    'notificaciones': [
        'NotificacionesPortal', 'NotificacionesSaldo',
        'SolicitudesNotificacion', 'PreferenciasNotificacion',
        'EmailsEnviados', 'SmsEnviados',
        'PlantillasEmail', 'PlantillasSms',
        'CampanasComunicacion',
        'AlertasAutomaticas', 'AlertaDestinatarios', 'AlertasSistema', 'HistorialAlertas',
        'AnomaliasDetectadas', 'RestriccionesHorarias'
    ],
    'api_integrations': [
        'ProveedoresApi', 'EndpointsApi',
        'LogsLlamadasApi', 'CredencialesApi',
        'LogsWebhooks', 'WebhookEndpoints'
    ],
    'reportes': [
        'PlantillasReporte', 'Dashboards',
        'KpiMetricas', 'ValoresKpi',
        'PlantillasTarea', 'EjecucionesTarea', 'DestinatariosTarea'
    ]
}

def extract_models_from_file():
    """Extrae todos los modelos del archivo generated_models.py"""
    # El archivo fue generado en UTF-16 LE
    try:
        with open(GENERATED_FILE, 'r', encoding='utf-16-le') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Intentar con BOM
        with open(GENERATED_FILE, 'r', encoding='utf-16') as f:
            content = f.read()
    
    # Patrón para extraer clases completas
    pattern = r'(class\s+(\w+)\(models\.Model\):.*?)(?=\n\nclass\s|\n\n$|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    models_dict = {}
    for match in matches:
        class_code = match[0].strip()
        class_name = match[1]
        models_dict[class_name] = class_code
    
    return models_dict

def build_models_file(app_name, model_names, all_models):
    """Construye el contenido del archivo models.py para una app"""
    header = f'''"""
Modelos de la app {app_name}
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


'''
    
    models_code = []
    for model_name in model_names:
        if model_name in all_models:
            model_code = all_models[model_name]
            # Reemplazar managed = False con managed = True
            model_code = model_code.replace('managed = False', 'managed = True')
            models_code.append(model_code)
    
    return header + '\n\n'.join(models_code) + '\n'

def distribute_models():
    """Distribuye los modelos a sus respectivas apps"""
    print("Extrayendo modelos del archivo generado...")
    all_models = extract_models_from_file()
    print(f"Total de modelos encontrados: {len(all_models)}")
    
    print("\nDistribuyendo modelos a las apps:")
    for app_name, model_names in MODEL_DISTRIBUTION.items():
        app_path = BASE_DIR / 'apps' / app_name
        models_file = app_path / 'models.py'
        
        # Construir contenido del archivo
        content = build_models_file(app_name, model_names, all_models)
        
        # Escribir archivo
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ {app_name}: {len(model_names)} modelos -> {models_file}")
    
    print("\n¡Distribución completada!")
    
    # Verificar modelos no asignados
    assigned_models = set()
    for models in MODEL_DISTRIBUTION.values():
        assigned_models.update(models)
    
    unassigned = set(all_models.keys()) - assigned_models
    if unassigned:
        print(f"\n⚠ Modelos no asignados ({len(unassigned)}):")
        for model in sorted(unassigned):
            print(f"    - {model}")

if __name__ == '__main__':
    distribute_models()
