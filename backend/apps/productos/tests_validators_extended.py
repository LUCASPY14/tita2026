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
    validar_nombre_unidad,
    validar_abreviatura_unidad,
    validar_nombre_lista_precios,
    validar_moneda_lista,
    validar_variacion_precio,
    validar_cambio_precio_historico,
    validar_fecha_cambio_precio,
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
        producto.activo = True
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
        producto.activo = True
        producto.stock_actual = 10
        producto.permite_stock_negativo = True
        result = validar_cambio_estado_producto(producto, False)
        self.assertTrue(result)

    def test_activar_producto(self):
        """Line 221: activating a product returns True."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.activo = False
        result = validar_cambio_estado_producto(producto, True)
        self.assertTrue(result)

    def test_desactivar_sin_stock(self):
        """Deactivating product without stock works."""
        producto = MagicMock()
        producto.id_producto = 1
        producto.activo = True
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
