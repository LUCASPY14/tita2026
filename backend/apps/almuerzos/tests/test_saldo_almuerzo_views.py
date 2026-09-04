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
