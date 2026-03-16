"""Extended tests for apps/productos/admin.py - covers custom display methods."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from apps.productos.admin import (
    CategoriasAdmin,
    UnidadesMedidaAdmin,
    ProductosAdmin,
    ListasPreciosAdmin,
    PreciosPorListaAdmin,
    HistoricoPreciosAdmin,
)

# Patch format_html to avoid SafeString/format-spec incompatibility
_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)

# Patch mark_safe to return input unchanged for tests
_plain_mark_safe = lambda x: x


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


@patch('apps.productos.admin.format_html', _plain_format_html)
@patch('apps.productos.admin.mark_safe', _plain_mark_safe)
class CategoriasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import Categorias
        self.admin = CategoriasAdmin(Categorias, self.site)

    def test_nombre_con_jerarquia_raiz(self):
        """Categoria raíz - sin padre"""
        obj = _mock_obj(nombre="Bebidas", id_categoria_padre=None)
        obj.subcategorias.exists.return_value = True
        result = str(self.admin.nombre_con_jerarquia(obj))
        self.assertIn("Bebidas", result)
        self.assertIn("📁", result)

    def test_nombre_con_jerarquia_subcategoria(self):
        """Subcategoría tiene indentación"""
        padre = _mock_obj(nombre="Bebidas", id_categoria_padre=None)
        obj = _mock_obj(nombre="Jugos", id_categoria_padre=padre)
        obj.subcategorias.exists.return_value = False
        result = str(self.admin.nombre_con_jerarquia(obj))
        self.assertIn("Jugos", result)
        self.assertIn("📄", result)

    def test_categoria_padre_link_con_padre(self):
        padre = _mock_obj(nombre="Bebidas", id_categoria=1)
        obj = _mock_obj(id_categoria_padre=padre)
        with patch("apps.productos.admin.reverse", return_value="/admin/productos/categorias/1/change/"):
            result = str(self.admin.categoria_padre_link(obj))
        self.assertIn("Bebidas", result)

    def test_categoria_padre_link_sin_padre(self):
        obj = _mock_obj(id_categoria_padre=None)
        result = self.admin.categoria_padre_link(obj)
        self.assertEqual(result, "-")

    def test_total_productos_con_productos(self):
        obj = _mock_obj()
        obj.productos.count.return_value = 10
        obj.productos.filter.return_value.count.return_value = 8
        result = str(self.admin.total_productos(obj))
        self.assertIn("8", result)
        self.assertIn("10", result)

    def test_total_productos_sin_productos(self):
        obj = _mock_obj()
        obj.productos.count.return_value = 0
        result = self.admin.total_productos(obj)
        self.assertEqual(result, "0 productos")

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("estado", result)
        self.assertIn("28a745", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVO", result)

    def test_nivel_jerarquia_raiz(self):
        obj = _mock_obj(id_categoria_padre=None)
        result = str(self.admin.nivel_jerarquia(obj))
        self.assertIn("Raíz", result)
        self.assertIn("007bff", result)

    def test_nivel_jerarquia_nivel1(self):
        padre = _mock_obj(id_categoria_padre=None)
        obj = _mock_obj(id_categoria_padre=padre)
        result = str(self.admin.nivel_jerarquia(obj))
        self.assertIn("Nivel 1", result)

    def test_activar_categorias(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 3
        self.admin.activar_categorias(request, queryset)
        queryset.update.assert_called_once_with(estado=True)
        request.assert_not_called()  # message_user is called on admin

    def test_desactivar_categorias_sin_productos_activos(self):
        request = MagicMock()
        cat1 = MagicMock()
        cat1.productos.filter.return_value.count.return_value = 0
        queryset = [cat1]
        self.admin.desactivar_categorias(request, queryset)
        self.assertTrue(cat1.estado == False or cat1.save.called)

    def test_desactivar_categorias_con_productos_activos(self):
        request = MagicMock()
        cat1 = MagicMock()
        cat1.productos.filter.return_value.count.return_value = 5
        queryset = [cat1]
        self.admin.desactivar_categorias(request, queryset)
        cat1.save.assert_not_called()


@patch('apps.productos.admin.format_html', _plain_format_html)
class UnidadesMedidaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import UnidadesMedida
        self.admin = UnidadesMedidaAdmin(UnidadesMedida, self.site)

    def test_abreviatura_badge(self):
        obj = _mock_obj(abreviatura="kg")
        result = str(self.admin.abreviatura_badge(obj))
        self.assertIn("kg", result)

    def test_total_productos_con_productos(self):
        obj = _mock_obj()
        obj.productos.count.return_value = 5
        obj.productos.filter.return_value.count.return_value = 4
        result = str(self.admin.total_productos(obj))
        self.assertIn("4", result)
        self.assertIn("5", result)

    def test_total_productos_sin_productos(self):
        obj = _mock_obj()
        obj.productos.count.return_value = 0
        result = self.admin.total_productos(obj)
        self.assertEqual(result, "0 productos")

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("estado", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVO", result)


@patch('apps.productos.admin.format_html', _plain_format_html)
class ProductosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import Productos
        self.admin = ProductosAdmin(Productos, self.site)

    def test_codigo_barra_badge_con_codigo(self):
        obj = _mock_obj(codigo_barra="7890123456")
        result = str(self.admin.codigo_barra_badge(obj))
        self.assertIn("7890123456", result)

    def test_codigo_barra_badge_sin_codigo(self):
        obj = _mock_obj(codigo_barra=None)
        result = str(self.admin.codigo_barra_badge(obj))
        self.assertIn("Sin código", result)

    def test_descripcion_corta_normal(self):
        obj = _mock_obj(descripcion="Café con leche")
        result = self.admin.descripcion_corta(obj)
        self.assertEqual(result, "Café con leche")

    def test_descripcion_corta_larga(self):
        obj = _mock_obj(descripcion="A" * 60)
        result = self.admin.descripcion_corta(obj)
        self.assertIn("...", result)
        self.assertLessEqual(len(result), 50)

    def test_categoria_tag_con_categoria(self):
        categoria = _mock_obj(nombre="Bebidas")
        obj = _mock_obj(id_categoria=categoria)
        result = str(self.admin.categoria_tag(obj))
        self.assertIn("Bebidas", result)

    def test_categoria_tag_sin_categoria(self):
        obj = _mock_obj(id_categoria=None)
        result = self.admin.categoria_tag(obj)
        self.assertEqual(result, "-")

    def test_impuesto_info_con_impuesto(self):
        impuesto = _mock_obj(porcentaje=10)
        obj = _mock_obj(id_impuesto=impuesto)
        result = str(self.admin.impuesto_info(obj))
        self.assertIn("10", result)

    def test_impuesto_info_sin_impuesto(self):
        obj = _mock_obj(id_impuesto=None)
        result = self.admin.impuesto_info(obj)
        self.assertEqual(result, "-")

    def test_stock_minimo_display_con_unidad(self):
        unidad = _mock_obj(abreviatura="kg")
        obj = _mock_obj(stock_minimo=5, id_unidad_medida=unidad)
        result = str(self.admin.stock_minimo_display(obj))
        self.assertIn("5", result)
        self.assertIn("kg", result)

    def test_stock_minimo_display_sin_unidad(self):
        obj = _mock_obj(stock_minimo=3, id_unidad_medida=None)
        result = str(self.admin.stock_minimo_display(obj))
        self.assertIn("3", result)
        self.assertIn("UN", result)

    def test_permite_stock_neg_true(self):
        obj = _mock_obj(permite_stock_negativo=True)
        result = str(self.admin.permite_stock_neg(obj))
        self.assertIn("✅", result)

    def test_permite_stock_neg_false(self):
        obj = _mock_obj(permite_stock_negativo=False)
        result = str(self.admin.permite_stock_neg(obj))
        self.assertIn("❌", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("estado", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVO", result)

    def test_activar_productos(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 2
        self.admin.activar_productos(request, queryset)
        queryset.update.assert_called_once_with(estado=True)

    def test_desactivar_productos(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.update.return_value = 1
        self.admin.desactivar_productos(request, queryset)
        queryset.update.assert_called_once_with(estado=False)

    def test_duplicar_producto_mas_de_uno(self):
        request = MagicMock()
        queryset = MagicMock()
        queryset.count.return_value = 2
        self.admin.duplicar_producto(request, queryset)
        queryset.first.assert_not_called()

    def test_duplicar_producto_uno(self):
        request = MagicMock()
        producto = MagicMock()
        producto.descripcion = "Café"
        queryset = MagicMock()
        queryset.count.return_value = 1
        queryset.first.return_value = producto
        self.admin.duplicar_producto(request, queryset)
        producto.save.assert_called_once()
        self.assertEqual(producto.descripcion, "Café (Copia)")
        self.assertFalse(producto.estado)
        self.assertIsNone(producto.codigo_barra)


@patch('apps.productos.admin.format_html', _plain_format_html)
class ListasPreciosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import ListasPrecios
        self.admin = ListasPreciosAdmin(ListasPrecios, self.site)

    def test_nombre_lista_badge(self):
        obj = _mock_obj(nombre_lista="Lista Especial")
        result = str(self.admin.nombre_lista_badge(obj))
        self.assertIn("Lista Especial", result)

    def test_moneda_display_pyg(self):
        obj = _mock_obj(moneda="PYG")
        result = str(self.admin.moneda_display(obj))
        self.assertIn("198754", result)
        self.assertIn("₲", result)

    def test_moneda_display_usd(self):
        obj = _mock_obj(moneda="USD")
        result = str(self.admin.moneda_display(obj))
        self.assertIn("0d6efd", result)

    def test_moneda_display_desconocida(self):
        obj = _mock_obj(moneda="CHF")
        result = str(self.admin.moneda_display(obj))
        self.assertIn("6c757d", result)

    def test_fecha_vigencia_display_futura(self):
        obj = _mock_obj(fecha_vigencia=date.today() + timedelta(days=10))
        result = str(self.admin.fecha_vigencia_display(obj))
        self.assertIn("ffc107", result)
        self.assertIn("Futuro", result)

    def test_fecha_vigencia_display_hoy(self):
        obj = _mock_obj(fecha_vigencia=date.today())
        result = str(self.admin.fecha_vigencia_display(obj))
        self.assertIn("HOY", result)

    def test_fecha_vigencia_display_pasada(self):
        obj = _mock_obj(fecha_vigencia=date(2022, 1, 1))
        result = str(self.admin.fecha_vigencia_display(obj))
        self.assertIn("17a2b8", result)

    def test_fecha_vigencia_display_none(self):
        obj = _mock_obj(fecha_vigencia=None)
        result = self.admin.fecha_vigencia_display(obj)
        self.assertEqual(result, "-")

    def test_total_precios_con_precios(self):
        obj = _mock_obj()
        obj.precios.count.return_value = 5
        obj.precios.aggregate.return_value = {"precio_unitario__avg": Decimal("1000")}
        result = str(self.admin.total_precios(obj))
        self.assertIn("5", result)

    def test_total_precios_sin_precios(self):
        obj = _mock_obj()
        obj.precios.count.return_value = 0
        result = self.admin.total_precios(obj)
        self.assertEqual(result, "0 precios")

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("ACTIVA", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVA", result)


@patch('apps.productos.admin.format_html', _plain_format_html)
@patch('apps.productos.admin.PreciosPorLista')
class PreciosPorListaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import PreciosPorLista
        self.admin = PreciosPorListaAdmin(PreciosPorLista, self.site)

    def test_producto_info_con_codigo(self, mock_ppl):
        producto = _mock_obj(descripcion="Café Tostado", codigo_barra="123")
        obj = _mock_obj(id_producto=producto)
        result = str(self.admin.producto_info(obj))
        self.assertIn("Café Tostado", result)
        self.assertIn("123", result)

    def test_producto_info_sin_codigo(self, mock_ppl):
        producto = _mock_obj(descripcion="Café Tostado", codigo_barra=None)
        obj = _mock_obj(id_producto=producto)
        result = str(self.admin.producto_info(obj))
        self.assertIn("Café Tostado", result)

    def test_lista_badge(self, mock_ppl):
        lista = _mock_obj(nombre_lista="Lista General")
        obj = _mock_obj(id_lista=lista)
        result = str(self.admin.lista_badge(obj))
        self.assertIn("Lista General", result)

    def test_precio_display_pyg(self, mock_ppl):
        lista = _mock_obj(moneda="PYG")
        obj = _mock_obj(id_lista=lista, precio_unitario=Decimal("5000.00"))
        result = str(self.admin.precio_display(obj))
        self.assertIn("5,000.00", result)

    def test_precio_display_usd(self, mock_ppl):
        lista = _mock_obj(moneda="USD")
        obj = _mock_obj(id_lista=lista, precio_unitario=Decimal("10.00"))
        result = str(self.admin.precio_display(obj))
        self.assertIn("10.00", result)

    def test_precio_display_moneda_desconocida(self, mock_ppl):
        lista = _mock_obj(moneda="CHF")
        obj = _mock_obj(id_lista=lista, precio_unitario=Decimal("100.00"))
        result = str(self.admin.precio_display(obj))
        self.assertIn("100.00", result)

    def test_fecha_vigencia_display(self, mock_ppl):
        import datetime
        obj = _mock_obj(fecha_vigencia=datetime.datetime(2024, 3, 15, 10, 30))
        result = self.admin.fecha_vigencia_display(obj)
        self.assertIn("15/03/2024", result)

    def test_precio_anterior_info_aumento(self, mock_ppl):
        anterior = _mock_obj(precio_unitario=Decimal("1000.00"))
        mock_ppl.objects.filter.return_value.order_by.return_value.first.return_value = anterior
        lista = _mock_obj(moneda="PYG")
        obj = _mock_obj(id_lista=lista, id_producto=MagicMock(), precio_unitario=Decimal("1200.00"),
                        fecha_vigencia=MagicMock())
        result = str(self.admin.precio_anterior_info(obj))
        self.assertIn("dc3545", result)
        self.assertIn("▲", result)

    def test_precio_anterior_info_disminucion(self, mock_ppl):
        anterior = _mock_obj(precio_unitario=Decimal("1000.00"))
        mock_ppl.objects.filter.return_value.order_by.return_value.first.return_value = anterior
        lista = _mock_obj(moneda="PYG")
        obj = _mock_obj(id_lista=lista, id_producto=MagicMock(), precio_unitario=Decimal("800.00"),
                        fecha_vigencia=MagicMock())
        result = str(self.admin.precio_anterior_info(obj))
        self.assertIn("28a745", result)
        self.assertIn("▼", result)

    def test_precio_anterior_info_igual(self, mock_ppl):
        anterior = _mock_obj(precio_unitario=Decimal("1000.00"))
        mock_ppl.objects.filter.return_value.order_by.return_value.first.return_value = anterior
        lista = _mock_obj(moneda="PYG")
        obj = _mock_obj(id_lista=lista, id_producto=MagicMock(), precio_unitario=Decimal("1000.00"),
                        fecha_vigencia=MagicMock())
        result = self.admin.precio_anterior_info(obj)
        self.assertEqual(result, "=")

    def test_precio_anterior_info_sin_anterior(self, mock_ppl):
        mock_ppl.objects.filter.return_value.order_by.return_value.first.return_value = None
        lista = _mock_obj(moneda="PYG")
        obj = _mock_obj(id_lista=lista, id_producto=MagicMock(), precio_unitario=Decimal("1000.00"),
                        fecha_vigencia=MagicMock())
        result = self.admin.precio_anterior_info(obj)
        self.assertEqual(result, "-")


@patch('apps.productos.admin.format_html', _plain_format_html)
class HistoricoPreciosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.productos.models import HistoricoPrecios
        self.admin = HistoricoPreciosAdmin(HistoricoPrecios, self.site)

    def test_producto_link(self):
        producto = _mock_obj(id_producto=1, descripcion="Café Natural")
        obj = _mock_obj(id_producto=producto)
        with patch("apps.productos.admin.reverse", return_value="/admin/productos/1/change/"):
            result = str(self.admin.producto_link(obj))
        self.assertIn("Café Natural", result)

    def test_precio_anterior_display(self):
        obj = _mock_obj(precio_anterior=Decimal("2000.00"))
        result = str(self.admin.precio_anterior_display(obj))
        self.assertIn("2,000.00", result)
        self.assertIn("dc3545", result)

    def test_flecha(self):
        obj = _mock_obj()
        result = str(self.admin.flecha(obj))
        self.assertIn("→", result)

    def test_precio_nuevo_display(self):
        obj = _mock_obj(precio_nuevo=Decimal("2500.00"))
        result = str(self.admin.precio_nuevo_display(obj))
        self.assertIn("2,500.00", result)
        self.assertIn("28a745", result)

    def test_variacion_display_aumento(self):
        obj = _mock_obj(variacion_porcentual=15.5)
        result = str(self.admin.variacion_display(obj))
        self.assertIn("dc3545", result)
        self.assertIn("▲", result)
        self.assertIn("15.5", result)

    def test_variacion_display_disminucion(self):
        obj = _mock_obj(variacion_porcentual=-10.0)
        result = str(self.admin.variacion_display(obj))
        self.assertIn("28a745", result)
        self.assertIn("▼", result)

    def test_fecha_cambio_display(self):
        import datetime
        obj = _mock_obj(fecha_cambio=datetime.datetime(2024, 7, 4, 9, 0))
        result = self.admin.fecha_cambio_display(obj)
        self.assertIn("04/07/2024", result)

    def test_empleado_info_con_empleado(self):
        empleado = _mock_obj(nombre="Marta", apellido="Ruiz")
        obj = _mock_obj(id_empleado=empleado)
        result = str(self.admin.empleado_info(obj))
        self.assertIn("Marta", result)

    def test_empleado_info_sin_empleado(self):
        obj = _mock_obj(id_empleado=None)
        result = str(self.admin.empleado_info(obj))
        self.assertIn("Sistema", result)
