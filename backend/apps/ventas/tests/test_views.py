"""
Tests de vistas de ventas.
Cubre: VentaViewSet (list, anular), PagoVenta (bloqueo en estado final),
ReporteVentasProductoView y ReporteVentasCajeroView.
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
    return Caja.objects.create(nombre="Caja Principal Test", activo=True)


@pytest.fixture
def cierre_cajero(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def venta_activa(db, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, cierre_cajero):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=usuario_cajero,
        tipo="CONTADO",
        medio_pago=medio_pago_efectivo,
        items=[{"producto": producto, "cantidad": Decimal("2"), "precio_unitario": Decimal("3000")}],
        cierre_caja=cierre_cajero,
    )


@pytest.fixture
def pago_conciliado(db, cliente, venta_activa, medio_pago_efectivo, usuario_cajero):
    from apps.ventas.models import PagoVenta
    return PagoVenta.objects.create(
        cliente=cliente,
        venta=venta_activa,
        monto=Decimal("6000"),
        medio_pago=medio_pago_efectivo,
        cajero=usuario_cajero,
        estado=PagoVenta.Estado.CONCILIADO,
    )


# ── VentaViewSet ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVentaViewSet:

    def test_list_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/ventas/ventas/")
        assert resp.status_code in (401, 403)

    def test_list_cajero_puede_listar(self, api_cajero):
        resp = api_cajero.get("/api/v1/ventas/ventas/")
        assert resp.status_code == 200

    def test_list_admin_puede_listar(self, api_admin):
        resp = api_admin.get("/api/v1/ventas/ventas/")
        assert resp.status_code == 200

    def test_create_ok(self, api_cajero, cliente, producto, medio_pago_efectivo, cierre_cajero, stock_producto):
        resp = api_cajero.post(
            "/api/v1/ventas/ventas/",
            {
                "cliente": cliente.pk,
                "tipo": "CONTADO",
                "medio_pago": medio_pago_efectivo.pk,
                "monto_total": 6000,
                "items": [{"producto": producto.pk, "cantidad": "2", "precio_unitario": "3000"}],
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_create_sin_caja_abierta_falla(self, api_cajero, cliente, producto, medio_pago_efectivo, stock_producto):
        resp = api_cajero.post(
            "/api/v1/ventas/ventas/",
            {
                "cliente": cliente.pk,
                "tipo": "CONTADO",
                "medio_pago": medio_pago_efectivo.pk,
                "monto_total": 6000,
                "items": [{"producto": producto.pk, "cantidad": "2", "precio_unitario": "3000"}],
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_anular_admin_ok(self, api_admin, venta_activa):
        resp = api_admin.post(f"/api/v1/ventas/ventas/{venta_activa.pk}/anular/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "ANULADA"

    def test_anular_requiere_admin(self, api_cajero, venta_activa):
        resp = api_cajero.post(f"/api/v1/ventas/ventas/{venta_activa.pk}/anular/")
        assert resp.status_code in (401, 403)

    def test_anular_dos_veces_falla(self, api_admin, venta_activa):
        api_admin.post(f"/api/v1/ventas/ventas/{venta_activa.pk}/anular/")
        resp = api_admin.post(f"/api/v1/ventas/ventas/{venta_activa.pk}/anular/")
        assert resp.status_code == 400

    def test_detail_retorna_venta(self, api_cajero, venta_activa):
        resp = api_cajero.get(f"/api/v1/ventas/ventas/{venta_activa.pk}/")
        assert resp.status_code == 200
        assert resp.data["id_venta"] == venta_activa.pk


# ── PagoVentaViewSet ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPagoVentaViewSet:

    def test_no_puede_editar_pago_conciliado(self, api_cajero, pago_conciliado):
        resp = api_cajero.patch(
            f"/api/v1/ventas/pagos/{pago_conciliado.pk}/",
            {"monto": "9000"},
            format="json",
        )
        assert resp.status_code == 400

    def test_no_puede_eliminar_pago_conciliado(self, api_cajero, pago_conciliado):
        resp = api_cajero.delete(f"/api/v1/ventas/pagos/{pago_conciliado.pk}/")
        assert resp.status_code == 400

    def test_lista_pagos(self, api_cajero):
        resp = api_cajero.get("/api/v1/ventas/pagos/")
        assert resp.status_code == 200


# ── ReporteVentasProductoView ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteVentasProducto:

    def test_sin_params_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/ventas/reporte-productos/")
        assert resp.status_code == 400

    def test_con_params_retorna_json(self, api_admin, venta_activa):
        resp = api_admin.get(
            "/api/v1/ventas/reporte-productos/",
            {"desde": "2020-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert "productos" in resp.data
        assert "total_monto" in resp.data

    def test_formato_csv(self, api_admin, venta_activa):
        resp = api_admin.get(
            "/api/v1/ventas/reporte-productos/",
            {"desde": "2020-01-01", "hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE" in resp.content

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/ventas/reporte-productos/")
        assert resp.status_code in (401, 403)


# ── ReporteVentasCajeroView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteVentasCajero:

    def test_sin_params_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/ventas/reporte-cajeros/")
        assert resp.status_code == 400

    def test_con_params_retorna_json(self, api_admin, venta_activa):
        resp = api_admin.get(
            "/api/v1/ventas/reporte-cajeros/",
            {"desde": "2020-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert "cajeros" in resp.data

    def test_formato_csv(self, api_admin, venta_activa):
        resp = api_admin.get(
            "/api/v1/ventas/reporte-cajeros/",
            {"desde": "2020-01-01", "hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]


# ── DetalleVentaViewSet ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDetalleVentaViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/ventas/detalles-venta/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/ventas/detalles-venta/")
        assert resp.status_code in (401, 403)


# ── AplicacionPagoViewSet ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAplicacionPagoViewSet:

    def test_list_ok(self, api_admin):
        resp = api_admin.get("/api/v1/ventas/aplicaciones-pago/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/ventas/aplicaciones-pago/")
        assert resp.status_code in (401, 403)


# ── NotaCreditoViewSet ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotaCreditoViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/ventas/notas-credito/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/ventas/notas-credito/")
        assert resp.status_code in (401, 403)


# ── CondicionVentaViewSet ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCondicionVentaViewSet:

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/ventas/condiciones-venta/")
        assert resp.status_code == 200

    def test_create_ok(self, api_admin):
        resp = api_admin.post(
            "/api/v1/ventas/condiciones-venta/",
            {"nombre": "Contado inmediato", "plazo_dias": 0},
            format="json",
        )
        assert resp.status_code == 201


# ── Cobertura adicional ───────────────────────────────────────────────────────

@pytest.fixture
def hijo_view(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Lucas", apellido="Test", cliente_responsable=cliente, activo=True
    )


@pytest.fixture
def tarjeta_de_hijo(db, hijo_view):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(nro_tarjeta="TARJ-ALERG-1", hijo=hijo_view, saldo_actual=Decimal("50000"))


@pytest.fixture
def pago_pendiente(db, cliente, venta_activa, medio_pago_efectivo, usuario_cajero):
    from apps.ventas.models import PagoVenta
    return PagoVenta.objects.create(
        cliente=cliente,
        venta=venta_activa,
        monto=Decimal("6000"),
        medio_pago=medio_pago_efectivo,
        cajero=usuario_cajero,
        estado=PagoVenta.Estado.PENDIENTE,
    )


@pytest.mark.django_db
class TestVentaViewSetCoberturaExtra:

    def test_create_con_hijo_ejecuta_verificacion_alergenos(
        self, api_cajero, cliente, producto, medio_pago_efectivo,
        cierre_cajero, stock_producto, hijo_view
    ):
        """POST con hijo → ejecuta verificar_alergenos_venta (líneas 73-78 views.py)."""
        from unittest.mock import patch
        with patch("apps.almuerzos.validators.verificar_alergenos_venta", return_value=[]):
            resp = api_cajero.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente.pk,
                    "hijo": hijo_view.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_efectivo.pk,
                    "monto_total": 3000,
                    "items": [{"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"}],
                },
                format="json",
            )
        assert resp.status_code == 201

    def test_create_con_hijo_con_alergenos_bloquea_sin_forzar(
        self, api_cajero, cliente, producto, medio_pago_efectivo,
        cierre_cajero, stock_producto, hijo_view
    ):
        """POST con hijo + alergenos, sin forzar_alergenos → 400, no crea la venta."""
        from unittest.mock import patch
        from apps.ventas.models import Venta
        with patch(
            "apps.almuerzos.validators.verificar_alergenos_venta",
            return_value=[{"alergeno": "Gluten"}],
        ):
            resp = api_cajero.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente.pk,
                    "hijo": hijo_view.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_efectivo.pk,
                    "monto_total": 3000,
                    "items": [{"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"}],
                },
                format="json",
            )
        assert resp.status_code == 400
        assert resp.data["advertencias_alergenos"] == [{"alergeno": "Gluten"}]
        assert Venta.objects.count() == 0

    def test_create_con_hijo_con_alergenos_forzar_true_crea_la_venta(
        self, api_cajero, cliente, producto, medio_pago_efectivo,
        cierre_cajero, stock_producto, hijo_view
    ):
        """POST con hijo + alergenos + forzar_alergenos=true → crea la venta e incluye la advertencia en la respuesta."""
        from unittest.mock import patch
        with patch(
            "apps.almuerzos.validators.verificar_alergenos_venta",
            return_value=[{"alergeno": "Gluten"}],
        ):
            resp = api_cajero.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente.pk,
                    "hijo": hijo_view.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_efectivo.pk,
                    "monto_total": 3000,
                    "items": [{"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"}],
                    "forzar_alergenos": True,
                },
                format="json",
            )
        assert resp.status_code == 201
        assert resp.data["advertencias_alergenos"] == [{"alergeno": "Gluten"}]

    def test_venta_con_tarjeta_sin_hijo_explicito_igual_verifica_alergenos(
        self, api_cajero, cliente, producto, medio_pago_efectivo,
        cierre_cajero, stock_producto, tarjeta_de_hijo
    ):
        """La mayoría de las ventas de ModoRecreo no mandan 'hijo' explícito —
        viaja implícito en la tarjeta escaneada. El chequeo de alérgenos debe
        igual dispararse, resolviendo el hijo desde la tarjeta."""
        from unittest.mock import patch
        with patch(
            "apps.almuerzos.validators.verificar_alergenos_venta",
            return_value=[{"alergeno": "Maní"}],
        ) as mock_verificar:
            resp = api_cajero.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente.pk,
                    "tarjeta": tarjeta_de_hijo.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_efectivo.pk,
                    "monto_total": 3000,
                    "items": [{"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"}],
                },
                format="json",
            )
        assert resp.status_code == 400
        assert resp.data["advertencias_alergenos"] == [{"alergeno": "Maní"}]
        mock_verificar.assert_called_once()
        assert mock_verificar.call_args.args[0] == tarjeta_de_hijo.hijo

    def test_anular_excepcion_generica_retorna_400_con_mensaje(
        self, api_admin, venta_activa
    ):
        """VentaService.anular_venta lanza Exception genérica → 400 con error (línea 97)."""
        from unittest.mock import patch
        with patch(
            "apps.ventas.views.VentaService.anular_venta",
            side_effect=Exception("fallo inesperado"),
        ):
            resp = api_admin.post(f"/api/v1/ventas/ventas/{venta_activa.pk}/anular/")
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_create_producto_inexistente_en_items_se_ignora(
        self, api_cajero, cliente, producto, medio_pago_efectivo,
        cierre_cajero, stock_producto
    ):
        """Item con producto_id inexistente se salta con continue (línea 126)."""
        resp = api_cajero.post(
            "/api/v1/ventas/ventas/",
            {
                "cliente": cliente.pk,
                "tipo": "CONTADO",
                "medio_pago": medio_pago_efectivo.pk,
                "monto_total": 3000,
                "items": [
                    {"producto": producto.pk, "cantidad": "1", "precio_unitario": "3000"},
                    {"producto": 99999, "cantidad": "1", "precio_unitario": "3000"},
                ],
            },
            format="json",
        )
        assert resp.status_code == 201


@pytest.mark.django_db
class TestPagoVentaViewSetCoberturaExtra:

    def test_actualizar_pago_pendiente_ok(self, api_cajero, pago_pendiente):
        """PATCH sobre pago en PENDIENTE ejecuta serializer.save() (línea 170 views.py)."""
        resp = api_cajero.patch(
            f"/api/v1/ventas/pagos/{pago_pendiente.pk}/",
            {"referencia": "REF-UPDATED"},
            format="json",
        )
        assert resp.status_code == 200

    def test_eliminar_pago_pendiente_ok(self, api_cajero, pago_pendiente):
        """DELETE sobre pago en PENDIENTE ejecuta super().perform_destroy() (línea 178)."""
        resp = api_cajero.delete(f"/api/v1/ventas/pagos/{pago_pendiente.pk}/")
        assert resp.status_code == 204
