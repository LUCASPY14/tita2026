"""
Tests para ventas/services.py (PromocionService y DevolucionService)
Cubre métodos privados y ramas no cubiertas
"""

from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase
from django.utils import timezone


class PromocionServiceValidarHorarioTest(TestCase):
    """Tests para _validar_horario"""

    def _make_promo(self, hora_inicio=None, hora_fin=None):
        promo = Mock()
        promo.hora_inicio = hora_inicio
        promo.hora_fin = hora_fin
        return promo

    def test_sin_restriccion_horaria(self):
        """Sin hora_inicio ni hora_fin debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(None, None)
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertTrue(PromocionService._validar_horario(promo, fecha_hora))

    def test_hora_antes_de_inicio(self):
        """Hora actual antes de hora_inicio debe retornar False"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(hora_inicio=time(14, 0), hora_fin=None)
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertFalse(PromocionService._validar_horario(promo, fecha_hora))

    def test_hora_despues_de_fin(self):
        """Hora actual después de hora_fin debe retornar False"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(hora_inicio=None, hora_fin=time(11, 0))
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertFalse(PromocionService._validar_horario(promo, fecha_hora))

    def test_hora_dentro_del_rango(self):
        """Hora dentro del rango debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(hora_inicio=time(10, 0), hora_fin=time(14, 0))
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertTrue(PromocionService._validar_horario(promo, fecha_hora))

    def test_solo_hora_inicio_dentro(self):
        """Con solo hora_inicio y hora actual >= debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(hora_inicio=time(10, 0), hora_fin=None)
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertTrue(PromocionService._validar_horario(promo, fecha_hora))

    def test_solo_hora_fin_dentro(self):
        """Con solo hora_fin y hora actual <= debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(hora_inicio=None, hora_fin=time(14, 0))
        fecha_hora = datetime(2024, 6, 15, 12, 0, 0)
        self.assertTrue(PromocionService._validar_horario(promo, fecha_hora))


class PromocionServiceValidarDiaSemanaTest(TestCase):
    """Tests para _validar_dia_semana"""

    def _make_promo(self, dias_semana):
        promo = Mock()
        promo.dias_semana = dias_semana
        return promo

    def test_sin_restriccion_de_dias(self):
        """dias_semana vacío/None debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo(None)
        fecha_hora = datetime(2024, 6, 17, 12, 0, 0)  # Monday=1
        self.assertTrue(PromocionService._validar_dia_semana(promo, fecha_hora))

    def test_dia_en_lista(self):
        """Día actual en dis_semana debe retornar True"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo([1, 2, 3])  # lunes, martes, miercoles
        fecha_hora = datetime(2024, 6, 17, 12, 0, 0)  # Monday=1
        self.assertTrue(PromocionService._validar_dia_semana(promo, fecha_hora))

    def test_dia_no_en_lista(self):
        """Día actual no en dias_semana debe retornar False"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo([6, 7])  # sábado y domingo
        fecha_hora = datetime(2024, 6, 17, 12, 0, 0)  # Monday=1
        self.assertFalse(PromocionService._validar_dia_semana(promo, fecha_hora))


class PromocionServiceCalcularDescuentoTest(TestCase):
    """Tests para calcular_descuento - todas las ramas"""

    def _make_promo(self, tipo, valor_descuento, aplica_a="total"):
        promo = Mock()
        promo.tipo_promocion = tipo
        promo.valor_descuento = valor_descuento
        promo.aplica_a = aplica_a
        return promo

    def test_descuento_porcentaje(self):
        """Tipo porcentaje debe calcular % del monto total"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo("porcentaje", Decimal("10"), "total")
        items = [{"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("100.00")}]
        monto = Decimal("100.00")

        result = PromocionService.calcular_descuento(promo, items, monto)
        self.assertEqual(result["tipo_descuento"], "porcentaje")
        self.assertEqual(result["monto_descuento"], Decimal("10.00"))
        self.assertIn("descripcion", result)

    def test_descuento_monto_fijo(self):
        """Tipo monto_fijo debe retornar valor fijo"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo("monto_fijo", Decimal("5000"))
        items = []
        monto = Decimal("50000.00")

        result = PromocionService.calcular_descuento(promo, items, monto)
        self.assertEqual(result["tipo_descuento"], "monto_fijo")
        self.assertEqual(result["monto_descuento"], Decimal("5000"))

    def test_descuento_2x1(self):
        """Tipo 2x1 debe llamar a _calcular_2x1"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo("2x1", Decimal("0"), "total")
        items = [{"id_producto": 1, "cantidad": Decimal("2"), "precio": Decimal("10.00")}]
        monto = Decimal("20.00")

        result = PromocionService.calcular_descuento(promo, items, monto)
        self.assertEqual(result["tipo_descuento"], "2x1")
        self.assertGreaterEqual(result["monto_descuento"], Decimal("0"))

    def test_descuento_combo(self):
        """Tipo combo debe llamar a _calcular_combo"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo("combo", Decimal("2000"), "total")
        items = [{"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("5000.00")}]
        monto = Decimal("5000.00")

        with patch("apps.ventas.models.ProductosPromocion") as mock_pp:
            mock_pp.objects.filter.return_value.values_list.return_value = []
            result = PromocionService.calcular_descuento(promo, items, monto)
            self.assertEqual(result["tipo_descuento"], "combo")

    def test_descuento_tipo_desconocido(self):
        """Tipo desconocido debe retornar monto 0"""
        from apps.ventas.services import PromocionService

        promo = self._make_promo("descuento_especial", Decimal("0"))
        items = []
        monto = Decimal("100.00")

        result = PromocionService.calcular_descuento(promo, items, monto)
        self.assertEqual(result["monto_descuento"], Decimal("0.00"))
        self.assertEqual(result["tipo_descuento"], "ninguno")


class PromocionServiceCalcular2x1Test(TestCase):
    """Tests para _calcular_2x1"""

    def test_2x1_aplica_a_total(self):
        """2x1 con aplica_a=total debe calcular correctamente"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "total"
        items = [{"id_producto": 1, "cantidad": Decimal("4"), "precio": Decimal("10.00")}]

        # Aplica_a=total: _obtener_productos_afectados retorna todos
        result = PromocionService._calcular_2x1(promo, items)
        # 4 unidades → 2 gratis → 2 * 10 = 20
        self.assertEqual(result, Decimal("20.00"))

    def test_2x1_cantidad_impar(self):
        """3 unidades → 1 gratis"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "total"
        items = [{"id_producto": 2, "cantidad": Decimal("3"), "precio": Decimal("15.00")}]

        result = PromocionService._calcular_2x1(promo, items)
        # 3 // 2 = 1 gratis → 1 * 15 = 15
        self.assertEqual(result, Decimal("15.00"))


class PromocionServiceCalcularComboTest(TestCase):
    """Tests para _calcular_combo"""

    def test_combo_sin_productos_definidos(self):
        """Sin productos en combo, retorna valor_descuento directamente"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.valor_descuento = Decimal("3000")
        items = [{"id_producto": 1, "cantidad": Decimal("2"), "precio": Decimal("10.00")}]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = []
            result = PromocionService._calcular_combo(promo, items)
            self.assertEqual(result, Decimal("3000"))

    def test_combo_productos_incompletos(self):
        """Faltan productos del combo en el carrito → 0"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.valor_descuento = Decimal("3000")
        # Combo requires products 1 AND 2, but cart only has product 1
        items = [{"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("10.00")}]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = [1, 2]
            result = PromocionService._calcular_combo(promo, items)
            self.assertEqual(result, Decimal("0.00"))

    def test_combo_completo(self):
        """Todos los productos del combo presentes → descuento * repeticiones"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.valor_descuento = Decimal("1000")
        items = [
            {"id_producto": 1, "cantidad": Decimal("2"), "precio": Decimal("5000")},
            {"id_producto": 2, "cantidad": Decimal("3"), "precio": Decimal("2000")},
        ]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = [1, 2]
            result = PromocionService._calcular_combo(promo, items)
            # min(2, 3) = 2 combos → 2 * 1000 = 2000
            self.assertEqual(result, Decimal("2000"))


class PromocionServiceValidarAlcanceTest(TestCase):
    """Tests para _validar_alcance"""

    def test_aplica_a_total(self):
        """aplica_a='total' siempre True"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "total"
        self.assertTrue(PromocionService._validar_alcance(promo, []))

    def test_aplica_a_producto_con_interseccion(self):
        """aplica_a='producto' con produtos en la promición → True"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "producto"
        items = [{"id_producto": 5, "cantidad": Decimal("1"), "precio": Decimal("10")}]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = [5, 6]
            result = PromocionService._validar_alcance(promo, items)
            self.assertTrue(result)

    def test_aplica_a_producto_sin_interseccion(self):
        """aplica_a='producto' sin intersección con items → False"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "producto"
        items = [{"id_producto": 99, "cantidad": Decimal("1"), "precio": Decimal("10")}]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = [1, 2]
            result = PromocionService._validar_alcance(promo, items)
            self.assertFalse(result)

    def test_aplica_a_categoria_con_match(self):
        """aplica_a='categoria' con producto en categoría → True"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "categoria"
        items = [{"id_producto": 7, "cantidad": Decimal("1"), "precio": Decimal("10")}]

        producto_mock = Mock()
        producto_mock.id_categoria_id = 3

        with patch("apps.ventas.models.CategoriasPromocion.objects") as mock_obj_cp:
            mock_obj_cp.filter.return_value.values_list.return_value = [3, 4]
            with patch("apps.productos.models.Productos.objects") as mock_obj_prod:
                mock_obj_prod.get.return_value = producto_mock
                result = PromocionService._validar_alcance(promo, items)
                self.assertTrue(result)

    def test_aplica_a_categoria_sin_match(self):
        """aplica_a='categoria' sin categoría en promo → False"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "categoria"
        items = [{"id_producto": 7, "cantidad": Decimal("1"), "precio": Decimal("10")}]

        producto_mock = Mock()
        producto_mock.id_categoria_id = 99  # Not in promo categories

        with patch("apps.ventas.models.CategoriasPromocion.objects") as mock_obj_cp:
            mock_obj_cp.filter.return_value.values_list.return_value = [3, 4]
            with patch("apps.productos.models.Productos.objects") as mock_obj_prod:
                mock_obj_prod.get.return_value = producto_mock
                result = PromocionService._validar_alcance(promo, items)
                self.assertFalse(result)

    def test_aplica_a_desconocido(self):
        """aplica_a desconocido → False"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "desconocido"
        result = PromocionService._validar_alcance(promo, [])
        self.assertFalse(result)


class PromocionServiceObtenerProductosAfectadosTest(TestCase):
    """Tests para _obtener_productos_afectados"""

    def test_aplica_a_total(self):
        """aplica_a='total' retorna todos los items"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "total"
        items = [
            {"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("10")},
            {"id_producto": 2, "cantidad": Decimal("2"), "precio": Decimal("20")},
        ]
        result = PromocionService._obtener_productos_afectados(promo, items)
        self.assertEqual(result, [1, 2])

    def test_aplica_a_producto_filtrado(self):
        """aplica_a='producto' retorna solo los que están en la promo"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "producto"
        items = [
            {"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("10")},
            {"id_producto": 2, "cantidad": Decimal("2"), "precio": Decimal("20")},
        ]

        with patch("apps.ventas.models.ProductosPromocion.objects") as mock_objs:
            mock_objs.filter.return_value.values_list.return_value = [2]
            result = PromocionService._obtener_productos_afectados(promo, items)
            self.assertEqual(result, [2])

    def test_aplica_a_categoria_filtrado(self):
        """aplica_a='categoria' retorna productos de la categoría"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "categoria"
        items = [
            {"id_producto": 1, "cantidad": Decimal("1"), "precio": Decimal("10")},
            {"id_producto": 2, "cantidad": Decimal("1"), "precio": Decimal("20")},
        ]

        prod1 = Mock()
        prod1.id_categoria_id = 5
        prod2 = Mock()
        prod2.id_categoria_id = 99  # not in promo

        with patch("apps.ventas.models.CategoriasPromocion.objects") as mock_obj_cp:
            mock_obj_cp.filter.return_value.values_list.return_value = [5]
            with patch("apps.productos.models.Productos.objects") as mock_obj_prod:
                mock_obj_prod.get.side_effect = lambda **kw: (
                    {1: prod1, 2: prod2}[kw["id_produto"]] if "id_produto" in kw else [prod1, prod2][0]
                )
                # Use side_effect that returns based on call args
                mock_obj_prod.get.side_effect = None
                mock_obj_prod.get.return_value = prod1  # returns prod1 for id 1
                # Since we have 2 items, need to return different prods
                mock_obj_prod.get.side_effect = [prod1, prod2]
                result = PromocionService._obtener_productos_afectados(promo, items)
                self.assertEqual(result, [1])

    def test_aplica_a_desconocido(self):
        """aplica_a desconocido retorna lista vacía"""
        from apps.ventas.services import PromocionService

        promo = Mock()
        promo.aplica_a = "special"
        result = PromocionService._obtener_productos_afectados(promo, [])
        self.assertEqual(result, [])


class DevolucionServiceValidarProductosTest(TestCase):
    """Tests para validar_productos_devolucion"""

    def test_venta_no_existe(self):
        """Venta inexistente → {valido: False, errores: [...]}"""
        from apps.ventas.models import Ventas
        from apps.ventas.services import DevolucionService

        with patch("apps.ventas.models.Ventas.objects.get", side_effect=Ventas.DoesNotExist()):
            result = DevolucionService.validar_productos_devolucion(999, [{"id_producto": 1, "cantidad": "1"}])
            self.assertFalse(result["valido"])
            self.assertTrue(len(result["errores"]) > 0)

    def test_producto_no_en_venta(self):
        """Producto no en venta → error"""
        from apps.ventas.services import DevolucionService

        venta_mock = Mock()
        venta_mock.fecha = timezone.now()

        with patch("apps.ventas.models.Ventas.objects.get", return_value=venta_mock):
            with patch("apps.ventas.models.DetallesVenta.objects.filter", return_value=[]):
                result = DevolucionService.validar_productos_devolucion(1, [{"id_producto": 5, "cantidad": "1"}])
                self.assertFalse(result["valido"])
                self.assertTrue(any("5" in e for e in result["errores"]))

    def test_cantidad_excede_comprada(self):
        """Cantidad a devolver > comprada → error"""
        from apps.ventas.services import DevolucionService

        venta_mock = Mock()
        venta_mock.fecha = timezone.now()

        detalle_mock = Mock()
        detalle_mock.id_producto_id = 1
        detalle_mock.cantidad = Decimal("2")

        with patch("apps.ventas.models.Ventas.objects.get", return_value=venta_mock):
            with patch("apps.ventas.models.DetallesVenta.objects.filter", return_value=[detalle_mock]):
                result = DevolucionService.validar_productos_devolucion(1, [{"id_producto": 1, "cantidad": "5"}])
                self.assertFalse(result["valido"])

    def test_validacion_exitosa_dentro_plazo(self):
        """Productos válidos dentro del plazo → {valido: True, errores: []}"""
        from apps.ventas.services import DevolucionService

        venta_mock = Mock()
        venta_mock.fecha = timezone.now()

        detalle_mock = Mock()
        detalle_mock.id_producto_id = 1
        detalle_mock.cantidad = Decimal("3")

        with patch("apps.ventas.models.Ventas.objects.get", return_value=venta_mock):
            with patch("apps.ventas.models.DetallesVenta.objects.filter", return_value=[detalle_mock]):
                result = DevolucionService.validar_productos_devolucion(1, [{"id_producto": 1, "cantidad": "2"}])
                self.assertTrue(result["valido"])
                self.assertEqual(result["errores"], [])

    def test_fuera_de_plazo_genera_warning(self):
        """Venta antigua → warnings pero puede ser válida"""
        from datetime import timedelta

        from apps.ventas.services import DevolucionService

        fecha_antigua = timezone.now() - timedelta(days=10)
        venta_mock = Mock()
        venta_mock.fecha = fecha_antigua

        detalle_mock = Mock()
        detalle_mock.id_producto_id = 1
        detalle_mock.cantidad = Decimal("3")

        with patch("apps.ventas.models.Ventas.objects.get", return_value=venta_mock):
            with patch("apps.ventas.models.DetallesVenta.objects.filter", return_value=[detalle_mock]):
                result = DevolucionService.validar_productos_devolucion(1, [{"id_producto": 1, "cantidad": "1"}])
                self.assertTrue(len(result["warnings"]) > 0)
