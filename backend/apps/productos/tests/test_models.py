"""
Tests para modelos de la app productos.
Cubre __str__, @property y save() de todos los modelos.
"""
import pytest
from decimal import Decimal
from django.utils import timezone


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cat_raiz(db):
    from apps.productos.models import Categoria
    return Categoria.objects.create(nombre="Bebidas", activo=True)


@pytest.fixture
def cat_hija(db, cat_raiz):
    from apps.productos.models import Categoria
    return Categoria.objects.create(nombre="Jugos", categoria_padre=cat_raiz, activo=True)


@pytest.fixture
def unidad(db):
    from apps.productos.models import UnidadMedida
    return UnidadMedida.objects.create(nombre="Kilogramo", abreviatura="kg")


@pytest.fixture
def lista_defecto(db):
    from apps.productos.models import ListaPrecio
    return ListaPrecio.objects.create(nombre="General", activo=True, es_por_defecto=True)


@pytest.fixture
def prod(db, cat_raiz, unidad):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Agua mineral",
        categoria=cat_raiz,
        unidad_medida=unidad,
        requiere_stock=True,
        activo=True,
    )


@pytest.fixture
def precio_en_lista(db, prod, lista_defecto):
    from apps.productos.models import PrecioPorLista
    return PrecioPorLista.objects.create(
        producto=prod, lista=lista_defecto, precio_unitario=Decimal("3000")
    )


# ── Categoria ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCategoriaModel:

    def test_str_raiz(self, cat_raiz):
        assert str(cat_raiz) == "Bebidas"

    def test_str_con_padre(self, cat_hija, cat_raiz):
        """Categoría con padre → 'Padre > Hijo' (líneas 36-38)."""
        assert str(cat_hija) == "Bebidas > Jugos"

    def test_es_categoria_raiz_true(self, cat_raiz):
        """Sin padre → es_categoria_raiz=True (línea 42)."""
        assert cat_raiz.es_categoria_raiz is True

    def test_es_categoria_raiz_false(self, cat_hija):
        assert cat_hija.es_categoria_raiz is False


# ── UnidadMedida ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUnidadMedidaModel:

    def test_str(self, unidad):
        """__str__ incluye nombre y abreviatura (línea 62)."""
        assert str(unidad) == "Kilogramo (kg)"


# ── Producto ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductoModel:

    def test_str(self, prod):
        assert "Agua mineral" in str(prod)

    def test_precio_actual_con_lista_defecto(self, prod, lista_defecto, precio_en_lista):
        """precio_actual devuelve precio de la lista por defecto (líneas 132-134)."""
        assert prod.precio_actual == Decimal("3000")

    def test_precio_actual_sin_lista_defecto(self, prod, lista_precio):
        """Sin lista por defecto, usa el primer precio disponible (línea 135-136)."""
        from apps.productos.models import PrecioPorLista
        PrecioPorLista.objects.create(
            producto=prod, lista=lista_precio, precio_unitario=Decimal("2500")
        )
        assert prod.precio_actual == Decimal("2500")

    def test_precio_actual_sin_precios(self, prod):
        """Sin ningún precio → retorna 0 (línea 136)."""
        assert prod.precio_actual == Decimal("0")

    def test_stock_actual_con_stock(self, prod):
        """stock_actual obtiene cantidad del inventario (líneas 141-144)."""
        from apps.inventario.models import Stock
        Stock.objects.create(producto=prod, cantidad=Decimal("25"))
        assert prod.stock_actual == Decimal("25")

    def test_stock_actual_sin_stock(self, prod):
        """Sin Stock en DB → retorna 0 (líneas 142, 145)."""
        assert prod.stock_actual == Decimal("0")

    def test_requiere_reposicion_true(self, prod):
        """stock_actual < stock_minimo → requiere_reposicion=True (línea 149)."""
        from apps.inventario.models import Stock
        prod.stock_minimo = Decimal("10")
        prod.save()
        Stock.objects.create(producto=prod, cantidad=Decimal("5"))
        assert prod.requiere_reposicion is True

    def test_requiere_reposicion_false(self, prod):
        from apps.inventario.models import Stock
        prod.stock_minimo = Decimal("10")
        prod.save()
        Stock.objects.create(producto=prod, cantidad=Decimal("50"))
        assert prod.requiere_reposicion is False


# ── ListaPrecio ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListaPrecioModel:

    def test_str(self, lista_defecto):
        """__str__ incluye nombre y moneda (línea 174)."""
        assert str(lista_defecto) == "General (PYG)"

    def test_save_es_por_defecto_desactiva_anterior(self, lista_defecto):
        """Guardar nueva lista por defecto desactiva la anterior (líneas 178-183)."""
        from apps.productos.models import ListaPrecio
        nueva = ListaPrecio.objects.create(
            nombre="Premium", activo=True, es_por_defecto=True
        )
        lista_defecto.refresh_from_db()
        assert lista_defecto.es_por_defecto is False
        assert nueva.es_por_defecto is True

    def test_save_no_defecto_no_desactiva(self, lista_defecto):
        """Guardar lista sin es_por_defecto no toca la lista actual (línea 184-185)."""
        from apps.productos.models import ListaPrecio
        ListaPrecio.objects.create(nombre="Mayorista", activo=True, es_por_defecto=False)
        lista_defecto.refresh_from_db()
        assert lista_defecto.es_por_defecto is True


# ── PrecioPorLista ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrecioPorListaModel:

    def test_str(self, precio_en_lista):
        """__str__ incluye producto, lista y precio formateado (línea 214)."""
        s = str(precio_en_lista)
        assert "General" in s
        assert "3.000" in s or "3,000" in s


# ── HistoricoPrecio ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHistoricoPrecioModel:

    def test_str(self, prod, usuario_cajero):
        """__str__ muestra precio_anterior → precio_nuevo (línea 244)."""
        from apps.productos.models import HistoricoPrecio
        h = HistoricoPrecio.objects.create(
            producto=prod,
            precio_anterior=Decimal("2000"),
            precio_nuevo=Decimal("3000"),
            modificado_por=usuario_cajero,
        )
        assert "2.000" in str(h) or "2,000" in str(h)
        assert "3.000" in str(h) or "3,000" in str(h)

    def test_variacion_porcentual(self, prod):
        """variacion_porcentual = ((nuevo - anterior) / anterior) * 100 (líneas 248-250)."""
        from apps.productos.models import HistoricoPrecio
        h = HistoricoPrecio.objects.create(
            producto=prod,
            precio_anterior=Decimal("2000"),
            precio_nuevo=Decimal("2200"),
        )
        assert h.variacion_porcentual == Decimal("10")

    def test_variacion_porcentual_precio_anterior_cero(self, prod):
        """precio_anterior=0 → retorna 0 (línea 250 else branch)."""
        from apps.productos.models import HistoricoPrecio
        h = HistoricoPrecio.objects.create(
            producto=prod,
            precio_anterior=Decimal("0"),
            precio_nuevo=Decimal("3000"),
        )
        assert h.variacion_porcentual == Decimal("0")


# ── Impuesto ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestImpuestoModel:

    def test_str(self, db):
        """__str__ incluye nombre y porcentaje (línea 272)."""
        from apps.productos.models import Impuesto
        imp = Impuesto.objects.create(
            nombre="IVA 10%",
            porcentaje=Decimal("10.00"),
            vigente_desde=timezone.now().date(),
        )
        assert str(imp) == "IVA 10% (10.00%)"


# ── ProductoImpuesto ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductoImpuestoModel:

    def test_str(self, prod, db):
        """__str__ = 'Producto - Impuesto' (línea 296)."""
        from apps.productos.models import Impuesto, ProductoImpuesto
        imp = Impuesto.objects.create(
            nombre="IVA 5%",
            porcentaje=Decimal("5.00"),
            vigente_desde=timezone.now().date(),
        )
        pi = ProductoImpuesto.objects.create(producto=prod, impuesto=imp)
        assert "IVA 5%" in str(pi)
