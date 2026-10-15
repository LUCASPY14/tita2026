"""
Tests para sincronizar_usuario_portal() — propaga email/nombre/apellido del
Cliente a su Usuario del portal cuando el Cliente se edita después de haber
creado el acceso (crear_usuario_portal() solo copia esos datos una vez).
"""
import pytest

from apps.clientes.services import crear_usuario_portal, sincronizar_usuario_portal
from apps.usuarios.models import Usuario


@pytest.mark.django_db
class TestSincronizarUsuarioPortal:

    def test_sin_usuario_portal_no_hace_nada(self, cliente):
        sincronizar_usuario_portal(cliente)
        assert not hasattr(cliente, "usuario_portal")

    def test_sincroniza_email_nombre_apellido(self, cliente):
        cliente.email = "juan.perez@example.com"
        cliente.save(update_fields=["email"])
        crear_usuario_portal(cliente)
        usuario_id = cliente.usuario_portal.pk

        cliente.email = "juan.nuevo@example.com"
        cliente.nombres = "Juan Carlos"
        cliente.apellidos = "Pérez González"
        cliente.save()

        sincronizar_usuario_portal(cliente)

        usuario = Usuario.objects.get(pk=usuario_id)
        assert usuario.email == "juan.nuevo@example.com"
        assert usuario.nombre == "Juan Carlos"
        assert usuario.apellido == "Pérez González"

    def test_no_pisa_email_si_ya_lo_usa_otro_usuario(self, cliente, usuario_cajero):
        cliente.email = "juan.perez@example.com"
        cliente.save(update_fields=["email"])
        crear_usuario_portal(cliente)
        usuario_id = cliente.usuario_portal.pk

        cliente.email = usuario_cajero.email
        cliente.save(update_fields=["email"])

        sincronizar_usuario_portal(cliente)

        usuario = Usuario.objects.get(pk=usuario_id)
        assert usuario.email == "juan.perez@example.com"

    def test_email_vacio_no_borra_el_existente(self, cliente):
        cliente.email = "juan.perez@example.com"
        cliente.save(update_fields=["email"])
        crear_usuario_portal(cliente)
        usuario_id = cliente.usuario_portal.pk

        cliente.email = ""
        cliente.save(update_fields=["email"])

        sincronizar_usuario_portal(cliente)

        usuario = Usuario.objects.get(pk=usuario_id)
        assert usuario.email == "juan.perez@example.com"

    def test_sin_cambios_no_guarda(self, cliente, django_assert_num_queries):
        cliente.email = "juan.perez@example.com"
        cliente.save(update_fields=["email"])
        crear_usuario_portal(cliente)

        cliente.refresh_from_db()
        with django_assert_num_queries(1):
            # Solo el SELECT del related usuario_portal — ningún UPDATE.
            sincronizar_usuario_portal(cliente)
