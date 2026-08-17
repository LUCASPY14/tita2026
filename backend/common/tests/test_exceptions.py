"""
Tests para common.exceptions.custom_exception_handler

Cubre la conversión de django.db.models.ProtectedError (levantado por
Model.delete() cuando hay FKs on_delete=PROTECT apuntando al registro)
en una respuesta 400 normalizada, en vez del 500 no controlado que se
producía antes (fix #5 de la auditoría CRUD: catálogos de bajo riesgo
como Categoria/Rol no tenían ningún guard ante un hard-delete en uso).
"""
import pytest
from django.db.models import ProtectedError
from rest_framework.test import APIClient

from common.exceptions import custom_exception_handler


class TestCustomExceptionHandlerProtectedError:
    def test_protected_error_se_normaliza_a_400(self):
        exc = ProtectedError("no se puede eliminar", set())
        response = custom_exception_handler(exc, {"view": None})

        assert response is not None
        assert response.status_code == 400
        assert response.data["code"] == "validation_error"
        assert "en uso" in response.data["detail"]

    def test_protected_error_sin_contexto_view_no_rompe(self):
        exc = ProtectedError("no se puede eliminar", set())
        response = custom_exception_handler(exc, {})

        assert response.status_code == 400


@pytest.mark.django_db
class TestProtectedErrorEndToEnd:
    """Confirma que el fix llega hasta la capa HTTP en catálogos reales con on_delete=PROTECT."""

    def test_no_se_puede_eliminar_categoria_con_productos(self, usuario_admin):
        from apps.productos.models import Categoria, Producto

        categoria = Categoria.objects.create(nombre="Bebidas")
        Producto.objects.create(descripcion="Agua", categoria=categoria)

        client = APIClient()
        client.force_authenticate(user=usuario_admin)
        response = client.delete(f"/api/v1/productos/categorias/{categoria.pk}/")

        assert response.status_code == 400
        assert "en uso" in response.data["detail"]
        assert Categoria.objects.filter(pk=categoria.pk).exists()

    def test_no_se_puede_eliminar_rol_con_empleados(self, usuario_admin):
        from apps.usuarios.models import Rol, Empleado

        rol = Rol.objects.create(nombre_rol="Cocinero")
        Empleado.objects.create(nombre="Juan", apellido="Perez", id_rol=rol)

        client = APIClient()
        client.force_authenticate(user=usuario_admin)
        response = client.delete(f"/api/v1/usuarios/roles/{rol.pk}/")

        assert response.status_code == 400
        assert "en uso" in response.data["detail"]
        assert Rol.objects.filter(pk=rol.pk).exists()

    def test_se_puede_eliminar_categoria_sin_productos(self, usuario_admin):
        from apps.productos.models import Categoria

        categoria = Categoria.objects.create(nombre="Sin uso")

        client = APIClient()
        client.force_authenticate(user=usuario_admin)
        response = client.delete(f"/api/v1/productos/categorias/{categoria.pk}/")

        assert response.status_code == 204
        assert not Categoria.objects.filter(pk=categoria.pk).exists()
