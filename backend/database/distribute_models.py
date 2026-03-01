"""
Script para extraer y distribuir modelos desde generated_models.py a las apps correspondientes
"""

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
        'LogsWebhooks'
    ],
    'reportes': [
        'PlantillasReporte', 'Dashboards',
        'KpiMetricas', 'ValoresKpi',
        'PlantillasTarea', 'EjecucionesTarea', 'DestinatariosTarea'
    ]
}

# Generar resumen
total_models = sum(len(models) for models in MODEL_DISTRIBUTION.values())
print(f"Total de modelos a distribuir: {total_models}")
print("\nDistribución por app:")
for app, models in MODEL_DISTRIBUTION.items():
    print(f"  {app}: {len(models)} modelos")
