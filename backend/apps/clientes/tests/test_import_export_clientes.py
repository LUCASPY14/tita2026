"""
Tests para los comandos de management `importar_clientes`, `exportar_clientes`
y `seed_ciudades`.
"""
import csv
import io

import pytest
from django.core.management import CommandError, call_command

from apps.clientes.models import Ciudad, Cliente, Grado, Hijo, Pais, TipoCliente
from apps.core.models import Tarjeta
from apps.productos.models import ListaPrecio

CLIENTE_FIELDS = {
    "ruc_ci": "4123456", "cliente_nombres": "Ana", "cliente_apellidos": "García",
    "cliente_email": "ana@test.com", "cliente_telefono": "0981000000",
    "cliente_direccion": "Calle Falsa 123", "cliente_ciudad": "Asunción",
}

HIJOS_DEFAULT = [
    {"nombre": "Sofía", "apellido": "García", "fecha_nacimiento": "2015-03-10", "grado": ""},
    {"nombre": "Pedro", "apellido": "García", "fecha_nacimiento": "2017-01-01", "grado": ""},
    {"nombre": "Lucía", "apellido": "García", "fecha_nacimiento": "2019-06-15", "grado": ""},
]


def fila_base(n_hijos=1, **overrides):
    fila = dict(CLIENTE_FIELDS)
    for i in range(n_hijos):
        n = i + 1
        h = HIJOS_DEFAULT[i] if i < len(HIJOS_DEFAULT) else {
            "nombre": f"Hijo{n}", "apellido": "García", "fecha_nacimiento": "", "grado": "",
        }
        fila[f"hijo{n}_nombre"] = h["nombre"]
        fila[f"hijo{n}_apellido"] = h["apellido"]
        fila[f"hijo{n}_fecha_nacimiento"] = h["fecha_nacimiento"]
        fila[f"hijo{n}_grado"] = h["grado"]
    fila.update(overrides)
    return fila


def escribir_csv(path, filas):
    columnas: list[str] = []
    vistas = set()
    for fila in filas:
        for k in fila:
            if k not in vistas:
                vistas.add(k)
                columnas.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)
    return str(path)


def run_importar(*args, **kwargs):
    out = io.StringIO()
    call_command("importar_clientes", *args, stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
class TestImportarClientesUnHijo:

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

    def test_lista_precio_cae_a_es_por_defecto_si_no_se_especifica(self, tmp_path, tipo_cliente):
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

    def test_falta_hijo1_es_error_de_fila_completa(self, tmp_path, tipo_cliente, lista_precio):
        fila = fila_base()
        fila["hijo1_nombre"] = ""
        csv_path = escribir_csv(tmp_path / "in.csv", [fila])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.count() == 0
        assert "Errores (1)" in salida
        assert "al menos un hijo" in salida

    def test_fila_valida_y_fila_invalida_en_el_mismo_csv_no_se_afectan(self, tmp_path, tipo_cliente, lista_precio):
        filas = [
            fila_base(),
            fila_base(ruc_ci="", cliente_nombres="Sin Documento"),
        ]
        csv_path = escribir_csv(tmp_path / "in.csv", filas)
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Cliente.objects.filter(ruc_ci="4123456").exists()
        assert "Hijos creados: 1" in salida
        assert "Errores (1)" in salida

    def test_grado_inexistente_genera_aviso_pero_crea_el_hijo(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_grado="Grado Que No Existe")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.grado is None
        assert "Avisos" in salida
        assert "no coincide con ningún Grado" in salida

    def test_grado_existente_se_asigna_por_nombre(self, tmp_path, tipo_cliente, lista_precio):
        grado = Grado.objects.create(nombre="3er Grado", nivel=3, orden=3)
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_grado="3er Grado")])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.grado_id == grado.id

    def test_fecha_nacimiento_invalida_no_bloquea_la_fila(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_fecha_nacimiento="fecha-mala")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        assert hijo.fecha_nacimiento is None
        assert "Fecha de nacimiento inválida" in salida

    def test_ciudad_fuera_de_catalogo_genera_aviso_pero_se_guarda(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(cliente_ciudad="Ciudad Inventada")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert cliente.ciudad == "Ciudad Inventada"
        assert 'Ciudad "Ciudad Inventada" no está en el catálogo' in salida

    def test_ciudad_en_catalogo_no_genera_aviso(self, tmp_path, tipo_cliente, lista_precio):
        paraguay = Pais.objects.create(nombre="Paraguay")
        Ciudad.objects.create(nombre="Asunción", pais=paraguay)
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(cliente_ciudad="Asunción")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert "no está en el catálogo" not in salida

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
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(cliente_tipo="Docente")])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert cliente.tipo_cliente.nombre == "Docente"
        assert cliente.tipo_cliente != tipo_padre

    def test_csv_sin_columnas_obligatorias_lanza_command_error(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [{"algo": "1"}])
        with pytest.raises(CommandError):
            run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

    def test_tipo_cliente_inexistente_por_cli_lanza_command_error(self, tmp_path, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        with pytest.raises(CommandError):
            run_importar(csv_path, tipo_cliente="No Existe", lista_precio="General")


@pytest.mark.django_db
class TestImportarClientesMultiplesHijos:

    def test_tres_hijos_en_una_fila_se_crean_los_tres(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(n_hijos=3)])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert Hijo.objects.filter(cliente_responsable=cliente).count() == 3
        assert {"Sofía", "Pedro", "Lucía"} == set(
            Hijo.objects.filter(cliente_responsable=cliente).values_list("nombre", flat=True)
        )
        assert "Hijos creados: 3" in salida

    def test_hijo2_vacio_se_omite_en_silencio(self, tmp_path, tipo_cliente, lista_precio):
        fila = fila_base(n_hijos=3)
        fila["hijo2_nombre"] = ""
        fila["hijo2_apellido"] = ""
        csv_path = escribir_csv(tmp_path / "in.csv", [fila])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert Hijo.objects.filter(cliente_responsable=cliente).count() == 2
        assert "Hijos creados: 2" in salida
        assert "hijo2" not in salida  # el slot vacío no debe generar ningún aviso

    def test_hijo_con_solo_nombre_o_solo_apellido_genera_aviso_y_se_omite(self, tmp_path, tipo_cliente, lista_precio):
        fila = fila_base(n_hijos=2)
        fila["hijo2_apellido"] = ""  # nombre presente, apellido vacío
        csv_path = escribir_csv(tmp_path / "in.csv", [fila])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        cliente = Cliente.objects.get(ruc_ci="4123456")
        assert Hijo.objects.filter(cliente_responsable=cliente).count() == 1
        assert "tiene nombre o apellido vacío" in salida

    def test_familias_con_distinta_cantidad_de_hijos_en_el_mismo_csv(self, tmp_path, tipo_cliente, lista_precio):
        filas = [
            fila_base(n_hijos=1),
            fila_base(n_hijos=3, ruc_ci="9876543", cliente_nombres="Otro", cliente_apellidos="Cliente"),
        ]
        csv_path = escribir_csv(tmp_path / "in.csv", filas)
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Hijo.objects.filter(cliente_responsable__ruc_ci="4123456").count() == 1
        assert Hijo.objects.filter(cliente_responsable__ruc_ci="9876543").count() == 3
        assert "Hijos creados: 4" in salida

    def test_reimportar_multi_hijo_no_duplica_ninguno(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(n_hijos=3)])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")
        salida2 = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Hijo.objects.count() == 3
        assert "Hijos creados: 0" in salida2
        assert "omitidos (ya existían): 3" in salida2


@pytest.mark.django_db
class TestImportarClientesTarjeta:

    def test_tarjeta_declarada_se_crea_y_se_vincula_al_hijo(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_tarjeta="T-001")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        hijo = Hijo.objects.get(nombre="Sofía")
        tarjeta = Tarjeta.objects.get(pk="T-001")
        assert tarjeta.hijo_id == hijo.id
        assert tarjeta.estado == Tarjeta.Estado.ACTIVA
        assert tarjeta.saldo_actual == 0
        assert "Tarjetas vinculadas: 1" in salida

    def test_sin_tarjeta_no_se_crea_nada(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base()])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Tarjeta.objects.count() == 0
        assert "Tarjetas vinculadas: 0" in salida

    def test_reimportar_misma_tarjeta_no_falla_ni_duplica(self, tmp_path, tipo_cliente, lista_precio):
        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_tarjeta="T-001")])
        run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")
        salida2 = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert Tarjeta.objects.count() == 1
        assert "Tarjetas vinculadas: 0" in salida2  # segunda vez ya estaba vinculada, no hay nada que crear

    def test_numero_de_tarjeta_ya_usado_por_otro_hijo_no_se_reasigna(self, tmp_path, tipo_cliente, lista_precio):
        otro_cliente = Cliente.objects.create(
            nombres="Marta", apellidos="Ruiz", ruc_ci="7654321",
            tipo_cliente=tipo_cliente, lista_precio=lista_precio,
        )
        otro_hijo = Hijo.objects.create(cliente_responsable=otro_cliente, nombre="Bruno", apellido="Ruiz")
        Tarjeta.objects.create(nro_tarjeta="T-001", hijo=otro_hijo)

        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_tarjeta="T-001")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        tarjeta = Tarjeta.objects.get(pk="T-001")
        assert tarjeta.hijo_id == otro_hijo.id  # sin cambios
        assert "ya está registrada a nombre de" in salida
        assert "Tarjetas vinculadas: 0" in salida

    def test_hijo_con_otra_tarjeta_ya_asociada_no_se_pisa(self, tmp_path, tipo_cliente, lista_precio):
        cliente = Cliente.objects.create(
            nombres="Ana", apellidos="García", ruc_ci="4123456",
            tipo_cliente=tipo_cliente, lista_precio=lista_precio,
        )
        hijo = Hijo.objects.create(cliente_responsable=cliente, nombre="Sofía", apellido="García")
        Tarjeta.objects.create(nro_tarjeta="T-VIEJA", hijo=hijo)

        csv_path = escribir_csv(tmp_path / "in.csv", [fila_base(hijo1_tarjeta="T-NUEVA")])
        salida = run_importar(csv_path, tipo_cliente="Padre", lista_precio="General")

        assert not Tarjeta.objects.filter(pk="T-NUEVA").exists()
        hijo.refresh_from_db()
        assert hijo.tarjeta.pk == "T-VIEJA"
        assert "ya tiene la tarjeta" in salida


@pytest.mark.django_db
class TestExportarClientes:

    def test_exporta_una_familia_con_un_hijo(self, tmp_path, cliente):
        Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        out_path = tmp_path / "out.csv"

        run = io.StringIO()
        call_command("exportar_clientes", str(out_path), stdout=run)

        with open(out_path, encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f))
        assert len(filas) == 1
        assert filas[0]["ruc_ci"] == cliente.ruc_ci
        assert filas[0]["hijo1_nombre"] == "Lucía"
        assert filas[0]["cliente_tipo"] == cliente.tipo_cliente.nombre
        assert "1 familia" in run.getvalue()

    def test_incluye_numero_de_tarjeta_si_el_hijo_ya_tiene_una(self, tmp_path, cliente):
        hijo = Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        Tarjeta.objects.create(nro_tarjeta="T-001", hijo=hijo)
        otro_hijo = Hijo.objects.create(cliente_responsable=cliente, nombre="Mateo", apellido="Pérez")
        out_path = tmp_path / "out.csv"
        call_command("exportar_clientes", str(out_path))

        with open(out_path, encoding="utf-8-sig") as f:
            fila = next(csv.DictReader(f))
        columnas_tarjeta = {fila["hijo1_tarjeta"], fila["hijo2_tarjeta"]}
        assert "T-001" in columnas_tarjeta
        assert "" in columnas_tarjeta  # el otro hijo no tiene tarjeta

    def test_familia_con_varios_hijos_usa_columnas_hijo1_hijo2(self, tmp_path, cliente):
        Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        Hijo.objects.create(cliente_responsable=cliente, nombre="Mateo", apellido="Pérez")
        out_path = tmp_path / "out.csv"
        call_command("exportar_clientes", str(out_path))

        with open(out_path, encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f))
        assert len(filas) == 1
        nombres = {filas[0]["hijo1_nombre"], filas[0]["hijo2_nombre"]}
        assert nombres == {"Lucía", "Mateo"}

    def test_header_se_ajusta_al_maximo_de_hijos_entre_familias(self, tmp_path, cliente, tipo_cliente, lista_precio):
        Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        otro = Cliente.objects.create(
            nombres="Marta", apellidos="Ruiz", ruc_ci="7654321",
            tipo_cliente=tipo_cliente, lista_precio=lista_precio,
        )
        Hijo.objects.create(cliente_responsable=otro, nombre="A", apellido="Ruiz")
        Hijo.objects.create(cliente_responsable=otro, nombre="B", apellido="Ruiz")
        Hijo.objects.create(cliente_responsable=otro, nombre="C", apellido="Ruiz")
        out_path = tmp_path / "out.csv"
        call_command("exportar_clientes", str(out_path))

        with open(out_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            columnas = reader.fieldnames
            filas = list(reader)
        assert "hijo3_nombre" in columnas
        assert "hijo4_nombre" not in columnas
        fila_cliente = next(f for f in filas if f["ruc_ci"] == cliente.ruc_ci)
        assert fila_cliente["hijo2_nombre"] == ""  # solo tiene 1 hijo, slots extra vacíos

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
        assert filas[0]["cliente_activo"] == "True"

    def test_round_trip_exportar_y_reimportar_no_duplica(self, tmp_path, cliente):
        hijo1 = Hijo.objects.create(cliente_responsable=cliente, nombre="Lucía", apellido="Pérez")
        Hijo.objects.create(cliente_responsable=cliente, nombre="Mateo", apellido="Pérez")
        Tarjeta.objects.create(nro_tarjeta="T-001", hijo=hijo1)
        out_path = tmp_path / "roundtrip.csv"
        call_command("exportar_clientes", str(out_path))

        salida = run_importar(str(out_path), tipo_cliente=cliente.tipo_cliente.nombre)

        assert Cliente.objects.filter(ruc_ci=cliente.ruc_ci).count() == 1
        assert Hijo.objects.filter(cliente_responsable=cliente).count() == 2
        assert Tarjeta.objects.count() == 1
        assert "Clientes creados: 0" in salida
        assert "Hijos creados: 0" in salida
        assert "Tarjetas vinculadas: 0" in salida


@pytest.mark.django_db
class TestSeedCiudades:

    def test_crea_paraguay_y_las_27_ciudades(self):
        out = io.StringIO()
        call_command("seed_ciudades", stdout=out)

        assert Pais.objects.filter(nombre="Paraguay").exists()
        assert Ciudad.objects.count() == 27
        assert Ciudad.objects.filter(nombre="Asunción", pais__nombre="Paraguay").exists()
        assert "27 creadas" in out.getvalue()

    def test_correrlo_dos_veces_no_duplica(self):
        call_command("seed_ciudades")
        out = io.StringIO()
        call_command("seed_ciudades", stdout=out)

        assert Ciudad.objects.count() == 27
        assert "0 creadas" in out.getvalue()
