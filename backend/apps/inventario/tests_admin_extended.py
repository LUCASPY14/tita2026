"""
Tests for apps/inventario/admin.py
Covers all custom display methods across 8 admin classes.
"""
from unittest.mock import MagicMock, patch, call
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from apps.inventario.admin import (
    StockUnicoAdmin,
    MovimientosStockAdmin,
    AjustesInventarioAdmin,
    DetallesAjusteAdmin,
    CostosHistoricosAdmin,
    AlertasStockAdmin,
    LotesProductoAdmin,
    AlertasVencimientoAdmin,
)
from apps.inventario.models import (
    StockUnico,
    MovimientosStock,
    AjustesInventario,
    DetallesAjuste,
    CostosHistoricos,
    AlertasStock,
    LotesProducto,
    AlertasVencimiento,
)

_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# StockUnicoAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class StockUnicoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = StockUnicoAdmin(StockUnico, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Arroz 1kg")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Arroz 1kg")

    def test_cantidad_actual_requiere_reposicion(self):
        obj = _mock_obj(requiere_reposicion=True, cantidad=5)
        result = str(self.admin.cantidad_actual(obj))
        self.assertIn("red", result)
        self.assertIn("5", result)

    def test_cantidad_actual_ok(self):
        obj = _mock_obj(requiere_reposicion=False, cantidad=100)
        result = self.admin.cantidad_actual(obj)
        self.assertEqual(result, 100)

    def test_estado_stock_bajo(self):
        obj = _mock_obj(requiere_reposicion=True)
        result = str(self.admin.estado_stock(obj))
        self.assertIn("dc3545", result)
        self.assertIn("BAJO", result)

    def test_estado_stock_ok(self):
        obj = _mock_obj(requiere_reposicion=False)
        result = str(self.admin.estado_stock(obj))
        self.assertIn("28a745", result)
        self.assertIn("OK", result)

    def test_valor_inventario(self):
        obj = _mock_obj(valor_inventario=500000)
        result = self.admin.valor_inventario(obj)
        self.assertIn("500,000", result)


# =============================================================================
# MovimientosStockAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class MovimientosStockAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = MovimientosStockAdmin(MovimientosStock, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Leche")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Leche")

    def test_tipo_movimiento_color_ingreso(self):
        obj = _mock_obj(tipo_movimiento="Ingreso")
        result = str(self.admin.tipo_movimiento_color(obj))
        self.assertIn("28a745", result)
        self.assertIn("Ingreso", result)

    def test_tipo_movimiento_color_egreso(self):
        obj = _mock_obj(tipo_movimiento="Egreso")
        result = str(self.admin.tipo_movimiento_color(obj))
        self.assertIn("dc3545", result)
        self.assertIn("Egreso", result)

    def test_motivo_breve_corto(self):
        obj = _mock_obj(motivo="Compra directa")
        result = self.admin.motivo_breve(obj)
        self.assertEqual(result, "Compra directa")

    def test_motivo_breve_largo(self):
        obj = _mock_obj(motivo="X" * 60)
        result = self.admin.motivo_breve(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 53)

    def test_motivo_breve_exactamente_50(self):
        obj = _mock_obj(motivo="A" * 50)
        result = self.admin.motivo_breve(obj)
        self.assertEqual(result, "A" * 50)


# =============================================================================
# AjustesInventarioAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class AjustesInventarioAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AjustesInventarioAdmin(AjustesInventario, self.site)

    def test_tipo_ajuste_color_merma(self):
        obj = _mock_obj(tipo_ajuste="Merma")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("dc3545", result)
        self.assertIn("Merma", result)

    def test_tipo_ajuste_color_sobrante(self):
        obj = _mock_obj(tipo_ajuste="Sobrante")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("28a745", result)

    def test_tipo_ajuste_color_correccion(self):
        obj = _mock_obj(tipo_ajuste="Correccion")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("ffc107", result)

    def test_tipo_ajuste_color_vencimiento(self):
        obj = _mock_obj(tipo_ajuste="Vencimiento")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("6c757d", result)

    def test_tipo_ajuste_color_deterioro(self):
        obj = _mock_obj(tipo_ajuste="Deterioro")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("fd7e14", result)

    def test_tipo_ajuste_color_desconocido(self):
        obj = _mock_obj(tipo_ajuste="Otro")
        result = str(self.admin.tipo_ajuste_color(obj))
        self.assertIn("6c757d", result)

    def test_estado_ajuste_color_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_ajuste_color(obj))
        self.assertIn("ffc107", result)
        self.assertIn("Pendiente", result)

    def test_estado_ajuste_color_aprobado(self):
        obj = _mock_obj(estado="Aprobado")
        result = str(self.admin.estado_ajuste_color(obj))
        self.assertIn("28a745", result)

    def test_estado_ajuste_color_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_ajuste_color(obj))
        self.assertIn("dc3545", result)

    def test_estado_ajuste_color_aplicado(self):
        obj = _mock_obj(estado="Aplicado")
        result = str(self.admin.estado_ajuste_color(obj))
        self.assertIn("007bff", result)

    def test_estado_ajuste_color_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_ajuste_color(obj))
        self.assertIn("6c757d", result)

    def test_motivo_breve_corto(self):
        obj = _mock_obj(motivo="Ajuste normal")
        result = self.admin.motivo_breve(obj)
        self.assertEqual(result, "Ajuste normal")

    def test_motivo_breve_largo(self):
        obj = _mock_obj(motivo="Z" * 50)
        result = self.admin.motivo_breve(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 43)

    def test_autorizado_por_con_empleado(self):
        empleado = _mock_obj(nombre="Juan")
        obj = _mock_obj(id_empleado=empleado)
        result = self.admin.autorizado_por(obj)
        self.assertEqual(result, "Juan")

    def test_autorizado_por_sin_empleado(self):
        obj = _mock_obj(id_empleado=None)
        result = self.admin.autorizado_por(obj)
        self.assertEqual(result, "-")

    def test_aprobar_ajustes(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 3
        self.admin.aprobar_ajustes(request, queryset)
        queryset.update.assert_called_once_with(estado="Aprobado")

    def test_rechazar_ajustes(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 2
        self.admin.rechazar_ajustes(request, queryset)
        queryset.update.assert_called_once_with(estado="Rechazado")


# =============================================================================
# DetallesAjusteAdmin
# =============================================================================

class DetallesAjusteAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DetallesAjusteAdmin(DetallesAjuste, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Azúcar")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Azúcar")


# =============================================================================
# CostosHistoricosAdmin
# =============================================================================

class CostosHistoricosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CostosHistoricosAdmin(CostosHistoricos, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Aceite")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Aceite")

    def test_costo_unitario_format(self):
        obj = _mock_obj(costo_unitario=12500)
        result = self.admin.costo_unitario_format(obj)
        self.assertIn("12,500", result)


# =============================================================================
# AlertasStockAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class AlertasStockAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlertasStockAdmin(AlertasStock, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Pan")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Pan")

    def test_tipo_alerta_color_critico(self):
        obj = _mock_obj(tipo_alerta="stock_critico")
        obj.get_tipo_alerta_display.return_value = "Stock Crítico"
        result = str(self.admin.tipo_alerta_color(obj))
        self.assertIn("dc3545", result)

    def test_tipo_alerta_color_cero(self):
        obj = _mock_obj(tipo_alerta="stock_cero")
        obj.get_tipo_alerta_display.return_value = "Stock Cero"
        result = str(self.admin.tipo_alerta_color(obj))
        self.assertIn("fd7e14", result)

    def test_tipo_alerta_color_minimo(self):
        obj = _mock_obj(tipo_alerta="stock_minimo")
        obj.get_tipo_alerta_display.return_value = "Stock Mínimo"
        result = str(self.admin.tipo_alerta_color(obj))
        self.assertIn("ffc107", result)

    def test_tipo_alerta_color_desconocido(self):
        obj = _mock_obj(tipo_alerta="otro")
        obj.get_tipo_alerta_display.return_value = "Otro"
        result = str(self.admin.tipo_alerta_color(obj))
        self.assertIn("6c757d", result)

    def test_marcar_como_resuelta(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 1
        with patch('django.utils.timezone.now', return_value="2024-01-01"):
            self.admin.marcar_como_resuelta(request, queryset)
        queryset.update.assert_called_once()
        args = queryset.update.call_args[1]
        self.assertFalse(args['activa'])


# =============================================================================
# LotesProductoAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class LotesProductoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = LotesProductoAdmin(LotesProducto, self.site)

    def test_nombre_producto(self):
        producto = _mock_obj(descripcion="Harina")
        obj = _mock_obj(id_producto=producto)
        result = self.admin.nombre_producto(obj)
        self.assertEqual(result, "Harina")

    def test_fecha_vencimiento_color_sin_fecha(self):
        obj = _mock_obj(fecha_vencimiento=None)
        result = self.admin.fecha_vencimiento_color(obj)
        self.assertEqual(result, "-")

    def test_fecha_vencimiento_color_vencido(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "01/01/2020"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=-5)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("dc3545", result)  # rojo

    def test_fecha_vencimiento_color_muy_pronto(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "01/01/2024"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=3)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("fd7e14", result)  # naranja

    def test_fecha_vencimiento_color_pronto(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "15/01/2024"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=15)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("ffc107", result)  # amarillo

    def test_fecha_vencimiento_color_ok(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "01/06/2024"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=60)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("28a745", result)  # verde

    def test_fecha_vencimiento_color_exactamente_7_dias(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "08/01/2024"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=7)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("fd7e14", result)  # naranja (<=7)

    def test_fecha_vencimiento_color_exactamente_30_dias(self):
        fecha = MagicMock()
        fecha.strftime.return_value = "30/01/2024"
        obj = _mock_obj(fecha_vencimiento=fecha, dias_hasta_vencimiento=30)
        result = str(self.admin.fecha_vencimiento_color(obj))
        self.assertIn("ffc107", result)  # amarillo (<=30)

    def test_marcar_como_bloqueado(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 2
        with patch('django.utils.timezone.now', return_value="2024-01-01"):
            self.admin.marcar_como_bloqueado(request, queryset)
        queryset.update.assert_called_once()
        args = queryset.update.call_args[1]
        self.assertTrue(args['bloqueado'])
        self.assertEqual(args['motivo_bloqueo'], 'vencido')


# =============================================================================
# AlertasVencimientoAdmin
# =============================================================================

@patch('apps.inventario.admin.format_html', _plain_format_html)
class AlertasVencimientoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlertasVencimientoAdmin(AlertasVencimiento, self.site)

    def test_nombre_lote(self):
        lote = _mock_obj(numero_lote="L001")
        obj = _mock_obj(id_lote=lote)
        result = self.admin.nombre_lote(obj)
        self.assertEqual(result, "L001")

    def test_dias_restantes_color_vencido(self):
        obj = _mock_obj(dias_restantes=-3)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("dc3545", result)
        self.assertIn("VENCIDO", result)
        self.assertIn("3 días", result)

    def test_dias_restantes_color_critico(self):
        obj = _mock_obj(dias_restantes=2)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("dc3545", result)
        self.assertIn("CRÍTICO", result)

    def test_dias_restantes_color_urgente(self):
        obj = _mock_obj(dias_restantes=5)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("fd7e14", result)

    def test_dias_restantes_color_atencion(self):
        obj = _mock_obj(dias_restantes=10)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("ffc107", result)

    def test_dias_restantes_color_ok(self):
        obj = _mock_obj(dias_restantes=20)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("17a2b8", result)

    def test_dias_restantes_color_exactamente_0(self):
        obj = _mock_obj(dias_restantes=0)
        result = str(self.admin.dias_restantes_color(obj))
        # 0 <= 3 so CRÍTICO
        self.assertIn("dc3545", result)

    def test_dias_restantes_color_exactamente_3(self):
        obj = _mock_obj(dias_restantes=3)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("dc3545", result)

    def test_dias_restantes_color_exactamente_7(self):
        obj = _mock_obj(dias_restantes=7)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("fd7e14", result)

    def test_dias_restantes_color_exactamente_15(self):
        obj = _mock_obj(dias_restantes=15)
        result = str(self.admin.dias_restantes_color(obj))
        self.assertIn("ffc107", result)

    def test_marcar_como_descartado(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 1
        with patch('django.utils.timezone.now', return_value="2024-01-01"):
            self.admin.marcar_como_descartado(request, queryset)
        queryset.update.assert_called_once()
        args = queryset.update.call_args[1]
        self.assertEqual(args['accion_tomada'], 'descartado')
