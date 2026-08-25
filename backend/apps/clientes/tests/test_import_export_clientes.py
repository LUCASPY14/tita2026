"""
Tests para los comandos de management `importar_clientes` y `exportar_clientes`.
"""
import csv
import io

import pytest
from django.core.management import CommandError, call_command

from apps.clientes.models import Cliente, Grado, Hijo, TipoCliente
from apps.productos.models import ListaPrecio

COLUMNAS = [
    "ruc_ci", "cliente_nombres", "cliente_apellidos", "cliente_email",
    "cliente_telefono", "cliente_direccion", "cliente_ciudad",
    "hijo_nombre", "hijo_apellido", "hijo_fecha_nacimiento", "hijo_grado",
]


def escribir_csv(path, filas, columnas=COLUMNAS):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)
    return str(path)


def fila_base(**overrides):
    base = {
        "ruc_ci": "4123456", "cliente_nombres": "Ana", "cliente_apellidos": "García",
        "cliente_email": "ana@test.com", "cliente_telefono": "0981000000",
        "cliente_direccion": "Calle Falsa 123", "cliente_ciudad": "Asunción",
        "hijo_nombre": "Sofía", "hijo_apellido": "García",
        "hijo_fecha_nacimiento": "2015-03-10", "hijo_grado": "",
    }
    base.update(overrides)
    return base


def run_importar(*args, **kwargs):
    out = io.StringIO()
    call_command("importar_clientes", *args, stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
class TestImportarClientes:

    def test_fila_valida_crea_cliente_e_hijo(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert cliente.nombres == "Ana"
        assert cliente.tipo_cliente == tipo_cliente
        hijo = Hijo.objects.get(cliente_responsable=cliente)
        assert hijo.nombre == "Sofía"
        assert hijo.fecha_nacimiento.isoformat() == "2015-03-10"
        assert "Clientes creados: 1" in salida
        assert "Hijos creados: 1" in salida

    def test_lista_precio_cae_a_es_por_defecto_si_no_se_especifica(self, tmp_path, tipo_cliente, db):
        ListaPrecio.objects.create(nombre="Defecto", activo=True, es_por_defecto=True)
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        run_importar(csv_path, tipo_cliente="Padre")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert cliente.lista_precio.nombre == "Defecto"

    def test_reimportar_mismo_csv_no_duplica(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")
        salida2 = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.filter(ruc_ci="4123456").count() == 1
        assert Hijo.objects.filter(nombre="Sofía").count() == 1
        assert "Clientes creados: 0" in salida2
        assert "reutilizados: 1" in salida2
        assert "omitidos (ya existían): 1" in salida2

    def test_dos_hijos_mismo_cliente_reutiliza_el_cliente(self, tmp_path, tipo_cliente, lista_precio):
        filas = [
            fila_base(),
            fila_base(hijo_nombre="Pedro", hijo_fecha_nacimiento="2017-01-01"),
        ]
        csv_path = escribir_csv(tmp_path / "in.csv", filas)
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.filter(ruc_ci="4123456").count() == 1
        assert Hijo.objects.filter(cliente_responsable__ruc_ci="4123456").count() == 2
        assert "Clientes creados: 1" in salida
        assert "Hijos creados: 2" in salida

    def test_cliente_existente_no_se_toca_sin_flag_actualizar(self, tmp_path, tipo_cliente, lista_precio, cliente):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(
            ruc_ci=cliente.ruc_ci, cliente_nombres="Nombre Distinto",
        )])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente.refresh_from_db()
        assert cliente.nombres == "Juan"  # sin cambios

    def test_actualizar_clientes_pisa_datos_de_contacto(self, tmp_path, tipo_cliente, lista_precio, cliente):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(
            ruc_ci=cliente.ruc_ci, cliente_nombres="Nombre Nuevo", cliente_telefono="0999111222",
        )])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General", actualizar_clientes=True)

        cliente.refresh_from_db()
        assert cliente.nombres == "Nombre Nuevo"
        assert cliente.telefono == "0999111222"

    def test_ci_con_formato_invalido_no_crea_nada_para_esa_fila(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(ruc_ci="abc-no-es-un-documento")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.count() == 0
        assert "Errores (1)" in salida
        assert "formato reconocible" in salida

    def test_fila_valida_y_fila_invalida_en_el_mismo_csv_no_se_afectan(self, tmp_path, tipo_cliente, lista_precio):
        filas = [
            fila_base(),
            fila_base(ruc_ci="", cliente_nombres="Sin Documento", hijo_nombre="Hijo2"),
        ]
        csv_path = escribir_csv(tmp_path / "in.csv", filas)
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.filter(ruc_ci="4123456").exists()
        assert "Hijos creados: 1" in salida
        assert "Errores (1)" in salida

    def test_grado_inexistente_genera_aviso_pero_crea_el_hijo(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo_grado="Grado Que No Existe")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.grado is None
        assert "Avisos (1)" in salida
        assert "no coincide con ningún Grado" in salida

    def test_grado_existente_se_asigna_por_nombre(self, tmp_path, tipo_cliente, lista_precio):
        grado = Grado.objects.create(nombre="3er Grado", nivel=3, orden=3)
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo_grado="3er Grado")])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.grado_id == grado.id

    def test_fecha_nacimiento_invalida_no_bloquea_la_fila(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo_fecha_nacimiento="fecha-mala")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.fecha_nacimiento is None
        assert "Fecha de nacimiento inválida" in salida

    def test_dry_run_no_escribe_en_la_base(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General", dry_run=True)

        assert Cliente.objects.count() == 0
        assert Hijo.objects.count() == 0
        assert "DRY RUN" in salida
        assert "Clientes creados: 1" in salida  # reporta lo que HARÍA

    def test_sin_tipo_cliente_ni_columna_en_csv_es_error_por_fila(self, tmp_path, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        salida = run_importar(csv_path, lista_precio="General")

        assert Cliente.objects.count() == 0
        assert "Errores (1)" in salida
        assert "tipo-cliente" in salida

    def test_columna_cliente_tipo_en_csv_tiene_prioridad_sobre_el_flag(self, tmp_path, lista_precio):
        TipoCliente.objects.create(nombre="Docente")
        tipo_padre = TipoCliente.objects.create(nombre="Padre")
        csv_path = escribir_csv(
            tmp_path / "in.csv",
            [fila_base(cliente_tipo="Docente")],
            columnas=COLUMNAS + ["cliente_tipo"],
        )
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert cliente.tipo_cliente.nombre == "Docente"
        assert cliente.tipo_cliente != tipo_padre

    def test_csv_sin_columnas_obligatorias_lanza_command_error(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [{"algo": "1"}], columnas=["algo"])
        with pytest.raises(CommandError):
            run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

    def test_tipo_cliente_inexistente_por_cli_lanza_command_error(self, tmp_path, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        with pytest.raises(CommandError):
            run_importar(csv_path, tipo_cliente="No Existe", lista_precio="General")


@pytest.mark.django_db
class TestExportarClientes:

    def test_exporta_clientes_e_hijos_activos(self, tmp_path, cliente):
        hijo = Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        out_path = tmp_path / "out.csv"

        run = io.StringIO()
        call_command("exportar_clientes", str(out_path), stdout=run)

        with open(out_path, encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f))
        assert len(filas) == 1
        assert filas[0]["ruc_ci"] == cliente.ruc_ci
        assert filas[0]["hijo_nombre"] == "Lucía"
        assert filas[0]["cliente_tipo"] == cliente.tipo_cliente.nombre
        assert "Exportados 1 hijo" in run.getvalue()

    def test_hijo_inactivo_se_excluye_por_defecto_e_incluye_con_todos(self, tmp_path, cliente):
        Hijo.objects.create(cliente_responsable=cliente, nombre="Baja", apellido="Pérez", activo=False)
        out_path = tmp_path / "out.csv"

        call_command("exportar_clientes", str(out_path))
        with open(out_path, encoding="utf-8-sig") as f:
            assert list(csv.DictReader(f)) == []

        call_command("exportar_clientes", str(out_path), todos=True)
        with open(out_path, encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f))
        assert len(filas) == 1
        assert filas[0]["hijo_activo"] == "False"

    def test_round_trip_exportar_y_reimportar_no_duplica(self, tmp_path, cliente):
        Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        out_path = tmp_path / "roundtrip.csv"
        call_command("exportar_clientes", str(out_path))

        salida = run_importar(str(out_path), tipo_cliente=cliente.tipo_cliente.nombre)

        assert Cliente.objects.filter(ruc_ci=cliente.ruc_ci).count() == 1
        assert Hijo.objects.filter(cliente_responsable=cliente).count() == 1
        assert "Clientes creados: 0" in salida
        assert "Hijos creados: 0" in salida
