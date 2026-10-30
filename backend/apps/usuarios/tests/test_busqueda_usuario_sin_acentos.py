"""Búsqueda de Usuario (personal interno) ignorando acentos (UnaccentSearchFilter)."""
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
def usuario_con_acento(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="andres_acento@test.com", password="test1234",
        nombre="Andrés", apellido="Núñez", rol=Usuario.Rol.CAJERO,
    )


@pytest.mark.django_db
def test_busca_apellido_sin_tilde_encuentra_usuario_con_tilde(api_admin, usuario_con_acento):
    resp = api_admin.get("/api/v1/usuarios/usuarios/", {"search": "Nunez"})
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.data["results"]]
    assert "andres_acento@test.com" in emails
