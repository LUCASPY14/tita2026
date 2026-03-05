"""
API v1 URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets
from apps.clientes.views import ClientesViewSet, HijosViewSet
from apps.productos.views import ProductosViewSet, CategoriasViewSet, UnidadesMedidaViewSet, ListasPreciosViewSet, PreciosPorListaViewSet
from apps.ventas.views import VentasViewSet, DetallesVentaViewSet, PagosVentaViewSet, NotasCreditoClienteViewSet, PromocionesViewSet
from apps.compras.views import ProveedoresViewSet, ComprasViewSet, DetallesCompraViewSet, PagosProveedoresViewSet, NotasCreditoProveedorViewSet
from apps.core.views import TarjetasViewSet, CargasSaldoViewSet, ConsumosTarjetaViewSet, MediosPagoViewSet, ConfiguracionSistemaViewSet
from apps.almuerzos.views import PlanesAlmuerzoViewSet, TiposAlmuerzoViewSet, SuscripcionesAlmuerzoViewSet, RegistrosConsumoAlmuerzoViewSet, AlergenosViewSet, CuentasAlmuerzoMensualViewSet
from apps.usuarios.views import RolesViewSet, EmpleadosViewSet, PerfilesUsuarioViewSet, UsuariosPortalViewSet, AuthViewSet, PermisosViewSet, AuditoriaOperacionesViewSet
from apps.inventario.views import StockUnicoViewSet, MovimientosStockViewSet, AjustesInventarioViewSet
from apps.reportes.views import ReportesViewSet
from apps.notificaciones.views import NotificacionesPortalViewSet, NotificacionesSaldoViewSet, AlertasSistemaViewSet, PreferenciasNotificacionViewSet

# Create a router for ViewSets
router = DefaultRouter()

# Register Clientes ViewSets
router.register(r'clientes', ClientesViewSet)
router.register(r'hijos', HijosViewSet)

# Register Productos ViewSets
router.register(r'productos', ProductosViewSet)
router.register(r'categorias', CategoriasViewSet)
router.register(r'unidades-medida', UnidadesMedidaViewSet)
router.register(r'listas-precios', ListasPreciosViewSet)
router.register(r'precios-por-lista', PreciosPorListaViewSet)

# Register Ventas ViewSets
router.register(r'ventas', VentasViewSet)
router.register(r'detalles-venta', DetallesVentaViewSet)
router.register(r'pagos-venta', PagosVentaViewSet)
router.register(r'notas-credito-cliente', NotasCreditoClienteViewSet)
router.register(r'promociones', PromocionesViewSet)

# Register Compras ViewSets
router.register(r'proveedores', ProveedoresViewSet)
router.register(r'compras', ComprasViewSet)
router.register(r'detalles-compra', DetallesCompraViewSet)
router.register(r'pagos-proveedores', PagosProveedoresViewSet)
router.register(r'notas-credito-proveedor', NotasCreditoProveedorViewSet)

# Register Core ViewSets
router.register(r'tarjetas', TarjetasViewSet)
router.register(r'cargas-saldo', CargasSaldoViewSet)
router.register(r'consumos-tarjeta', ConsumosTarjetaViewSet)
router.register(r'medios-pago', MediosPagoViewSet)
router.register(r'configuracion-sistema', ConfiguracionSistemaViewSet)

# Register Almuerzos ViewSets
router.register(r'planes-almuerzo', PlanesAlmuerzoViewSet)
router.register(r'tipos-almuerzo', TiposAlmuerzoViewSet)
router.register(r'suscripciones-almuerzo', SuscripcionesAlmuerzoViewSet)
router.register(r'registros-consumo-almuerzo', RegistrosConsumoAlmuerzoViewSet)
router.register(r'alergenos', AlergenosViewSet)
router.register(r'cuentas-almuerzo-mensual', CuentasAlmuerzoMensualViewSet)

# Register Usuarios ViewSets
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'roles', RolesViewSet)
router.register(r'empleados', EmpleadosViewSet)
router.register(r'perfiles-usuario', PerfilesUsuarioViewSet)
router.register(r'usuarios-portal', UsuariosPortalViewSet)
router.register(r'permisos', PermisosViewSet, basename='permisos')
router.register(r'usuarios/auditoria', AuditoriaOperacionesViewSet, basename='auditoria')

# Register Inventario ViewSets
router.register(r'stock', StockUnicoViewSet)
router.register(r'movimientos-stock', MovimientosStockViewSet)
router.register(r'ajustes-inventario', AjustesInventarioViewSet)

# Register Reportes ViewSets
router.register(r'reportes', ReportesViewSet, basename='reportes')

# Register Notificaciones ViewSets
router.register(r'notificaciones-portal', NotificacionesPortalViewSet, basename='notificaciones-portal')
router.register(r'notificaciones-saldo', NotificacionesSaldoViewSet, basename='notificaciones-saldo')
router.register(r'alertas-sistema', AlertasSistemaViewSet, basename='alertas-sistema')
router.register(r'preferencias-notificacion', PreferenciasNotificacionViewSet, basename='preferencias-notificacion')

urlpatterns = [
    path('', include(router.urls)),
]
