"""
Tests para alcanzar 100% cobertura en apps/reportes/views.py

Líneas faltantes:
- 225-260: reporte_consumos_hijo validaciones y errores
- 489-517: TareasProgramadasViewSet.list
- 524-545: TareasProgramadasViewSet.partial_update
"""
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.clientes.models import Hijos, Clientes, TiposCliente
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Roles, Empleados


class ReporteConsumosHijoValidacionTest(TestCase):
    """Test validación de parámetros en reporte_consumos_hijo (líneas 225-260)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_parametros_faltantes_retorna_400(self):
        """Línea 231-234: Returns 400 when required params are missing."""
        url = reverse("reportes-reporte-consumos-hijo")
        
        # Sin parámetros
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("requeridos", str(response.data["error"]))

        # Solo id_hijo
        response = self.client.get(url, {"id_hijo": "1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Solo id_hijo y fecha_inicio
        response = self.client.get(url, {"id_hijo": "1", "fecha_inicio": "2026-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_id_hijo_no_entero_retorna_400(self):
        """Línea 237-241: Returns 400 when id_hijo is not an integer."""
        url = reverse("reportes-reporte-consumos-hijo")
        response = self.client.get(url, {
            "id_hijo": "abc",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-01-31"
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("número entero", str(response.data["error"]))

    def test_fecha_invalida_retorna_400(self):
        """Línea 246-250: Returns 400 when date format is invalid."""
        url = reverse("reportes-reporte-consumos-hijo")
        
        # Fecha inválida en fecha_inicio
        response = self.client.get(url, {
            "id_hijo": "1",
            "fecha_inicio": "invalid-date",
            "fecha_fin": "2026-01-31"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Formato de fecha inválido", str(response.data["error"]))

        # Fecha inválida en fecha_fin
        response = self.client.get(url, {
            "id_hijo": "1",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "not-a-date"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Formato de fecha inválido", str(response.data["error"]))

    @patch("apps.reportes.views.ReporteService.generar_reporte_consumos_hijo")
    def test_exception_general_retorna_500(self, mock_service):
        """Línea 258-259: Returns 500 on general Exception."""
        mock_service.side_effect = Exception("Database connection failed")
        
        url = reverse("reportes-reporte-consumos-hijo")
        response = self.client.get(url, {
            "id_hijo": "1",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-01-31"
        })
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertIn("Database connection failed", str(response.data["error"]))


class TareasProgramadasViewSetTest(TestCase):
    """Test TareasProgramadasViewSet methods (líneas 489-517, 524-545)."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("django_celery_beat.models.PeriodicTask")
    def test_list_tareas_programadas_success(self, mock_periodic_task):
        """Líneas 489-517: List periodic tasks with crontab details."""
        # Mock task con crontab
        mock_cron = Mock()
        mock_cron.id = 1
        mock_cron.minute = "0"
        mock_cron.hour = "*/6"
        mock_cron.day_of_week = "*"
        mock_cron.day_of_month = "*"
        mock_cron.month_of_year = "*"

        mock_task = Mock()
        mock_task.id = 1
        mock_task.name = "test-task"
        mock_task.task = "apps.core.tasks.test"
        mock_task.enabled = True
        mock_task.last_run_at = None
        mock_task.total_run_count = 0
        mock_task.crontab = mock_cron

        mock_periodic_task.objects.select_related.return_value.order_by.return_value = [mock_task]

        url = reverse("tareas-programadas-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "test-task")
        self.assertEqual(response.data[0]["crontab"]["minute"], "0")

    @patch("django_celery_beat.models.PeriodicTask")
    def test_list_tareas_exception_retorna_500(self, mock_periodic_task):
        """Línea 515-516: Returns 500 on exception in list."""
        mock_periodic_task.objects.select_related.side_effect = Exception("DB error")

        url = reverse("tareas-programadas-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)

    @patch("django_celery_beat.models.PeriodicTask")
    def test_partial_update_enabled_field(self, mock_periodic_task):
        """Líneas 524-545: Update task enabled status."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.enabled = False
        mock_periodic_task.objects.get.return_value = mock_task

        url = reverse("tareas-programadas-detail", kwargs={"pk": 1})
        response = self.client.patch(url, {"enabled": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertTrue(mock_task.enabled)
        mock_task.save.assert_called_once_with(update_fields=["enabled"])

    @patch("django_celery_beat.models.PeriodicTask")
    def test_partial_update_crontab_fields(self, mock_periodic_task):
        """Líneas 533-539: Update crontab schedule."""
        mock_cron = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.enabled = True
        mock_task.crontab = mock_cron
        mock_periodic_task.objects.get.return_value = mock_task

        url = reverse("tareas-programadas-detail", kwargs={"pk": 1})
        response = self.client.patch(url, {
            "minute": "*/15",
            "hour": "8-17"
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_cron.minute, "*/15")
        self.assertEqual(mock_cron.hour, "8-17")
        mock_cron.save.assert_called_once()

    @patch("django_celery_beat.models.PeriodicTask")
    def test_partial_update_task_not_found(self, mock_periodic_task):
        """Línea 541-542: Returns 404 when task not found."""
        from django_celery_beat.models import PeriodicTask as PT
        mock_periodic_task.DoesNotExist = PT.DoesNotExist
        mock_periodic_task.objects.get.side_effect = PT.DoesNotExist()

        url = reverse("tareas-programadas-detail", kwargs={"pk": 999})
        response = self.client.patch(url, {"enabled": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self.assertIn("no encontrada", str(response.data["detail"]))

    @patch("django_celery_beat.models.PeriodicTask")
    def test_partial_update_exception_retorna_400(self, mock_periodic_task):
        """Línea 543-544: Returns 400 on general exception."""
        mock_periodic_task.objects.get.side_effect = Exception("Invalid data")

        url = reverse("tareas-programadas-detail", kwargs={"pk": 1})
        response = self.client.patch(url, {"enabled": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
