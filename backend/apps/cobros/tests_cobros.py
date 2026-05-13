"""
Tests para el módulo de cobros.
Cubre: PagosClientesViewSet (facturas_pendientes, registrar_pago, generar_qr_sipap, CRUD)
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.utils import timezone

import pytest
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.clientes.models import Clientes, TiposCliente
from apps.cobros.models import AplicacionPagosClientes, PagosClientes
from apps.cobros.views import PagosClientesViewSet
from apps.contabilidad.models import Impuestos
from apps.core.models import MediosPago
from apps.productos.models import Categorias, ListasPrecios, Productos, UnidadesMedida
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import Ventas

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rol(nombre="Cajero"):
    rol, _ = Roles.objects.get_or_create(nombre_rol=nombre, defaults={"descripcion": nombre, "estado": True})
    return rol


def _make_empleado(rol, suffix="cob"):
    email = f"cajero_{suffix}@test.com"
    emp, _ = Empleados.objects.get_or_create(
        usuario=f"cajero_{suffix}",
        defaults={
            "nombre": "Juan",
            "apellido": "Cajero",
            "contrasena_hash": "hash",
            "fecha_ingreso": timezone.now(),
            "email": email,
            "id_rol": rol,
            "estado": True,
        },
    )
    return emp


def _make_user(username="cobros_user", email="cajero_cob@test.com", is_staff=True):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"email": email, "is_staff": is_staff},
    )
    if not user.has_usable_password():
        user.set_password("testpass123")
        user.save()
    return user


def _make_cliente(suffix="cob"):
    lista, _ = ListasPrecios.objects.get_or_create(nombre_lista="General", defaults={"estado": True})
    tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo="Regular", defaults={"estado": True})
    cliente, _ = Clientes.objects.get_or_create(
        ruc_ci=f"12345{suffix}",
        defaults={
            "nombres": "Pedro",
            "apellidos": "Test",
            "id_lista": lista,
            "id_tipo_cliente": tipo,
            "estado": True,
        },
    )
    return cliente


def _make_medio_pago(descripcion="Efectivo"):
    mp, _ = MediosPago.objects.get_or_create(descripcion=descripcion, defaults={"estado": True})
    return mp


def _make_venta(cliente, empleado, monto=500_000, saldo=500_000, estado_pago="pendiente"):
    return Ventas.objects.create(
        id_cliente=cliente,
        id_empleado_cajero=empleado,
        monto_total=Decimal(str(monto)),
        saldo_pendiente=Decimal(str(saldo)),
        estado_pago=estado_pago,
        tipo_venta="credito",
        estado="Activa",
    )


# ---------------------------------------------------------------------------
# Setup base class
# ---------------------------------------------------------------------------

class CobrosBaseTest:
    """Fixtures compartidas para todos los tests de cobros."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.factory = APIRequestFactory()
        self.client_api = APIClient()

        self.rol = _make_rol()
        self.empleado = _make_empleado(self.rol)
        self.user = _make_user(email=self.empleado.email)
        self.cliente = _make_cliente()
        self.medio_pago = _make_medio_pago()

        self.client_api.force_authenticate(user=self.user)

    def _get(self, path, data=None):
        req = self.factory.get(path, data or {})
        force_authenticate(req, user=self.user)
        return req

    def _post(self, path, data=None):
        req = self.factory.post(path, data or {}, format="json")
        force_authenticate(req, user=self.user)
        return req

    def _post_as(self, path, user, data=None):
        req = self.factory.post(path, data or {}, format="json")
        force_authenticate(req, user=user)
        return req


# ===========================================================================
# facturas_pendientes
# ===========================================================================

@pytest.mark.django_db
class TestFacturasPendientes(CobrosBaseTest):

    def test_sin_parametro_id_cliente_retorna_400(self):
        view = PagosClientesViewSet.as_view({"get": "facturas_pendientes"})
        response = view(self._get("/api/v1/cobros/facturas_pendientes/"))
        assert response.status_code == 400
        assert "id_cliente" in str(response.data)

    def test_id_cliente_inexistente_retorna_404(self):
        view = PagosClientesViewSet.as_view({"get": "facturas_pendientes"})
        response = view(self._get("/api/v1/cobros/facturas_pendientes/", {"id_cliente": 99999}))
        assert response.status_code == 404

    def test_cliente_sin_facturas_pendientes_retorna_lista_vacia(self):
        view = PagosClientesViewSet.as_view({"get": "facturas_pendientes"})
        response = view(self._get("/api/v1/cobros/facturas_pendientes/", {"id_cliente": self.cliente.id_cliente}))
        assert response.status_code == 200
        assert response.data["resumen"]["cantidad_facturas"] == 0
        assert response.data["resumen"]["total_pendiente"] == 0

    def test_cliente_con_facturas_pendientes(self):
        _make_venta(self.cliente, self.empleado, monto=300_000, saldo=300_000)
        _make_venta(self.cliente, self.empleado, monto=200_000, saldo=200_000)

        view = PagosClientesViewSet.as_view({"get": "facturas_pendientes"})
        response = view(self._get("/api/v1/cobros/facturas_pendientes/", {"id_cliente": self.cliente.id_cliente}))

        assert response.status_code == 200
        assert response.data["resumen"]["cantidad_facturas"] == 2
        assert Decimal(str(response.data["resumen"]["total_pendiente"])) == Decimal("500000")

    def test_respuesta_incluye_datos_del_cliente(self):
        view = PagosClientesViewSet.as_view({"get": "facturas_pendientes"})
        response = view(self._get("/api/v1/cobros/facturas_pendientes/", {"id_cliente": self.cliente.id_cliente}))

        assert response.status_code == 200
        assert "nombre_completo" in response.data["cliente"]
        assert response.data["cliente"]["id_cliente"] == self.cliente.id_cliente


# ===========================================================================
# registrar_pago
# ===========================================================================

@pytest.mark.django_db
class TestRegistrarPago(CobrosBaseTest):

    def test_serializer_invalido_retorna_400(self):
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", {}))
        assert response.status_code == 400

    def test_monto_negativo_retorna_400(self):
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": -1000,
            "id_medio_pago": self.medio_pago.id_medio_pago,
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))
        assert response.status_code == 400

    def test_usuario_sin_empleado_retorna_400(self):
        user_sin_emp = User.objects.create_user(
            username="sin_empleado", email="sin_empleado@test.com", password="pass"
        )
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "aplicaciones": [{"id_venta": venta.id_venta, "monto_aplicado": "100000"}],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post_as("/api/v1/cobros/registrar_pago/", user_sin_emp, data))
        assert response.status_code == 400
        assert "empleado" in str(response.data).lower()

    def test_pago_con_aplicaciones_explicitas_retorna_201(self):
        venta = _make_venta(self.cliente, self.empleado, monto=300_000, saldo=300_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "300000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "referencia": "TRF-001",
            "aplicaciones": [{"id_venta": venta.id_venta, "monto_aplicado": "300000"}],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))

        assert response.status_code == 201
        assert PagosClientes.objects.count() == 1
        assert AplicacionPagosClientes.objects.count() == 1

        venta.refresh_from_db()
        assert venta.saldo_pendiente == Decimal("0.00")
        assert venta.estado_pago == "pagada"

    def test_pago_sin_aplicaciones_usa_fifo(self):
        v1 = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        v2 = _make_venta(self.cliente, self.empleado, monto=200_000, saldo=200_000)

        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "150000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))

        assert response.status_code == 201
        v1.refresh_from_db()
        v2.refresh_from_db()
        assert v1.saldo_pendiente == Decimal("0.00")
        assert v2.saldo_pendiente == Decimal("150000.00")

    def test_aplicacion_venta_sin_saldo_retorna_400(self):
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=0, estado_pago="pagada")
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "aplicaciones": [{"id_venta": venta.id_venta, "monto_aplicado": "100000"}],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))
        assert response.status_code == 400

    def test_aplicacion_excede_saldo_retorna_400(self):
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=50_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "aplicaciones": [{"id_venta": venta.id_venta, "monto_aplicado": "100000"}],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))
        assert response.status_code == 400

    def test_suma_aplicaciones_excede_monto_total_retorna_400(self):
        v1 = _make_venta(self.cliente, self.empleado, monto=300_000, saldo=300_000)
        v2 = _make_venta(self.cliente, self.empleado, monto=300_000, saldo=300_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "aplicaciones": [
                {"id_venta": v1.id_venta, "monto_aplicado": "100000"},
                {"id_venta": v2.id_venta, "monto_aplicado": "100000"},
            ],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))
        assert response.status_code == 400

    def test_venta_inexistente_en_aplicacion_retorna_400(self):
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": self.medio_pago.id_medio_pago,
            "aplicaciones": [{"id_venta": 99999, "monto_aplicado": "100000"}],
        }
        view = PagosClientesViewSet.as_view({"post": "registrar_pago"})
        response = view(self._post("/api/v1/cobros/registrar_pago/", data))
        assert response.status_code == 400


# ===========================================================================
# generar_qr_sipap
# ===========================================================================

@pytest.mark.django_db
class TestGenerarQrSipap(CobrosBaseTest):

    def test_sin_id_cliente_retorna_400(self):
        view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
        response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {}))
        assert response.status_code == 400
        assert "id_cliente" in str(response.data)

    def test_cliente_inexistente_retorna_404(self):
        view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
        response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {"id_cliente": 99999}))
        assert response.status_code == 404

    def test_cliente_sin_deuda_retorna_400(self):
        view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
        response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {"id_cliente": self.cliente.id_cliente}))
        assert response.status_code == 400
        assert "deuda" in str(response.data).lower()

    def test_monto_negativo_retorna_400(self):
        _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
        response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {
            "id_cliente": self.cliente.id_cliente, "monto": -1
        }))
        assert response.status_code == 400

    def _sipap_patch(self, return_value=None, side_effect=None):
        """Context manager that mocks the entire SIPAPService class."""
        mock_cls = MagicMock()
        if side_effect:
            mock_cls.return_value.generar_qr_dinamico.side_effect = side_effect
        else:
            mock_cls.return_value.generar_qr_dinamico.return_value = return_value
        return patch("apps.api_integrations.services.sipap_service.SIPAPService", mock_cls), mock_cls

    def test_sipap_falla_retorna_500_y_borra_pago(self):
        _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        pagos_antes = PagosClientes.objects.count()

        mock_cls = MagicMock()
        mock_cls.return_value.generar_qr_dinamico.side_effect = Exception("SIPAP timeout")

        with patch("apps.api_integrations.services.sipap_service.SIPAPService", mock_cls):
            view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
            response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {
                "id_cliente": self.cliente.id_cliente
            }))

        assert response.status_code == 500
        assert PagosClientes.objects.count() == pagos_antes

    def test_sipap_exitoso_retorna_200(self):
        _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        qr_mock = {
            "qr_image": "data:image/png;base64,abc123",
            "qr_string": "00020126...",
            "txn_id": "COB-999-1713308400",
            "expira_en": 900,
            "expira_at": "2026-05-11T15:00:00Z",
            "banco": "continental",
            "ambiente": "sandbox",
        }
        mock_cls = MagicMock()
        mock_cls.return_value.generar_qr_dinamico.return_value = qr_mock

        with patch("apps.api_integrations.services.sipap_service.SIPAPService", mock_cls):
            view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
            response = view(self._post("/api/v1/cobros/generar_qr_sipap/", {
                "id_cliente": self.cliente.id_cliente, "descripcion": "Pago test"
            }))

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["qr_data"]["txn_id"] == "COB-999-1713308400"
        assert "cliente" in response.data

    def test_descripcion_autogenerada_factura_unica(self):
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        qr_mock = {"txn_id": "COB-1-1234", "qr_image": "", "qr_string": "", "expira_en": 900}
        mock_cls = MagicMock()
        mock_cls.return_value.generar_qr_dinamico.return_value = qr_mock

        with patch("apps.api_integrations.services.sipap_service.SIPAPService", mock_cls):
            view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
            view(self._post("/api/v1/cobros/generar_qr_sipap/", {"id_cliente": self.cliente.id_cliente}))

        _, kwargs = mock_cls.return_value.generar_qr_dinamico.call_args
        assert str(venta.id_venta) in kwargs.get("descripcion", "")

    def test_descripcion_autogenerada_multiples_facturas(self):
        _make_venta(self.cliente, self.empleado, monto=50_000, saldo=50_000)
        _make_venta(self.cliente, self.empleado, monto=50_000, saldo=50_000)
        qr_mock = {"txn_id": "COB-1-1234", "qr_image": "", "qr_string": "", "expira_en": 900}
        mock_cls = MagicMock()
        mock_cls.return_value.generar_qr_dinamico.return_value = qr_mock

        with patch("apps.api_integrations.services.sipap_service.SIPAPService", mock_cls):
            view = PagosClientesViewSet.as_view({"post": "generar_qr_sipap"})
            view(self._post("/api/v1/cobros/generar_qr_sipap/", {"id_cliente": self.cliente.id_cliente}))

        _, kwargs = mock_cls.return_value.generar_qr_dinamico.call_args
        assert "facturas" in kwargs.get("descripcion", "").lower()


# ===========================================================================
# CRUD estándar (ModelViewSet)
# ===========================================================================

@pytest.mark.django_db
class TestCobrosListCreate(CobrosBaseTest):

    def test_lista_pagos_vacia(self):
        view = PagosClientesViewSet.as_view({"get": "list"})
        response = view(self._get("/api/v1/cobros/"))
        assert response.status_code == 200

    def test_lista_pagos_con_registros(self):
        PagosClientes.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("100000"),
            id_medio_pago=self.medio_pago,
            id_empleado_cajero=self.empleado,
            estado="Confirmado",
        )
        view = PagosClientesViewSet.as_view({"get": "list"})
        response = view(self._get("/api/v1/cobros/"))
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_detalle_pago(self):
        pago = PagosClientes.objects.create(
            id_cliente=self.cliente,
            monto_total=Decimal("100000"),
            id_medio_pago=self.medio_pago,
            id_empleado_cajero=self.empleado,
            estado="Confirmado",
        )
        view = PagosClientesViewSet.as_view({"get": "retrieve"})
        response = view(self._get(f"/api/v1/cobros/{pago.id_pago_cliente}/"), pk=pago.id_pago_cliente)
        assert response.status_code == 200
        assert response.data["monto_total"] == "100000.00"


# ===========================================================================
# Serializer unit tests
# ===========================================================================

@pytest.mark.django_db
class TestRegistrarPagoSerializer:

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.rol = _make_rol()
        self.empleado = _make_empleado(self.rol, "ser")
        self.cliente = _make_cliente("ser")

    def test_aplicacion_con_campos_faltantes_invalida(self):
        from apps.cobros.serializers import RegistrarPagoSerializer

        medio = _make_medio_pago("Transferencia")
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": medio.id_medio_pago,
            "aplicaciones": [{"id_venta": venta.id_venta}],  # falta monto_aplicado
        }
        s = RegistrarPagoSerializer(data=data)
        assert not s.is_valid()
        assert "aplicaciones" in s.errors

    def test_aplicacion_monto_negativo_invalida(self):
        from apps.cobros.serializers import RegistrarPagoSerializer

        medio = _make_medio_pago("Cheque")
        venta = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        data = {
            "id_cliente": self.cliente.id_cliente,
            "monto_total": "100000",
            "id_medio_pago": medio.id_medio_pago,
            "aplicaciones": [{"id_venta": venta.id_venta, "monto_aplicado": "-1"}],
        }
        s = RegistrarPagoSerializer(data=data)
        assert not s.is_valid()


# ===========================================================================
# _aplicar_automatico unit tests
# ===========================================================================

@pytest.mark.django_db
class TestAplicarAutomatico:

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.rol = _make_rol()
        self.empleado = _make_empleado(self.rol, "auto")
        self.cliente = _make_cliente("auto")
        self.vs = PagosClientesViewSet()

    def test_sin_facturas_pendientes_retorna_lista_vacia(self):
        resultado = self.vs._aplicar_automatico(self.cliente.id_cliente, Decimal("100000"))
        assert resultado == []

    def test_monto_cubre_primera_factura_completamente(self):
        v1 = _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        _make_venta(self.cliente, self.empleado, monto=200_000, saldo=200_000)

        resultado = self.vs._aplicar_automatico(self.cliente.id_cliente, Decimal("100000"))
        assert len(resultado) == 1
        assert resultado[0]["id_venta"] == v1.id_venta
        assert float(resultado[0]["monto_aplicado"]) == 100_000.0

    def test_monto_parcial_en_primera_factura(self):
        _make_venta(self.cliente, self.empleado, monto=200_000, saldo=200_000)

        resultado = self.vs._aplicar_automatico(self.cliente.id_cliente, Decimal("50000"))
        assert len(resultado) == 1
        assert float(resultado[0]["monto_aplicado"]) == 50_000.0

    def test_monto_cubre_multiples_facturas(self):
        _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)
        _make_venta(self.cliente, self.empleado, monto=100_000, saldo=100_000)

        resultado = self.vs._aplicar_automatico(self.cliente.id_cliente, Decimal("200000"))
        assert len(resultado) == 2
