"""
Tests para el comando de backfill `crear_usuarios_portal` — crea cuentas
CLIENTE_WEB para clientes que ya existen en la base pero no tienen acceso
al portal (por ejemplo, clientes cargados por `importar_clientes` antes de
que ese comando llamara a crear_usuario_portal()).
"""
import io

import pytest
from django.core.management import call_command

from apps.usuarios.models import Usuario


def run_backfill(*args, **kwargs):
    out = io.StringIO()
    call_command("crear_usuarios_portal", *args, stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
class TestCrearUsuariosPortal:

    def test_crea_usuario_para_cliente_sin_cuenta(self, cliente):
        assert not hasattr(cliente, "usuario_portal")

        salida = run_backfill()

        usuario = Usuario.objects.get(cliente=cliente)
        assert usuario.rol == Usuario.Rol.CLIENTE_WEB
        assert usuario.check_password(cliente.ruc_ci)
        assert "Creados: 1" in salida

    def test_cliente_que_ya_tiene_cuenta_no_se_toca(self, cliente):
        from apps.clientes.services import crear_usuario_portal
        crear_usuario_portal(cliente)
        usuario_previo = cliente.usuario_portal

        run_backfill()

        cliente.refresh_from_db()
        assert cliente.usuario_portal.pk == usuario_previo.pk
        assert Usuario.objects.filter(cliente=cliente).count() == 1

    def test_dry_run_no_crea_nada(self, cliente):
        salida = run_backfill(dry_run=True)

        assert "dry-run" in salida
        assert not Usuario.objects.filter(cliente=cliente).exists()

    def test_cliente_inactivo_se_excluye_por_defecto(self, cliente):
        cliente.activo = False
        cliente.save(update_fields=["activo"])

        run_backfill()

        assert not Usuario.objects.filter(cliente=cliente).exists()

    def test_flag_todos_incluye_clientes_inactivos(self, cliente):
        cliente.activo = False
        cliente.save(update_fields=["activo"])

        run_backfill(todos=True)

        assert Usuario.objects.filter(cliente=cliente).exists()
