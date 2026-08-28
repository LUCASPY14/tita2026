"""Tests para la impresión de facturas sobre talonario preimpreso:
condición de venta real, tabla de líneas desde DetalleVenta, y total en
letras (ver factura_print.html / FacturaViewSet.pdf)."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.contabilidad.models import Factura
from apps.core.models import CargaSaldo
from apps.almuerzos.models import RecargaSaldoAlmuerzo
from apps.ventas.models import DetalleVenta, Venta


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def venta_con_detalle(db, cliente, usuario_cajero, producto):
    venta = Venta.objects.create(
        cliente=cliente, cajero=usuario_cajero, tipo=Venta.Tipo.CREDITO,
        monto_total=Decimal("6000"),
        monto_gravada_10=Decimal("5455"), iva_10=Decimal("545"),
    )
    DetalleVenta.objects.create(
        venta=venta, producto=producto, cantidad=Decimal("2.000"),
        precio_unitario=Decimal("3000"), subtotal=Decimal("6000"),
        monto_gravada_10=Decimal("5455"), iva_10=Decimal("545"),
    )
    return venta


@pytest.fixture
def factura_con_venta(db, cliente, venta_con_detalle):
    return Factura.objects.create(
        nro_factura="001-001-0000002",
        monto_total=Decimal("6000"),
        iva_10=Decimal("545"),
        cliente=cliente,
        venta=venta_con_detalle,
    )


@pytest.mark.django_db
class TestFacturaPrintLineasYCondicion:

    def test_factura_con_venta_imprime_linea_de_producto_y_condicion_credito(
        self, api_admin, factura_con_venta, producto
    ):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura_con_venta.pk}/pdf/")
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert producto.descripcion in content
        assert "CRÉDITO" in content
        # Total 6.000 Gs → "SEIS MIL GUARANÍES"
        assert "SEIS MIL GUARANÍES" in content

    def test_factura_sin_venta_condicion_contado_por_defecto(self, api_admin, factura):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert "CONTADO" in content

    def test_factura_de_carga_a_cuenta_corriente_muestra_credito(
        self, api_admin, factura, cliente
    ):
        CargaSaldo.objects.create(
            cliente_origen=cliente,
            monto_cargado=Decimal("50000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
            metodo_pago="CUENTA_CORRIENTE",
            factura=factura,
        )
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert "CRÉDITO" in resp.content.decode("utf-8")

    def test_linea_de_venta_gravada_al_5_por_ciento_va_en_columna_5(
        self, api_admin, cliente, usuario_cajero, producto
    ):
        venta = Venta.objects.create(
            cliente=cliente, cajero=usuario_cajero, tipo=Venta.Tipo.CONTADO,
            monto_total=Decimal("2100"), monto_gravada_5=Decimal("2000"), iva_5=Decimal("100"),
        )
        DetalleVenta.objects.create(
            venta=venta, producto=producto, cantidad=Decimal("1.000"),
            precio_unitario=Decimal("2100"), subtotal=Decimal("2100"),
            monto_gravada_5=Decimal("2000"), iva_5=Decimal("100"),
        )
        factura = Factura.objects.create(
            nro_factura="001-001-0000003", monto_total=Decimal("2100"),
            iva_5=Decimal("100"), cliente=cliente, venta=venta,
        )
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert 'pf-col-5' in resp.content.decode("utf-8")

    def test_factura_sin_venta_gravada_al_5_por_ciento_va_en_columna_5(self, api_admin, cliente):
        factura = Factura.objects.create(
            nro_factura="001-001-0000004", monto_total=Decimal("2100"),
            iva_5=Decimal("100"), cliente=cliente,
        )
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert 'pf-col-5' in resp.content.decode("utf-8")

    def test_factura_de_recarga_almuerzo_muestra_servicio_de_almuerzos(self, api_admin, cliente, factura):
        from apps.clientes.models import Hijo
        hijo = Hijo.objects.create(nombre="Sofía", apellido="García", cliente_responsable=cliente)
        RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo, monto_cargado=Decimal("50000"),
            estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
            factura=factura,
        )
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        content = resp.content.decode("utf-8")
        assert "Servicio de almuerzos" in content
        assert "Servicios" not in content  # ya no debe caer al genérico


@pytest.fixture
def factura(db, cliente):
    return Factura.objects.create(
        nro_factura="001-001-0000099",
        monto_total=Decimal("50000"),
        cliente=cliente,
    )
