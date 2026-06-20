"""Tests para apps.compras.views — ViewSets de proveedores, compras, pagos, etc."""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.fixture
def api(usuario_cajero):
    client = APIClient()
    client.force_authenticate(user=usuario_cajero)
    return client


@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(ruc="80002001-2", razon_social="Prov. View Test")


@pytest.fixture
def compra_contado(db, proveedor, usuario_cajero, producto):
    from apps.compras.services import CompraService
    return CompraService.registrar_compra(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago="CONTADO",
        items=[{
            "producto": producto,
            "cantidad": Decimal("2"),
            "costo_unitario": Decimal("5000"),
        }],
    )


@pytest.fixture
def compra_credito(db, proveedor, usuario_cajero, producto):
    from apps.compras.services import CompraService
    return CompraService.registrar_compra(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago="CREDITO",
        items=[{
            "producto": producto,
            "cantidad": Decimal("3"),
            "costo_unitario": Decimal("8000"),
        }],
    )


# ── ProveedorViewSet ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProveedorViewSet:
    def test_list(self, api, proveedor):
        resp = api.get("/api/v1/compras/proveedores/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_create(self, api):
        resp = api.post("/api/v1/compras/proveedores/", {
            "ruc": "80099001-9",
            "razon_social": "Nuevo Proveedor",
        })
        assert resp.status_code == 201

    def test_retrieve(self, api, proveedor):
        resp = api.get(f"/api/v1/compras/proveedores/{proveedor.pk}/")
        assert resp.status_code == 200
        assert resp.data["razon_social"] == "Prov. View Test"

    def test_sin_auth_retorna_401(self, proveedor):
        resp = APIClient().get("/api/v1/compras/proveedores/")
        assert resp.status_code == 401


# ── CuentaCorrienteProveedorViewSet ────────────────────────────────────────────

@pytest.mark.django_db
class TestCuentaCorrienteViewSet:
    def test_list(self, api, proveedor, usuario_cajero):
        from apps.compras.models import CuentaCorrienteProveedor
        CuentaCorrienteProveedor.objects.create(
            proveedor=proveedor,
            tipo=CuentaCorrienteProveedor.Tipo.DEBITO,
            monto=Decimal("100000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        resp = api.get("/api/v1/compras/cuentas-corrientes/")
        assert resp.status_code == 200


# ── CompraViewSet ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompraViewSet:
    def test_list_con_queryset_anotado(self, api, compra_contado):
        resp = api.get("/api/v1/compras/compras/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_retrieve(self, api, compra_contado):
        resp = api.get(f"/api/v1/compras/compras/{compra_contado.pk}/")
        assert resp.status_code == 200
        assert "saldo_pendiente" in resp.data

    def test_confirmar_entrega_contado_retorna_400(self, api, compra_contado):
        resp = api.post(f"/api/v1/compras/compras/{compra_contado.pk}/confirmar-entrega/")
        assert resp.status_code == 400
        assert "crédito" in resp.data["error"]

    def test_confirmar_entrega_credito_ok(self, api, compra_credito):
        from apps.compras.models import Compra
        resp = api.post(f"/api/v1/compras/compras/{compra_credito.pk}/confirmar-entrega/")
        assert resp.status_code == 200
        compra_credito.refresh_from_db()
        assert compra_credito.estado_entrega == Compra.EstadoEntrega.RECIBIDA

    def test_confirmar_entrega_ya_recibida_retorna_400(self, api, compra_credito):
        api.post(f"/api/v1/compras/compras/{compra_credito.pk}/confirmar-entrega/")
        resp = api.post(f"/api/v1/compras/compras/{compra_credito.pk}/confirmar-entrega/")
        assert resp.status_code == 400


# ── Otros ViewSets ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOtrosViewSets:
    def test_detalles_compra_list(self, api, compra_contado):
        resp = api.get("/api/v1/compras/detalles-compra/")
        assert resp.status_code == 200

    def test_pagos_list(self, api):
        resp = api.get("/api/v1/compras/pagos/")
        assert resp.status_code == 200

    def test_aplicaciones_pago_list(self, api):
        resp = api.get("/api/v1/compras/aplicaciones-pago/")
        assert resp.status_code == 200

    def test_notas_credito_list(self, api):
        resp = api.get("/api/v1/compras/notas-credito/")
        assert resp.status_code == 200

    def test_detalles_nc_list(self, api):
        resp = api.get("/api/v1/compras/detalles-nc/")
        assert resp.status_code == 200


# ── OrdenCompraViewSet ─────────────────────────────────────────────────────────

@pytest.fixture
def api_admin(usuario_admin):
    client = APIClient()
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def orden_borrador(db, proveedor, usuario_cajero, producto):
    from apps.compras.models import DetalleOrdenCompra, OrdenCompra
    orden = OrdenCompra.objects.create(
        proveedor=proveedor,
        creado_por=usuario_cajero,
        tipo_pago=OrdenCompra.TipoPago.CONTADO,
        estado=OrdenCompra.Estado.BORRADOR,
        monto_total=Decimal("10000"),
    )
    DetalleOrdenCompra.objects.create(
        orden=orden,
        producto=producto,
        cantidad=Decimal("2"),
        costo_unitario=Decimal("5000"),
        subtotal=Decimal("10000"),
    )
    return orden


@pytest.fixture
def orden_pendiente(db, orden_borrador, api_admin):
    api_admin.post(f"/api/v1/compras/ordenes/{orden_borrador.pk}/submit/")
    orden_borrador.refresh_from_db()
    return orden_borrador


@pytest.fixture
def orden_aprobada(db, orden_pendiente, api_admin):
    api_admin.post(f"/api/v1/compras/ordenes/{orden_pendiente.pk}/aprobar/")
    orden_pendiente.refresh_from_db()
    return orden_pendiente


@pytest.mark.django_db
class TestOrdenCompraViewSet:

    def test_crear_orden_borrador(self, api_admin, proveedor, producto):
        resp = api_admin.post("/api/v1/compras/ordenes/", {
            "proveedor": proveedor.pk,
            "tipo_pago": "CONTADO",
            "items": [{"producto": producto.pk, "cantidad": "1", "costo_unitario": "5000"}],
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["estado"] == "BORRADOR"

    def test_list_ordenes(self, api_admin, orden_borrador):
        resp = api_admin.get("/api/v1/compras/ordenes/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_submit_borrador_a_pendiente(self, api, orden_borrador):
        resp = api.post(f"/api/v1/compras/ordenes/{orden_borrador.pk}/submit/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "PENDIENTE"

    def test_submit_sin_detalles_retorna_400(self, api, proveedor, usuario_cajero):
        from apps.compras.models import OrdenCompra
        orden_vacia = OrdenCompra.objects.create(
            proveedor=proveedor, creado_por=usuario_cajero,
            tipo_pago=OrdenCompra.TipoPago.CONTADO,
            estado=OrdenCompra.Estado.BORRADOR, monto_total=Decimal("0"),
        )
        resp = api.post(f"/api/v1/compras/ordenes/{orden_vacia.pk}/submit/")
        assert resp.status_code == 400
        assert "producto" in resp.data["error"].lower()

    def test_submit_no_borrador_retorna_400(self, api, orden_pendiente):
        resp = api.post(f"/api/v1/compras/ordenes/{orden_pendiente.pk}/submit/")
        assert resp.status_code == 400

    def test_aprobar_pendiente_admin(self, api_admin, orden_pendiente):
        resp = api_admin.post(f"/api/v1/compras/ordenes/{orden_pendiente.pk}/aprobar/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "APROBADA"

    def test_aprobar_cajero_retorna_403(self, api, orden_pendiente):
        resp = api.post(f"/api/v1/compras/ordenes/{orden_pendiente.pk}/aprobar/")
        assert resp.status_code == 403

    def test_rechazar_pendiente_con_motivo(self, api_admin, orden_pendiente):
        resp = api_admin.post(
            f"/api/v1/compras/ordenes/{orden_pendiente.pk}/rechazar/",
            {"motivo": "Precio fuera de rango"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "RECHAZADA"
        assert resp.data["motivo_rechazo"] == "Precio fuera de rango"

    def test_rechazar_sin_motivo_retorna_400(self, api_admin, orden_pendiente):
        resp = api_admin.post(
            f"/api/v1/compras/ordenes/{orden_pendiente.pk}/rechazar/",
            {"motivo": ""},
            format="json",
        )
        assert resp.status_code == 400

    def test_convertir_aprobada_crea_compra(self, api_admin, orden_aprobada):
        from apps.compras.models import Compra
        resp = api_admin.post(f"/api/v1/compras/ordenes/{orden_aprobada.pk}/convertir/")
        assert resp.status_code == 200
        assert resp.data["orden"]["estado"] == "CONVERTIDA"
        compra_id = resp.data["compra_id"]
        assert Compra.objects.filter(pk=compra_id).exists()

    def test_convertir_cajero_retorna_403(self, api, orden_aprobada):
        resp = api.post(f"/api/v1/compras/ordenes/{orden_aprobada.pk}/convertir/")
        assert resp.status_code == 403
