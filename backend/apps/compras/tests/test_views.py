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
