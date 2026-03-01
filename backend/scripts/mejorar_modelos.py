"""
Script para mejorar automáticamente los modelos de Django.
Agrega __str__, verbose_name, docstrings y convierte IntegerField a BooleanField donde corresponde.
"""
import os
import re
import sys

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, 'apps')

# Campos que deben ser BooleanField
BOOLEAN_FIELDS = [
    'activo', 'esta_activo', 'es_activo', 'activa',
    'permite_stock_negativo', 'genera_factura_legal',
    'requiere_autorizacion', 'requiere_codigo',
    'es_ultimo_grado', 'es_predeterminado', 'es_default',
    'visible', 'mostrar', 'habilitado', 'disponible',
    'validado', 'aprobado', 'confirmado'
]

# Configuración de verbose_name por app
VERBOSE_NAMES = {
    'clientes': {
        'Clientes': ('Cliente', 'Clientes'),
        'TiposCliente': ('Tipo de Cliente', 'Tipos de Cliente'),
        'Hijos': ('Hijo/Estudiante', 'Hijos/Estudiantes'),
        'Grados': ('Grado', 'Grados'),
        'HistorialGradosHijos': ('Historial de Grado', 'Historial de Grados'),
        'RestriccionesHijos': ('Restricción de Hijo', 'Restricciones de Hijos'),
        'AutorizacionesSaldoNegativo': ('Autorización de Saldo Negativo', 'Autorizaciones de Saldo Negativo'),
        'LogsAutorizaciones': ('Log de Autorización', 'Logs de Autorizaciones'),
    },
    'productos': {
        'Productos': ('Producto', 'Productos'),
        'Categorias': ('Categoría', 'Categorías'),
        'UnidadesMedida': ('Unidad de Medida', 'Unidades de Medida'),
        'ListasPrecios': ('Lista de Precios', 'Listas de Precios'),
        'PreciosPorLista': ('Precio por Lista', 'Precios por Lista'),
        'HistoricoPrecios': ('Histórico de Precio', 'Histórico de Precios'),
    },
    'ventas': {
        'Ventas': ('Venta', 'Ventas'),
        'DetallesVenta': ('Detalle de Venta', 'Detalles de Venta'),
        'PagosVenta': ('Pago de Venta', 'Pagos de Venta'),
        'AplicacionPagosVentas': ('Aplicación de Pago', 'Aplicaciones de Pagos'),
        'NotasCreditoCliente': ('Nota de Crédito', 'Notas de Crédito'),
        'DetallesNotaCredito': ('Detalle de Nota de Crédito', 'Detalles de Notas de Crédito'),
        'Promociones': ('Promoción', 'Promociones'),
        'CategoriasPromocion': ('Categoría en Promoción', 'Categorías en Promociones'),
        'ProductosPromocion': ('Producto en Promoción', 'Productos en Promociones'),
        'PromocionesAplicadas': ('Promoción Aplicada', 'Promociones Aplicadas'),
    },
    'compras': {
        'Proveedores': ('Proveedor', 'Proveedores'),
        'Compras': ('Compra', 'Compras'),
        'DetallesCompra': ('Detalle de Compra', 'Detalles de Compra'),
        'PagosProveedores': ('Pago a Proveedor', 'Pagos a Proveedores'),
        'AplicacionPagosCompras': ('Aplicación de Pago de Compra', 'Aplicaciones de Pagos de Compras'),
        'NotasCreditoProveedor': ('Nota de Crédito de Proveedor', 'Notas de Crédito de Proveedores'),
        'DetallesNotaCreditoProveedor': ('Detalle de NC de Proveedor', 'Detalles de NC de Proveedores'),
    },
    'core': {
        'Tarjetas': ('Tarjeta', 'Tarjetas'),
        'TiposTarjeta': ('Tipo de Tarjeta', 'Tipos de Tarjeta'),
        'TarjetasAutorizacion': ('Tarjeta de Autorización', 'Tarjetas de Autorización'),
        'MediosPago': ('Medio de Pago', 'Medios de Pago'),
        'Cajas': ('Caja', 'Cajas'),
        'CierresCaja': ('Cierre de Caja', 'Cierres de Caja'),
        'DetallesCierre': ('Detalle de Cierre', 'Detalles de Cierre'),
        'HistorialSaldos': ('Historial de Saldo', 'Historial de Saldos'),
    },
    'almuerzos': {
        'MenusProfesor': ('Menú de Profesor', 'Menús de Profesores'),
        'OpcionesMenu': ('Opción de Menú', 'Opciones de Menú'),
        'IngredientesOpcion': ('Ingrediente de Opción', 'Ingredientes de Opciones'),
        'PedidosProfesor': ('Pedido de Profesor', 'Pedidos de Profesores'),
        'DetallesPedidoProfesor': ('Detalle de Pedido', 'Detalles de Pedidos'),
        'PagosProfesor': ('Pago de Profesor', 'Pagos de Profesores'),
        'MenusAlumnosSemanal': ('Menú Semanal de Alumno', 'Menús Semanales de Alumnos'),
        'OpcionesMenuAlumno': ('Opción de Menú de Alumno', 'Opciones de Menú de Alumnos'),
        'PedidosAlumnoSemanal': ('Pedido Semanal de Alumno', 'Pedidos Semanales de Alumnos'),
    },
    'inventario': {
        'Inventario': ('Inventario', 'Inventarios'),
        'MovimientosInventario': ('Movimiento de Inventario', 'Movimientos de Inventario'),
        'Mermas': ('Merma', 'Mermas'),
        'AjustesInventario': ('Ajuste de Inventario', 'Ajustes de Inventario'),
        'TransferenciasInventario': ('Transferencia de Inventario', 'Transferencias de Inventario'),
    },
    'contabilidad': {
        'CuentasContables': ('Cuenta Contable', 'Cuentas Contables'),
        'TiposCuenta': ('Tipo de Cuenta', 'Tipos de Cuenta'),
        'Impuestos': ('Impuesto', 'Impuestos'),
        'AsientosContables': ('Asiento Contable', 'Asientos Contables'),
        'DetallesAsiento': ('Detalle de Asiento', 'Detalles de Asientos'),
        'DocumentosTributarios': ('Documento Tributario', 'Documentos Tributarios'),
        'Timbrados': ('Timbrado', 'Timbrados'),
        'PeriodosContables': ('Período Contable', 'Períodos Contables'),
        'BalanceGeneral': ('Balance General', 'Balances Generales'),
        'EstadoResultados': ('Estado de Resultado', 'Estados de Resultados'),
        'LibroDiario': ('Libro Diario', 'Libros Diarios'),
        'LibroMayor': ('Libro Mayor', 'Libros Mayores'),
    },
    'usuarios': {
        'Empleados': ('Empleado', 'Empleados'),
        'Cargos': ('Cargo', 'Cargos'),
        'Turnos': ('Turno', 'Turnos'),
        'TurnosEmpleado': ('Turno de Empleado', 'Turnos de Empleados'),
        'AsistenciaEmpleados': ('Asistencia de Empleado', 'Asistencias de Empleados'),
        'Usuarios': ('Usuario', 'Usuarios'),
        'Roles': ('Rol', 'Roles'),
        'Permisos': ('Permiso', 'Permisos'),
        'RolesPermisos': ('Rol-Permiso', 'Roles-Permisos'),
        'UsuariosRoles': ('Usuario-Rol', 'Usuarios-Roles'),
        'SesionesUsuario': ('Sesión de Usuario', 'Sesiones de Usuarios'),
        'LogsAuditoria': ('Log de Auditoría', 'Logs de Auditoría'),
        'HistorialContrasenas': ('Historial de Contraseña', 'Historiales de Contraseñas'),
        'ConfiguracionesSeguridad': ('Configuración de Seguridad', 'Configuraciones de Seguridad'),
        'IntentosAcceso': ('Intento de Acceso', 'Intentos de Acceso'),
        'RecuperacionContrasena': ('Recuperación de Contraseña', 'Recuperaciones de Contraseñas'),
        'TokensAcceso': ('Token de Acceso', 'Tokens de Acceso'),
    },
    'notificaciones': {
        'Notificaciones': ('Notificación', 'Notificaciones'),
        'PlantillasNotificacion': ('Plantilla de Notificación', 'Plantillas de Notificaciones'),
        'ConfiguracionNotificaciones': ('Configuración de Notificación', 'Configuraciones de Notificaciones'),
        'PreferenciasNotificacion': ('Preferencia de Notificación', 'Preferencias de Notificaciones'),
        'LogsNotificaciones': ('Log de Notificación', 'Logs de Notificaciones'),
        'DestinatariosNotificacion': ('Destinatario de Notificación', 'Destinatarios de Notificaciones'),
        'Alertas': ('Alerta', 'Alertas'),
        'TiposAlerta': ('Tipo de Alerta', 'Tipos de Alerta'),
        'AlertasEnviadas': ('Alerta Enviada', 'Alertas Enviadas'),
        'SuscripcionesAlerta': ('Suscripción de Alerta', 'Suscripciones de Alertas'),
        'EmailsEnviados': ('Email Enviado', 'Emails Enviados'),
        'EmailsProgramados': ('Email Programado', 'Emails Programados'),
        'PlantillasEmail': ('Plantilla de Email', 'Plantillas de Emails'),
        'ConfiguracionEmail': ('Configuración de Email', 'Configuraciones de Emails'),
        'SMSEnviados': ('SMS Enviado', 'SMS Enviados'),
    },
    'reportes': {
        'Reportes': ('Reporte', 'Reportes'),
        'TiposReporte': ('Tipo de Reporte', 'Tipos de Reporte'),
        'ParametrosReporte': ('Parámetro de Reporte', 'Parámetros de Reportes'),
        'ReportesGenerados': ('Reporte Generado', 'Reportes Generados'),
        'ReportesProgramados': ('Reporte Programado', 'Reportes Programados'),
        'DestinatariosReporte': ('Destinatario de Reporte', 'Destinatarios de Reportes'),
        'PlantillasReporte': ('Plantilla de Reporte', 'Plantillas de Reportes'),
    },
    'api_integrations': {
        'IntegracionesAPI': ('Integración API', 'Integraciones API'),
        'ConfiguracionesIntegracion': ('Configuración de Integración', 'Configuraciones de Integraciones'),
        'LogsIntegracion': ('Log de Integración', 'Logs de Integraciones'),
        'CredencialesAPI': ('Credencial API', 'Credenciales API'),
        'WebhooksEntrantes': ('Webhook Entrante', 'Webhooks Entrantes'),
        'WebhooksSalientes': ('Webhook Saliente', 'Webhooks Salientes'),
    }
}


def convert_to_boolean_field(content, field_name):
    """Convierte un IntegerField a BooleanField"""
    # Buscar el patrón del campo
    pattern = rf"(\s+{field_name}\s*=\s*)models\.IntegerField\((.*?)\)"
    
    def replacement(match):
        prefix = match.group(1)
        params = match.group(2)
        
        # Remover parámetros no aplicables a BooleanField
        params = re.sub(r'max_length=\d+,?\s*', '', params)
        params = re.sub(r'unique=True,?\s*', '', params)
        
        # Asegurar que tenga default
        if 'default' not in params:
            if params and not params.strip().endswith(','):
                params += ', '
            params += 'default=True'
        
        return f"{prefix}models.BooleanField({params})"
    
    return re.sub(pattern, replacement, content)


def add_str_method(content, model_name):
    """Agrega método __str__ a un modelo si no lo tiene"""
    # Verificar si ya tiene __str__
    if re.search(rf'class {model_name}.*?def __str__', content, re.DOTALL):
        return content
    
    # Encontrar la clase y su Meta
    class_pattern = rf'(class {model_name}\(models\.Model\):.*?)(class Meta:)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if not match:
        return content
    
    # Agregar __str__ antes de Meta
    str_template = '\n\n    def __str__(self):\n        return f"{self.__class__.__name__} #{self.pk}"\n\n    '
    
    return content.replace(match.group(0), match.group(1) + str_template + match.group(2))


def add_verbose_name(content, app_name, model_name):
    """Agrega verbose_name y verbose_name_plural a Meta"""
    if app_name not in VERBOSE_NAMES or model_name not in VERBOSE_NAMES[app_name]:
        return content
    
    verbose, verbose_plural = VERBOSE_NAMES[app_name][model_name]
    
    # Buscar la clase Meta del modelo
    meta_pattern = rf'(class {model_name}\(models\.Model\):.*?class Meta:.*?db_table = [\'"].*?[\'"])'
    
    def add_verbose(match):
        meta_content = match.group(0)
        if 'verbose_name' not in meta_content:
            insertion = f"\n        verbose_name = '{verbose}'\n        verbose_name_plural = '{verbose_plural}'"
            # Insertar después de db_table
            meta_content = re.sub(
                r"(db_table = ['\"].*?['\"])",
                r"\1" + insertion,
                meta_content
            )
        return meta_content
    
    return re.sub(meta_pattern, add_verbose, content, flags=re.DOTALL)


def process_models_file(file_path, app_name):
    """Procesa un archivo models.py"""
    print(f"\n📝 Procesando: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Encontrar todos los modelos
    model_matches = re.findall(r'class (\w+)\(models\.Model\):', content)
    print(f"   Modelos encontrados: {', '.join(model_matches)}")
    
    # Convertir campos booleanos
    for field in BOOLEAN_FIELDS:
        if f'{field} = models.IntegerField' in content:
            content = convert_to_boolean_field(content, field)
            print(f"   ✓ Convertido campo booleano: {field}")
    
    # Agregar __str__ y verbose_name a cada modelo
    for model_name in model_matches:
        # Agregar __str__
        new_content = add_str_method(content, model_name)
        if new_content != content:
            print(f"   ✓ Agregado __str__() a {model_name}")
            content = new_content
        
        # Agregar verbose_name
        new_content = add_verbose_name(content, app_name, model_name)
        if new_content != content:
            print(f"   ✓ Agregado verbose_name a {model_name}")
            content = new_content
    
    # Guardar si hubo cambios
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Archivo actualizado")
        return True
    else:
        print(f"   ℹ️  Sin cambios necesarios")
        return False


def main():
    """Función principal"""
    print("=" * 70)
    print("🚀 INICIANDO MEJORA DE MODELOS")
    print("=" * 70)
    
    apps_to_process = [
        'clientes', 'productos', 'ventas', 'compras',
        'core', 'almuerzos', 'inventario', 'contabilidad',
        'usuarios', 'notificaciones', 'reportes', 'api_integrations'
    ]
    total_processed = 0
    total_modified = 0
    
    for app_name in apps_to_process:
        app_path = os.path.join(APPS_DIR, app_name)
        models_path = os.path.join(app_path, 'models.py')
        
        if os.path.exists(models_path):
            total_processed += 1
            if process_models_file(models_path, app_name):
                total_modified += 1
        else:
            print(f"\n⚠️  No encontrado: {models_path}")
    
    print("\n" + "=" * 70)
    print(f"✅ RESUMEN:")
    print(f"   Apps procesadas: {total_processed}")
    print(f"   Archivos modificados: {total_modified}")
    print("=" * 70)


if __name__ == '__main__':
    main()
