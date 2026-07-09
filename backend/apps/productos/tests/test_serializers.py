"""
Tests de serializers para la app productos.
Cubre: ProductoSerializer (precio_actual annotation), PrecioPorListaSerializer,
       ImpuestoSerializer.
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def lista_precio_custom(db):
    from apps.productos.models import ListaPrecio
    return ListaPrecio.objects.create(nombre="Lista Test", activo=True)


@pytest.mark.django_db
class TestProductoSerializer:

    def test_fields_present(self, producto):
        from apps.productos.serializers import ProductoSerializer
        data = ProductoSerializer(producto).data
        assert "id" in data
        assert "descripcion" in data
        assert "precio_actual" in data
        assert "categoria_nombre" in data

    def test_precio_actual_uses_annotation(self, producto):
        from apps.productos.serializers import ProductoSerializer
        producto._precio_actual = Decimal("9999")
        data = ProductoSerializer(producto).data
        assert str(data["precio_actual"]) == "9999"

    def test_precio_actual_falls_back_to_property(self, producto):
        from apps.productos.serializers import ProductoSerializer
        if hasattr(producto, "_precio_actual"):
            del producto._precio_actual
        data = ProductoSerializer(producto).data
        assert "precio_actual" in data

    def test_categoria_nombre_read_only(self, producto, categoria):
        from apps.productos.serializers import ProductoSerializer
        data = ProductoSerializer(producto).data
        assert data["categoria_nombre"] == categoria.nombre


@pytest.mark.django_db
class TestPrecioPorListaSerializer:

    def test_serializa_correctamente(self, producto, lista_precio_custom):
        from apps.productos.models import PrecioPorLista
        from apps.productos.serializers import PrecioPorListaSerializer
        precio = PrecioPorLista.objects.create(
            producto=producto,
            lista=lista_precio_custom,
            precio_unitario=Decimal("5000"),
        )
        data = PrecioPorListaSerializer(precio).data
        assert data["producto_nombre"] == producto.descripcion
        assert data["lista_nombre"] == lista_precio_custom.nombre

    def test_precio_unitario_en_datos(self, producto, lista_precio_custom):
        from apps.productos.models import PrecioPorLista
        from apps.productos.serializers import PrecioPorListaSerializer
        precio = PrecioPorLista.objects.create(
            producto=producto,
            lista=lista_precio_custom,
            precio_unitario=Decimal("7500"),
        )
        data = PrecioPorListaSerializer(precio).data
        assert Decimal(data["precio_unitario"]) == Decimal("7500")

    def test_fecha_vigencia_read_only(self, producto, lista_precio_custom):
        from apps.productos.serializers import PrecioPorListaSerializer
        assert "fecha_vigencia" in PrecioPorListaSerializer.Meta.read_only_fields


@pytest.mark.django_db
class TestImpuestoSerializer:

    def test_serializa_campos(self):
        from apps.productos.models import Impuesto
        from apps.productos.serializers import ImpuestoSerializer
        imp = Impuesto.objects.create(nombre="IVA 10%", porcentaje=Decimal("10.00"), vigente_desde=date.today(), activo=True)
        data = ImpuestoSerializer(imp).data
        assert data["nombre"] == "IVA 10%"
        assert data["activo"] is True

    def test_todos_los_campos_presentes(self):
        from apps.productos.models import Impuesto
        from apps.productos.serializers import ImpuestoSerializer
        imp = Impuesto.objects.create(nombre="IVA 5%", porcentaje=Decimal("5.00"), vigente_desde=date.today(), activo=True)
        data = ImpuestoSerializer(imp).data
        for campo in ("id", "nombre", "activo"):
            assert campo in data, f"Campo esperado '{campo}' no encontrado"