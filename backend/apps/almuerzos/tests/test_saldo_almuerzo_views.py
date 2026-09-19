"""
Tests de SaldoAlmuerzoViewSet y RecargaSaldoAlmuerzoViewSet (cuenta corriente
de almuerzo): listado, filtro CLIENTE_WEB, historial de movimientos, alta
confirmada/pendiente, confirmación manual y permisos.
"""
import pytest
from decimal import Decimal
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
def usuario_cobrador(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="cobrador_saldo@test.com", password="test1234",
        nombre="Cobrador", apellido="Test", rol=Usuario.Rol.COBRADOR,
    )


@pytest.fixture
def api_cobrador(api_client, usuario_cobrador):
    api_client.force_authenticate(user=usuario_cobrador)
    return api_client


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="Grado Saldo", defaults={"nivel": 3, "orden": 3, "activo": True},
    )
    return g


@pytest.fixture
def hijo_almuerzo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Sofía", apellido="Saldo",
        cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.fixture
def usuario_portal(db, cliente):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="padre_saldo@test.com", password="test1234",
        nombre="Padre", apellido="Saldo",
        rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
    )


@pytest.fixture
def api_padre(api_client, usuario_portal):
    api_client.force_authenticate(user=usuario_portal)
    return api_client


# ── SaldoAlmuerzoViewSet ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSaldoAlmuerzoViewSet:

    def test_admin_lista_todos_los_saldos(self, api_admin, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-10000"))
        resp = api_admin.get("/api/v1/almuerzos/saldos/")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["saldo_actual"] == "-10000"

    def test_cliente_web_solo_ve_su_propio_hijo(self, api_padre, hijo_almuerzo, cliente, db):
        from decimal import Decimal as D
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.clientes.models import Cliente, Hijo, Grado
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("5000"))

        otro_cliente = Cliente.objects.create(
            nombres="Otro", apellidos="Padre", ruc_ci="7654321",
            tipo_cliente=cliente.tipo_cliente, lista_precio=cliente.lista_precio,
            limite_credito=D("999999"),
        )
        grado, _ = Grado.objects.get_or_create(
            nombre="Grado Ajeno", defaults={"nivel": 1, "orden": 1, "activo": True},
        )
        otro_hijo = Hijo.objects.create(
            nombre="Ajeno", apellido="Hijo", cliente_responsable=otro_cliente,
            grado=grado, activo=True,
        )
        SaldoAlmuerzo.objects.create(hijo=otro_hijo, saldo_actual=Decimal("-99999"))

        resp = api_padre.get("/api/v1/almuerzos/saldos/")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["hijo"] == hijo_almuerzo.pk

    def test_cliente_web_sin_cliente_asociado_no_ve_nada(self, api_client, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="sin_cliente_saldo@test.com", password="test1234",
            nombre="Sin", apellido="Cliente", rol=Usuario.Rol.CLIENTE_WEB,
        )
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/almuerzos/saldos/")
        assert resp.status_code == 200
        assert resp.data["count"] == 0

    def test_movimientos_devuelve_historial_del_saldo(self, api_admin, hijo_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        recarga = AlmuerzoService.recargar_saldo(hijo=hijo_almuerzo, monto=Decimal("20000"))
        saldo_id = recarga.movimientos_saldo.first().saldo_id

        resp = api_admin.get(f"/api/v1/almuerzos/saldos/{saldo_id}/movimientos/")
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["tipo"] == "RECARGA"
        assert resp.data[0]["monto"] == "20000"


# ── RecargaSaldoAlmuerzoViewSet ─────────────────────────────────────────────

@pytest.mark.django_db
class TestRecargaSaldoAlmuerzoCreate:

    def test_efectivo_confirma_de_inmediato(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "CONFIRMADA"
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("30000")

    def test_cobrador_puede_recargar(self, api_cobrador, hijo_almuerzo):
        resp = api_cobrador.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "10000", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 201

    def test_cliente_web_no_puede_recargar(self, api_padre, hijo_almuerzo):
        resp = api_padre.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "10000", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 403

    def test_efectivo_bajo_el_minimo_falla(self, api_cajero, hijo_almuerzo):
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "4999", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 400
        assert "mínimo" in resp.data["error"]

    def test_efectivo_supera_el_maximo_falla(self, api_cajero, hijo_almuerzo):
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "5000001", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 400
        assert "máximo" in resp.data["error"]

    def test_transferencia_sin_limite_de_monto(self, api_cajero, hijo_almuerzo):
        """El tope solo aplica a confirmación inmediata (caja); transferencia queda
        PENDIENTE para revisión manual, sin este límite."""
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "10000000", "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201

    def test_transferencia_queda_pendiente(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "PENDIENTE"
        assert not SaldoAlmuerzo.objects.filter(hijo=hijo_almuerzo).exists()

    def test_con_nro_factura_emite_factura(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {
                "hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "EFECTIVO",
                "nro_factura": "001-001-0000001",
            },
            format="json",
        )
        assert resp.status_code == 201
        recarga = RecargaSaldoAlmuerzo.objects.get(pk=resp.data["id_recarga_almuerzo"])
        assert recarga.factura is not None
        assert recarga.factura.nro_factura == "001-001-0000001"

    def test_cuenta_corriente_confirma_de_inmediato_y_genera_deuda(self, api_cajero, hijo_almuerzo, cliente):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.clientes.models import CuentaCorrienteCliente
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "CONFIRMADA"

        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("30000")

        mov = CuentaCorrienteCliente.objects.get(cliente=cliente)
        assert mov.tipo == CuentaCorrienteCliente.Tipo.DEBITO
        assert mov.monto == Decimal("30000")
        assert mov.origen == CuentaCorrienteCliente.Origen.ALMUERZO
        assert cliente.saldo_cuenta_corriente == Decimal("30000")

    def test_cuenta_corriente_no_genera_ingreso_de_caja(self, api_cajero, hijo_almuerzo):
        """A diferencia de EFECTIVO/POS, un pago a crédito no debe registrar
        ingreso de caja — no entró plata física."""
        from apps.contabilidad.models import MovimientoCaja
        antes = MovimientoCaja.objects.count()
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 201
        assert MovimientoCaja.objects.count() == antes

    def test_cuenta_corriente_acumula_con_deuda_previa(self, api_cajero, usuario_cajero, hijo_almuerzo, cliente):
        from apps.clientes.models import CuentaCorrienteCliente
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("10000"), descripcion="Deuda previa", creado_por=usuario_cajero,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "5000", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 201
        assert cliente.saldo_cuenta_corriente == Decimal("15000")

    def test_cliente_sin_cuenta_corriente_habilitada_falla(self, api_cajero, hijo_almuerzo, cliente):
        cliente.permite_cuenta_corriente = False
        cliente.save(update_fields=["permite_cuenta_corriente"])
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "30000", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 400
        assert "no tiene habilitada" in resp.data["error"]

    def test_limite_credito_cero_es_sin_limite(self, api_cajero, hijo_almuerzo, cliente):
        cliente.limite_credito = Decimal("0")
        cliente.save(update_fields=["limite_credito"])
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "50000000", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 201

    def test_limite_credito_positivo_bloquea_al_superarlo(self, api_cajero, hijo_almuerzo, cliente):
        cliente.limite_credito = Decimal("100000")
        cliente.save(update_fields=["limite_credito"])
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "100001", "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 400
        assert "excede el límite" in resp.data["error"]


@pytest.mark.django_db
class TestRecargaSaldoAlmuerzoConfirmar:

    def test_confirma_recarga_pendiente(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo, SaldoAlmuerzo
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        resp = api_cajero.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/confirmar/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "CONFIRMADA"
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("15000")

    def test_confirmar_ya_confirmada_falla(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
        )
        resp = api_cajero.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/confirmar/")
        assert resp.status_code == 400

    def test_confirmar_con_nro_factura_emite_factura(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        resp = api_cajero.post(
            f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/confirmar/",
            {"nro_factura": "001-001-0000002"},
        )
        assert resp.status_code == 200
        recarga.refresh_from_db()
        assert recarga.factura is not None


# ── SaldoAlmuerzoViewSet: panel de cobranza (búsqueda, con_deuda, resumen) ───

@pytest.fixture
def saldos_variados(db, cliente, grado):
    """3 alumnos: deudor, deudor grande, y uno con saldo a favor."""
    from apps.almuerzos.models import SaldoAlmuerzo
    from apps.clientes.models import Hijo
    from apps.core.models import Tarjeta
    datos = [("Ana", "Deuda", "-10000"), ("Beto", "Debe", "-40000"), ("Caro", "Favor", "25000")]
    hijos = []
    for nombre, apellido, saldo in datos:
        h = Hijo.objects.create(
            nombre=nombre, apellido=apellido, cliente_responsable=cliente, grado=grado, activo=True,
        )
        Tarjeta.objects.create(nro_tarjeta=f"PC-{nombre}", hijo=h)
        SaldoAlmuerzo.objects.create(hijo=h, saldo_actual=Decimal(saldo))
        hijos.append(h)
    return hijos


@pytest.mark.django_db
class TestSaldoAlmuerzoPanelCobranza:

    def test_con_deuda_filtra_solo_negativos(self, api_admin, saldos_variados):
        resp = api_admin.get("/api/v1/almuerzos/saldos/", {"con_deuda": "true"})
        assert resp.status_code == 200
        assert resp.data["count"] == 2
        assert all(Decimal(r["saldo_actual"]) < 0 for r in resp.data["results"])

    def test_orden_por_saldo_pone_al_mayor_deudor_primero(self, api_admin, saldos_variados):
        resp = api_admin.get("/api/v1/almuerzos/saldos/", {"ordering": "saldo_actual"})
        assert resp.data["results"][0]["hijo_nombre"].startswith("Beto")

    def test_busqueda_por_nombre_y_por_tarjeta(self, api_admin, saldos_variados):
        r1 = api_admin.get("/api/v1/almuerzos/saldos/", {"search": "Caro"})
        assert r1.data["count"] == 1
        r2 = api_admin.get("/api/v1/almuerzos/saldos/", {"search": "PC-Ana"})
        assert r2.data["count"] == 1
        assert r2.data["results"][0]["nro_tarjeta"] == "PC-Ana"

    def test_resumen_totales_sobre_todos_los_alumnos(self, api_admin, saldos_variados):
        resp = api_admin.get("/api/v1/almuerzos/saldos/resumen/")
        assert resp.status_code == 200
        assert resp.data == {
            "deuda_total": 50000,
            "alumnos_con_deuda": 2,
            "saldo_a_favor_total": 25000,
            "alumnos_con_saldo_a_favor": 1,
        }

    def test_resumen_vacio(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/saldos/resumen/")
        assert resp.data["deuda_total"] == 0
        assert resp.data["alumnos_con_deuda"] == 0

    def test_resumen_de_padre_solo_cuenta_sus_hijos(self, api_padre, saldos_variados, db):
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.clientes.models import Cliente, Hijo
        otro = Cliente.objects.create(
            nombres="Otro", apellidos="Resumen", ruc_ci="5550001",
            tipo_cliente=saldos_variados[0].cliente_responsable.tipo_cliente,
            lista_precio=saldos_variados[0].cliente_responsable.lista_precio,
            limite_credito=Decimal("999999"),
        )
        h = Hijo.objects.create(
            nombre="Ajeno", apellido="R", cliente_responsable=otro,
            grado=saldos_variados[0].grado, activo=True,
        )
        SaldoAlmuerzo.objects.create(hijo=h, saldo_actual=Decimal("-777000"))
        resp = api_padre.get("/api/v1/almuerzos/saldos/resumen/")
        assert resp.data["deuda_total"] == 50000  # no incluye el -777000 ajeno

    def test_sin_n_mas_uno_en_listado(self, api_admin, saldos_variados):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            resp = api_admin.get("/api/v1/almuerzos/saldos/")
        assert resp.data["count"] == 3
        assert len(ctx.captured_queries) <= 6


# ── Advertencia de caja cerrada al cobrar ────────────────────────────────────

@pytest.fixture
def cierre_abierto_cajero(db, usuario_cajero):
    from apps.contabilidad.models import Caja, CierreCaja
    caja = Caja.objects.create(nombre="Caja advertencia")
    return CierreCaja.objects.create(
        caja=caja, empleado=usuario_cajero, estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.mark.django_db
class TestAdvertenciaSinCajaAbierta:

    def _post_efectivo(self, api, hijo):
        return api.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo.pk, "monto_cargado": "20000", "metodo_pago": "EFECTIVO"},
            format="json",
        )

    def test_efectivo_sin_caja_abierta_acredita_y_advierte(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        resp = self._post_efectivo(api_cajero, hijo_almuerzo)
        assert resp.status_code == 201
        assert "caja" in resp.data["advertencia"].lower()
        assert SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo).saldo_actual == Decimal("20000")

    def test_efectivo_con_caja_abierta_no_advierte_y_registra_movimiento(
        self, api_cajero, hijo_almuerzo, cierre_abierto_cajero,
    ):
        from apps.contabilidad.models import MovimientoCaja
        resp = self._post_efectivo(api_cajero, hijo_almuerzo)
        assert resp.status_code == 201
        assert "advertencia" not in resp.data
        assert MovimientoCaja.objects.filter(cierre=cierre_abierto_cajero, monto=Decimal("20000")).count() == 1

    def test_transferencia_pendiente_no_advierte_todavia(self, api_cajero, hijo_almuerzo):
        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_almuerzo.pk, "monto_cargado": "20000", "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201
        assert "advertencia" not in resp.data

    def test_confirmar_sin_caja_abierta_advierte(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        resp = api_cajero.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/confirmar/")
        assert resp.status_code == 200
        assert "caja" in resp.data["advertencia"].lower()

    def test_confirmar_con_caja_abierta_no_advierte(
        self, api_cajero, hijo_almuerzo, cierre_abierto_cajero,
    ):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        recarga = RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        resp = api_cajero.post(f"/api/v1/almuerzos/recargas-saldo/{recarga.pk}/confirmar/")
        assert resp.status_code == 200
        assert "advertencia" not in resp.data

    def test_listado_de_pendientes_filtra_por_estado(self, api_cajero, hijo_almuerzo):
        from apps.almuerzos.models import RecargaSaldoAlmuerzo
        RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            metodo_pago="TRANSFERENCIA", estado=RecargaSaldoAlmuerzo.Estado.PENDIENTE,
        )
        RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("9000"),
            metodo_pago="EFECTIVO", estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
        )
        resp = api_cajero.get("/api/v1/almuerzos/recargas-saldo/", {"estado": "PENDIENTE"})
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["hijo_nombre"]
