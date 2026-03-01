"""
API v1 URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets
from apps.clientes.views import ClientesViewSet, HijosViewSet
from apps.productos.views import ProductosViewSet, CategoriasViewSet
from apps.ventas.views import VentasViewSet, DetallesVentaViewSet, PagosVentaViewSet, NotasCreditoClienteViewSet, PromocionesViewSet
from apps.compras.views import ProveedoresViewSet, ComprasViewSet, DetallesCompraViewSet, PagosProveedoresViewSet, NotasCreditoProveedorViewSet
from apps.core.views import TarjetasViewSet, CargasSaldoViewSet, ConsumosTarjetaViewSet, MediosPagoViewSet, ConfiguracionSistemaViewSet
from apps.almuerzos.views import PlanesAlmuerzoViewSet, TiposAlmuerzoViewSet, SuscripcionesAlmuerzoViewSet, RegistrosConsumoAlmuerzoViewSet, AlergenosViewSet
from apps.usuarios.views import RolesViewSet, EmpleadosViewSet, PerfilesUsuarioViewSet, UsuariosPortalViewSet
from apps.inventario.views import StockUnicoViewSet, MovimientosStockViewSet, AjustesInventarioViewSet

# Create a router for ViewSets
router = DefaultRouter()

# Register Clientes ViewSets
router.register(r'clientes', ClientesViewSet)
router.register(r'hijos', HijosViewSet)

# Register Productos ViewSets
router.register(r'productos', ProductosViewSet)
router.register(r'categorias', CategoriasViewSet)

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

# Register Usuarios ViewSets
router.register(r'roles', RolesViewSet)
router.register(r'empleados', EmpleadosViewSet)
router.register(r'perfiles-usuario', PerfilesUsuarioViewSet)
router.register(r'usuarios-portal', UsuariosPortalViewSet)

# Register Inventario ViewSets
router.register(r'stock', StockUnicoViewSet)
router.register(r'movimientos-stock', MovimientosStockViewSet)
router.register(r'ajustes-inventario', AjustesInventarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
