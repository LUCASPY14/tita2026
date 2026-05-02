"""
Extended tests for apps/compras/admin.py targeting uncovered display methods.

Missing lines: 44, 50-54, 93-95, 101, 108, 115-122, 129-137, 148-151, 157-158,
181, 188, 195, 202, 209-211, 232, 242-250, 265, 275, 281, 320-322, 328, 335,
344-350, 361-362, 368-369, 391, 401, 408, 415
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.admin import AdminSite
from django.test import TestCase

from apps.compras.admin import (
    AplicacionPagosComprasAdmin,
    ComprasAdmin,
    DetallesCompraAdmin,
    DetallesNotaCreditoProveedorAdmin,
    NotasCreditoProveedorAdmin,
    PagosProveedoresAdmin,
    ProveedoresAdmin,
)
from apps.compras.models import (
    AplicacionPagosCompras,
    Compras,
    DetallesCompra,
    DetallesNotaCreditoProveedor,
    NotasCreditoProveedor,
    PagosProveedores,
    Proveedores,
)

# format_html compatibility patch
_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# ProveedoresAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class ProveedoresAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ProveedoresAdmin(Proveedores, self.site)

    def test_ruc_display(self):
        """Line 44: ruc_display wraps ruc in <code> tag."""
        obj = _mock_obj(ruc="80000001-1")
        result = self.admin.ruc_display(obj)
        self.assertIn("80000001-1", result)

    def test_estado_badge_activo(self):
        """Lines 50-54: estado=True returns green estado badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.estado_badge(obj)
        self.assertIn("ACTIVO", result)
        self.assertIn("#28a745", result)

    def test_estado_badge_inactivo(self):
        """Lines 50-54: estado=False returns red INACTIVO badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.estado_badge(obj)
        self.assertIn("INACTIVO", result)
        self.assertIn("#dc3545", result)


# =============================================================================
# ComprasAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class ComprasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ComprasAdmin(Compras, self.site)
        self.request = MagicMock()

    def test_nro_factura_display_with_value(self):
        """Lines 93-95: nro_factura truthy returns bold formatted string."""
        obj = _mock_obj(nro_factura="FAC-001")
        result = self.admin.nro_factura_display(obj)
        self.assertIn("FAC-001", result)
        self.assertIn("strong", result)

    def test_nro_factura_display_none(self):
        """Lines 93-95: nro_factura=None returns italic 'Sin factura'."""
        obj = _mock_obj(nro_factura=None)
        result = self.admin.nro_factura_display(obj)
        self.assertIn("Sin factura", result)

    def test_proveedor_nombre(self):
        """Line 101: proveedor_nombre returns razon_social from related object."""
        proveedor = _mock_obj(razon_social="Empresa XYZ")
        obj = _mock_obj(id_proveedor=proveedor)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "Empresa XYZ")

    def test_monto_display(self):
        """Line 108: monto_display returns formatted total amount."""
        obj = _mock_obj(monto_total=Decimal("500000"))
        result = self.admin.monto_display(obj)
        self.assertIn("500,000", result)

    def test_saldo_display_saldo_igual_monto(self):
        """Lines 115-122: saldo_pendiente == monto_total returns dc3545 (red)."""
        obj = _mock_obj(saldo_pendiente=Decimal("100000"), monto_total=Decimal("100000"))
        result = self.admin.saldo_display(obj)
        self.assertIn("#dc3545", result)
        self.assertIn("100,000", result)

    def test_saldo_display_saldo_parcial(self):
        """Lines 115-122: saldo_pendiente < monto_total returns fd7e14 (orange)."""
        obj = _mock_obj(saldo_pendiente=Decimal("50000"), monto_total=Decimal("100000"))
        result = self.admin.saldo_display(obj)
        self.assertIn("#fd7e14", result)

    def test_saldo_display_cero(self):
        """Lines 115-122: saldo_pendiente == 0 returns green ₲0."""
        obj = _mock_obj(saldo_pendiente=Decimal("0"), monto_total=Decimal("100000"))
        result = self.admin.saldo_display(obj)
        self.assertIn("#28a745", result)
        self.assertIn("₲ 0", result)

    def test_saldo_display_none(self):
        """Lines 115-122: saldo_pendiente=None also returns green ₲0."""
        obj = _mock_obj(saldo_pendiente=None, monto_total=Decimal("100000"))
        result = self.admin.saldo_display(obj)
        self.assertIn("₲ 0", result)

    def test_estado_badge_pendiente(self):
        """Lines 129-137: estado_pago='Pendiente' returns yellow badge."""
        obj = _mock_obj(estado_pago="Pendiente")
        result = self.admin.estado_badge(obj)
        self.assertIn("#ffc107", result)
        self.assertIn("PENDIENTE", result)

    def test_estado_badge_confirmado(self):
        """estado_pago='Confirmado' returns blue badge."""
        obj = _mock_obj(estado_pago="Confirmado")
        result = self.admin.estado_badge(obj)
        self.assertIn("#17a2b8", result)

    def test_estado_badge_parcial(self):
        """estado_pago='Parcial' returns orange badge."""
        obj = _mock_obj(estado_pago="Parcial")
        result = self.admin.estado_badge(obj)
        self.assertIn("#fd7e14", result)

    def test_estado_badge_pagado(self):
        """estado_pago='Pagado' returns green badge."""
        obj = _mock_obj(estado_pago="Pagado")
        result = self.admin.estado_badge(obj)
        self.assertIn("#28a745", result)

    def test_estado_badge_cancelado(self):
        """estado_pago='Cancelado' returns gray badge."""
        obj = _mock_obj(estado_pago="Cancelado")
        result = self.admin.estado_badge(obj)
        self.assertIn("#6c757d", result)

    def test_estado_badge_unknown(self):
        """Unknown estado_pago returns default gray badge."""
        obj = _mock_obj(estado_pago="Otro")
        result = self.admin.estado_badge(obj)
        self.assertIn("#6c757d", result)

    def test_marcar_como_pagado_action(self):
        """Lines 148-151: marcar_como_pagado updates eligible queryset."""
        queryset = MagicMock()
        queryset.filter.return_value = queryset
        queryset.update.return_value = 2
        self.admin.message_user = MagicMock()
        self.admin.marcar_como_pagado(self.request, queryset)
        queryset.update.assert_called_once_with(estado_pago="Pagado", saldo_pendiente=0)
        self.admin.message_user.assert_called_once()

    def test_generar_orden_pago_action(self):
        """Lines 157-158: generar_orden_pago calls message_user with count."""
        queryset = MagicMock()
        queryset.filter.return_value = queryset
        queryset.count.return_value = 3
        self.admin.message_user = MagicMock()
        self.admin.generar_orden_pago(self.request, queryset)
        self.admin.message_user.assert_called_once()
        call_args = str(self.admin.message_user.call_args)
        self.assertIn("3", call_args)


# =============================================================================
# DetallesCompraAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class DetallesCompraAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DetallesCompraAdmin(DetallesCompra, self.site)

    def test_compra_info(self):
        """Line 181: compra_info displays compra id and nro_factura."""
        compra = _mock_obj(nro_factura="FAC-001")
        obj = _mock_obj(id_compra_id=5, id_compra=compra)
        result = self.admin.compra_info(obj)
        self.assertIn("5", result)
        self.assertIn("FAC-001", result)

    def test_compra_info_sin_factura(self):
        """Line 181: compra with nro_factura=None shows 'S/F'."""
        compra = _mock_obj(nro_factura=None)
        obj = _mock_obj(id_compra_id=7, id_compra=compra)
        result = self.admin.compra_info(obj)
        self.assertIn("S/F", result)

    def test_producto_descripcion(self):
        """Line 188: producto_descripcion returns product description."""
        producto = _mock_obj(descripcion="Arroz 1kg")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.producto_descripcion(obj)
        self.assertEqual(result, "Arroz 1kg")

    def test_costo_display(self):
        """Line 195: costo_display returns formatted unit cost."""
        obj = _mock_obj(costo_unitario=Decimal("15000.50"))
        result = self.admin.costo_display(obj)
        self.assertIn("15,000.50", result)

    def test_subtotal_display(self):
        """Line 202: subtotal_display returns bold formatted subtotal."""
        obj = _mock_obj(subtotal=Decimal("75000.00"))
        result = self.admin.subtotal_display(obj)
        self.assertIn("75,000.00", result)
        self.assertIn("strong", result)

    def test_iva_display_with_value(self):
        """Lines 209-211: monto_iva truthy returns formatted IVA."""
        obj = _mock_obj(monto_iva=Decimal("10500.00"))
        result = self.admin.iva_display(obj)
        self.assertIn("10,500.00", result)

    def test_iva_display_none(self):
        """Lines 209-211: monto_iva=None returns '-'."""
        obj = _mock_obj(monto_iva=None)
        result = self.admin.iva_display(obj)
        self.assertEqual(result, "-")

    def test_iva_display_zero(self):
        """Lines 209-211: monto_iva=0 (falsy) returns '-'."""
        obj = _mock_obj(monto_iva=Decimal("0"))
        result = self.admin.iva_display(obj)
        self.assertEqual(result, "-")


# =============================================================================
# PagosProveedoresAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class PagosProveedoresAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PagosProveedoresAdmin(PagosProveedores, self.site)

    def test_medio_pago_nombre_with_nombre(self):
        """Line 232: medio_pago has nombre attribute."""
        medio = MagicMock(spec=["nombre"])
        medio.nombre = "Efectivo"
        obj = _mock_obj(id_medio_pago=medio)
        result = self.admin.medio_pago_nombre(obj)
        self.assertEqual(result, "Efectivo")

    def test_medio_pago_nombre_without_nombre(self):
        """Line 232: medio_pago without nombre uses str()."""
        medio = MagicMock()
        del medio.nombre  # Remove the attribute
        medio.__str__ = lambda self: "Medio Pago 1"
        obj = _mock_obj(id_medio_pago=medio)
        # hasattr check: if it has nombre attr, uses it; else str()
        # MagicMock auto-creates attributes, so let's test the str path differently
        obj.id_medio_pago = "Efectivo"  # String - no .nombre
        result = self.admin.medio_pago_nombre(obj)
        # obj.id_medio_pago is now a string "Efectivo", which doesn't have .nombre attribute
        # so it calls str(obj.id_medio_pago)
        self.assertIn("Efectivo", str(result))

    @patch("apps.compras.admin.AplicacionPagosCompras")
    def test_monto_total_aplicado_positive(self, mock_apc):
        """Lines 242-250: total > 0 returns green badge with amount."""
        mock_apc.objects.filter.return_value.aggregate.return_value = {"total": Decimal("75000.00")}
        obj = MagicMock()
        result = self.admin.monto_total_aplicado(obj)
        self.assertIn("#28a745", result)
        self.assertIn("75,000.00", result)

    @patch("apps.compras.admin.AplicacionPagosCompras")
    def test_monto_total_aplicado_zero(self, mock_apc):
        """Lines 242-250: total == 0 returns gray italic zero."""
        mock_apc.objects.filter.return_value.aggregate.return_value = {"total": None}
        obj = MagicMock()
        result = self.admin.monto_total_aplicado(obj)
        self.assertIn("₲ 0.00", result)


# =============================================================================
# AplicacionPagosComprasAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class AplicacionPagosComprasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AplicacionPagosComprasAdmin(AplicacionPagosCompras, self.site)

    def test_pago_info(self):
        """Line 265: pago_info displays pago id and formatted date."""
        from datetime import date

        pago = MagicMock()
        pago.fecha_creacion = date(2024, 3, 15)
        obj = _mock_obj(id_pago_proveedor_id=10, id_pago_proveedor=pago)
        result = self.admin.pago_info(obj)
        self.assertIn("10", result)
        self.assertIn("15/03/2024", result)

    def test_compra_info(self):
        """Line 275: compra_info displays compra id and nro_factura."""
        compra = _mock_obj(nro_factura="FAC-200")
        obj = _mock_obj(id_compra_id=20, id_compra=compra)
        result = self.admin.compra_info(obj)
        self.assertIn("20", result)
        self.assertIn("FAC-200", result)

    def test_monto_display(self):
        """Line 281: monto_display returns bold green amount."""
        obj = _mock_obj(monto_aplicado=Decimal("30000.00"))
        result = self.admin.monto_display(obj)
        self.assertIn("#28a745", result)
        self.assertIn("30,000.00", result)


# =============================================================================
# NotasCreditoProveedorAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class NotasCreditoProveedorAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = NotasCreditoProveedorAdmin(NotasCreditoProveedor, self.site)
        self.request = MagicMock()

    def test_nro_factura_display_with_value(self):
        """Lines 320-322: nro_factura_compra truthy returns code-formatted string."""
        obj = _mock_obj(nro_factura_compra="FAC-NC-001")
        result = self.admin.nro_factura_display(obj)
        self.assertIn("FAC-NC-001", result)

    def test_nro_factura_display_none(self):
        """Lines 320-322: nro_factura_compra=None returns italic 'S/F'."""
        obj = _mock_obj(nro_factura_compra=None)
        result = self.admin.nro_factura_display(obj)
        self.assertIn("S/F", result)

    def test_proveedor_nombre(self):
        """Line 328: proveedor_nombre returns razon_social."""
        proveedor = _mock_obj(razon_social="Dist ABC")
        obj = _mock_obj(id_proveedor=proveedor)
        result = self.admin.proveedor_nombre(obj)
        self.assertEqual(result, "Dist ABC")

    def test_monto_display(self):
        """Line 335: monto_display returns red bold formatted amount."""
        obj = _mock_obj(monto_total=Decimal("125000.00"))
        result = self.admin.monto_display(obj)
        self.assertIn("#dc3545", result)
        self.assertIn("125,000.00", result)

    def test_estado_badge_pendiente(self):
        """Lines 344-350: estado='Pendiente' returns yellow badge."""
        obj = _mock_obj(estado="Pendiente")
        result = self.admin.estado_badge(obj)
        self.assertIn("#ffc107", result)
        self.assertIn("PENDIENTE", result)

    def test_estado_badge_aplicado(self):
        """estado='Aplicado' returns green badge."""
        obj = _mock_obj(estado="Aplicado")
        result = self.admin.estado_badge(obj)
        self.assertIn("#28a745", result)

    def test_estado_badge_rechazado(self):
        """estado='Rechazado' returns red badge."""
        obj = _mock_obj(estado="Rechazado")
        result = self.admin.estado_badge(obj)
        self.assertIn("#dc3545", result)

    def test_estado_badge_unknown(self):
        """Unknown estado returns gray badge."""
        obj = _mock_obj(estado="Otro")
        result = self.admin.estado_badge(obj)
        self.assertIn("#6c757d", result)

    def test_marcar_como_aplicado_action(self):
        """Lines 361-362: marcar_como_aplicado updates Pendiente NCs to Aplicado."""
        queryset = MagicMock()
        queryset.filter.return_value = queryset
        queryset.update.return_value = 3
        self.admin.message_user = MagicMock()
        self.admin.marcar_como_aplicado(self.request, queryset)
        queryset.update.assert_called_once_with(estado="Aplicado")
        self.admin.message_user.assert_called_once()

    def test_rechazar_nota_action(self):
        """Lines 368-369: rechazar_nota updates Pendiente NCs to Rechazado."""
        queryset = MagicMock()
        queryset.filter.return_value = queryset
        queryset.update.return_value = 1
        self.admin.message_user = MagicMock()
        self.admin.rechazar_nota(self.request, queryset)
        queryset.update.assert_called_once_with(estado="Rechazado")
        self.admin.message_user.assert_called_once()


# =============================================================================
# DetallesNotaCreditoProveedorAdmin
# =============================================================================


@patch("apps.compras.admin.format_html", _plain_format_html)
class DetallesNotaCreditoProveedorAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DetallesNotaCreditoProveedorAdmin(DetallesNotaCreditoProveedor, self.site)

    def test_nota_info(self):
        """Line 391: nota_info displays NC id and nro_factura."""
        nota = _mock_obj(nro_factura_compra="FAC-NC-099")
        obj = _mock_obj(id_nota_proveedor_id=15, id_nota_proveedor=nota)
        result = self.admin.nota_info(obj)
        self.assertIn("15", result)
        self.assertIn("FAC-NC-099", result)

    def test_nota_info_sin_factura(self):
        """Line 391: nota with nro_factura_compra=None shows 'S/F'."""
        nota = _mock_obj(nro_factura_compra=None)
        obj = _mock_obj(id_nota_proveedor_id=16, id_nota_proveedor=nota)
        result = self.admin.nota_info(obj)
        self.assertIn("S/F", result)

    def test_producto_descripcion(self):
        """Line 401: producto_descripcion returns product description."""
        producto = _mock_obj(descripcion="Azúcar kg")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.producto_descripcion(obj)
        self.assertEqual(result, "Azúcar kg")

    def test_precio_display(self):
        """Line 408: precio_display returns formatted unit price."""
        obj = _mock_obj(precio_unitario=Decimal("5200.75"))
        result = self.admin.precio_display(obj)
        self.assertIn("5,200.75", result)

    def test_subtotal_display(self):
        """Line 415: subtotal_display returns bold red subtotal."""
        obj = _mock_obj(subtotal=Decimal("26003.75"))
        result = self.admin.subtotal_display(obj)
        self.assertIn("#dc3545", result)
        self.assertIn("26,003.75", result)
