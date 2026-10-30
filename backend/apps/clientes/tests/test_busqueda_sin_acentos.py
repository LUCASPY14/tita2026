"""
Búsqueda de Cliente/Hijo ignorando acentos (UnaccentSearchFilter). El
personal carga nombres con y sin tilde indistintamente, así que la
búsqueda debe encontrar "González" tipeando "Gonzalez" y viceversa.
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
def cesar(db, tipo_cliente, lista_precio):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="César", apellidos="González", ruc_ci="9001001",
        tipo_cliente=tipo_cliente, lista_precio=lista_precio,
    )


@pytest.fixture
def hijo_con_acento(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Jazmín", apellido="Núñez", cliente_responsable=cliente, activo=True,
    )


@pytest.mark.django_db
class TestBusquedaClienteSinAcentos:

    def test_busca_sin_tilde_encuentra_con_tilde(self, api_admin, cesar):
        resp = api_admin.get("/api/v1/clientes/clientes/", {"search": "Gonzalez"})
        assert resp.status_code == 200
        ids = [c["id_cliente"] for c in resp.data["results"]]
        assert cesar.id_cliente in ids

    def test_busca_con_tilde_encuentra_sin_tilde_en_el_nombre(self, api_admin, cesar):
        resp = api_admin.get("/api/v1/clientes/clientes/", {"search": "césar"})
        assert resp.status_code == 200
        ids = [c["id_cliente"] for c in resp.data["results"]]
        assert cesar.id_cliente in ids


@pytest.mark.django_db
class TestBusquedaHijoSinAcentos:

    def test_busca_sin_tilde_encuentra_apellido_con_tilde(self, api_admin, hijo_con_acento):
        resp = api_admin.get("/api/v1/clientes/hijos/", {"search": "Nunez"})
        assert resp.status_code == 200
        ids = [h["id_hijo"] for h in resp.data["results"]]
        assert hijo_con_acento.id_hijo in ids

    def test_busca_sin_tilde_encuentra_nombre_con_tilde(self, api_admin, hijo_con_acento):
        resp = api_admin.get("/api/v1/clientes/hijos/", {"search": "Jazmin"})
        assert resp.status_code == 200
        ids = [h["id_hijo"] for h in resp.data["results"]]
        assert hijo_con_acento.id_hijo in ids
