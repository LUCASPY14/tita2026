"""Tests de emisión y anulación de notas de crédito de venta."""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.ventas.services import VentaService
from apps.ventas.models import NotaCredito


@pytest.fixture
def api_admin(usuario_admin):
    client = APIClient()
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def api_cajero(usuario_cajero):
    client = APIClient()
    client.force_authenticate(user=usuario_cajero)
    return client


@pytest.mark.django_db
class TestEmitirNotaCreditoService:

    def test_emitir_con_items_calcula_monto_y_revierte_stock(
        self, cliente, usuario_cajero, producto, stock_producto
    ):
        from apps.inventario.models import Stock

        nc = VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-001", motivo="Devolución por producto vencido",
            items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        )
        assert nc.monto_total == Decimal("6000")
        assert nc.estado == NotaCredito.Estado.EMITIDA
        assert nc.detalles.count() == 1

        stock = Stock.objects.get(producto=producto)
        assert stock.cantidad == Decimal("52")  # 50 + 2 devueltas

    def test_emitir_sin_items_usa_monto_explicito(self, cliente, usuario_cajero):
        nc = VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-002", motivo="Descuento comercial",
            monto_total=Decimal("15000"),
        )
        assert nc.monto_total == Decimal("15000")
        assert nc.detalles.count() == 0

    def test_emitir_sin_items_ni_monto_falla(self, cliente, usuario_cajero):
        with pytest.raises(ValidationError, match="ítems o un monto_total"):
            VentaService.emitir_nota_credito(
                cliente=cliente, empleado=usuario_cajero,
                nro_nota_credito="NC-003", motivo="Sin datos",
            )

    def test_emitir_reduce_deuda_en_cuenta_corriente(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente

        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("20000"), creado_por=usuario_cajero,
        )
        VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-004", motivo="Descuento",
            monto_total=Decimal("5000"),
        )
        ultimo = CuentaCorrienteCliente.objects.filter(cliente=cliente).order_by("-id_movimiento_cc").first()
        assert ultimo.tipo == CuentaCorrienteCliente.Tipo.CREDITO
        assert ultimo.saldo_resultante == Decimal("15000")
        assert ultimo.origen == CuentaCorrienteCliente.Origen.CANTINA

    def test_nro_nota_credito_duplicado_falla(self, cliente, usuario_cajero):
        VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-DUP", motivo="Primera", monto_total=Decimal("1000"),
        )
        with pytest.raises(ValidationError, match="ya fue registrada"):
            VentaService.emitir_nota_credito(
                cliente=cliente, empleado=usuario_cajero,
                nro_nota_credito="NC-DUP", motivo="Segunda", monto_total=Decimal("2000"),
            )


@pytest.mark.django_db
class TestAnularNotaCreditoService:

    def test_anular_revierte_cc_y_stock(self, cliente, usuario_cajero, usuario_admin, producto, stock_producto):
        from apps.inventario.models import Stock
        from apps.clientes.models import CuentaCorrienteCliente

        nc = VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-ANU", motivo="Devolución",
            items=[{"producto": producto, "cantidad": Decimal("3"), "precio_unitario": Decimal("3000")}],
        )
        assert Stock.objects.get(producto=producto).cantidad == Decimal("53")

        nc = VentaService.anular_nota_credito(nc, anulado_por=usuario_admin)
        assert nc.estado == NotaCredito.Estado.ANULADA
        assert Stock.objects.get(producto=producto).cantidad == Decimal("50")

        ultimo_cc = CuentaCorrienteCliente.objects.filter(cliente=cliente).order_by("-id_movimiento_cc").first()
        assert ultimo_cc.tipo == CuentaCorrienteCliente.Tipo.DEBITO
        assert ultimo_cc.saldo_resultante == Decimal("0")
        assert ultimo_cc.origen == CuentaCorrienteCliente.Origen.CANTINA

    def test_anular_dos_veces_falla(self, cliente, usuario_cajero, usuario_admin):
        nc = VentaService.emitir_nota_credito(
            cliente=cliente, empleado=usuario_cajero,
            nro_nota_credito="NC-ANU2", motivo="Descuento", monto_total=Decimal("1000"),
        )
        VentaService.anular_nota_credito(nc, anulado_por=usuario_admin)
        with pytest.raises(ValidationError, match="ya está anulada"):
            VentaService.anular_nota_credito(nc, anulado_por=usuario_admin)


@pytest.mark.django_db
class TestNotaCreditoViewSet:

    def test_emitir_via_api_sin_items(self, api_cajero, cliente):
        resp = api_cajero.post("/api/v1/ventas/notas-credito/", {
            "cliente": cliente.pk, "nro_nota_credito": "NC-API-1",
            "motivo": "Descuento comercial", "monto_total": 8000,
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["monto_total"] == "8000"
        assert resp.data["estado"] == "EMITIDA"

    def test_emitir_via_api_con_items(self, api_cajero, cliente, producto, stock_producto):
        resp = api_cajero.post("/api/v1/ventas/notas-credito/", {
            "cliente": cliente.pk, "nro_nota_credito": "NC-API-2",
            "motivo": "Devolución", "detalles": [
                {"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"},
            ],
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["monto_total"] == "3000"
        assert len(resp.data["detalles"]) == 1

    def test_emitir_sin_cliente_falla_400(self, api_cajero):
        resp = api_cajero.post("/api/v1/ventas/notas-credito/", {
            "nro_nota_credito": "NC-API-3", "motivo": "x", "monto_total": 1000,
        }, format="json")
        assert resp.status_code == 400

    def test_anular_requiere_admin(self, api_cajero, cliente):
        create_resp = api_cajero.post("/api/v1/ventas/notas-credito/", {
            "cliente": cliente.pk, "nro_nota_credito": "NC-API-4",
            "motivo": "Descuento", "monto_total": 1000,
        }, format="json")
        nc_id = create_resp.data["id_nota_credito"]
        resp = api_cajero.post(f"/api/v1/ventas/notas-credito/{nc_id}/anular/")
        assert resp.status_code == 403

    def test_anular_via_api_como_admin(self, api_admin, api_cajero, cliente):
        create_resp = api_cajero.post("/api/v1/ventas/notas-credito/", {
            "cliente": cliente.pk, "nro_nota_credito": "NC-API-5",
            "motivo": "Descuento", "monto_total": 1000,
        }, format="json")
        nc_id = create_resp.data["id_nota_credito"]
        resp = api_admin.post(f"/api/v1/ventas/notas-credito/{nc_id}/anular/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "ANULADA"
