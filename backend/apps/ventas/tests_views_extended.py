"""
Tests extendidos para apps/ventas/views.py
Cubre: NotasCreditoClienteViewSet custom actions, PromocionesViewSet custom actions
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.ventas.models import Promociones
from apps.ventas.views import (
    NotasCreditoClienteViewSet,
    PromocionesViewSet,
)


def make_user(username="ventastest"):
    return User.objects.get_or_create(username=username, defaults={"password": "x"})[0]


# ==================== NotasCreditoClienteViewSet ====================


class NotasCreditoClienteCrearDevolucionTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("nc_user")
        patcher = patch("apps.common.permissions.CanManageVentas.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_crear_devolucion_sin_campos_requeridos(self):
        view = NotasCreditoClienteViewSet.as_view({"post": "crear_devolucion"})
        request = self.factory.post("/notas-credito/crear_devolucion/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_crear_devolucion_sin_id_venta(self):
        view = NotasCreditoClienteViewSet.as_view({"post": "crear_devolucion"})
        data = {"productos": [{"id_producto": 1, "cantidad": 1}]}
        request = self.factory.post("/notas-credito/crear_devolucion/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_devolucion_sin_empleado_asociado(self):
        """Usuario sin empleado asociado debe recibir 400"""
        view = NotasCreditoClienteViewSet.as_view({"post": "crear_devolucion"})
        data = {
            "id_venta": 1,
            "productos": [{"id_producto": 1, "cantidad": 1}],
        }
        request = self.factory.post("/notas-credito/crear_devolucion/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("apps.ventas.views.DevolucionService.crear_nota_credito")
    def test_crear_devolucion_exitosa(self, mock_crear):
        """Con empleado asociado y servicio exitoso, devuelve 201"""
        mock_nota = MagicMock()
        mock_crear.return_value = {
            "nota_credito": mock_nota,
            "monto_devuelto": Decimal("50000"),
            "mensaje": "Devolución creada exitosamente",
        }
        self.user.empleado = MagicMock()

        view = NotasCreditoClienteViewSet.as_view({"post": "crear_devolucion"})
        with patch.object(NotasCreditoClienteViewSet, "get_serializer") as mock_ser:
            mock_ser.return_value.data = {"id_nota": 1}
            data = {
                "id_venta": 1,
                "productos": [{"id_producto": 1, "cantidad": 1}],
                "motivo": "Producto defectuoso",
            }
            request = self.factory.post("/notas-credito/crear_devolucion/", data, format="json")
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["exito"])

    @patch("apps.ventas.views.DevolucionService.crear_nota_credito")
    def test_crear_devolucion_con_validation_error(self, mock_crear):
        """Si el servicio lanza ValidationError, devuelve 400"""
        mock_crear.side_effect = ValidationError({"error": "Venta no disponible"})
        self.user.empleado = MagicMock()

        view = NotasCreditoClienteViewSet.as_view({"post": "crear_devolucion"})
        data = {
            "id_venta": 999,
            "productos": [{"id_producto": 1, "cantidad": 1}],
        }
        request = self.factory.post("/notas-credito/crear_devolucion/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotasCreditoClienteValidarDevolucionTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("vd_user")
        patcher = patch("apps.common.permissions.CanManageVentas.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch("apps.ventas.views.DevolucionService.validar_productos_devolucion")
    def test_validar_devolucion_exitosa(self, mock_validar):
        mock_validar.return_value = {"valido": True, "productos": []}
        view = NotasCreditoClienteViewSet.as_view({"post": "validar_devolucion"})
        data = {"id_venta": 1, "productos": [{"id_producto": 1, "cantidad": 1}]}
        request = self.factory.post("/notas-credito/validar_devolucion/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valido"])


class NotasCreditoClienteAnularTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("an_user")
        patcher = patch("apps.common.permissions.CanManageVentas.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_anular_sin_motivo(self):
        view = NotasCreditoClienteViewSet.as_view({"post": "anular"})
        request = self.factory.post("/notas-credito/1/anular/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.ventas.views.DevolucionService.anular_nota_credito")
    def test_anular_exitoso(self, mock_anular):
        mock_anular.return_value = {"success": True, "mensaje": "Anulada"}
        self.user.empleado = MagicMock()
        view = NotasCreditoClienteViewSet.as_view({"post": "anular"})
        data = {"motivo_anulacion": "Error en registro"}
        request = self.factory.post("/notas-credito/1/anular/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.ventas.views.DevolucionService.anular_nota_credito")
    def test_anular_con_error(self, mock_anular):
        mock_anular.side_effect = ValidationError({"error": "No se puede anular"})
        view = NotasCreditoClienteViewSet.as_view({"post": "anular"})
        data = {"motivo_anulacion": "Error"}
        request = self.factory.post("/notas-credito/1/anular/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ==================== PromocionesViewSet ====================


class PromocionesViewSetValidarCodigoTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("promo_user")
        patcher = patch("apps.common.permissions.IsAdminOrReadOnly.has_permission", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_validar_codigo_sin_codigo(self):
        view = PromocionesViewSet.as_view({"post": "validar_codigo"})
        request = self.factory.post("/promociones/validar_codigo/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.ventas.views.PromocionService.obtener_promociones_aplicables")
    def test_validar_codigo_no_encontrado(self, mock_obtener):
        mock_obtener.return_value = []
        view = PromocionesViewSet.as_view({"post": "validar_codigo"})
        data = {"codigo_promocion": "INVALIDO", "monto_total": 50000, "productos": []}
        request = self.factory.post("/promociones/validar_codigo/", data, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["valido"])

    @patch("apps.ventas.views.PromocionService.calcular_descuento")
    @patch("apps.ventas.views.PromocionService.obtener_promociones_aplicables")
    def test_validar_codigo_valido(self, mock_obtener, mock_calcular):
        mock_promo = MagicMock()
        mock_promo.nombre = "VERANO2026"
        mock_promo.id_promocion = 1
        mock_obtener.return_value = [{"promocion": mock_promo}]
        mock_calcular.return_value = {
            "monto_descuento": Decimal("5000"),
            "tipo_descuento": "porcentaje",
            "descripcion": "10% desc",
            "productos_afectados": [],
        }
        view = PromocionesViewSet.as_view({"post": "validar_codigo"})
        with patch.object(PromocionesViewSet, "get_serializer") as mock_ser:
            mock_ser.return_value.data = {"id_promocion": 1}
            data = {"codigo_promocion": "VERANO2026", "monto_total": 50000, "productos": []}
            request = self.factory.post("/promociones/validar_codigo/", data, format="json")
            force_authenticate(request, user=self.user)
            response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valido"])


class PromocionesViewSetActivasTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("activas_user")

    def test_get_activas(self):
        """Debe retornar lista de promociones activas"""
        # Create a promotion
        Promociones.objects.create(
            nombre="Promo Test",
            tipo_promocion="porcentaje",
            valor_descuento=Decimal("10"),
            estado=True,
            fecha_inicio=date.today(),
            aplica_a="todos",
            min_cantidad=1,
            monto_minimo=Decimal("0"),
            usos_actuales=0,
            prioridad=1,
            fecha_creacion=timezone.now(),
        )
        view = PromocionesViewSet.as_view({"get": "activas"})
        request = self.factory.get("/promociones/activas/")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("promociones", response.data)


class PromocionesViewSetReporteTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = make_user("reporte_user")

    def test_reporte_efectividad_sin_fechas(self):
        view = PromocionesViewSet.as_view({"get": "reporte_efectividad"})
        request = self.factory.get("/promociones/reporte_efectividad/")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reporte_efectividad_con_fechas(self):
        view = PromocionesViewSet.as_view({"get": "reporte_efectividad"})
        request = self.factory.get(
            "/promociones/reporte_efectividad/",
            {
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-12-31",
            },
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resumen", response.data)

    def test_mas_usadas(self):
        view = PromocionesViewSet.as_view({"get": "mas_usadas"})
        request = self.factory.get("/promociones/mas_usadas/", {"limite": "5"})
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ranking", response.data)

    def test_historico_uso_sin_fechas(self):
        view = PromocionesViewSet.as_view({"get": "historico_uso"})
        request = self.factory.get("/promociones/historico_uso/")
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_historico_uso_mensual(self):
        view = PromocionesViewSet.as_view({"get": "historico_uso"})
        request = self.factory.get(
            "/promociones/historico_uso/",
            {
                "periodo": "mensual",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-12-31",
            },
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["periodo"], "mensual")

    def test_historico_uso_semanal(self):
        view = PromocionesViewSet.as_view({"get": "historico_uso"})
        request = self.factory.get(
            "/promociones/historico_uso/",
            {
                "periodo": "semanal",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-03-01",
            },
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["periodo"], "semanal")

    def test_historico_uso_diario(self):
        view = PromocionesViewSet.as_view({"get": "historico_uso"})
        request = self.factory.get(
            "/promociones/historico_uso/",
            {
                "periodo": "diario",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-01-31",
            },
        )
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["periodo"], "diario")
