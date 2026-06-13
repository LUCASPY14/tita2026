"""
Tests extendidos de vistas de contabilidad.
Cubre: mi-caja, registrar-movimiento, arqueo, ReportePeriodoView,
DashboardResumenView, DashboardTendenciaView.
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
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Ext Test", activo=True)


@pytest.fixture
def cierre_abierto(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("50000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


# ── CierreCajaViewSet.mi_caja ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestMiCaja:

    def test_sin_caja_abierta_retorna_null(self, api_cajero):
        resp = api_cajero.get("/api/v1/contabilidad/cierres-caja/mi-caja/")
        assert resp.status_code == 200
        assert resp.data is None

    def test_con_caja_abierta_retorna_cierre(self, api_cajero, cierre_abierto):
        resp = api_cajero.get("/api/v1/contabilidad/cierres-caja/mi-caja/")
        assert resp.status_code == 200
        assert resp.data is not None
        assert resp.data["id"] == cierre_abierto.pk
        assert resp.data["estado"] == "ABIERTO"

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/cierres-caja/mi-caja/")
        assert resp.status_code in (401, 403)


# ── CierreCajaViewSet.registrar_movimiento ────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarMovimiento:

    def test_ingreso_en_caja_abierta(self, api_cajero, cierre_abierto, medio_pago_efectivo):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {
                "tipo": "INGRESO",
                "monto": 20000,
                "medio_pago": medio_pago_efectivo.pk,
                "descripcion": "Cobro manual",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert int(resp.data["monto"]) == 20000

    def test_egreso_en_caja_abierta(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "EGRESO", "monto": 5000, "descripcion": "Retiro"},
            format="json",
        )
        assert resp.status_code == 201

    def test_tipo_invalido_falla(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "INVALIDO", "monto": 1000},
            format="json",
        )
        assert resp.status_code == 400

    def test_caja_cerrada_falla(self, api_cajero, caja, usuario_cajero):
        from apps.contabilidad.models import CierreCaja
        from django.utils import timezone
        cierre = CierreCaja.objects.create(
            caja=caja,
            empleado=usuario_cajero,
            monto_inicial=Decimal("0"),
            estado=CierreCaja.Estado.CERRADO,
            fecha_cierre=timezone.now(),
        )
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre.pk}/registrar-movimiento/",
            {"tipo": "INGRESO", "monto": 1000},
            format="json",
        )
        assert resp.status_code == 400


# ── CierreCajaViewSet.arqueo ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestArqueo:

    def test_arqueo_retorna_estructura(self, api_cajero, cierre_abierto):
        resp = api_cajero.get(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/arqueo/"
        )
        assert resp.status_code == 200
        campos = ["monto_inicial", "efectivo_esperado", "pos_total", "prepago_total",
                  "ingresos_total", "egresos_total", "ingresos_por_medio", "egresos_por_medio"]
        for campo in campos:
            assert campo in resp.data

    def test_arqueo_con_movimientos(self, api_cajero, cierre_abierto, medio_pago_efectivo):
        from apps.contabilidad.models import MovimientoCaja
        MovimientoCaja.objects.create(
            cierre=cierre_abierto,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("30000"),
            medio_pago=medio_pago_efectivo,
        )
        resp = api_cajero.get(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/arqueo/"
        )
        assert resp.status_code == 200
        assert resp.data["ingresos_total"] == 30000
        assert resp.data["efectivo_ingresos"] == 30000


# ── ReportePeriodoView ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReportePeriodo:

    def test_sin_params_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/reportes/")
        assert resp.status_code == 400

    def test_con_params_retorna_estructura(self, api_admin):
        resp = api_admin.get(
            "/api/v1/contabilidad/reportes/",
            {"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert "ventas" in resp.data
        assert "cierres_caja" in resp.data
        assert "periodo" in resp.data

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/reportes/")
        assert resp.status_code in (401, 403)


# ── DashboardResumenView ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardResumen:

    def test_retorna_campos_esperados(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/")
        assert resp.status_code == 200
        for campo in ["ventasHoy", "montoHoy", "clientes", "productos", "stockBajo", "cajasAbiertas"]:
            assert campo in resp.data

    def test_cajero_puede_acceder(self, api_cajero):
        resp = api_cajero.get("/api/v1/contabilidad/dashboard/")
        assert resp.status_code == 200

    def test_anonimo_no_puede_acceder(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/dashboard/")
        assert resp.status_code in (401, 403)

    def test_cajas_abiertas_refleja_estado(self, api_admin, cierre_abierto):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/")
        assert resp.data["cajasAbiertas"] >= 1


# ── DashboardTendenciaView ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardTendencia:

    def test_retorna_lista_de_dias(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/tendencia/", {"dias": 7})
        assert resp.status_code == 200
        datos = resp.data.get("data", resp.data)
        assert isinstance(datos, list)
        assert len(datos) == 7

    def test_default_7_dias(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/tendencia/")
        assert resp.status_code == 200
        datos = resp.data.get("data", resp.data)
        assert len(datos) >= 1

    def test_cada_item_tiene_fecha_y_monto(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/tendencia/", {"dias": 3})
        assert resp.status_code == 200
        datos = resp.data.get("data", resp.data)
        for item in datos:
            assert "fecha" in item
            assert "monto" in item


# ── registrar_movimiento — branches de validación ─────────────────────────────

@pytest.mark.django_db
class TestRegistrarMovimientoValidaciones:

    def test_monto_invalido_falla(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "INGRESO", "monto": "no-es-numero"},
            format="json",
        )
        assert resp.status_code == 400
        assert "Monto inválido" in str(resp.data)

    def test_monto_cero_falla(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "INGRESO", "monto": 0},
            format="json",
        )
        assert resp.status_code == 400

    def test_monto_negativo_falla(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "INGRESO", "monto": -500},
            format="json",
        )
        assert resp.status_code == 400

    def test_medio_pago_inexistente_falla(self, api_cajero, cierre_abierto):
        resp = api_cajero.post(
            f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/registrar-movimiento/",
            {"tipo": "INGRESO", "monto": 1000, "medio_pago": 999999},
            format="json",
        )
        assert resp.status_code == 400
        assert "Medio de pago no encontrado" in str(resp.data)


# ── FacturaViewSet ────────────────────────────────────────────────────────────

@pytest.fixture
def factura(db, cliente):
    from decimal import Decimal
    from apps.contabilidad.models import Factura
    return Factura.objects.create(
        nro_factura="001-001-0000001",
        monto_total=Decimal("50000"),
        cliente=cliente,
    )


@pytest.mark.django_db
class TestFacturaViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/contabilidad/facturas/")
        assert resp.status_code == 200

    def test_create_retorna_405(self, api_admin):
        resp = api_admin.post(
            "/api/v1/contabilidad/facturas/",
            {"nro_factura": "001-001-9999999", "monto_total": 10000},
            format="json",
        )
        assert resp.status_code == 405

    def test_anular_ok(self, api_admin, factura):
        resp = api_admin.post(f"/api/v1/contabilidad/facturas/{factura.pk}/anular/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "ANULADA"

    def test_pdf_retorna_html(self, api_admin, factura):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/facturas/")
        assert resp.status_code in (401, 403)


# ── ReportePeriodo — CSV y cierres cerrados ───────────────────────────────────

@pytest.fixture
def cierre_cerrado_hoy(db, caja, usuario_cajero):
    from decimal import Decimal
    from django.utils import timezone
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("80000"),
        monto_contado_fisico=Decimal("85000"),
        diferencia_efectivo=Decimal("5000"),
        fecha_cierre=timezone.now(),
        estado=CierreCaja.Estado.CERRADO,
    )


@pytest.mark.django_db
class TestReportePeriodoExtendido:

    def test_formato_csv(self, api_admin):
        resp = api_admin.get(
            "/api/v1/contabilidad/reportes/",
            {"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE VENTAS" in resp.content

    def test_cierres_cerrados_incluidos(self, api_admin, cierre_cerrado_hoy):
        resp = api_admin.get(
            "/api/v1/contabilidad/reportes/",
            {"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert len(resp.data["cierres_caja"]) >= 1

    def test_csv_con_cierres(self, api_admin, cierre_cerrado_hoy):
        resp = api_admin.get(
            "/api/v1/contabilidad/reportes/",
            {"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"CIERRES DE CAJA" in resp.content

    def test_csv_con_ventas_incluye_por_tipo(self, api_admin, cliente, usuario_cajero):
        from apps.ventas.models import Venta
        Venta.objects.create(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            monto_total=50000,
        )
        resp = api_admin.get(
            "/api/v1/contabilidad/reportes/",
            {"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"CONTADO" in resp.content


# ── FacturaViewSet.pendiente_facturar ─────────────────────────────────────────

@pytest.fixture
def carga_saldo_confirmada(db, cliente):
    from decimal import Decimal
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        cliente_origen=cliente,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.CONFIRMADA,
    )


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="Gómez",
        cliente_responsable=cliente,
    )


@pytest.fixture
def pago_almuerzo_sin_factura(db, hijo, usuario_cajero):
    from decimal import Decimal
    from apps.almuerzos.models import CuentaAlmuerzoMensual, PagoCuentaAlmuerzo
    cuenta = CuentaAlmuerzoMensual.objects.create(
        hijo=hijo,
        anio=2026,
        mes=6,
        cantidad_almuerzos=20,
        monto_total=Decimal("100000"),
        forma_cobro="EFECTIVO",
    )
    return PagoCuentaAlmuerzo.objects.create(
        cuenta=cuenta,
        monto=Decimal("100000"),
        medio_pago="EFECTIVO",
        registrado_por=usuario_cajero,
    )


@pytest.mark.django_db
class TestPendienteFacturar:

    def test_sin_pendientes_retorna_lista_vacia(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/facturas/pendiente-facturar/")
        assert resp.status_code == 200
        assert resp.data == []

    def test_lista_cargas_pendientes(self, api_admin, carga_saldo_confirmada):
        resp = api_admin.get("/api/v1/contabilidad/facturas/pendiente-facturar/")
        assert resp.status_code == 200
        tipos = [i["tipo"] for i in resp.data]
        assert "CARGA_SALDO" in tipos

    def test_carga_via_tarjeta_muestra_nombre_hijo(self, api_admin, hijo):
        from decimal import Decimal
        from apps.core.models import CargaSaldo, Tarjeta
        tarjeta = Tarjeta.objects.create(nro_tarjeta="TEST0001", hijo=hijo)
        CargaSaldo.objects.create(
            tarjeta=tarjeta,
            cliente_origen=None,
            monto_cargado=Decimal("30000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
        )
        resp = api_admin.get("/api/v1/contabilidad/facturas/pendiente-facturar/")
        assert resp.status_code == 200
        nombres = [i["cliente_nombre"] for i in resp.data]
        assert any("Pedro" in n for n in nombres)

    def test_lista_pagos_almuerzo(self, api_admin, pago_almuerzo_sin_factura):
        resp = api_admin.get("/api/v1/contabilidad/facturas/pendiente-facturar/")
        assert resp.status_code == 200
        tipos = [i["tipo"] for i in resp.data]
        assert "PAGO_ALMUERZO" in tipos

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/facturas/pendiente-facturar/")
        assert resp.status_code in (401, 403)


# ── FacturaViewSet.emitir ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirFactura:

    def test_emite_para_carga_saldo(self, api_admin, carga_saldo_confirmada):
        resp = api_admin.post(
            "/api/v1/contabilidad/facturas/emitir/",
            {
                "tipo": "CARGA_SALDO",
                "origen_id": carga_saldo_confirmada.pk,
                "nro_factura": "001-001-8888888",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["nro_factura"] == "001-001-8888888"

    def test_tipo_invalido_falla(self, api_admin):
        resp = api_admin.post(
            "/api/v1/contabilidad/facturas/emitir/",
            {"tipo": "INVALIDO", "origen_id": 1, "nro_factura": "X"},
            format="json",
        )
        assert resp.status_code == 400


# ── FacturaViewSet.pdf — branch CLIENTE_WEB ───────────────────────────────────

@pytest.fixture
def api_cliente_web(api_client, db):
    from apps.usuarios.models import Usuario
    user = Usuario.objects.create_user(
        email="clienteweb@test.com",
        password="test1234",
        nombre="Web",
        apellido="User",
        rol=Usuario.Rol.CLIENTE_WEB,
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestFacturaPDFClienteWeb:

    def test_cliente_web_sin_cliente_no_puede_ver_ajena(self, api_cliente_web, factura):
        resp = api_cliente_web.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 403


# ── FacturaViewSet.pdf — concepto carga_saldo ────────────────────────────────

@pytest.fixture
def factura_con_carga(db, factura, cliente):
    from decimal import Decimal
    from apps.core.models import CargaSaldo
    CargaSaldo.objects.create(
        cliente_origen=cliente,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.CONFIRMADA,
        factura=factura,
    )
    return factura


@pytest.fixture
def factura_con_pago_almuerzo(db, factura, hijo, usuario_cajero):
    from decimal import Decimal
    from apps.almuerzos.models import CuentaAlmuerzoMensual, PagoCuentaAlmuerzo
    cuenta = CuentaAlmuerzoMensual.objects.create(
        hijo=hijo,
        anio=2026,
        mes=6,
        cantidad_almuerzos=20,
        monto_total=Decimal("100000"),
        forma_cobro="EFECTIVO",
    )
    PagoCuentaAlmuerzo.objects.create(
        cuenta=cuenta,
        monto=Decimal("100000"),
        medio_pago="EFECTIVO",
        registrado_por=usuario_cajero,
        factura=factura,
    )
    return factura


@pytest.mark.django_db
class TestFacturaPDFConcepto:

    def test_pdf_con_carga_saldo_muestra_concepto(self, api_admin, factura_con_carga):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura_con_carga.pk}/pdf/")
        assert resp.status_code == 200
        assert b"Carga de saldo" in resp.content

    def test_pdf_con_pago_almuerzo_muestra_concepto(self, api_admin, factura_con_pago_almuerzo):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura_con_pago_almuerzo.pk}/pdf/")
        assert resp.status_code == 200
        assert b"Pago almuerzo" in resp.content
