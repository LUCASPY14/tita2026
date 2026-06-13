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
