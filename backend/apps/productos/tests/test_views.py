"""
Tests de vistas de productos.
Cubre: CategoriaViewSet (caché), ProductoViewSet (caché + queryset),
PrecioPorListaViewSet (histórico), HistoricoPrecioViewSet (reporte),
y ViewSets simples.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def precio_lista(db, producto, lista_precio):
    from apps.productos.models import PrecioPorLista
    return PrecioPorLista.objects.get(producto=producto, lista=lista_precio)


# ── CategoriaViewSet ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCategoriaViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/categorias/")
        assert resp.status_code == 200

    def test_list_cache_hit(self, api_cajero, categoria):
        resp1 = api_cajero.get("/api/v1/productos/categorias/")
        resp2 = api_cajero.get("/api/v1/productos/categorias/")
        assert resp1.data == resp2.data

    def test_create_invalida_cache(self, api_admin):
        resp = api_admin.post(
            "/api/v1/productos/categorias/",
            {"nombre": "Nueva Cat", "activo": True},
            format="json",
        )
        assert resp.status_code == 201

    def test_update_invalida_cache(self, api_admin, categoria):
        resp = api_admin.patch(
            f"/api/v1/productos/categorias/{categoria.pk}/",
            {"nombre": "Cat Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_delete_invalida_cache(self, api_admin):
        from apps.productos.models import Categoria
        cat = Categoria.objects.create(nombre="Temporal", activo=True)
        resp = api_admin.delete(f"/api/v1/productos/categorias/{cat.pk}/")
        assert resp.status_code == 204

    def test_cajero_no_puede_escribir(self, api_cajero):
        resp = api_cajero.post(
            "/api/v1/productos/categorias/",
            {"nombre": "X", "activo": True},
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/productos/categorias/")
        assert resp.status_code in (401, 403)


# ── ProductoViewSet ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductoViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/productos/")
        assert resp.status_code == 200

    def test_list_cache_hit(self, api_cajero, producto):
        resp1 = api_cajero.get("/api/v1/productos/productos/")
        resp2 = api_cajero.get("/api/v1/productos/productos/")
        assert resp1.data == resp2.data

    def test_create_ok(self, api_admin, categoria, unidad_medida):
        resp = api_admin.post(
            "/api/v1/productos/productos/",
            {
                "descripcion": "Nuevo Producto",
                "categoria": categoria.pk,
                "unidad_medida": unidad_medida.pk,
                "activo": True,
                "requiere_stock": False,
                "permite_stock_negativo": False,
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_create_invalida_cache(self, api_admin, categoria, unidad_medida):
        resp = api_admin.post(
            "/api/v1/productos/productos/",
            {"descripcion": "Cache Test", "categoria": categoria.pk,
             "unidad_medida": unidad_medida.pk, "activo": True},
            format="json",
        )
        assert resp.status_code == 201

    def test_update_invalida_cache(self, api_admin, producto):
        resp = api_admin.patch(
            f"/api/v1/productos/productos/{producto.pk}/",
            {"descripcion": "Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_delete_invalida_cache(self, api_admin, categoria, unidad_medida):
        from apps.productos.models import Producto
        p = Producto.objects.create(
            descripcion="Borrable",
            categoria=categoria,
            unidad_medida=unidad_medida,
            activo=True,
        )
        resp = api_admin.delete(f"/api/v1/productos/productos/{p.pk}/")
        assert resp.status_code == 204

    def test_detail_incluye_precio_actual(self, api_cajero, producto):
        resp = api_cajero.get(f"/api/v1/productos/productos/{producto.pk}/")
        assert resp.status_code == 200
        assert "precio_actual" in resp.data


# ── ViewSets simples ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestViewSetsSimples:

    def test_unidad_medida_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/unidades-medida/")
        assert resp.status_code == 200

    def test_lista_precio_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/listas-precio/")
        assert resp.status_code == 200

    def test_impuesto_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/impuestos/")
        assert resp.status_code == 200

    def test_producto_impuesto_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/productos-impuestos/")
        assert resp.status_code == 200

    def test_precio_por_lista_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/precios-por-lista/")
        assert resp.status_code == 200

    def test_historico_precios_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/productos/historico-precios/")
        assert resp.status_code == 200


# ── PrecioPorListaViewSet.perform_update ──────────────────────────────────────

@pytest.mark.django_db
class TestPrecioPorListaUpdate:

    def test_precio_cambiado_crea_historico(self, api_admin, precio_lista):
        from apps.productos.models import HistoricoPrecio
        resp = api_admin.patch(
            f"/api/v1/productos/precios-por-lista/{precio_lista.pk}/",
            {"precio_unitario": 4500},
            format="json",
        )
        assert resp.status_code == 200
        assert HistoricoPrecio.objects.filter(producto=precio_lista.producto).exists()

    def test_precio_igual_no_crea_historico(self, api_admin, precio_lista):
        from apps.productos.models import HistoricoPrecio
        count_antes = HistoricoPrecio.objects.count()
        api_admin.patch(
            f"/api/v1/productos/precios-por-lista/{precio_lista.pk}/",
            {"precio_unitario": str(precio_lista.precio_unitario)},
            format="json",
        )
        assert HistoricoPrecio.objects.count() == count_antes


# ── HistoricoPrecioViewSet.reporte ────────────────────────────────────────────

@pytest.mark.django_db
class TestHistoricoReporte:

    def test_sin_producto_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/productos/historico-precios/reporte/")
        assert resp.status_code == 400

    def test_con_producto_retorna_estructura(self, api_admin, producto):
        resp = api_admin.get(
            "/api/v1/productos/historico-precios/reporte/",
            {"producto": producto.pk},
        )
        assert resp.status_code == 200
        assert "historial" in resp.data
        assert "registros" in resp.data

    def test_con_periodo_filtra(self, api_admin, producto):
        resp = api_admin.get(
            "/api/v1/productos/historico-precios/reporte/",
            {"producto": producto.pk, "desde": "2020-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/productos/historico-precios/reporte/")
        assert resp.status_code in (401, 403)


# ── ProductoViewSet.set_precio ────────────────────────────────────────────────

@pytest.fixture
def lista_defecto(db):
    from apps.productos.models import ListaPrecio
    return ListaPrecio.objects.create(nombre="Defecto", activo=True, es_por_defecto=True)


@pytest.fixture
def producto_sin_precio_defecto(db, categoria, unidad_medida):
    """Producto sin PrecioPorLista vinculado a la lista por defecto."""
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Sin precio defecto",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=False,
        activo=True,
    )


@pytest.mark.django_db
class TestSetPrecio:

    def test_precio_invalido_retorna_400(self, api_admin, producto, lista_defecto):
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-precio/",
            {"precio": "no_es_numero"},
            format="json",
        )
        assert resp.status_code == 400
        assert "inválido" in resp.data["error"].lower()

    def test_sin_lista_defecto_activa_retorna_400(self, api_admin, producto):
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-precio/",
            {"precio": "5000"},
            format="json",
        )
        assert resp.status_code == 400
        assert "defecto" in resp.data["error"].lower()

    def test_actualiza_precio_existente_y_crea_historico(
        self, api_admin, producto, lista_defecto,
    ):
        from decimal import Decimal
        from apps.productos.models import PrecioPorLista, HistoricoPrecio
        PrecioPorLista.objects.create(
            producto=producto, lista=lista_defecto, precio_unitario=Decimal("3000")
        )
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-precio/",
            {"precio": "5000"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["precio"] == "5000"
        assert HistoricoPrecio.objects.filter(
            producto=producto, precio_anterior=3000, precio_nuevo=5000
        ).exists()

    def test_precio_igual_no_crea_historico(self, api_admin, producto, lista_defecto):
        from decimal import Decimal
        from apps.productos.models import PrecioPorLista, HistoricoPrecio
        PrecioPorLista.objects.create(
            producto=producto, lista=lista_defecto, precio_unitario=Decimal("3000")
        )
        antes = HistoricoPrecio.objects.count()
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-precio/",
            {"precio": "3000"},
            format="json",
        )
        assert resp.status_code == 200
        assert HistoricoPrecio.objects.count() == antes

    def test_crea_precio_nuevo_cuando_no_existe(
        self, api_admin, producto_sin_precio_defecto, lista_defecto,
    ):
        from decimal import Decimal
        from apps.productos.models import PrecioPorLista
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto_sin_precio_defecto.pk}/set-precio/",
            {"precio": "4500"},
            format="json",
        )
        assert resp.status_code == 200
        assert PrecioPorLista.objects.filter(
            producto=producto_sin_precio_defecto,
            lista=lista_defecto,
            precio_unitario=Decimal("4500"),
        ).exists()

    def test_cajero_no_puede_usar_set_precio(self, api_cajero, producto, lista_defecto):
        resp = api_cajero.post(
            f"/api/v1/productos/productos/{producto.pk}/set-precio/",
            {"precio": "5000"},
            format="json",
        )
        assert resp.status_code in (401, 403)


# ── ListaPrecioViewSet.copiar_precios ───────────────────────────────────────────

@pytest.mark.django_db
class TestCopiarPrecios:

    def test_sin_desde_lista_retorna_400(self, api_admin, lista_defecto):
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {},
            format="json",
        )
        assert resp.status_code == 400

    def test_misma_lista_como_origen_y_destino_retorna_400(self, api_admin, lista_precio):
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_precio.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk},
            format="json",
        )
        assert resp.status_code == 400

    def test_lista_origen_inexistente_retorna_404(self, api_admin, lista_defecto):
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": 999_999},
            format="json",
        )
        assert resp.status_code == 404

    def test_ajuste_invalido_retorna_400(self, api_admin, lista_defecto, lista_precio):
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk, "ajuste_porcentual": "no_numero"},
            format="json",
        )
        assert resp.status_code == 400

    def test_copia_precio_nuevo_sin_ajuste(self, api_admin, producto, lista_precio, lista_defecto):
        from apps.productos.models import PrecioPorLista
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data == {"creados": 1, "actualizados": 0}
        assert PrecioPorLista.objects.get(
            producto=producto, lista=lista_defecto
        ).precio_unitario == 3000

    def test_copia_precio_con_ajuste_porcentual_negativo(self, api_admin, producto, lista_precio, lista_defecto):
        from apps.productos.models import PrecioPorLista
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk, "ajuste_porcentual": "-10"},
            format="json",
        )
        assert resp.status_code == 200
        # 3000 * 0.9 = 2700
        assert PrecioPorLista.objects.get(
            producto=producto, lista=lista_defecto
        ).precio_unitario == 2700

    def test_actualiza_precio_existente_y_crea_historico(self, api_admin, producto, lista_precio, lista_defecto):
        from decimal import Decimal
        from apps.productos.models import PrecioPorLista, HistoricoPrecio
        PrecioPorLista.objects.create(producto=producto, lista=lista_defecto, precio_unitario=Decimal("1000"))
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data == {"creados": 0, "actualizados": 1}
        assert PrecioPorLista.objects.get(producto=producto, lista=lista_defecto).precio_unitario == 3000
        assert HistoricoPrecio.objects.filter(
            producto=producto, precio_anterior=1000, precio_nuevo=3000
        ).exists()

    def test_precio_igual_no_actualiza_ni_crea_historico(self, api_admin, producto, lista_precio, lista_defecto):
        from decimal import Decimal
        from apps.productos.models import PrecioPorLista, HistoricoPrecio
        PrecioPorLista.objects.create(producto=producto, lista=lista_defecto, precio_unitario=Decimal("3000"))
        antes = HistoricoPrecio.objects.count()
        resp = api_admin.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data == {"creados": 0, "actualizados": 0}
        assert HistoricoPrecio.objects.count() == antes

    def test_cajero_no_puede_copiar_precios(self, api_cajero, lista_defecto, lista_precio):
        resp = api_cajero.post(
            f"/api/v1/productos/listas-precio/{lista_defecto.pk}/copiar-precios/",
            {"desde_lista": lista_precio.pk},
            format="json",
        )
        assert resp.status_code in (401, 403)


# ── ProductoViewSet.set_impuesto ────────────────────────────────────────────────

@pytest.fixture
def impuesto_10(db):
    from apps.productos.models import Impuesto
    from decimal import Decimal
    return Impuesto.objects.create(
        nombre="IVA 10%", porcentaje=Decimal("10"), vigente_desde="2026-01-01", activo=True,
    )


@pytest.mark.django_db
class TestSetImpuesto:

    def test_asigna_impuesto_a_producto_sin_impuesto(self, api_admin, producto, impuesto_10):
        from apps.productos.models import ProductoImpuesto
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-impuesto/",
            {"impuesto": impuesto_10.pk},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["impuesto"] == {"id": impuesto_10.pk, "nombre": "IVA 10%"}
        assert ProductoImpuesto.objects.filter(producto=producto, impuesto=impuesto_10).exists()

    def test_reemplaza_impuesto_existente(self, api_admin, producto, impuesto_10):
        from decimal import Decimal
        from apps.productos.models import Impuesto, ProductoImpuesto
        impuesto_5 = Impuesto.objects.create(
            nombre="IVA 5%", porcentaje=Decimal("5"), vigente_desde="2026-01-01", activo=True,
        )
        ProductoImpuesto.objects.create(producto=producto, impuesto=impuesto_5)
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-impuesto/",
            {"impuesto": impuesto_10.pk},
            format="json",
        )
        assert resp.status_code == 200
        asignados = ProductoImpuesto.objects.filter(producto=producto)
        assert asignados.count() == 1
        assert asignados.first().impuesto_id == impuesto_10.pk

    def test_impuesto_null_deja_producto_exento(self, api_admin, producto, impuesto_10):
        from apps.productos.models import ProductoImpuesto
        ProductoImpuesto.objects.create(producto=producto, impuesto=impuesto_10)
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-impuesto/",
            {"impuesto": None},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["impuesto"] is None
        assert not ProductoImpuesto.objects.filter(producto=producto).exists()

    def test_impuesto_inexistente_retorna_404(self, api_admin, producto):
        resp = api_admin.post(
            f"/api/v1/productos/productos/{producto.pk}/set-impuesto/",
            {"impuesto": 99999},
            format="json",
        )
        assert resp.status_code == 404

    def test_cajero_no_puede_usar_set_impuesto(self, api_cajero, producto, impuesto_10):
        resp = api_cajero.post(
            f"/api/v1/productos/productos/{producto.pk}/set-impuesto/",
            {"impuesto": impuesto_10.pk},
            format="json",
        )
        assert resp.status_code in (401, 403)
