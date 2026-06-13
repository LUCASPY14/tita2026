from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProveedorViewSet,
    CuentaCorrienteProveedorViewSet,
    CompraViewSet,
    DetalleCompraViewSet,
    PagoProveedorViewSet,
    AplicacionPagoCompraViewSet,
    NotaCreditoProveedorViewSet,
    DetalleNotaCreditoProveedorViewSet,
)

router = DefaultRouter()
router.register(r"proveedores", ProveedorViewSet, basename="proveedores")
router.register(r"cuentas-corrientes", CuentaCorrienteProveedorViewSet, basename="cuentas-corrientes")
router.register(r"compras", CompraViewSet, basename="compras")
router.register(r"detalles-compra", DetalleCompraViewSet, basename="detalles-compra")
router.register(r"pagos", PagoProveedorViewSet, basename="pagos-proveedor")
router.register(r"aplicaciones-pago", AplicacionPagoCompraViewSet, basename="aplicaciones-pago")
router.register(r"notas-credito", NotaCreditoProveedorViewSet, basename="notas-credito-proveedor")
router.register(r"detalles-nc", DetalleNotaCreditoProveedorViewSet, basename="detalles-nc")

urlpatterns = [
    path("", include(router.urls)),
]
