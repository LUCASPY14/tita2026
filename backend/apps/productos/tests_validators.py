"""
Tests para los validadores del módulo productos
Pruebas exhaustivas de todas las validaciones de negocio
"""

import warnings
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.models import Impuestos
from apps.productos.models import (
    Categorias,
    ListasPrecios,
    PreciosPorLista,
    Productos,
    UnidadesMedida,
)
from apps.productos.validators import (  # Validadores de productos; Validadores de categorías; Validadores de unidades de medida; Validadores de listas de precios; Validadores de precios por lista; Validadores de histórico
    validar_abreviatura_unidad,
    validar_cambio_estado_producto,
    validar_cambio_precio_historico,
    validar_categoria_activa_con_productos,
    validar_codigo_barra,
    validar_descripcion_producto,
    validar_fecha_cambio_precio,
    validar_fecha_vigencia_lista,
    validar_jerarquia_categoria,
    validar_lista_activa_con_precios,
    validar_margen_utilidad,
    validar_moneda_lista,
    validar_nombre_categoria,
    validar_nombre_lista_precios,
    validar_nombre_unidad,
    validar_precio_positivo,
    validar_precio_unitario_lista,
    validar_producto_unico,
    validar_stock_minimo,
    validar_unicidad_precio_lista,
    validar_unidad_activa_con_productos,
    validar_variacion_precio,
)

# ==================== TESTS DE VALIDADORES DE PRODUCTOS ====================


class ValidadoresCodigoBarraTestCase(TestCase):
    """Tests para validar_codigo_barra"""

    def test_codigo_ean13_valido(self):
        """Test: Código EAN-13 (13 dígitos) válido"""
        try:
            validar_codigo_barra("7891234567890")
        except ValidationError:  # pragma: no cover
            self.fail("validar_codigo_barra() falló con EAN-13 válido")

    def test_codigo_ean8_valido(self):
        """Test: Código EAN-8 (8 dígitos) válido"""
        try:
            validar_codigo_barra("12345678")
        except ValidationError:  # pragma: no cover
            self.fail("validar_codigo_barra() falló con EAN-8 válido")

    def test_codigo_upc_valido(self):
        """Test: Código UPC (12 dígitos) válido"""
        try:
            validar_codigo_barra("123456789012")
        except ValidationError:  # pragma: no cover
            self.fail("validar_codigo_barra() falló con UPC válido")

    def test_codigo_alfanumerico_valido(self):
        """Test: Código interno alfanumérico válido"""
        codigos_validos = ["PROD-001", "SKU_123", "ART.456"]
        for codigo in codigos_validos:
            with self.subTest(codigo=codigo):
                try:
                    validar_codigo_barra(codigo)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_codigo_barra() falló con código válido: {codigo}")

    def test_codigo_numerico_longitud_invalida(self):
        """Test: Código numérico con longitud inválida (ni 8, ni 12, ni 13)"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_barra("123456")  # Solo 6 dígitos

        self.assertIn("8 (EAN-8), 12 (UPC) o 13 (EAN-13)", str(context.exception))

    def test_codigo_alfanumerico_muy_corto(self):
        """Test: Código alfanumérico demasiado corto (< 4 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_barra("ABC")

        self.assertIn("entre 4 y 20 caracteres", str(context.exception))

    def test_codigo_alfanumerico_muy_largo(self):
        """Test: Código alfanumérico demasiado largo (> 20 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_barra("A" * 21)

        self.assertIn("entre 4 y 20 caracteres", str(context.exception))

    def test_codigo_con_caracteres_invalidos(self):
        """Test: Código con caracteres no permitidos"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_barra("PROD@123#")

        self.assertIn("letras, números, guiones", str(context.exception))

    def test_codigo_vacio(self):
        """Test: Código vacío"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_barra("")

        self.assertIn("no puede estar vacío", str(context.exception))


class ValidadoresDescripcionProductoTestCase(TestCase):
    """Tests para validar_descripcion_producto"""

    def test_descripcion_valida(self):
        """Test: Descripción válida"""
        descripciones = [
            "Coca Cola 500ml",
            "Empanada de Carne (Picante)",
            "Agua Mineral 1.5L",
            "Café con Leche 200ml",
        ]
        for desc in descripciones:
            with self.subTest(descripcion=desc):
                try:
                    validar_descripcion_producto(desc)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_descripcion_producto() falló con descripción válida: {desc}")

    def test_descripcion_muy_corta(self):
        """Test: Descripción muy corta (< 3 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_descripcion_producto("AB")

        self.assertIn("al menos 3 caracteres", str(context.exception))

    def test_descripcion_muy_larga(self):
        """Test: Descripción muy larga (> 255 caracteres)"""
        desc_larga = "A" * 256
        with self.assertRaises(ValidationError) as context:
            validar_descripcion_producto(desc_larga)

        self.assertIn("no puede exceder 255 caracteres", str(context.exception))

    def test_descripcion_con_caracteres_invalidos(self):
        """Test: Descripción con caracteres no permitidos"""
        with self.assertRaises(ValidationError) as context:
            validar_descripcion_producto("Producto @ #")

        self.assertIn("caracteres no permitidos", str(context.exception))

    def test_descripcion_vacia(self):
        """Test: Descripción vacía"""
        with self.assertRaises(ValidationError) as context:
            validar_descripcion_producto("")

        self.assertIn("es obligatoria", str(context.exception))


class ValidadoresStockMinimoTestCase(TestCase):
    """Tests para validar_stock_minimo"""

    def test_stock_minimo_valido(self):
        """Test: Stock mínimo válido"""
        valores_validos = [Decimal("0"), Decimal("10.000"), Decimal("100.500")]
        for valor in valores_validos:
            with self.subTest(valor=valor):
                try:
                    validar_stock_minimo(valor)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_stock_minimo() falló con valor válido: {valor}")

    def test_stock_minimo_negativo(self):
        """Test: Stock mínimo negativo"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo(Decimal("-1"))

        self.assertIn("no puede ser negativo", str(context.exception))

    def test_stock_minimo_excesivo(self):
        """Test: Stock mínimo excesivo (> 100,000)"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo(Decimal("100001"))

        self.assertIn("no puede exceder 100,000", str(context.exception))

    def test_stock_minimo_demasiados_decimales(self):
        """Test: Stock mínimo con más de 3 decimales"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo(Decimal("10.1234"))

        self.assertIn("no puede tener más de 3 decimales", str(context.exception))


class ValidadoresPrecioPositivoTestCase(TestCase):
    """Tests para validar_precio_positivo"""

    def test_precio_valido(self):
        """Test: Precio válido"""
        precios_validos = [Decimal("1.00"), Decimal("5000.00"), Decimal("125000.50")]
        for precio in precios_validos:
            with self.subTest(precio=precio):
                try:
                    validar_precio_positivo(precio)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_precio_positivo() falló con precio válido: {precio}")

    def test_precio_cero(self):
        """Test: Precio cero no permitido"""
        with self.assertRaises(ValidationError) as context:
            validar_precio_positivo(Decimal("0"))

        self.assertIn("debe ser mayor a cero", str(context.exception))

    def test_precio_negativo(self):
        """Test: Precio negativo no permitido"""
        with self.assertRaises(ValidationError) as context:
            validar_precio_positivo(Decimal("-100"))

        self.assertIn("debe ser mayor a cero", str(context.exception))

    def test_precio_excesivo(self):
        """Test: Precio excesivo (> ₲100,000,000)"""
        with self.assertRaises(ValidationError) as context:
            validar_precio_positivo(Decimal("100000001"))

        self.assertIn("no puede exceder", str(context.exception))

    def test_precio_demasiados_decimales(self):
        """Test: Precio con más de 2 decimales"""
        with self.assertRaises(ValidationError) as context:
            validar_precio_positivo(Decimal("5000.123"))

        self.assertIn("no puede tener más de 2 decimales", str(context.exception))


class ValidadoresMargenUtilidadTestCase(TestCase):
    """Tests para validar_margen_utilidad"""

    def test_margen_adecuado(self):
        """Test: Margen de utilidad adecuado (>10%)"""
        try:
            validar_margen_utilidad(Decimal("5000"), Decimal("3000"))  # ~67% margen
        except ValidationError:  # pragma: no cover
            self.fail("validar_margen_utilidad() falló con margen adecuado")

    def test_margen_exacto_minimo(self):
        """Test: Margen exactamente en el mínimo (10%)"""
        try:
            validar_margen_utilidad(Decimal("110"), Decimal("100"))  # 10% margen
        except ValidationError:  # pragma: no cover
            self.fail("validar_margen_utilidad() falló con margen mínimo exacto")

    def test_margen_menor_al_minimo(self):
        """Test: Margen menor al mínimo (<10%)"""
        with self.assertRaises(ValidationError) as context:
            validar_margen_utilidad(Decimal("105"), Decimal("100"))  # 5% margen

        self.assertIn("menor al mínimo permitido", str(context.exception))

    def test_precio_menor_que_costo(self):
        """Test: Precio de venta menor que costo (pérdida)"""
        with self.assertRaises(ValidationError) as context:
            validar_margen_utilidad(Decimal("2000"), Decimal("3000"))

        self.assertIn("vendiendo con pérdida", str(context.exception))

    def test_margen_muy_alto_warning(self):
        """Test: Margen muy alto (>300%) genera warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validar_margen_utilidad(Decimal("1000"), Decimal("200"))  # 400% margen

            self.assertEqual(len(w), 1)
            self.assertIn("muy alto", str(w[0].message))


# ==================== TESTS DE VALIDADORES DE CATEGORÍAS ====================


class ValidadoresNombreCategoriaTestCase(TestCase):
    """Tests para validar_nombre_categoria"""

    def test_nombre_categoria_valido(self):
        """Test: Nombre de categoría válido"""
        nombres = ["Bebidas", "Snacks Salados", "Lácteos"]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                try:
                    validar_nombre_categoria(nombre)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_nombre_categoria() falló con nombre válido: {nombre}")

    def test_nombre_muy_corto(self):
        """Test: Nombre demasiado corto (< 3 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_nombre_categoria("AB")

        self.assertIn("al menos 3 caracteres", str(context.exception))

    def test_nombre_muy_largo(self):
        """Test: Nombre demasiado largo (> 100 caracteres)"""
        nombre_largo = "A" * 101
        with self.assertRaises(ValidationError) as context:
            validar_nombre_categoria(nombre_largo)

        self.assertIn("no puede exceder 100 caracteres", str(context.exception))

    def test_nombre_con_caracteres_invalidos(self):
        """Test: Nombre con caracteres no permitidos"""
        with self.assertRaises(ValidationError) as context:
            validar_nombre_categoria("Categoría @ #")

        self.assertIn("solo puede contener letras", str(context.exception))


class ValidadoresJerarquiaCategoriaTestCase(TestCase):
    """Tests para validar_jerarquia_categoria"""

    def setUp(self):
        """Configurar categorías de prueba"""
        self.padre = Categorias.objects.create(id_categoria=1, nombre="Bebidas", estado=True)

        self.hija = Categorias.objects.create(
            id_categoria=2, nombre="Gaseosas", estado=True, id_categoria_padre=self.padre
        )

    def test_jerarquia_valida(self):
        """Test: Jerarquía válida (asignar padre existente)"""
        try:
            validar_jerarquia_categoria(self.padre)
        except ValidationError:  # pragma: no cover
            self.fail("validar_jerarquia_categoria() falló con jerarquía válida")

    def test_categoria_raiz(self):
        """Test: Categoría raíz (sin padre)"""
        try:
            validar_jerarquia_categoria(None)
        except ValidationError:  # pragma: no cover
            self.fail("validar_jerarquia_categoria() falló con categoría raíz")

    def test_categoria_propio_padre(self):
        """Test: Categoría no puede ser su propio padre"""
        with self.assertRaises(ValidationError) as context:
            validar_jerarquia_categoria(self.padre, categoria_actual_id=self.padre.id_categoria)

        self.assertIn("no puede ser su propio padre", str(context.exception))

    def test_ciclo_en_jerarquia(self):
        """Test: Detectar ciclo en jerarquía"""
        # Intentar hacer que padre sea hijo de hija (ciclo)
        with self.assertRaises(ValidationError) as context:
            validar_jerarquia_categoria(self.hija, categoria_actual_id=self.padre.id_categoria)

        self.assertIn("crearía un ciclo", str(context.exception))


# ==================== TESTS DE VALIDADORES DE UNIDADES DE MEDIDA ====================


class ValidadoresNombreUnidadTestCase(TestCase):
    """Tests para validar_nombre_unidad"""

    def test_nombre_unidad_valido(self):
        """Test: Nombre de unidad válido"""
        nombres = ["Kilogramo", "Litro", "Unidad", "Metro cúbico"]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                try:
                    validar_nombre_unidad(nombre)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_nombre_unidad() falló con nombre válido: {nombre}")

    def test_nombre_muy_corto(self):
        """Test: Nombre muy corto (< 2 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_nombre_unidad("A")

        self.assertIn("al menos 2 caracteres", str(context.exception))

    def test_nombre_muy_largo(self):
        """Test: Nombre muy largo (> 50 caracteres)"""
        nombre_largo = "A" * 51
        with self.assertRaises(ValidationError) as context:
            validar_nombre_unidad(nombre_largo)

        self.assertIn("no puede exceder 50 caracteres", str(context.exception))

    def test_nombre_con_caracteres_invalidos(self):
        """Test: Nombre con caracteres no permitidos (números, símbolos)"""
        with self.assertRaises(ValidationError) as context:
            validar_nombre_unidad("Kilo123")

        self.assertIn("solo puede contener letras", str(context.exception))


class ValidadoresAbreviaturaUnidadTestCase(TestCase):
    """Tests para validar_abreviatura_unidad"""

    def test_abreviatura_valida(self):
        """Test: Abreviatura válida"""
        abreviaturas = ["Kg", "L", "UN", "m²", "m³", "g"]
        for abr in abreviaturas:
            with self.subTest(abreviatura=abr):
                try:
                    validar_abreviatura_unidad(abr)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_abreviatura_unidad() falló con abreviatura válida: {abr}")

    def test_abreviatura_muy_larga(self):
        """Test: Abreviatura muy larga (> 10 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_abreviatura_unidad("Abreviatura")

        self.assertIn("no puede exceder 10 caracteres", str(context.exception))

    def test_abreviatura_con_espacios(self):
        """Test: Abreviatura con espacios no permitida"""
        with self.assertRaises(ValidationError) as context:
            validar_abreviatura_unidad("K g")

        self.assertIn("no puede contener espacios", str(context.exception))

    def test_abreviatura_con_caracteres_invalidos(self):
        """Test: Abreviatura con caracteres no permitidos"""
        with self.assertRaises(ValidationError) as context:
            validar_abreviatura_unidad("Kg@")

        self.assertIn("solo puede contener", str(context.exception))


# ==================== TESTS DE VALIDADORES DE LISTAS DE PRECIOS ====================


class ValidadoresNombreListaPreciosTestCase(TestCase):
    """Tests para validar_nombre_lista_precios"""

    def test_nombre_lista_valido(self):
        """Test: Nombre de lista válido"""
        nombres = ["Minorista", "Mayorista (10+ unidades)", "Estudiantes"]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                try:
                    validar_nombre_lista_precios(nombre)
                except ValidationError:  # pragma: no cover
                    self.fail(f"validar_nombre_lista_precios() falló con nombre válido: {nombre}")

    def test_nombre_muy_corto(self):
        """Test: Nombre muy corto (< 3 caracteres)"""
        with self.assertRaises(ValidationError) as context:
            validar_nombre_lista_precios("AB")

        self.assertIn("al menos 3 caracteres", str(context.exception))

    def test_nombre_muy_largo(self):
        """Test: Nombre muy largo (> 100 caracteres)"""
        nombre_largo = "A" * 101
        with self.assertRaises(ValidationError) as context:
            validar_nombre_lista_precios(nombre_largo)

        self.assertIn("no puede exceder 100 caracteres", str(context.exception))


class ValidadoresFechaVigenciaListaTestCase(TestCase):
    """Tests para validar_fecha_vigencia_lista"""

    def test_fecha_vigencia_hoy(self):
        """Test: Fecha de vigencia hoy"""
        try:
            validar_fecha_vigencia_lista(date.today())
        except ValidationError:  # pragma: no cover
            self.fail("validar_fecha_vigencia_lista() falló con fecha hoy")

    def test_fecha_vigencia_pasada_reciente(self):
        """Test: Fecha de vigencia pasada (hace 1 mes)"""
        fecha = date.today() - timedelta(days=30)
        try:
            validar_fecha_vigencia_lista(fecha)
        except ValidationError:  # pragma: no cover
            self.fail("validar_fecha_vigencia_lista() falló con fecha pasada reciente")

    def test_fecha_vigencia_futura_cercana(self):
        """Test: Fecha de vigencia futura cercana (en 1 mes)"""
        fecha = date.today() + timedelta(days=30)
        try:
            validar_fecha_vigencia_lista(fecha)
        except ValidationError:  # pragma: no cover
            self.fail("validar_fecha_vigencia_lista() falló con fecha futura cercana")

    def test_fecha_vigencia_muy_futura(self):
        """Test: Fecha de vigencia muy futura (> 1 año)"""
        fecha = date.today() + timedelta(days=400)
        with self.assertRaises(ValidationError) as context:
            validar_fecha_vigencia_lista(fecha)

        self.assertIn("más de 1 año en el futuro", str(context.exception))

    def test_fecha_vigencia_muy_antigua(self):
        """Test: Fecha muy antigua (> 2 años) genera warning"""
        fecha = date.today() - timedelta(days=800)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validar_fecha_vigencia_lista(fecha)

            self.assertEqual(len(w), 1)
            self.assertIn("muy antigua", str(w[0].message))


class ValidadoresMonedaListaTestCase(TestCase):
    """Tests para validar_moneda_lista"""

    def test_moneda_pyg_valida(self):
        """Test: Moneda PYG válida"""
        try:
            validar_moneda_lista("PYG")
        except ValidationError:  # pragma: no cover
            self.fail("validar_moneda_lista() falló con PYG")

    def test_moneda_usd_valida(self):
        """Test: Moneda USD válida"""
        try:
            validar_moneda_lista("USD")
        except ValidationError:  # pragma: no cover
            self.fail("validar_moneda_lista() falló con USD")

    def test_moneda_lowercase_convertida(self):
        """Test: Moneda en minúsculas se acepta (convertida a mayúsculas)"""
        try:
            validar_moneda_lista("pyg")
        except ValidationError:  # pragma: no cover
            self.fail("validar_moneda_lista() falló con moneda en minúsculas")

    def test_moneda_invalida(self):
        """Test: Moneda no soportada"""
        with self.assertRaises(ValidationError) as context:
            validar_moneda_lista("XYZ")

        self.assertIn("no soportado", str(context.exception))

    def test_moneda_longitud_invalida(self):
        """Test: Código de moneda con longitud incorrecta"""
        with self.assertRaises(ValidationError) as context:
            validar_moneda_lista("PYGS")

        self.assertIn("3 caracteres", str(context.exception))


# ==================== TESTS DE VALIDADORES DE PRECIOS POR LISTA ====================


class ValidadoresPrecioUnitarioListaTestCase(TestCase):
    """Tests para validar_precio_unitario_lista"""

    def test_precio_unitario_valido(self):
        """Test: Precio unitario válido"""
        try:
            validar_precio_unitario_lista(Decimal("5000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("validar_precio_unitario_lista() falló con precio válido")

    def test_precio_unitario_cero(self):
        """Test: Precio unitario cero no permitido"""
        with self.assertRaises(ValidationError):
            validar_precio_unitario_lista(Decimal("0"))


class ValidadoresVariacionPrecioTestCase(TestCase):
    """Tests para validar_variacion_precio"""

    def test_variacion_pequena_valida(self):
        """Test: Variación pequeña (10%)"""
        try:
            validar_variacion_precio(Decimal("5500"), Decimal("5000"))  # +10%
        except ValidationError:  # pragma: no cover
            self.fail("validar_variacion_precio() falló con variación pequeña")

    def test_variacion_moderada_valida(self):
        """Test: Variación moderada (30%)"""
        try:
            validar_variacion_precio(Decimal("6500"), Decimal("5000"))  # +30%
        except ValidationError:  # pragma: no cover
            self.fail("validar_variacion_precio() falló con variación moderada")

    def test_variacion_grande_warning(self):
        """Test: Variación grande (>50%) genera warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validar_variacion_precio(Decimal("8000"), Decimal("5000"))  # +60%

            self.assertEqual(len(w), 1)
            self.assertIn("supera el límite", str(w[0].message))

    def test_variacion_excesiva(self):
        """Test: Variación excesiva (>200%) rechazada"""
        with self.assertRaises(ValidationError) as context:
            validar_variacion_precio(Decimal("20000"), Decimal("5000"))  # +300%

        self.assertIn("excesiva", str(context.exception))


# ==================== TESTS DE VALIDADORES DE HISTÓRICO ====================


class ValidadoresCambioPrecioHistoricoTestCase(TestCase):
    """Tests para validar_cambio_precio_historico"""

    def test_cambio_precio_valido(self):
        """Test: Cambio de precio válido"""
        try:
            validar_cambio_precio_historico(Decimal("4000"), Decimal("5000"))
        except ValidationError:  # pragma: no cover
            self.fail("validar_cambio_precio_historico() falló con cambio válido")

    def test_precios_iguales(self):
        """Test: Precios iguales no permitidos"""
        with self.assertRaises(ValidationError) as context:
            validar_cambio_precio_historico(Decimal("5000"), Decimal("5000"))

        self.assertIn("son iguales", str(context.exception))

    def test_precio_anterior_cero(self):
        """Test: Precio anterior cero no permitido"""
        with self.assertRaises(ValidationError) as context:
            validar_cambio_precio_historico(Decimal("0"), Decimal("5000"))

        self.assertIn("mayores a cero", str(context.exception))

    def test_diferencia_muy_pequena(self):
        """Test: Diferencia muy pequeña (<₲1) genera warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validar_cambio_precio_historico(Decimal("5000.00"), Decimal("5000.50"))

            self.assertEqual(len(w), 1)
            self.assertIn("muy pequeña", str(w[0].message))


class ValidadoresFechaCambioPrecioTestCase(TestCase):
    """Tests para validar_fecha_cambio_precio"""

    def test_fecha_cambio_ahora(self):
        """Test: Fecha de cambio actual"""
        try:
            validar_fecha_cambio_precio(timezone.now())
        except ValidationError:  # pragma: no cover
            self.fail("validar_fecha_cambio_precio() falló con fecha actual")

    def test_fecha_cambio_pasada_reciente(self):
        """Test: Fecha de cambio pasada reciente"""
        fecha = timezone.now() - timedelta(days=30)
        try:
            validar_fecha_cambio_precio(fecha)
        except ValidationError:  # pragma: no cover
            self.fail("validar_fecha_cambio_precio() falló con fecha pasada reciente")

    def test_fecha_cambio_futura(self):
        """Test: Fecha de cambio futura no permitida"""
        fecha = timezone.now() + timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            validar_fecha_cambio_precio(fecha)

        self.assertIn("no puede ser futura", str(context.exception))

    def test_fecha_cambio_muy_antigua(self):
        """Test: Fecha de cambio muy antigua (> 5 años)"""
        fecha = timezone.now() - timedelta(days=2000)
        with self.assertRaises(ValidationError) as context:
            validar_fecha_cambio_precio(fecha)

        self.assertIn("demasiado antigua", str(context.exception))


# ==================== TESTS DE VALIDADORES CON MODELOS ====================


class ValidadoresConModelosTestCase(TestCase):
    """Tests que requieren instancias de modelos"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Crear impuesto
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
            estado=True,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre="Bebidas", estado=True)

        # Crear unidad de medida
        self.unidad = UnidadesMedida.objects.create(nombre="Unidad", abreviatura="UN", estado=True)

    def test_validar_producto_unico_nuevo(self):
        """Test: Validar que un producto nuevo sea único"""
        try:
            validar_producto_unico("Coca Cola 500ml", "7890123456789")
        except ValidationError:  # pragma: no cover
            self.fail("validar_producto_unico() falló con producto nuevo")

    def test_validar_producto_unico_descripcion_duplicada(self):
        """Test: No permitir descripción duplicada"""
        # Crear producto
        Productos.objects.create(
            descripcion="Coca Cola",
            codigo_barra="123456",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Intentar crear otro con misma descripción
        with self.assertRaises(ValidationError) as context:
            validar_producto_unico("Coca Cola", "789012")

        self.assertIn("Ya existe un producto", str(context.exception))

    def test_validar_producto_unico_codigo_duplicado(self):
        """Test: No permitir código de barras duplicado"""
        # Crear producto
        Productos.objects.create(
            descripcion="Coca Cola",
            codigo_barra="123456789012",
            stock_minimo=Decimal("0"),
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Intentar crear otro con mismo código
        with self.assertRaises(ValidationError) as context:
            validar_producto_unico("Pepsi", "123456789012")

        self.assertIn("Ya existe un producto", str(context.exception))

    def test_validar_categoria_activa_con_productos_existentes(self):
        """Test: No desactivar categoría con productos activos"""
        # Crear producto estado en la categoría
        Productos.objects.create(
            descripcion="Producto Test",
            stock_minimo=Decimal("0"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Intentar desactivar categoría
        with self.assertRaises(ValidationError) as context:
            validar_categoria_activa_con_productos(self.categoria)

        self.assertIn("producto(s) estado(s)", str(context.exception))

    def test_validar_unidad_activa_con_productos_existentes(self):
        """Test: No desactivar unidad con productos activos"""
        # Crear producto estado con esta unidad
        Productos.objects.create(
            descripcion="Producto Test",
            stock_minimo=Decimal("0"),
            estado=True,
            id_categoria=self.categoria,
            id_impuesto=self.impuesto,
            id_unidad_medida=self.unidad,
        )

        # Intentar desactivar unidad
        with self.assertRaises(ValidationError) as context:
            validar_unidad_activa_con_productos(self.unidad)

        self.assertIn("producto(s) estado(s)", str(context.exception))
