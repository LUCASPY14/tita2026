import pytest
from django.core.management import call_command
from apps.clientes.models import Cliente, TipoCliente
from apps.core.models import Tarjeta
from apps.productos.models import ListaPrecio


@pytest.mark.django_db
def test_import_cliente_tarjeta(tmp_path):
    TipoCliente.objects.create(nombre="Profesores")
    ListaPrecio.objects.create(nombre="Lista General", es_por_defecto=True)

    csv_path = tmp_path / "import.csv"
    csv_path.write_text(
        "ruc_ci,cliente_nombres,cliente_apellidos,cliente_tipo,cliente_tarjeta\n"
        "9988776-5,Test,Profesor,Profesores,TEST01\n",
        encoding="utf-8",
    )
    call_command("importar_clientes", str(csv_path))

    cliente = Cliente.objects.get(ruc_ci="9988776-5")
    tarjeta = Tarjeta.objects.get(pk="TEST01")
    assert tarjeta.cliente_directo_id == cliente.id_cliente
    assert tarjeta.hijo_id is None
    assert tarjeta.estado == "ACTIVA"
