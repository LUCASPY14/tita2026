"""
Tests para actions de VentasViewSet no cubiertas:
- cancelar   (lines 718-742)
- sin_facturar (lines 744-778)
- efectividad_promociones (lines 1100-1196)

Usa fixtures globales de conftest.py: authenticated_client, cliente_test,
empleado_test, medio_pago_efectivo.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from apps.ventas.models import Promociones, Ventas


# ============================================================================
# cancelar
# ============================================================================

@pytest.mark.django_db
class TestCancelarAction:
    """Tests para POST /api/v1/ventas/{id}/cancelar/"""

    def _create_venta(self, cliente, empleado, medio_pago, estado="Activa"):
        return Ventas.objects.create(
            id_cliente=cliente,
            id_empleado_cajero=empleado,
            id_medio_pago=medio_pago,
            monto_total=Decimal("50000.00"),
            tipo_venta="Contado",
            estado_pago="Pagada",
            estado=estado,
        )

    def test_cancelar_venta_activa_exitoso(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        venta = self._create_venta(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-cancelar", kwargs={"pk": venta.id_venta})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "cancelada" in response.data["mensaje"].lower()
        venta.refresh_from_db()
        assert venta.estado == "Cancelada"

    def test_cancelar_venta_ya_cancelada(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        venta = self._create_venta(
            cliente_test, empleado_test, medio_pago_efectivo, estado="Cancelada"
        )
        url = reverse("ventas-cancelar", kwargs={"pk": venta.id_venta})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cancelada" in response.data["error"].lower()

    def test_cancelar_venta_anulada(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        venta = self._create_venta(
            cliente_test, empleado_test, medio_pago_efectivo, estado="Anulada"
        )
        url = reverse("ventas-cancelar", kwargs={"pk": venta.id_venta})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "anulada" in response.data["error"].lower()

    def test_cancelar_sin_autenticacion(
        self, api_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        venta = self._create_venta(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-cancelar", kwargs={"pk": venta.id_venta})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cancelar_venta_no_existente(self, authenticated_client):
        url = reverse("ventas-cancelar", kwargs={"pk": 999999})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# sin_facturar
# ============================================================================

@pytest.mark.django_db
class TestSinFacturarAction:
    """Tests para GET /api/v1/ventas/sin_facturar/"""

    def _create_venta_sin_factura(self, cliente, empleado, medio_pago, genera=True):
        return Ventas.objects.create(
            id_cliente=cliente,
            id_empleado_cajero=empleado,
            id_medio_pago=medio_pago,
            monto_total=Decimal("75000.00"),
            tipo_venta="Contado",
            estado_pago="pagada",
            estado="activa",
            genera_factura_legal=genera,
            id_documento=None,
        )

    def test_listar_ventas_sin_facturar(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        self._create_venta_sin_factura(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "results" in response.data
        assert response.data["count"] >= 1

    def test_ventas_con_genera_factura_false_no_aparecen(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        self._create_venta_sin_factura(
            cliente_test, empleado_test, medio_pago_efectivo, genera=False
        )
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Ventas sin genera_factura_legal=True no deben aparecer
        for r in response.data.get("results", []):
            assert r.get("genera_factura_legal", True) is True

    def test_sin_facturar_filtra_por_cliente(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        self._create_venta_sin_factura(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url, {"id_cliente": cliente_test.id_cliente})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_sin_facturar_filtra_cliente_sin_ventas(
        self, authenticated_client
    ):
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url, {"id_cliente": 99999})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_sin_facturar_filtra_por_fecha_desde(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        self._create_venta_sin_factura(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url, {"fecha_desde": "2025-01-01"})

        assert response.status_code == status.HTTP_200_OK

    def test_sin_facturar_filtra_por_fecha_hasta(
        self, authenticated_client, cliente_test, empleado_test, medio_pago_efectivo
    ):
        self._create_venta_sin_factura(cliente_test, empleado_test, medio_pago_efectivo)
        url = reverse("ventas-sin-facturar")
        response = authenticated_client.get(url, {"fecha_hasta": "2099-12-31"})

        assert response.status_code == status.HTTP_200_OK

    def test_sin_facturar_sin_autenticacion(self, api_client):
        url = reverse("ventas-sin-facturar")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# efectividad_promociones (PromocionesViewSet)
# ============================================================================

@pytest.mark.django_db
class TestEfectividadPromocionesAction:
    """Tests para GET /api/v1/ventas/promociones/efectividad/"""

    def test_efectividad_sin_fechas_retorna_400(self, authenticated_client):
        url = reverse("promociones-reporte-efectividad")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fecha" in response.data["error"].lower()

    def test_efectividad_con_fechas_validas(self, authenticated_client):
        url = reverse("promociones-reporte-efectividad")
        response = authenticated_client.get(
            url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "periodo" in response.data
        assert "resumen" in response.data
        assert "por_promocion" in response.data

    def test_efectividad_periodo_mensual(self, authenticated_client):
        url = reverse("promociones-reporte-efectividad")
        response = authenticated_client.get(
            url,
            {
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-12-31",
                "periodo": "mensual",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_efectividad_periodo_semanal(self, authenticated_client):
        url = reverse("promociones-reporte-efectividad")
        response = authenticated_client.get(
            url,
            {
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-12-31",
                "periodo": "semanal",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_efectividad_periodo_diario(self, authenticated_client):
        url = reverse("promociones-reporte-efectividad")
        response = authenticated_client.get(
            url,
            {
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-12-31",
                "periodo": "diario",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_efectividad_sin_autenticacion(self, api_client):
        url = reverse("promociones-reporte-efectividad")
        response = api_client.get(
            url, {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
