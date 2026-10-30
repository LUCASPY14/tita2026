"""
Búsqueda de Tarjeta por nombre de alumno/docente ignorando acentos
(UnaccentSearchFilter) — usado en Modo Recreo para buscar por nombre
cuando no se tiene el número de tarjeta.
"""
from decimal import Decimal

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
def tarjeta_hijo_con_acento(db, cliente):
    from apps.clientes.models import Hijo
    from apps.core.models import Tarjeta
    hijo = Hijo.objects.create(
        nombre="Jazmín", apellido="Núñez", cliente_responsable=cliente, activo=True,
    )
    return Tarjeta.objects.create(
        nro_tarjeta="T-ACENTO", hijo=hijo, saldo_actual=Decimal("0"), estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.mark.django_db
class TestBusquedaTarjetaSinAcentos:

    def test_busca_apellido_sin_tilde_encuentra_tarjeta_con_tilde(self, api_admin, tarjeta_hijo_con_acento):
        resp = api_admin.get("/api/v1/core/tarjetas/", {"search": "Nunez"})
        assert resp.status_code == 200
        numeros = [t["nro_tarjeta"] for t in resp.data["results"]]
        assert "T-ACENTO" in numeros
