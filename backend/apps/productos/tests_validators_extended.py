"""
Extended tests for apps/productos/validators.py covering previously missing lines.

Missing lines targeted: 127, 131-132, 167, 171-172, 206-221, 245, 250-251, 254,
299, 311, 343, 404, 421, 434-438, 467, 508, 513, 541, 577, 594, 619, 662, 673,
692-701, 744-752, 778, 783-784, 787, 832, 837-838, 875
"""
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.productos.validators import (
    validar_stock_minimo,
    validar_precio_positivo,
    validar_cambio_estado_producto,
    validar_margen_utilidad,
    validar_nombre_categoria,
    validar_jerarquia_categoria,
    validar_categoria_activa_con_productos,
    validar_nombre_unidad,
    validar_abreviatura_unidad,
    validar_unidad_activa_con_productos,
    validar_nombre_lista_precios,
    validar_fecha_vigencia_lista,
    validar_lista_activa_con_precios,
    validar_unicidad_precio_lista,
    validar_moneda_lista,
    validar_variacion_precio,
    validar_cambio_precio_historico,
    validar_fecha_cambio_precio,
    validar_producto_unico,
)


def _mock_product(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# ==============================================================================
# validar_stock_minimo
# ==============================================================================


class ValidarStockMinimoExtendedTest(TestCase):
    """Lines 127, 131-132."""

    def test_stock_minimo_none(self):
        """Line 127: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_stock_minimo(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_stock_minimo_valido(self):
        """Valid stock passes."""
        validar_stock_minimo(Decimal("10.000"))  # Should not raise


# ==============================================================================
# validar_precio_positivo
# ==============================================================================


class ValidarPrecioPositivoExtendedTest(TestCase):
    """Lines 167, 171-172."""

    def test_precio_none(self):
        """Line 167: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_positivo(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_precio_valido(self):
        """Valid price passes."""
        validar_precio_positivo(Decimal("5000.00"))  # Should not raise


# ==============================================================================
# validar_cambio_estado_producto
# ==============================================================================


class ValidarCambioEstadoProductoExtendedTest(TestCase):
    """Lines 206-221: various branches."""

    def test_producto_invalido(self):
        """Line 206-207: product without id_producto raises."""
        obj = object()  # No 'id_producto' attribute
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_estado_producto(obj, False)
        self.assertIn("inválido", str(ctx.exception).lower())

    def test_desactivar_con_stock_sin_permitir_negativo(self):
        """Lines 210-218: deactivating product with stock > 0 and no negative allowed raises."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.estado = True
        producto.stock_actual = 10
        producto.permite_stock_negativo = False
        producto.descripcion = "Arroz"
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_estado_producto(producto, False)
        self.assertIn("stock", str(ctx.exception).lower())

    def test_desactivar_con_stock_permite_negativo(self):
        """Lines 210-218: deactivating with stock but negativo allowed — no error."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.estado = True
        producto.stock_actual = 10
        producto.permite_stock_negativo = True
        result = validar_cambio_estado_producto(producto, False)
        self.assertTrue(result)

    def test_activar_producto(self):
        """Line 221: activating a product returns True."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.estado = False
        result = validar_cambio_estado_producto(producto, True)
        self.assertTrue(result)

    def test_desactivar_sin_stock(self):
        """Deactivating product without stock works."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.estado = True
        producto.stock_actual = 0
        result = validar_cambio_estado_producto(producto, False)
        self.assertTrue(result)


# ==============================================================================
# validar_margen_utilidad
# ==============================================================================


class ValidarMargenUtilidadExtendedTest(TestCase):
    """Lines 245, 250-251, 254."""

    def test_precio_none_returns(self):
        """Line 245: None returns without error."""
        validar_margen_utilidad(None, Decimal("3000"))  # Should not raise

    def test_costo_none_returns(self):
        """Line 245: None cost returns without error."""
        validar_margen_utilidad(Decimal("5000"), None)  # Should not raise

    def test_costo_cero_returns(self):
        """Line 254: costo == 0 returns without error."""
        validar_margen_utilidad(Decimal("5000"), Decimal("0"))  # Should not raise

    def test_margen_valido(self):
        """Valid margin passes."""
        validar_margen_utilidad(Decimal("5000"), Decimal("3000"))  # 67% margin


# ==============================================================================
# validar_nombre_categoria
# ==============================================================================


class ValidarNombreCategoriaExtendedTest(TestCase):
    """Line 343."""

    def test_nombre_none(self):
        """Line 343: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nombre_categoria(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_nombre_vacio(self):
        """Empty string raises ValidationError."""
        with self.assertRaises(ValidationError):
            validar_nombre_categoria("")

    def test_nombre_valido(self):
        """Valid category name passes."""
        validar_nombre_categoria("Bebidas")  # Should not raise


# ==============================================================================
# validar_nombre_unidad
# ==============================================================================


class ValidarNombreUnidadExtendedTest(TestCase):
    """Line 467."""

    def test_nombre_none(self):
        """Line 467: None raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nombre_unidad(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_nombre_valido(self):
        """Valid unit name passes."""
        validar_nombre_unidad("Kilogramos")


# ==============================================================================
# validar_abreviatura_unidad
# ==============================================================================


class ValidarAbreviaturaUnidadExtendedTest(TestCase):
    """Lines 508, 513."""

    def test_abreviatura_none(self):
        """Line 508: None raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_abreviatura_unidad(None)
        self.assertIn("obligatoria", str(ctx.exception).lower())

    def test_abreviatura_vacia_raises(self):
        """Line 513: empty string after strip raises (< 1 char)."""
        with self.assertRaises(ValidationError) as ctx:
            validar_abreviatura_unidad("   ")  # strips to empty
        self.assertIn("1 carác", str(ctx.exception))

    def test_abreviatura_valida(self):
        """Valid abbreviation passes."""
        validar_abreviatura_unidad("kg")


# ==============================================================================
# validar_nombre_lista_precios
# ==============================================================================


class ValidarNombreListaPreciosExtendedTest(TestCase):
    """Lines 577, 594."""

    def test_nombre_none(self):
        """Line 577: None raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nombre_lista_precios(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_nombre_valido(self):
        """Valid list name passes."""
        validar_nombre_lista_precios("Lista Mayorista 2024")


# ==============================================================================
# validar_moneda_lista
# ==============================================================================


class ValidarMonedaListaExtendedTest(TestCase):
    """Lines 662, 673."""

    def test_moneda_none(self):
        """Line 662: None raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_moneda_lista(None)
        self.assertIn("obligatorio", str(ctx.exception).lower())

    def test_moneda_invalida_con_numeros(self):
        """Line 673: moneda with digits raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_moneda_lista("US1")
        self.assertIn("letras", str(ctx.exception).lower())

    def test_moneda_valida(self):
        """Valid currency code passes."""
        validar_moneda_lista("PYG")
        validar_moneda_lista("USD")


# ==============================================================================
# validar_variacion_precio
# ==============================================================================


class ValidarVariacionPrecioExtendedTest(TestCase):
    """Lines 778, 783-784, 787."""

    def test_precio_anterior_none_returns(self):
        """Line 778: None precio_anterior returns without error."""
        validar_variacion_precio(Decimal("5000"), None)  # Should not raise

    def test_precio_valido(self):
        """Valid pricing variation passes."""
        validar_variacion_precio(Decimal("5000"), Decimal("4500"))  # 11% increase -- OK

    def test_precio_nuevo_none_returns(self):
        """Line 778: None precio_nuevo returns without error."""
        validar_variacion_precio(None, Decimal("4500"))  # Should not raise


# ==============================================================================
# validar_cambio_precio_historico
# ==============================================================================


class ValidarCambioPrecioHistoricoExtendedTest(TestCase):
    """Lines 832, 837-838."""

    def test_precio_anterior_none(self):
        """Line 832: None raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_precio_historico(None, Decimal("5000"))
        self.assertIn("obligatorios", str(ctx.exception).lower())

    def test_precio_nuevo_none(self):
        """Line 832: None precio_nuevo raises."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_precio_historico(Decimal("4000"), None)
        self.assertIn("obligatorios", str(ctx.exception).lower())

    def test_precios_validos(self):
        """Valid prices pass."""
        validar_cambio_precio_historico(Decimal("4000"), Decimal("5000"))  # Should not raise


# ==============================================================================
# validar_fecha_cambio_precio
# ==============================================================================


class ValidarFechaCambioPrecioExtendedTest(TestCase):
    """Line 875: None returns early."""

    def test_fecha_none_returns(self):
        """Line 875: None returns without error."""
        validar_fecha_cambio_precio(None)  # Should not raise

    def test_fecha_valida(self):
        """Valid datetime passes."""
        from datetime import datetime
        validar_fecha_cambio_precio(datetime.now())  # Should not raise


# ==============================================================================
# Lines 131-132: except (ValueError, TypeError) in validar_stock_minimo
# ==============================================================================

class ValidarStockMinimoDecimalErrorTest(TestCase):
    """Cover the except (ValueError, TypeError) block (lines 131-132)."""

    @patch("apps.productos.validators.Decimal", side_effect=ValueError("bad"))
    def test_stock_decimal_value_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_stock_minimo("not-a-number")
        self.assertIn("número", str(ctx.exception).lower())

    @patch("apps.productos.validators.Decimal", side_effect=TypeError("bad"))
    def test_stock_decimal_type_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_stock_minimo(object())
        self.assertIn("número", str(ctx.exception).lower())


# ==============================================================================
# Lines 171-172: except (ValueError, TypeError) in validar_precio_positivo
# ==============================================================================

class ValidarPrecioPositivoDecimalErrorTest(TestCase):
    """Cover the except (ValueError, TypeError) block (lines 171-172)."""

    @patch("apps.productos.validators.Decimal", side_effect=ValueError("bad"))
    def test_precio_decimal_value_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_positivo("not-a-number")
        self.assertIn("número", str(ctx.exception).lower())

    @patch("apps.productos.validators.Decimal", side_effect=TypeError("bad"))
    def test_precio_decimal_type_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_precio_positivo(object())
        self.assertIn("número", str(ctx.exception).lower())


# ==============================================================================
# Lines 250-251: except (ValueError, TypeError) in validar_margen_utilidad
# ==============================================================================

class ValidarMargenUtilidadDecimalErrorTest(TestCase):
    """Cover the except (ValueError, TypeError) block (lines 250-251)."""

    @patch("apps.productos.validators.Decimal", side_effect=ValueError("bad"))
    def test_margen_decimal_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_margen_utilidad("bad", "bad")
        self.assertIn("número", str(ctx.exception).lower())

    @patch("apps.productos.validators.Decimal", side_effect=TypeError("bad"))
    def test_margen_decimal_type_error(self, _mock):
        with self.assertRaises(ValidationError) as ctx:
            validar_margen_utilidad(object(), object())
        self.assertIn("número", str(ctx.exception).lower())


# ==============================================================================
# Lines 299, 308->exit, 311: validar_producto_unico with producto_id
# ==============================================================================

class ValidarProductoUnicoMockedTest(TestCase):
    """Cover branches in validar_producto_unico that require producto_id."""

    @patch("apps.productos.models.Productos")
    def test_con_producto_id_sin_codigo_barra(self, MockProductos):
        """Lines 299, 308->exit: producto_id given, codigo_barra=None, no duplicates."""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exclude.return_value = qs
        qs.exists.return_value = False
        MockProductos.objects.filter.return_value = qs

        validar_producto_unico("Producto Nuevo", codigo_barra=None, producto_id=5)
        qs.exclude.assert_called_once_with(id_producto=5)

    @patch("apps.productos.models.Productos")
    def test_con_producto_id_y_codigo_barra(self, MockProductos):
        """Line 311: producto_id + codigo_barra, both excluded, no duplicates."""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exclude.return_value = qs
        qs.exists.return_value = False
        MockProductos.objects.filter.return_value = qs

        validar_producto_unico("Producto Nuevo", codigo_barra="CODE123", producto_id=5)
        # exclude is called twice: once for descripcion, once for codigo_barra
        self.assertEqual(qs.exclude.call_count, 2)


# ==============================================================================
# Line 404: MAX_DEPTH exceeded in validar_jerarquia_categoria
# ==============================================================================

class ValidarJerarquiaCategoriaMaxDepthTest(TestCase):
    """Cover line 404: depth >= MAX_DEPTH raises ValidationError."""

    def test_jerarquia_demasiado_profunda(self):
        """Build a chain of 12 mock categories to exceed MAX_DEPTH=10."""
        cats = [MagicMock() for _ in range(12)]
        for i, cat in enumerate(cats):
            cat.id_categoria = 1000 + i
        for i in range(len(cats) - 1):
            cats[i].id_categoria_padre = cats[i + 1]
        cats[-1].id_categoria_padre = None

        with self.assertRaises(ValidationError) as ctx:
            validar_jerarquia_categoria(cats[0], categoria_actual_id=999)
        self.assertIn("profunda", str(ctx.exception).lower())


# ==============================================================================
# Line 421: validar_categoria_activa_con_productos — invalid object
# Lines 434-438: subcategorias activas branch
# ==============================================================================

class ValidarCategoriaActivaConProductosExtendedTest(TestCase):

    def test_categoria_invalida_sin_id(self):
        """Line 421: object without id_categoria raises ValidationError."""
        obj = object()
        with self.assertRaises(ValidationError) as ctx:
            validar_categoria_activa_con_productos(obj)
        self.assertIn("inválida", str(ctx.exception).lower())

    def test_con_subcategorias_activas(self):
        """Lines 434-438: category with 0 products but active subcategories raises."""
        categoria = MagicMock()
        categoria.id_categoria = 1
        categoria.nombre = "Bebidas"
        categoria.productos.filter.return_value.count.return_value = 0
        categoria.subcategorias.filter.return_value.count.return_value = 3

        with self.assertRaises(ValidationError) as ctx:
            validar_categoria_activa_con_productos(categoria)
        self.assertIn("subcategoría", str(ctx.exception).lower())

    def test_categoria_sin_subcategorias_attr(self):
        """434->exit: spec limits object to no 'subcategorias' attr — skips that check."""
        categoria = MagicMock(spec=["id_categoria", "nombre", "productos"])
        categoria.id_categoria = 1
        categoria.nombre = "Test"
        categoria.productos.filter.return_value.count.return_value = 0
        # hasattr(categoria, "subcategorias") → False → no error raised
        validar_categoria_activa_con_productos(categoria)

    def test_categoria_con_subcategorias_inactivas(self):
        """437->exit: subcategorias presente pero count=0 → no error."""
        categoria = MagicMock()
        categoria.id_categoria = 1
        categoria.nombre = "Test"
        categoria.productos.filter.return_value.count.return_value = 0
        categoria.subcategorias.filter.return_value.count.return_value = 0
        validar_categoria_activa_con_productos(categoria)


# ==============================================================================
# Remaining branch gaps: 546->exit, 698->exit, 748->751, 837-838
# ==============================================================================

class ValidarUnidadActivaSinProductosTest(TestCase):
    """546->exit: unidad with 0 active products — function completes without raising."""

    def test_unidad_sin_productos_activos(self):
        unidad = MagicMock()
        unidad.id_unidad_medida = 1
        unidad.nombre = "Kilogramo"
        unidad.productos.filter.return_value.count.return_value = 0
        validar_unidad_activa_con_productos(unidad)  # Should not raise


class ValidarListaActivaSinPreciosTest(TestCase):
    """698->exit: lista with 0 precios — function completes without warning."""

    def test_lista_sin_precios(self):
        lista = MagicMock()
        lista.id_lista = 1
        lista.nombre_lista = "Lista Vacía"
        lista.precios.count.return_value = 0
        validar_lista_activa_con_precios(lista)  # Should not raise


class ValidarUnicidadPrecioSinIdPrecioTest(TestCase):
    """748->751: call without id_precio, exists=True → raises ValidationError."""

    @patch("apps.productos.models.PreciosPorLista")
    def test_sin_id_precio_duplicado_raises(self, MockPPL):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exists.return_value = True
        MockPPL.objects.filter.return_value = qs

        with self.assertRaises(ValidationError) as ctx:
            validar_unicidad_precio_lista(1, 1)
        self.assertIn("precio", str(ctx.exception).lower())


class ValidarCambioPrecioHistoricoPequenioExplicitTest(TestCase):
    """837-838: except (ValueError, TypeError) in validar_cambio_precio_historico."""

    @patch("apps.productos.validators.Decimal", side_effect=ValueError("bad"))
    def test_decimal_value_error(self, _mock):
        """Lines 837-838: Decimal raises ValueError → ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_precio_historico("bad", "bad")
        self.assertIn("número", str(ctx.exception).lower())

    @patch("apps.productos.validators.Decimal", side_effect=TypeError("bad"))
    def test_decimal_type_error(self, _mock):
        """Lines 837-838: Decimal raises TypeError → ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_cambio_precio_historico(object(), object())
        self.assertIn("número", str(ctx.exception).lower())

    def test_diferencia_pequenia_emite_warning(self):
        """warnings.warn is called when diferencia < 1.00 guaraní."""
        with patch("warnings.warn") as mock_warn:
            validar_cambio_precio_historico(Decimal("1000.00"), Decimal("1000.50"))
        mock_warn.assert_called_once()


# ==============================================================================
# Line 541: validar_unidad_activa_con_productos — invalid object
# Line 546->exit: with active products raises
# ==============================================================================

class ValidarUnidadActivaConProductosExtendedTest(TestCase):

    def test_unidad_invalida_sin_id(self):
        """Line 541: object without id_unidad_medida raises ValidationError."""
        obj = object()
        with self.assertRaises(ValidationError) as ctx:
            validar_unidad_activa_con_productos(obj)
        self.assertIn("inválida", str(ctx.exception).lower())

    def test_unidad_con_productos_activos(self):
        """Line 546->exit: unidad with active products raises."""
        unidad = MagicMock()
        unidad.id_unidad_medida = 1
        unidad.nombre = "Kilogramo"
        unidad.productos.filter.return_value.count.return_value = 5

        with self.assertRaises(ValidationError) as ctx:
            validar_unidad_activa_con_productos(unidad)
        self.assertIn("estado", str(ctx.exception).lower())


# ==============================================================================
# Line 594: invalid chars in validar_nombre_lista_precios
# ==============================================================================

class ValidarNombreListaPreciosInvalidCharTest(TestCase):

    def test_nombre_con_caracter_invalido(self):
        """Line 594: name with @ raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_nombre_lista_precios("Lista@Especial#99")
        self.assertIn("letras", str(ctx.exception).lower())


# ==============================================================================
# Line 619: validar_fecha_vigencia_lista(None) returns early
# ==============================================================================

class ValidarFechaVigenciaListaNoneTest(TestCase):

    def test_fecha_none_retorna_sin_error(self):
        """Line 619: None fecha_vigencia returns immediately."""
        result = validar_fecha_vigencia_lista(None)
        self.assertIsNone(result)


# ==============================================================================
# Lines 692-701: validar_lista_activa_con_precios with precios_count > 0
# ==============================================================================

class ValidarListaActivaConPreciosExtendedTest(TestCase):

    def test_lista_invalida_sin_id(self):
        """No id_lista → raises ValidationError."""
        obj = object()
        with self.assertRaises(ValidationError):
            validar_lista_activa_con_precios(obj)

    def test_lista_con_precios_emite_warning(self):
        """Lines 692-701: lista with precios > 0 emits UserWarning."""
        import warnings as _warnings
        lista = MagicMock()
        lista.id_lista = 1
        lista.nombre_lista = "Lista Mayorista"
        lista.precios.count.return_value = 5

        with _warnings.catch_warnings(record=True) as w:
            _warnings.simplefilter("always")
            validar_lista_activa_con_precios(lista)

        self.assertEqual(len(w), 1)
        self.assertIn("precio", str(w[0].message).lower())


# ==============================================================================
# Lines 744-752: validar_unicidad_precio_lista — with id_precio + duplicate
# ==============================================================================

class ValidarUnicidadPrecioListaExtendedTest(TestCase):

    @patch("apps.productos.models.PreciosPorLista")
    def test_con_id_precio_excluye_y_no_duplicado(self, MockPPL):
        """Lines 744-752: id_precio given → exclude called; exists=False → no error."""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exclude.return_value = qs
        qs.exists.return_value = False
        MockPPL.objects.filter.return_value = qs

        validar_unicidad_precio_lista(1, 1, id_precio=5)
        qs.exclude.assert_called_once_with(id_precio=5)

    @patch("apps.productos.models.PreciosPorLista")
    def test_con_duplicado_raises(self, MockPPL):
        """Lines 744-752: duplicate combination raises ValidationError."""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.exclude.return_value = qs
        qs.exists.return_value = True
        MockPPL.objects.filter.return_value = qs

        with self.assertRaises(ValidationError) as ctx:
            validar_unicidad_precio_lista(1, 1, id_precio=5)
        self.assertIn("precio", str(ctx.exception).lower())


# ==============================================================================
# Lines 783-784: except (ValueError, TypeError) in validar_variacion_precio
# Line 787: if anterior <= 0 returns
# ==============================================================================

class ValidarVariacionPrecioEdgeCasesTest(TestCase):

    @patch("apps.productos.validators.Decimal", side_effect=ValueError("bad"))
    def test_variacion_decimal_error(self, _mock):
        """Lines 783-784: Decimal raises ValueError → ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_variacion_precio("bad", "bad")
        self.assertIn("número", str(ctx.exception).lower())

    @patch("apps.productos.validators.Decimal", side_effect=TypeError("bad"))
    def test_variacion_decimal_type_error(self, _mock):
        """Lines 783-784: Decimal raises TypeError → ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            validar_variacion_precio(object(), object())
        self.assertIn("número", str(ctx.exception).lower())

    def test_anterior_cero_retorna(self):
        """Line 787: anterior <= 0 returns without error."""
        validar_variacion_precio(Decimal("5000"), Decimal("0"))

    def test_anterior_negativo_retorna(self):
        """Line 787: anterior < 0 returns without error."""
        validar_variacion_precio(Decimal("5000"), Decimal("-100"))


# ==============================================================================
# Lines 837-838: warnings.warn for small difference in validar_cambio_precio_historico
# ==============================================================================

class ValidarCambioPrecioHistoricoPequenioTest(TestCase):

    def test_diferencia_menor_a_un_guarani(self):
        """Lines 837-838: diferencia < 1.00 emits UserWarning."""
        import warnings as _warnings
        with _warnings.catch_warnings(record=True) as w:
            _warnings.simplefilter("always")
            validar_cambio_precio_historico(Decimal("5000.00"), Decimal("5000.50"))

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        self.assertGreater(len(user_warnings), 0)
        self.assertIn("pequeña", str(user_warnings[0].message).lower())
