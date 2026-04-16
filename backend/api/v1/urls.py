"""
API v1 URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets
from apps.clientes.views import ClientesViewSet, HijosViewSet, TiposClienteViewSet, GradosViewSet, RestriccionesHijosViewSet, PaisViewSet, CiudadViewSet
from apps.productos.views import ProductosViewSet, CategoriasViewSet, UnidadesMedidaViewSet, ListasPreciosViewSet, PreciosPorListaViewSet
from apps.contabilidad.views import (
    ImpuestosViewSet, DatosEmpresaViewSet, TimbradosViewSet,
    DocumentosTributariosViewSet, PuntosExpedicionViewSet,
    CajasViewSet, CierresCajaViewSet, MovimientosCajaViewSet,
    FacturacionViewSet,
)
from apps.ventas.views import VentasViewSet, DetallesVentaViewSet, PagosVentaViewSet, NotasCreditoClienteViewSet, PromocionesViewSet, CondicionVentaViewSet
from apps.compras.views import ProveedoresViewSet, ComprasViewSet, DetallesCompraViewSet, PagosProveedoresViewSet, NotasCreditoProveedorViewSet
from apps.cobros.views import PagosClientesViewSet
from apps.core.views import TarjetasViewSet, CargasSaldoViewSet, ConsumosTarjetaViewSet, MediosPagoViewSet, ConfiguracionSistemaViewSet
from apps.almuerzos.views import PlanesAlmuerzoViewSet, TiposAlmuerzoViewSet, SuscripcionesAlmuerzoViewSet, RegistrosConsumoAlmuerzoViewSet, AlergenosViewSet, CuentasAlmuerzoMensualViewSet, PrecioAlmuerzoViewSet
from apps.usuarios.views import RolesViewSet, EmpleadosViewSet, PerfilesUsuarioViewSet, UsuariosPortalViewSet, PortalAuthViewSet, AuthViewSet, PermisosViewSet, AuditoriaOperacionesViewSet, TwoFactorViewSet, SesionesViewSet, PasswordRecoveryViewSet
from apps.inventario.views import StockUnicoViewSet, MovimientosStockViewSet, AjustesInventarioViewSet
from apps.reportes.views import (
    ReportesViewSet,
    PlantillasReporteViewSet, DashboardsViewSet, KpiMetricasViewSet,
    PlantillasTareaViewSet, EjecucionesTareaViewSet,
    TareasProgradasViewSet,
    reportes_util_view, reportes_export_view,
)
from apps.notificaciones.views import NotificacionesPortalViewSet, NotificacionesSaldoViewSet, AlertasSistemaViewSet, PreferenciasNotificacionViewSet, PlantillasEmailViewSet
# BANCARD REMOVIDO - Usando SIPAP QR nativo de Paraguay
# from apps.api_integrations.views import bancard_webhook, webhook_test
from apps.api_integrations.views import sipap_webhook, webhook_test

# Create a router for ViewSets
router = DefaultRouter()

# Register Clientes ViewSets
router.register(r'clientes', ClientesViewSet)
router.register(r'hijos', HijosViewSet)
router.register(r'tipos-cliente', TiposClienteViewSet)
router.register(r'grados', GradosViewSet)
router.register(r'restricciones-hijos', RestriccionesHijosViewSet)
router.register(r'paises', PaisViewSet, basename='paises')
router.register(r'ciudades', CiudadViewSet, basename='ciudades')

# Register Productos ViewSets
router.register(r'productos', ProductosViewSet)
router.register(r'categorias', CategoriasViewSet)
router.register(r'unidades-medida', UnidadesMedidaViewSet)
router.register(r'listas-precios', ListasPreciosViewSet)
router.register(r'precios-por-lista', PreciosPorListaViewSet)
router.register(r'impuestos', ImpuestosViewSet, basename='impuestos')
router.register(r'datos-empresa', DatosEmpresaViewSet, basename='datos-empresa')
router.register(r'timbrados', TimbradosViewSet, basename='timbrados')
router.register(r'puntos-expedicion', PuntosExpedicionViewSet, basename='puntos-expedicion')
router.register(r'documentos-tributarios', DocumentosTributariosViewSet, basename='documentos-tributarios')
router.register(r'facturacion', FacturacionViewSet, basename='facturacion')
# Caja
router.register(r'cajas', CajasViewSet, basename='cajas')
router.register(r'cierres-caja', CierresCajaViewSet, basename='cierres-caja')
router.register(r'movimientos-caja', MovimientosCajaViewSet, basename='movimientos-caja')

# Register Ventas ViewSets
router.register(r'ventas', VentasViewSet)
router.register(r'detalles-venta', DetallesVentaViewSet)
router.register(r'pagos-venta', PagosVentaViewSet)
router.register(r'notas-credito-cliente', NotasCreditoClienteViewSet)
router.register(r'promociones', PromocionesViewSet)
router.register(r'condiciones-venta', CondicionVentaViewSet, basename='condiciones-venta')
router.register(r'notas-credito-proveedor', NotasCreditoProveedorViewSet)

# Register Core ViewSets
router.register(r'tarjetas', TarjetasViewSet)
router.register(r'cargas-saldo', CargasSaldoViewSet)
router.register(r'consumos-tarjeta', ConsumosTarjetaViewSet)
router.register(r'medios-pago', MediosPagoViewSet)
router.register(r'configuracion-sistema', ConfiguracionSistemaViewSet)
router.register(r'configuracion', ConfiguracionSistemaViewSet, basename='configuracion')

# Register Almuerzos ViewSets
router.register(r'planes-almuerzo', PlanesAlmuerzoViewSet)
router.register(r'tipos-almuerzo', TiposAlmuerzoViewSet)
router.register(r'suscripciones-almuerzo', SuscripcionesAlmuerzoViewSet)
router.register(r'registros-consumo-almuerzo', RegistrosConsumoAlmuerzoViewSet)
router.register(r'alergenos', AlergenosViewSet)
router.register(r'cuentas-almuerzo-mensual', CuentasAlmuerzoMensualViewSet)
router.register(r'precios-almuerzo', PrecioAlmuerzoViewSet)

# Register Usuarios ViewSets
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'roles', RolesViewSet)
router.register(r'empleados', EmpleadosViewSet)
router.register(r'perfiles-usuario', PerfilesUsuarioViewSet)
router.register(r'usuarios-portal', UsuariosPortalViewSet)
router.register(r'portal-auth', PortalAuthViewSet, basename='portal-auth')
router.register(r'permisos', PermisosViewSet, basename='permisos')
router.register(r'usuarios/auditoria', AuditoriaOperacionesViewSet, basename='auditoria')
router.register(r'2fa', TwoFactorViewSet, basename='2fa')
router.register(r'sesiones', SesionesViewSet, basename='sesiones')
router.register(r'password', PasswordRecoveryViewSet, basename='password')

# Register Reportes ViewSets
router.register(r'reportes', ReportesViewSet, basename='reportes')
router.register(r'reportes/plantillas', PlantillasReporteViewSet, basename='plantillas-reporte')
router.register(r'reportes/dashboards', DashboardsViewSet, basename='dashboards')
router.register(r'reportes/kpis', KpiMetricasViewSet, basename='kpi-metricas')
router.register(r'reportes/tareas', PlantillasTareaViewSet, basename='plantillas-tarea')
router.register(r'reportes/ejecuciones', EjecucionesTareaViewSet, basename='ejecuciones-tarea')
router.register(r'tareas-programadas', TareasProgradasViewSet, basename='tareas-programadas')

# Register Inventario ViewSets
router.register(r'stock', StockUnicoViewSet, basename='stock')
router.register(r'movimientos-stock', MovimientosStockViewSet, basename='movimientos-stock')
router.register(r'ajustes-inventario', AjustesInventarioViewSet, basename='ajustes-inventario')

# Register Compras ViewSets
router.register(r'proveedores', ProveedoresViewSet, basename='proveedores')
router.register(r'compras', ComprasViewSet, basename='compras')
router.register(r'detalles-compra', DetallesCompraViewSet, basename='detalles-compra')
router.register(r'pagos-proveedores', PagosProveedoresViewSet, basename='pagos-proveedores')

# Register Cobros ViewSets
router.register(r'cobros', PagosClientesViewSet, basename='cobros')

# Register Notificaciones ViewSets
router.register(r'notificaciones-portal', NotificacionesPortalViewSet, basename='notificaciones-portal')
router.register(r'notificaciones-saldo', NotificacionesSaldoViewSet, basename='notificaciones-saldo')
router.register(r'alertas-sistema', AlertasSistemaViewSet, basename='alertas-sistema')
router.register(r'preferencias-notificacion', PreferenciasNotificacionViewSet, basename='preferencias-notificacion')
router.register(r'plantillas-email', PlantillasEmailViewSet, basename='plantillas-email')

urlpatterns = [
    path('', include(router.urls)),
    # Webhook endpoints (no auth required)
    # BANCARD REMOVIDO - Usando SIPAP QR
    # path('webhooks/bancard/', bancard_webhook, name='bancard-webhook'),
    path('webhooks/sipap/', sipap_webhook, name='sipap-webhook'),
    path('webhooks/test/', webhook_test, name='webhook-test'),
    # Reportes utility endpoints
    path('reportes/utils/validar_cron/', reportes_util_view, name='reportes-validar-cron'),
    path('reportes/utils/test_conexion/', reportes_util_view, name='reportes-test-conexion'),
    path('reportes/utils/esquema_bd/', reportes_util_view, name='reportes-esquema-bd'),
    path('reportes/utils/preview_query/', reportes_util_view, name='reportes-preview-query'),
    # Reportes export endpoints
    path('reportes/exportar/reporte/<int:pk>/', reportes_export_view, name='reportes-exportar-reporte'),
    path('reportes/exportar/dashboard/<int:pk>/', reportes_export_view, name='reportes-exportar-dashboard'),
    path('reportes/exportar/archivo/<str:file_id>/', reportes_export_view, name='reportes-descargar-archivo'),
]
